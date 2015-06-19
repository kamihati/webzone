#coding: utf-8
'''
Created on 2014年8月25日

@author: Administrator
'''
from django.core.cache import cache
from django.db import connections
import json
from utils.decorator import login_required

from math import ceil

from gateway import SuccessResponse, FailResponse


from WebZone.conf import DOU_RES_HOST
from WebZone.conf import DOU_VIDEO_STREAM_HOST

def has_perm(res_code):
    """
        判断当前登录用户，有没有当前视频类型的权限
    """
    return True


def get_catalog_dict(classify_id=1):
    """
    classify_id:分类法ID，1类别
    2:年龄段
    这个放缓存里避免过频请求
    """
    cache_key = "gateway.get_catalog_dict.%d" % classify_id
    catalog_dict = cache.get(cache_key, {})

    if not catalog_dict:
        cursor = connections['KidsLibrarySystem'].cursor()
        if classify_id == 1:
            sql = "select Res_Id,Res_Name,Res_Code,Res_Parent from Res_Class WHERE Res_MetaId=%s ORDER BY Res_Parent, Res_Id" % classify_id
        else:
            sql = "select Res_Id,Res_Name,Res_Code,Res_Parent from Res_Class WHERE Res_MetaId=%s ORDER BY Res_Id" % classify_id
            #print sql
        cursor.execute(sql)
        rows = cursor.fetchall()
        #print len(rows)
        for row in rows:
            if not row or not row[0]: continue
            res_id = int(row[0])
            #print res_id
            res_name = row[1]
            res_code = row[2]
            res_type = res_type_by_code(res_code)   #video, game, book
            res_parent = int(row[3])
            catalog_dict[res_id] = {"class_id":res_id, "name":res_name, "type":res_type, "parent_id":res_parent}
        cache.set(cache_key, catalog_dict)

    #print catalog_dict
    return catalog_dict

@login_required
def get_3qdou_catalog(request, param):
    if param.has_key("classify_id"): classify_id = int(param.classify_id)
    else: classify_id = 1

    catalog_dict = get_catalog_dict(classify_id)    #所到所有的列表
    if classify_id == 2:    #按年龄分类
        return SuccessResponse(catalog_dict.values())

    auth_3qdou_list = ""
    if request.user.library:
        auth_3qdou_list = request.user.library.auth_3qdou_list
        #print auth_3qdou_list
    if not auth_3qdou_list:
        return FailResponse(u"没有可用的资源")
    catalog_list = []
    id_list = []
    for auth_id in auth_3qdou_list.split(','):
        auth_id = int(auth_id)
        if catalog_dict.has_key(auth_id):
            id_list.append(auth_id)
            catalog_list.append({"class_id":auth_id, "name":catalog_dict[auth_id]['name'], "type":catalog_dict[auth_id]['type'], "parent":catalog_dict[auth_id]['parent_id']})
            parent_id = catalog_dict[auth_id]['parent_id']
            while parent_id and id_list.count(parent_id) == 0:
                catalog_list.append({"class_id":parent_id, "name":catalog_dict[parent_id]['name'], "type":catalog_dict[auth_id]['type'], "parent":catalog_dict[parent_id]['parent_id']})
                id_list.append(parent_id)
                parent_id = catalog_dict[parent_id]['parent_id']
            
    return SuccessResponse(catalog_list)


def get_code_by_id(class_id):
    cursor = connections['KidsLibrarySystem'].cursor()
    sql = "select Res_Id,Res_Name,Res_Code,Res_Parent,Res_Type from Res_Class WHERE Res_Id=%s" % class_id
    cursor.execute(sql)
    row = cursor.fetchone()
    if row and row[0]: res_code = row[2]
    else: res_code = None
    cursor.close()
    return res_code

# View_AllResQuery    Res_Category
# 2:/Upload/Book/    images/video.gif
# 3:/Upload/Game/    images/game.gif
# 4:/Upload/Music/    images/music.gif
# 6:/Upload/Video/    images/video.gif
def res_type_by_code(res_code):
    if not res_code: return None
    first_letter = res_code[0].upper()
    if first_letter in ("A","B","C","D","E"):
        return "video"
    elif first_letter in ("F"):
        return "game"
    elif first_letter in ("G"):
        return "book"
    else:
        return "unknown"
    
def get_video_url(request, video_title, extension, guid):
    #print video_title, extension, extension.lower == "flv", guid
    if extension.lower() == "flv":
        return request.build_absolute_uri("/3qdou_video/?title=" + video_title)
        #return "http://v.3qdou.com/ResourceList/video.aspx?title=" + video_title
    else:
        cursor = connections['KidsLibrarySystem'].cursor()
        sql = "select Res_Path from Res_VideosItem where Res_MetaId='%s'" % guid
        cursor.execute(sql)
        row = cursor.fetchone()
        path = ""
        if row and row[0]: path = row[0]
        cursor.close()
        if path:
            return DOU_RES_HOST + "/ResourceList/video/" + path
        else: return u"资源文件不存在，请联系管理员"
        
        
def get_game_url(request, video_title, extension, guid):
    if extension.lower() == "flv":
        return request.build_absolute_uri("/3qdou_video/?title=" + video_title)
        #return "http://v.3qdou.com/ResourceList/video.aspx?title=" + video_title
    else:
        cursor = connections['KidsLibrarySystem'].cursor()
        sql = "select Res_Path from Res_GameItem where Res_MetaId='%s'" % guid
        cursor.execute(sql)
        row = cursor.fetchone()
        path = ""
        if row and row[0]: path = row[0]
        cursor.close()
        if path:
            return DOU_RES_HOST + "/ResourceList/game/" + path
        else: return u"资源文件不存在，请联系管理员"                


@login_required
def get_video_list(request, param):
    """
        得到3qdou的视频列表
    """
    if param.has_key("class_id"): class_id = int(param.class_id)
    else: class_id = None
    if param.has_key("class_id2"): class_id2 = int(param.class_id2)
    else: class_id2 = None
    
    if param.has_key("page_index"): page_index = int(param.page_index)
    else: page_index = 1
    if param.has_key("page_size"): page_size = int(param.page_size)
    else: page_size = 15
    
    where_clause = ""
    if class_id:
        res_code = get_code_by_id(class_id)
        res_type = res_type_by_code(res_code)
        if res_type <> "video":
            return FailResponse(u"错误的请求(id:%s)(type:%s)" % (class_id, res_type))
        where_clause = "Res_Type LIKE '%%%s%%'" % res_code
    if class_id2:
        res_code2 = get_code_by_id(class_id2)
        #print res_code2, type(res_code2), res_code2.encode('utf-8')
        where_clause += " and Res_Type LIKE '%%%s%%'" % res_code2 if where_clause else "Res_Type LIKE '%%%s%%'" % res_code2
    
    cursor = connections['KidsLibrarySystem'].cursor()
    if where_clause:
        sql = "select count(*) from Res_Videos where %s" % where_clause
    else:
        sql = "select count(*) from Res_Videos"
    cursor.execute(sql.encode('utf-8'))
    row = cursor.fetchone()
    #print row
    count = 0
    if row: count = row[0]
    page_count = int(ceil(count/float(page_size)))
    
    sql = "select top %s Res_id,Res_Guid,Res_Title,Res_SeriesName,Res_Lable,Res_Description,Res_FacePath,Res_Extension from Res_Videos" % page_size
    if where_clause:
        sql += " where Res_id not in (select top %s Res_id from Res_Videos where %s) and %s" % ((page_index-1)*page_size, where_clause, where_clause)
    else:
        sql += " where Res_id not in (select top %s Res_id from Res_Videos)" % ((page_index-1)*page_size)
    #print sql
    cursor.execute(sql.encode('utf-8'))
    rows = cursor.fetchall()
    video_list = []
    for row in rows:
        if not row: continue
        id = row[0]
        guid = row[1]
        title = row[2]
        series_name = row[3]
        label = row[4]
        description = row[5]
        face_path = row[6]
        extension = row[7]
        video_dict = {"id":id, "guid":guid, "title":title, "series_name":series_name, "label":label, "description":description, "publisher":""}
        video_dict["thumbnail"] = DOU_RES_HOST + "/Upload/Video/" + face_path
        video_dict["url"] = get_video_url(request, title, extension, guid)
        video_list.append(video_dict)
    cursor.close()
    
    return SuccessResponse({"data":video_list, "page_index": page_index, "page_count": page_count})



@login_required
def get_game_list(request, param):
    """
        得到3qdou的游戏、娱乐列表
    """
    if param.has_key("class_id"): class_id = int(param.class_id)
    else: class_id = None
    if param.has_key("class_id2"): class_id2 = int(param.class_id2)
    else: class_id2 = None
    
    if param.has_key("page_index"): page_index = int(param.page_index)
    else: page_index = 1
    if param.has_key("page_size"): page_size = int(param.page_size)
    else: page_size = 15
    
    where_clause = ""
    if class_id:
        res_code = get_code_by_id(class_id)
        res_type = res_type_by_code(res_code)
        if res_type <> "game":
            return FailResponse(u"错误的请求(id:%s)(type:%s)" % (class_id, res_type))
        where_clause = "Res_Type LIKE '%%%s%%'" % res_code
    if class_id2:
        res_code2 = get_code_by_id(class_id2)
        where_clause += " and Res_Type LIKE '%%%s%%'" % res_code2 if where_clause else "Res_Type LIKE '%%%s%%'" % res_code2
    
    cursor = connections['KidsLibrarySystem'].cursor()
    if where_clause:
        sql = "select count(*) from Res_Game where %s" % where_clause
    else:
        sql = "select count(*) from Res_Game"
    #print sql
    cursor.execute(sql.encode('utf-8'))
    row = cursor.fetchone()
    count = 0
    if row: count = row[0]
    page_count = int(ceil(count/float(page_size)))
    
    sql = "select top %s Res_id,Res_Guid,Res_Title,Res_SeriesName,Res_Lable,Res_Description,Res_FacePath,Res_Extension from Res_Game" % page_size
    if where_clause:
        sql += " where Res_id not in (select top %s Res_id from Res_Game where %s) and %s" % ((page_index-1)*page_size, where_clause, where_clause) 
    else:
        sql += " where Res_id not in (select top %s Res_id from Res_Game)" % ((page_index-1)*page_size)
    #print sql
    cursor.execute(sql.encode('utf-8'))
    rows = cursor.fetchall()
    video_list = []
    for row in rows:
        if not row: continue
        id = row[0]
        guid = row[1]
        title = row[2]
        series_name = row[3]
        label = row[4]
        description = row[5]
        face_path = row[6]
        extension = row[7]
        video_dict = {"id":id, "guid":guid, "title":title, "series_name":series_name, "label":label, "description":description, "publisher":""}
        video_dict["thumbnail"] = DOU_RES_HOST + "/Upload/Game/" + face_path
        video_dict["url"] = get_game_url(request, title, extension, guid)
        video_list.append(video_dict)
    cursor.close()
    
    return SuccessResponse({"data":video_list, "page_index": page_index, "page_count": page_count})



@login_required
def get_book_list(request, param):
    """
        得到3qdou的图书列表
    """
    if param.has_key("class_id"): class_id = int(param.class_id)
    else: class_id = None
    if param.has_key("class_id2"): class_id2 = int(param.class_id2)
    else: class_id2 = None
    
    if param.has_key("page_index"): page_index = int(param.page_index)
    else: page_index = 1
    if param.has_key("page_size"): page_size = int(param.page_size)
    else: page_size = 15

    where_clause = ""
    if class_id:
        res_code = get_code_by_id(class_id)
        res_type = res_type_by_code(res_code)
        if res_type <> "book":
            return FailResponse(u"错误的请求(id:%s)(type:%s)" % (class_id, res_type))
        where_clause = "Res_Type LIKE '%%%s%%'" % res_code
    if class_id2:
        res_code2 = get_code_by_id(class_id2)
        where_clause += " and Res_Type LIKE '%%%s%%'" % res_code2 if where_clause else "Res_Type LIKE '%%%s%%'" % res_code2
    
    cursor = connections['KidsLibrarySystem'].cursor()
    if where_clause:
        sql = "select count(*) from Res_Books where %s" % where_clause
    else:
        sql = "select count(*) from Res_Books"
    #print sql
    cursor.execute(sql.encode('utf-8'))
    row = cursor.fetchone()
    count = 0
    if row: count = row[0]
    page_count = int(ceil(count/float(page_size)))
    
    sql = "select top %s Res_id,Res_Guid,Res_Title,Res_SeriesTitle,Res_Label,Res_Abstract,Res_Publisher,Res_FacePath from Res_Books" % page_size
    if where_clause:
        sql += " where Res_id not in (select top %s Res_id from Res_Books where %s) and %s" % ((page_index-1)*page_size, where_clause, where_clause)
    else:
        sql = sql + " where Res_id not in (select top %s Res_id from Res_Books)" % ((page_index-1)*page_size)
    #print sql
    cursor.execute(sql.encode('utf-8'))
    rows = cursor.fetchall()
    video_list = []
    for row in rows:
        if not row: continue
        id = row[0]
        guid = row[1]
        title = row[2]
        series_name = row[3]
        label = row[4]
        abstract = row[5]
        publisher = row[6]
        face_path = row[7]
        video_dict = {"id":id, "guid":guid, "title":title, "series_name":series_name, "label":label, "description":abstract, "publisher":publisher}
        video_dict["thumbnail"] = DOU_RES_HOST + "/Upload/Book/" + face_path
        video_dict["url"] = "/3qdou_book/?guid=" + guid
        video_list.append(video_dict)
    cursor.close()
    
    return SuccessResponse({"data":video_list, "page_index": page_index, "page_count": page_count})


@login_required
def get_all_list(request, param):
    """
        得到3qdou的所有资源列表
    """
    if param.has_key("class_id"): class_id = int(param.class_id)
    else: class_id = 659

    if class_id:
        res_code = get_code_by_id(class_id)
        res_type = res_type_by_code(res_code)
        if res_type == "video":
            return get_video_list(request, param)
        elif res_type == "game":
            return get_game_list(request, param)
        elif res_type == "book":
            return get_book_list(request, param)
        else:
            return FailResponse(u"错误的请求(class_id:%d)，不存在的类型:%s" % (class_id, res_type))
    
    if param.has_key("class_id2"): class_id2 = int(param.class_id2)
    else: class_id2 = None
    
    if param.has_key("page_index"): page_index = int(param.page_index)
    else: page_index = 1
    if param.has_key("page_size"): page_size = int(param.page_size)
    else: page_size = 15

    where_clause = ""
    if class_id2:
        res_code2 = get_code_by_id(class_id2)
        where_clause ="Res_Type LIKE '%%%s%%'" % res_code2

    cursor = connections['KidsLibrarySystem'].cursor()
    if where_clause:
        sql = "select count(*) from View_allResQuery where %s" % where_clause
    else:
        sql = "select count(*) from View_allResQuery"
    cursor.execute(sql)
    row = cursor.fetchone()
    count = 0
    if row: count = row[0]
    page_count = int(ceil(count/float(page_size)))
    
    sql = "select top %s Res_Category,Res_Guid,Res_Title,Res_SeriesName,Res_Lable,Res_Description,Res_Publisher,Res_FacePath,Res_Extension from View_allResQuery" % page_size
    if where_clause:
        sql += " where Res_Guid not in (select top %s Res_Guid from View_allResQuery where %s) and %s" % ((page_index-1)*page_size, where_clause, where_clause)
    else:
        sql += " where Res_Guid not in (select top %s Res_Guid from View_allResQuery)" % ((page_index-1)*page_size)
    #print sql
    cursor.execute(sql)
    rows = cursor.fetchall()
    video_list = []
    for row in rows:
        if not row: continue
        category_id = int(row[0])
        guid = row[1]
        title = row[2]
        series_name = row[3]
        label = row[4]
        description = row[5]
        publisher = row[6]
        face_path = row[7]
        extension = row[8]
        video_dict = {"guid":guid, "title":title, "series_name":series_name, "label":label, "description":description, "publisher":publisher}
        #Res_Article: 1
        #Res_Books: 2
        #Res_Game: 3
        #Res_Music: 4
        #Res_Picture: 5
        #Res_Video: 6
        if category_id == 2:
            video_dict["thumbnail"] = DOU_RES_HOST + "/Upload/Book/" + face_path
            video_dict["url"] = "/3qdou_book/?guid=" + guid
        elif category_id == 3:
            video_dict["thumbnail"] = DOU_RES_HOST + "/Upload/Game/" + face_path
            video_dict["url"] = get_game_url(request, title, extension, guid)
        elif category_id == 6:
            video_dict["thumbnail"] = DOU_RES_HOST + "/Upload/Video/" + face_path
            video_dict["url"] = get_video_url(request, title, extension, guid)
        video_list.append(video_dict)
    cursor.close()
    
    return SuccessResponse({"data":video_list, "page_index": page_index, "page_count": page_count})


@login_required
def search_res_list(request, param):
    """
        搜索所有的可用的资源
    """
    if param.has_key("search_text"): search_text = param.search_text.lower()
    else: search_text = ""

    if len(search_text) == 0: return FailResponse(u"请输入搜索项")

    if param.has_key("type_name"): type_name = param.type_name.lower()
    else: type_name = 'all'
    if type_name not in ('all', 'video', 'game', 'book'):
        return FailResponse(u"错误的搜索类型:%s" % type_name)
    
    if param.has_key("page_index"): page_index = int(param.page_index)
    else: page_index = 1
    if param.has_key("page_size"): page_size = int(param.page_size)
    else: page_size = 15
    
    cursor = connections['KidsLibrarySystem'].cursor()
    where_clause ="Res_Title LIKE '%%%s%%'" % search_text

    if type_name == 'all':
        sql = "select count(*) from View_allResQuery where %s" % where_clause
    elif type_name == 'video':
        sql = "select count(*) from Res_Videos where %s" % where_clause
    elif type_name == 'game':
        sql = "select count(*) from Res_Game where %s" % where_clause
    elif type_name == 'book':
        sql = "select count(*) from Res_Books where %s" % where_clause

    cursor.execute(sql.encode('utf-8'))
    row = cursor.fetchone()
    count = 0
    if row: count = row[0]
    page_count = int(ceil(count/float(page_size)))
    
    
    if type_name == 'all':
        sql = "select top %s Res_Category,Res_Guid,Res_Title,Res_SeriesName,Res_Lable,Res_Description,Res_Publisher,Res_FacePath,Res_Extension from View_allResQuery" % page_size
        sql += " where Res_Guid not in (select top %s Res_Guid from View_allResQuery where %s) and %s" % ((page_index-1)*page_size, where_clause, where_clause)
    elif type_name == 'video':
        sql = "select top %s Res_id,Res_Guid,Res_Title,Res_SeriesName,Res_Lable,Res_Description,NULL,Res_FacePath,Res_Extension from Res_Videos" % page_size
        sql += " where Res_id not in (select top %s Res_id from Res_Videos where %s) and %s" % ((page_index-1)*page_size, where_clause, where_clause)
    elif type_name == 'game':
        sql = "select top %s Res_id,Res_Guid,Res_Title,Res_SeriesName,Res_Lable,Res_Description,NULL,Res_FacePath,Res_Extension from Res_Game" % page_size
        sql += " where Res_id not in (select top %s Res_id from Res_Game where %s) and %s" % ((page_index-1)*page_size, where_clause, where_clause) 
    elif type_name == 'book':
        sql = "select top %s Res_id,Res_Guid,Res_Title,Res_SeriesTitle,Res_Label,Res_Abstract,Res_Publisher,Res_FacePath,Res_Extension from Res_Books" % page_size
        sql += " where Res_id not in (select top %s Res_id from Res_Books where %s) and %s" % ((page_index-1)*page_size, where_clause, where_clause)
    cursor.execute(sql.encode('utf-8'))
    rows = cursor.fetchall()
    video_list = []
    for row in rows:
        if not row: continue
        id = row[0]
        guid = row[1]
        title = row[2]
        series_name = row[3]
        label = row[4]
        description = row[5]
        publisher = row[6]
        face_path = row[7]
        extension = row[8]
        video_dict = {"guid":guid, "title":title, "series_name":series_name, "label":label, "description":description, "publisher":publisher}

        if type_name == 'all':
            if id == 2:
                video_dict["thumbnail"] = DOU_RES_HOST + "/Upload/Book/" + face_path
                video_dict["url"] = "/3qdou_book/?guid=" + guid
            elif id == 3:
                video_dict["thumbnail"] = DOU_RES_HOST + "/Upload/Game/" + face_path
                video_dict["url"] = get_game_url(request, title, extension, guid)
            elif id == 6:
                video_dict["thumbnail"] = DOU_RES_HOST + "/Upload/Video/" + face_path
                video_dict["url"] = get_video_url(request, title, extension, guid)
        elif type_name == 'video':
            video_dict["thumbnail"] = DOU_RES_HOST + "/Upload/Video/" + face_path
            video_dict["url"] = get_video_url(request, title, extension, guid)
        elif type_name == 'game':
            video_dict["thumbnail"] = DOU_RES_HOST + "/Upload/Game/" + face_path
            video_dict["url"] = get_game_url(request, title, extension, guid)
        elif type_name == 'book':
            video_dict["thumbnail"] = DOU_RES_HOST + "/Upload/Book/" + face_path
            video_dict["url"] = "/3qdou_book/?guid=" + guid
        video_list.append(video_dict)
    cursor.close()
    
    return SuccessResponse({"data":video_list, "page_index": page_index, "page_count": page_count})





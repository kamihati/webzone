#coding: utf-8
'''
Created on 2014年8月25日

@author: Administrator
'''
from math import ceil
import json
from utils.decorator import login_required
from django.core.cache import cache
from django.db import connection, connections
from WebZone.settings import DB_READ_NAME

from gateway import SuccessResponse, FailResponse

from WebZone.conf import DOU_RES_HOST
from WebZone.conf import DOU_VIDEO_STREAM_HOST


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

#Res_Article: 1
#Res_Books: 2
#Res_Game: 3
#Res_Music: 4
#Res_Picture: 5
#Res_Video: 6
def asset_type_name(type_id):
    if type_id == 1:
        return 'article'
    elif type_id == 2:
        return 'book'
    elif type_id == 3:
        return 'game'
    elif type_id == 4:
        return 'music'
    elif type_id == 5:
        return 'picture'
    elif type_id == 6:
        return 'video'
    else:
        return 'unknow'      


@login_required
def get_all_list(request, param):
    """
        得到3qdou的所有资源列表
        editor: kamihati 2015/4/28  增加搜索的支持范围 。并改进搜索逻辑
    """
    where_clause = "status=1"
    if param.has_key("class_id") and int(param.class_id):
        class_id = int(param.class_id)
        res_code = get_code_by_id(class_id)
        if res_code:
            where_clause += " and type_content LIKE '%%<%s%%'" % res_code
    if param.has_key("class_id2") and int(param.class_id2):
        class_id2 = int(param.class_id2)
        res_code2 = get_code_by_id(class_id2)
        if res_code2:
            where_clause += " and (type_content LIKE '%%<%s%%')" % res_code2

    key = param.key if param.has_key('key') else ''
    if key != '':
        where_clause += ' AND (title LIKE \'%' + key + '%\' OR series_title LIKE \'%' + key + '%\' OR description LIKE \'%' + key + '%\' OR primary_responser LIKE  \'%' + key + '%\' OR other_responser LIKE  \'%' + key + '%\')'

    if param.has_key("page_index"): page_index = int(param.page_index)
    else: page_index = 1
    if param.has_key("page_size"): page_size = int(param.page_size)
    else: page_size = 15

    cursor = connections[DB_READ_NAME].cursor()
    if where_clause:
        sql = "select count(*) from dou_asset where %s" % where_clause
    else:
        sql = "select count(*) from dou_asset"
    cursor.execute(sql)
    row = cursor.fetchone()
    count = 0
    if row: count = row[0]
    total_page_count = int(ceil(count/float(page_size)))
    #print "total_page_count", total_page_count
    
    sql = "select id, guid, type_id, title, series_title, label, description, publisher, page_count, width, height, res_path, thumbnail, extension,file_path,thumb_path from dou_asset"
    sql += " where %s limit %s, %s" % (where_clause, (page_index-1)*page_size, page_size)
    cursor.execute(sql)
    rows = cursor.fetchall()
    asset_list = []
    # 由于不同域名下可能会触发flash客户端的跨域bug。故资源地质随余名改变。不再统一使用yh.3qdou.com
    DOU_RES_HOST = ""
    for row in rows:
        if not row: continue
        id = int(row[0])
        guid = row[1]
        type_id = int(row[2])
        title = row[3]
        series_title = row[4]
        label = row[5]
        description = row[6]
        publisher = row[7]
        page_count = int(row[8]) if row[8] else 0
        width = int(row[9]) if row[9] else 0
        height = int(row[10]) if row[10] else 0

        res_path = row[11]
        thumbnail = row[12]
        extension = row[13]
        file_path = row[14]
        thumb_path = row[15]

        asset_dict = {"id":id, "guid":guid, "title":title, "series_title":series_title, "label":label, "description":description, "publisher":publisher}
        asset_dict["type_id"] = type_id
        asset_dict["type_name"] = asset_type_name(type_id)
        asset_dict["page_count"] = page_count
        asset_dict["extension"] = extension


        asset_dict["thumbnail"] = DOU_RES_HOST + '/media/4t/3qdou/' + thumbnail
        if type_id == 2:    #book
            asset_dict["thumbnail"] = DOU_RES_HOST + '/media/4t/3qdou/cover/book/' + thumbnail
            if page_count == 1: #单页的电子书
                asset_dict["url"] = DOU_RES_HOST + '/media/4t/3qdou/book/' + res_path
                asset_dict["extension"] = 'swf'
            else:
                asset_dict["extension"] = ''
                asset_dict["width"] = width
                asset_dict["height"] = height
                page_list = []
                for i in xrange(1, page_count+1):
                    page = {"page":i}
                    page['url'] = DOU_RES_HOST + '/media/4t/3qdou/book/%s/%d.swf' % (file_path, i)
                    page['thumbnail'] = DOU_RES_HOST + '/media/4t/3qdou/book/%s/%d.jpg' % (thumb_path, i)
                    page_list.append(page)
                asset_dict["pages"] = page_list
        elif type_id == 3:  #game
            asset_dict["thumbnail"] = DOU_RES_HOST + '/media/4t/3qdou/cover/game/' + thumbnail
            if extension.lower() == 'swf':
                asset_dict["url"] = DOU_RES_HOST + '/media/4t/3qdou/game/' + res_path
            elif extension.lower() == 'flv':
                #asset_dict["url"] = '/3qdou_video/?title=%s' % title    #视频资源，用800li流媒体服务器
                asset_dict["url"] = DOU_RES_HOST + '/media/4t/3qdou/game/' + res_path  #视频资源，直接读flv文件
        elif type_id == 6:  #video
            asset_dict["thumbnail"] = DOU_RES_HOST + '/media/4t/3qdou/cover/video/' + thumbnail
            if extension.lower() == 'swf':
                asset_dict["url"] = DOU_RES_HOST + '/media/4t/3qdou/video/' + res_path
            elif extension.lower() == 'flv':
                #asset_dict["url"] = '/3qdou_video/?title=%s' % title    #视频资源，用800li流媒体服务器
                asset_dict["url"] = DOU_RES_HOST + '/media/4t/3qdou/video/' + res_path  #视频资源，直接读flv文件

        asset_list.append(asset_dict)
    cursor.close()
    
    return SuccessResponse({"data":asset_list, "page_index": page_index, "page_count": total_page_count})


@login_required
def search_res_list(request, param):
    """
        搜索所有的可用的资源
    """
    if param.has_key("search_text"): search_text = param.search_text.lower()
    else: search_text = ""

    if len(search_text) == 0: return FailResponse(u"请输入搜索项")

    where_clause = "status=1 and (title like '%%%s%%' or label like '%%%s%%' or description like '%%%s%%')" % (search_text, search_text, search_text)

    if param.has_key("page_index"): page_index = int(param.page_index)
    else: page_index = 1
    if param.has_key("page_size"): page_size = int(param.page_size)
    else: page_size = 15

    cursor = connections[DB_READ_NAME].cursor()
    if where_clause:
        sql = "select count(*) from dou_asset where %s" % where_clause
    else:
        sql = "select count(*) from dou_asset"
    #print sql
    cursor.execute(sql)
    row = cursor.fetchone()
    count = 0
    if row: count = row[0]
    total_page_count = int(ceil(count/float(page_size)))
    #print "total_page_count", total_page_count
    
    sql = "select id, guid, type_id, title, series_title, label, description, publisher, page_count, width, height, res_path, thumbnail, extension,file_path,thumb_path from dou_asset"
    sql += " where %s limit %s, %s" % (where_clause, (page_index-1)*page_size, page_size)
    #print sql
    cursor.execute(sql)
    rows = cursor.fetchall()
    asset_list = []
    for row in rows:
        if not row: continue
        id = int(row[0])
        guid = row[1]
        type_id = int(row[2])
        title = row[3]
        series_title = row[4]
        label = row[5]
        description = row[6]
        publisher = row[7]
        page_count = int(row[8]) if row[8] else 0
        width = int(row[9]) if row[9] else 0
        height = int(row[10]) if row[10] else 0

        res_path = row[11]
        thumbnail = row[12]
        extension = row[13]
        file_path = row[14]
        thumb_path = row[15]

        asset_dict = {"id":id, "guid":guid, "title":title, "series_title":series_title, "label":label, "description":description, "publisher":publisher}
        asset_dict["type_id"] = type_id
        asset_dict["type_name"] = asset_type_name(type_id)
        asset_dict["page_count"] = page_count
        asset_dict["extension"] = extension
        asset_dict["thumbnail"] = DOU_RES_HOST + '/media/4t/3qdou/' + thumbnail
        if type_id == 2:    #book
            asset_dict["thumbnail"] = DOU_RES_HOST + '/media/4t/3qdou/cover/book/' + thumbnail
            if page_count == 1: #单页的电子书
                asset_dict["url"] = DOU_RES_HOST + '/media/4t/3qdou/book/' + res_path
                asset_dict["extension"] = 'swf'
            else:
                asset_dict["extension"] = ''
                asset_dict["width"] = width
                asset_dict["height"] = height
                page_list = []
                for i in xrange(1, page_count+1):
                    page = {"page":i}
                    page['url'] = DOU_RES_HOST + '/media/4t/3qdou/book/%s/%d.swf' % (file_path, i)
                    page['thumbnail'] = DOU_RES_HOST + '/media/4t/3qdou/book/%s/%d.jpg' % (thumb_path, i)
                    page_list.append(page)
                asset_dict["pages"] = page_list
        elif type_id == 3:  #game
            asset_dict["thumbnail"] = DOU_RES_HOST + '/media/4t/3qdou/cover/game/' + thumbnail
            asset_dict["url"] = DOU_RES_HOST + '/media/4t/3qdou/game/' + res_path
        elif type_id == 6:  #video
            asset_dict["thumbnail"] = DOU_RES_HOST + '/media/4t/3qdou/cover/video/' + thumbnail
            asset_dict["url"] = DOU_RES_HOST + '/media/4t/3qdou/video/' + res_path

        asset_list.append(asset_dict)
    cursor.close()
    
    return SuccessResponse({"data":asset_list, "page_index": page_index, "page_count": total_page_count})





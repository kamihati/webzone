#coding: utf-8
'''
Created on 2014-11-10

@author: Administrator
'''
from math import ceil
from datetime import datetime
from django.db import connection, connections
from django.core.cache import cache
from WebZone.settings import MEDIA_URL
from WebZone.settings import DB_READ_NAME

from utils.decorator import login_required

from diy.models import ZoneAsset, ZoneAssetTemplate, AuthAsset
from diy.models import ZoneAssetLike
from gateway import SuccessResponse, FailResponse

#喜欢列表最少返回的数量
LIKE_BACK_LEAST = 10

def fetch_public_like(user_id, res_type):
    """
    res_type in ((1,u"背景"),(2,u"装饰"),(3,u"画框"),(4,u"模板"),(5,u"声音"),(6,u"视频"),(7,u"图片"),(8,u"特效"),(9,u"标签"),(10,u"表情"))
    """
    cache_key = "gateway.views_zone.fetch_public_like.%d_%d" % (user_id, res_type)
    public_like_dict = cache.get(cache_key, {})
    if not public_like_dict:
        cursor = connections[DB_READ_NAME].cursor()
        sql = "select zone_asset_id,update_time from zone_asset_like where user_id=%d and res_type=%d and is_like=1" % (user_id, res_type)
        cursor.execute(sql)
        rows = cursor.fetchall()
        cursor.close()
        for row in rows:
            asset_id = int(row[0])
            update_time = row[1].strftime("%Y-%m-%d %H:%M:%S")
            public_like_dict[asset_id] = {"id": asset_id, "update_time": update_time}
        cache.set(cache_key, public_like_dict, 1)
    return public_like_dict


def fetch_public_recommend(res_type, notin_list, count, page_type=0):
    """
    res_type in ((1,u"背景"),(2,u"装饰"),(3,u"画框"),(4,u"模板"),(5,u"声音"),(6,u"视频"),(7,u"图片"),(8,u"特效"),(9,u"标签"),(10,u"表情"))
    editor: kamihati 2015/6/9  获取推荐列表的方法
    """
    #print "fetch_public_recommend", res_type, notin_list, count, page_type
    cache_key = "gateway.views_zone.fetch_public_recommend.%d_%d" % (res_type, page_type)
    public_recommend_id_dict = cache.get(cache_key, {})
    if not public_recommend_id_dict:
        cursor = connections[DB_READ_NAME].cursor()
        sql = "select id,res_type from zone_asset where is_recommend=1 and status=1"
        if page_type:
            sql += " and page_type=%d" % page_type
        sql += " order by update_time desc"
        cursor.execute(sql)
        rows = cursor.fetchall()
        cursor.close()
        for row in rows:
            asset_id = int(row[0])
            res_type_key = int(row[1])
            if not public_recommend_id_dict.has_key(res_type_key):
                public_recommend_id_dict[res_type_key] = []
            public_recommend_id_dict[res_type_key].append(asset_id)
        cache.set(cache_key, cache_key, 1)
    recommend_id_list = public_recommend_id_dict.get(res_type, [])
    for key in notin_list:
        if recommend_id_list.count(key) > 0:
            recommend_id_list.remove(key)
    #print recommend_id_list
    return recommend_id_list[:count]

def fetch_zone_asset(res_type, **kwargs):
    """
    fetch public list from cache 
    (res_type:((1,u"背景"),(2,u"装饰"),(3,u"画框"),(4,u"模板"),(5,u"声音"),(6,u"视频"),(7,u"图片"),(8,u"特效"),(9,u"标签"),(10,u"表情")))
    editor: kamihati 2015/6/8 增加kwargs参数。增加对size_id搜索的支持
    """
    cache_key = "gateway.views_zone.fetch_zone_asset:%d" % res_type
    if kwargs.has_key('size_id') and kwargs['size_id'] != 0:
        cache_key += ",%s" % kwargs['size_id']

    zone_asset_dict = cache.get(cache_key, {})
    if not zone_asset_dict:
        cursor = connections[DB_READ_NAME].cursor()
        
        sql = "select id,res_title,page_type,res_style,type_id,class_id,res_path,mask_path,width,height"
        sql += ",img_large_path,img_medium_path,img_small_path,page_count,update_time from zone_asset"
        sql += " where res_type=%d and `status`=1" % res_type
        if res_type in (5, 6):
            sql += " and codec_status=1"
        if kwargs.has_key('size_id') and kwargs['size_id'] != 0:
            sql += " AND size_id=%s" % kwargs['size_id']
        cursor.execute(sql)
        rows = cursor.fetchall()
        cursor.close()
        for row in rows:
            if not row:
                continue
            id = int(row[0])
            title = row[1]
            page_type = int(row[2])
            style_id = int(row[3])
            type_id = int(row[4]) if row[4] else 0
            class_id = int(row[5]) if row[5] else 0
            url =  MEDIA_URL + row[6] if row[6] else ''
            mask =  MEDIA_URL + row[7] if row[7] else ""
            width = int(row[8]) if row[8] else 0
            height = int(row[9]) if row[9] else 0
            
            large =  MEDIA_URL + row[10] if row[10] else ""
            medium =  MEDIA_URL + row[11] if row[11] else ""
            small =  MEDIA_URL + row[12] if row[12] else ""
            page_count = int(row[13])
            update_time = row[14].strftime("%Y-%m-%d %H:%M:%S")
            zone_asset_dict[id] = {"id":id, "title":title, "page_type":page_type, "style_id":style_id, "type_id":type_id, "class_id":class_id}
            zone_asset_dict[id]["url"] = url
            zone_asset_dict[id]["mask"] = mask
            zone_asset_dict[id]["width"] = width
            zone_asset_dict[id]["height"] = height
            zone_asset_dict[id]["large"] = large
            zone_asset_dict[id]["medium"] = medium
            zone_asset_dict[id]["small"] = small
            zone_asset_dict[id]["page_count"] = page_count
            zone_asset_dict[id]["update_time"] = update_time
            zone_asset_dict[id]["is_public"] = 1    #公有资源
        cache.set(cache_key, zone_asset_dict, 1)
    return zone_asset_dict


def fetch_auth_asset(user_id, res_type, is_like=0):
    """
    res_type in ((1,u"图片"),(2,u"声音"),(3,u"视频"),(4,u"涂鸦"),(11,u"故事大王"))
    """
    cache_key = "gateway.views_zone.fetch_auth_asset.%d_%d_%d" % (user_id, res_type, is_like)
    auth_asset_dict = cache.get(cache_key, {})
    if not auth_asset_dict:
        cursor = connections[DB_READ_NAME].cursor()
        sql = "select id,res_title,res_path,width,height,img_large_path,img_medium_path,img_small_path,is_like,update_time from auth_asset"
        sql += " where user_id=%d and res_type=%d" % (user_id, res_type)
        if is_like:
            sql += " and is_like=1"
        if res_type in (2, 3, 11):
            sql += " and codec_status=1"
        cursor.execute(sql)
        rows = cursor.fetchall()
        cursor.close()
        for row in rows:
            id = int(row[0])
            title = row[1]
            url = MEDIA_URL + row[2]
            width = int(row[3])
            height = int(row[4])
            
            large =  MEDIA_URL + row[5] if row[5] else ""
            medium =  MEDIA_URL + row[6] if row[6] else ""
            small =  MEDIA_URL + row[7] if row[7] else ""
            
            is_like = int(row[8])
            update_time = row[9].strftime("%Y-%m-%d %H:%M:%S")
            auth_asset_dict['a%d' % id] = {"id":id, "title":title, "url":url, "width":width, "height":height, "large":large, "medium":medium, "small":small, "is_like":is_like, "update_time":update_time}
            auth_asset_dict['a%d' % id]["is_public"] = 0    #私有资源
            #auth_asset_dict['a%d' % id]["width"] = width
            #auth_asset_dict['a%d' % id]["height"] = height
            #auth_asset_dict['a%d' % id]["large"] = large
            #auth_asset_dict['a%d' % id]["medium"] = medium
            #auth_asset_dict['a%d' % id]["small"] = small
        cache.set(cache_key, auth_asset_dict, 1)
    return auth_asset_dict



@login_required  
def like_personal_res(request, param):
    """
        对个人资源喜欢
    """
    if param.has_key("id"): asset_id = int(param.id)
    else: return FailResponse(u'必须传入资源ID')
    
    if param.has_key("is_like"): is_like = int(param.is_like)
    else: return FailResponse(u'必须指定喜欢/不喜欢')
    
    try: auth_asset = AuthAsset.objects.get(id=asset_id)
    except(AuthAsset.DoesNotExist): return FailResponse(u'资源ID:%d不存在' % asset_id)
    
    if auth_asset.is_like == is_like:
        return SuccessResponse({"id":asset_id, "is_like":is_like})
    else:
        auth_asset.is_like = is_like
        auth_asset.update_time = datetime.now()
        auth_asset.save()
        return SuccessResponse({"id":asset_id, "is_like":is_like})
    

@login_required  
def like_public_res(request, param):
    """
        对公共资源喜欢
    """
    if param.has_key("id"): asset_id = int(param.id)
    else: return FailResponse(u'必须传入资源ID')
    
    if param.has_key("is_like"): is_like = int(param.is_like)
    else: return FailResponse(u'必须指定喜欢/不喜欢')
    
    try: zone_asset = ZoneAsset.objects.get(id=asset_id)
    except(ZoneAsset.DoesNotExist): return FailResponse(u'资源ID:%d不存在' % asset_id)
    
    try:
        zone_asset_like = ZoneAssetLike.objects.get(user_id=request.user.id, zone_asset_id=asset_id)
        if zone_asset_like.is_like <> is_like:
            zone_asset_like.is_like = is_like
            zone_asset_like.update_time = datetime.now()
            zone_asset_like.save()
    except(ZoneAssetLike.DoesNotExist):
        zone_asset_like = ZoneAssetLike()
        zone_asset_like.user_id = request.user.id
        zone_asset_like.zone_asset_id = asset_id
        zone_asset_like.res_type = zone_asset.res_type
        zone_asset_like.is_like = is_like
        zone_asset_like.save()
    return SuccessResponse({"id":asset_id, "is_like":is_like})


@login_required  
def fetch_bg_list(request, param):
    """
        背景列表，需要根据单双页显示背景, page_type:1,2
        is_like=1时，把喜欢的放前排
        editor: kamihati 2015/6/8  增加size_id的支持。可根据size_id取出对应的背景
    """
    if param.has_key("style_id"): style_id = int(param.style_id)
    else: style_id = 0
    if param.has_key("page_type"): page_type = param.page_type
    else: page_type = 0
    if param.has_key("is_like"): is_like = int(param.is_like)
    else: is_like = 0
    if param.has_key("page_index"): page_index = int(param.page_index)
    else: page_index = 1
    if param.has_key("page_size"): page_size = int(param.page_size)
    else: page_size = 20
    # 尺寸的id
    size_id = int(param['size_id']) if param.has_key('size_id') else 0
    
    res_type = 1    #背景
    zone_asset_dict = fetch_zone_asset(res_type, size_id=size_id)    #所有当前分类的资源，然后进行选取
    public_like_dict = fetch_public_like(request.user.id, res_type)
    for key in public_like_dict.keys():
        if zone_asset_dict.has_key(key):
            zone_asset_dict[key]['is_like'] = 1
            zone_asset_dict[key]['update_time'] = public_like_dict[key]['update_time']
    
    #重新条件过滤
    ready_asset_dict = {}
    if style_id and page_type:
        for key in zone_asset_dict.keys():
            if zone_asset_dict[key]["style_id"] == style_id and (zone_asset_dict[key]["page_type"] == page_type or zone_asset_dict[key]["page_type"] == 0):
                ready_asset_dict[key] = zone_asset_dict[key]
    elif style_id:  #风格
        for key in zone_asset_dict.keys():
            if zone_asset_dict[key]["style_id"] == style_id:
                ready_asset_dict[key] = zone_asset_dict[key]
    elif page_type: #单双页
        for key in zone_asset_dict.keys():
            if zone_asset_dict[key]["page_type"] == page_type or zone_asset_dict[key]["page_type"] == 0:
                ready_asset_dict[key] = zone_asset_dict[key]
    else:
        ready_asset_dict = zone_asset_dict.copy()

    ready_list = []
    if is_like:
        like_asset_dict = {}
        for key in public_like_dict.keys():
            if ready_asset_dict.has_key(key):   #有些单双页的可能没有
                like_asset_dict[key] = ready_asset_dict[key]
        if len(like_asset_dict) < LIKE_BACK_LEAST:
            #print public_like_dict, like_asset_dict, page_type
            recommend_id_list = fetch_public_recommend(res_type, like_asset_dict.keys(), LIKE_BACK_LEAST-len(like_asset_dict), page_type)
        else: recommend_id_list = []
        #print len(like_asset_dict), len(recommend_id_list)
        for key in recommend_id_list:
            like_asset_dict[key] = ready_asset_dict[key]
            like_asset_dict[key]['is_like'] = 0
        total_count = len(like_asset_dict.keys())
        
        sorted_list = sorted(like_asset_dict.items(), key=lambda d:(d[1]['is_like'], d[1]['update_time']), reverse=True)
        sorted_id_list = [item[0] for item in sorted_list]
        back_id_list = sorted_id_list[(page_index-1)*page_size:page_index*page_size]
        #print sorted_id_list, back_id_list
        for id in back_id_list:
            ready_list.append(like_asset_dict[id])
    else:
        total_count = len(ready_asset_dict)
        
        sorted_list = sorted(ready_asset_dict.items(), key=lambda d:d[1]['update_time'], reverse=True)
        sorted_id_list = [item[0] for item in sorted_list]
        back_id_list = sorted_id_list[(page_index-1)*page_size:page_index*page_size]
        #print sorted_id_list, back_id_list
        for id in back_id_list:
            ready_list.append(ready_asset_dict[id])
            
    page_count = int(ceil(total_count/float(page_size)))
    return SuccessResponse({"data":ready_list, "page_index": page_index, "page_count": page_count}) 
    

@login_required  
def fetch_decorator_list(request, param):
    """
        装饰列表，喜欢的放前边
    """
    if param.has_key("style_id"): style_id = int(param.style_id)
    else: style_id = 0
    if param.has_key("is_like"): is_like = int(param.is_like)
    else: is_like = 0
    if param.has_key("page_index"): page_index = int(param.page_index)
    else: page_index = 1
    if param.has_key("page_size"): page_size = int(param.page_size)
    else: page_size = 20
    
    res_type = 2    #装饰
    zone_asset_dict = fetch_zone_asset(res_type)    #所有当前分类的资源，然后进行选取
    public_like_dict = fetch_public_like(request.user.id, res_type)
    for key in public_like_dict.keys():
        zone_asset_dict[key]['is_like'] = 1
        zone_asset_dict[key]['update_time'] = public_like_dict[key]['update_time']
    
    #重新条件过滤
    ready_asset_dict = {}
    if style_id:  #风格
        for key in zone_asset_dict.keys():
            if zone_asset_dict[key]["style_id"] == style_id:
                ready_asset_dict[key] = zone_asset_dict[key]
    else:
        ready_asset_dict = zone_asset_dict.copy()
        
    ready_list = []
    if is_like:
        if len(public_like_dict) < LIKE_BACK_LEAST:
            recommend_id_list = fetch_public_recommend(res_type, public_like_dict.keys(), LIKE_BACK_LEAST-len(public_like_dict))
        else: recommend_id_list = []
        like_asset_dict = {}
        for key in public_like_dict.keys():
            like_asset_dict[key] = ready_asset_dict[key]
        for key in recommend_id_list:
            like_asset_dict[key] = ready_asset_dict[key]
            like_asset_dict[key]['is_like'] = 0
        total_count = len(like_asset_dict.keys())
        
        sorted_list = sorted(like_asset_dict.items(), key=lambda d:(d[1]['is_like'], d[1]['update_time']), reverse=True)
        sorted_id_list = [item[0] for item in sorted_list]
        back_id_list = sorted_id_list[(page_index-1)*page_size:page_index*page_size]
        #print sorted_id_list, back_id_list
        for id in back_id_list:
            ready_list.append(like_asset_dict[id])
    else:
        total_count = len(ready_asset_dict)
        
        sorted_list = sorted(ready_asset_dict.items(), key=lambda d:d[1]['update_time'], reverse=True)
        sorted_id_list = [item[0] for item in sorted_list]
        back_id_list = sorted_id_list[(page_index-1)*page_size:page_index*page_size]
        #print sorted_id_list, back_id_list
        for id in back_id_list:
            ready_list.append(ready_asset_dict[id])
            
    page_count = int(ceil(total_count/float(page_size)))
    return SuccessResponse({"data":ready_list, "page_index": page_index, "page_count": page_count}) 


@login_required  
def fetch_frame_list(request, param):
    '''
    获取画框素材
    editor: kamihati 2015/6/11 解决某些账号获取不到画框资源的问题
    :param request:
    :param param:
    :return:
    '''
    if param.has_key("style_id"): style_id = int(param.style_id)
    else: style_id = 0
    if param.has_key("is_like"): is_like = int(param.is_like)
    else: is_like = 0
    if param.has_key("page_index"): page_index = int(param.page_index)
    else: page_index = 1
    if param.has_key("page_size"): page_size = int(param.page_size)
    else: page_size = 20
    
    res_type = 3    #画框
    zone_asset_dict = fetch_zone_asset(res_type)    #所有当前分类的资源，然后进行选取
    public_like_dict = fetch_public_like(request.user.id, res_type)
    for key in public_like_dict.keys():
        if zone_asset_dict.has_key(key):
            zone_asset_dict[key]['is_like'] = 1
            zone_asset_dict[key]['update_time'] = public_like_dict[key]['update_time']
    
    #重新条件过滤
    ready_asset_dict = {}
    if style_id:  #风格
        for key in zone_asset_dict.keys():
            if zone_asset_dict[key]["style_id"] == style_id:
                ready_asset_dict[key] = zone_asset_dict[key]
    else:
        ready_asset_dict = zone_asset_dict.copy()

    ready_list = []
    if is_like:
        if len(public_like_dict) < LIKE_BACK_LEAST:
            recommend_id_list = fetch_public_recommend(res_type, public_like_dict.keys(), LIKE_BACK_LEAST-len(public_like_dict))
        else: recommend_id_list = []
        #print recommend_id_list
        like_asset_dict = {}
        for key in public_like_dict.keys():
            like_asset_dict[key] = ready_asset_dict[key]
        
        for key in recommend_id_list:
            like_asset_dict[key] = ready_asset_dict[key]
            like_asset_dict[key]['is_like'] = 0
        total_count = len(like_asset_dict.keys())
        
        sorted_list = sorted(like_asset_dict.items(), key=lambda d:(d[1]['is_like'], d[1]['update_time']), reverse=True)
        sorted_id_list = [item[0] for item in sorted_list]
        back_id_list = sorted_id_list[(page_index-1)*page_size:page_index*page_size]
        #print sorted_id_list, back_id_list
        for id in back_id_list:
            ready_list.append(like_asset_dict[id])
    else:
        total_count = len(ready_asset_dict)
        
        sorted_list = sorted(ready_asset_dict.items(), key=lambda d:d[1]['update_time'], reverse=True)
        sorted_id_list = [item[0] for item in sorted_list]
        back_id_list = sorted_id_list[(page_index-1)*page_size:page_index*page_size]
        #print sorted_id_list, back_id_list
        for id in back_id_list:
            ready_list.append(ready_asset_dict[id])
            
    page_count = int(ceil(total_count/float(page_size)))
    return SuccessResponse({"data":ready_list, "page_index": page_index, "page_count": page_count})


@login_required  
def fetch_template_list(request, param):
    """
        据作品分类查模板列表
    """
    if param.has_key("type_id"): type_id = int(param.type_id)
    else: type_id = 0
    if param.has_key("class_id"): class_id = int(param.class_id)
    else: class_id = 0
    if param.has_key("is_like"): is_like = int(param.is_like)
    else: is_like = 0
    if param.has_key("page_index"): page_index = int(param.page_index)
    else: page_index = 1
    if param.has_key("page_size"): page_size = int(param.page_size)
    else: page_size = 20
    
    res_type = 4    #模板
    zone_asset_dict = fetch_zone_asset(res_type)    #所有当前分类的资源，然后进行选取
    public_like_dict = fetch_public_like(request.user.id, res_type)
    for key in public_like_dict.keys():
        zone_asset_dict[key]['is_like'] = 1
        zone_asset_dict[key]['update_time'] = public_like_dict[key]['update_time']
    
    #重新条件过滤
    ready_asset_dict = {}
    if type_id and class_id:
        for key in zone_asset_dict.keys():
            if zone_asset_dict[key]["type_id"] == type_id and zone_asset_dict[key]["class_id"] == class_id:
                ready_asset_dict[key] = zone_asset_dict[key]
    elif type_id:  #大类ID
        for key in zone_asset_dict.keys():
            if zone_asset_dict[key]["type_id"] == type_id:
                ready_asset_dict[key] = zone_asset_dict[key]
    elif class_id: #小类ID
        for key in zone_asset_dict.keys():
            if zone_asset_dict[key]["class_id"] == class_id:
                ready_asset_dict[key] = zone_asset_dict[key]
    else:
        ready_asset_dict = zone_asset_dict.copy()

    ready_list = []
    if is_like:
        if len(public_like_dict) < LIKE_BACK_LEAST:
            recommend_id_list = fetch_public_recommend(res_type, public_like_dict.keys(), LIKE_BACK_LEAST-len(public_like_dict))
        else: recommend_id_list = []
        like_asset_dict = {}
        for key in public_like_dict.keys():
            like_asset_dict[key] = ready_asset_dict[key]
        for key in recommend_id_list:
            like_asset_dict[key] = ready_asset_dict[key]
            like_asset_dict[key]['is_like'] = 0
        total_count = len(like_asset_dict.keys())
        
        sorted_list = sorted(like_asset_dict.items(), key=lambda d:(d[1]['is_like'], d[1]['update_time']), reverse=True)
        sorted_id_list = [item[0] for item in sorted_list]
        back_id_list = sorted_id_list[(page_index-1)*page_size:page_index*page_size]
        #print sorted_id_list, back_id_list
        for id in back_id_list:
            ready_list.append(like_asset_dict[id])
    else:
        total_count = len(ready_asset_dict)
        
        sorted_list = sorted(ready_asset_dict.items(), key=lambda d:d[1]['update_time'], reverse=True)
        sorted_id_list = [item[0] for item in sorted_list]
        back_id_list = sorted_id_list[(page_index-1)*page_size:page_index*page_size]
        #print sorted_id_list, back_id_list
        for id in back_id_list:
            ready_list.append(ready_asset_dict[id])
            
    page_count = int(ceil(total_count/float(page_size)))
    return SuccessResponse({"data":ready_list, "page_index": page_index, "page_count": page_count}) 


@login_required  
def fetch_template_info(request, param):
    """
        得到模板的每页的详细信息
    """
    if param.has_key("zone_asset_id"): zone_asset_id = int(param.zone_asset_id)
    else: return FailResponse(u'必须传入模板ID')
    
    try: zone_asset = ZoneAsset.objects.get(id=zone_asset_id)
    except(ZoneAsset.DoesNotExist):
        return FailResponse(u'模板ID:%s不存在' % zone_asset_id)
    
    #非公共资源，只能自己图书馆下的用户可以使用
    if zone_asset.library:
        if zone_asset.library <> request.user.library:
            return FailResponse(u'没有权限')
    
    template_dict = {"id":zone_asset.id, "title":zone_asset.res_title, "page_count":zone_asset.page_count}
#     template_dict["origin"] = request.build_absolute_uri(MEDIA_URL + zone_asset.res_path)
#     template_dict["large"] = request.build_absolute_uri(MEDIA_URL + zone_asset.img_large_path)
#     template_dict["medium"] = request.build_absolute_uri(MEDIA_URL + zone_asset.img_medium_path)
#     template_dict["small"] = request.build_absolute_uri(MEDIA_URL + zone_asset.img_small_path)
    template_dict["origin"] = MEDIA_URL + zone_asset.res_path
    template_dict["large"] = MEDIA_URL + zone_asset.img_large_path
    template_dict["medium"] = MEDIA_URL + zone_asset.img_medium_path
    template_dict["small"] = MEDIA_URL + zone_asset.img_small_path
    template_dict["page_count"] = zone_asset.page_count
    template_dict["width"] = zone_asset.width
    template_dict["height"] = zone_asset.height
    template_dict["create_type"] = zone_asset.create_type
    template_dict["read_type"] = zone_asset.read_type
    template_dict["pages"] = []
    if zone_asset.page_count > 0:
        query_set = ZoneAssetTemplate.objects.filter(zone_asset=zone_asset).order_by("page_index")
        for template in query_set:
            page_info = {"page_index":template.page_index}
            page_info["media"] = template.is_multimedia
            #page_info["json"] = request.build_absolute_uri(MEDIA_URL + template.json_path)
            #page_info["origin"] = request.build_absolute_uri(MEDIA_URL + template.img_path)
            #page_info["small"] = request.build_absolute_uri(MEDIA_URL + template.img_small_path)
            page_info["json"] = MEDIA_URL + template.json_path
            page_info["origin"] = MEDIA_URL + template.img_path
            page_info["small"] = MEDIA_URL + template.img_small_path
            template_dict["pages"].append(page_info)
    return SuccessResponse(template_dict)
            

@login_required  
def fetch_effect_list(request, param):
    """
        得到特效列表
    """
    if param.has_key("is_like"): is_like = int(param.is_like)
    else: is_like = 0
    if param.has_key("page_index"): page_index = int(param.page_index)
    else: page_index = 1
    if param.has_key("page_size"): page_size = int(param.page_size)
    else: page_size = 20
    
    res_type = 8    #特效
    zone_asset_dict = fetch_zone_asset(res_type)    #所有当前分类的资源，然后进行选取
    public_like_dict = fetch_public_like(request.user.id, res_type)
    for key in public_like_dict.keys():
        zone_asset_dict[key]['is_like'] = 1
        zone_asset_dict[key]['update_time'] = public_like_dict[key]['update_time']
    
    #重新条件过滤
    ready_asset_dict = zone_asset_dict.copy()

    ready_list = []
    if is_like:
        if len(public_like_dict) < LIKE_BACK_LEAST:
            recommend_id_list = fetch_public_recommend(res_type, public_like_dict.keys(), LIKE_BACK_LEAST-len(public_like_dict))
        else: recommend_id_list = []
        like_asset_dict = {}
        for key in ready_asset_dict.keys():
            if key in public_like_dict.keys() or key in recommend_id_list:
                like_asset_dict[key] = ready_asset_dict[key]
        total_count = len(like_asset_dict.keys())
        
        sorted_list = sorted(like_asset_dict.items(), key=lambda d:(d[1]['is_like'], d[1]['update_time']), reverse=True)
        sorted_id_list = [item[0] for item in sorted_list]
        back_id_list = sorted_id_list[(page_index-1)*page_size:page_index*page_size]
        #print sorted_id_list, back_id_list
        for id in back_id_list:
            ready_list.append(like_asset_dict[id])
    else:
        total_count = len(ready_asset_dict)
        
        sorted_list = sorted(ready_asset_dict.items(), key=lambda d:d[1]['update_time'], reverse=True)
        sorted_id_list = [item[0] for item in sorted_list]
        back_id_list = sorted_id_list[(page_index-1)*page_size:page_index*page_size]
        #print sorted_id_list, back_id_list
        for id in back_id_list:
            ready_list.append(ready_asset_dict[id])
            
    page_count = int(ceil(total_count/float(page_size)))
    return SuccessResponse({"data":ready_list, "page_index": page_index, "page_count": page_count})


@login_required  
def fetch_audio_list(request, param):
    """
        只返回转码成功，可用的音频
        type_id:0:个人，-1:所有，-2:公开    (查询范围)
    """
    if param.has_key("is_like"): is_like = int(param.is_like)
    else: is_like = 0
    if param.has_key("album_id"): album_id = int(param.album_id)
    else: album_id = 0
    if param.has_key("page_index"): page_index = int(param.page_index)
    else: page_index = 1
    if param.has_key("page_size"): page_size = int(param.page_size)
    else: page_size = 20
    
    ready_list = []
    res_type=5  #音频
    if album_id == -2:    #公开
        zone_asset_dict = fetch_zone_asset(res_type)
        public_like_dict = fetch_public_like(request.user.id, res_type)
        for key in public_like_dict.keys():
            zone_asset_dict[key]['is_like'] = 1
            zone_asset_dict[key]['update_time'] = public_like_dict[key]['update_time']
        if is_like:
            if len(public_like_dict) < LIKE_BACK_LEAST:
                recommend_id_list = fetch_public_recommend(res_type, public_like_dict.keys(), LIKE_BACK_LEAST-len(public_like_dict))
            else: recommend_id_list = []
            like_asset_dict = {}
            for key in public_like_dict.keys():
                like_asset_dict[key] = zone_asset_dict[key]
            for key in recommend_id_list:
                like_asset_dict[key] = zone_asset_dict[key]
                like_asset_dict[key]['is_like'] = 0
            total_count = len(like_asset_dict)
            
            sorted_list = sorted(like_asset_dict.items(), key=lambda d:(d[1]['is_like'], d[1]['update_time']), reverse=True)
            sorted_id_list = [item[0] for item in sorted_list]
            back_id_list = sorted_id_list[(page_index-1)*page_size:page_index*page_size]
            #print sorted_id_list, back_id_list
            for id in back_id_list:
                ready_list.append(like_asset_dict[id])
        else:
            total_count = len(zone_asset_dict)
            
            sorted_list = sorted(zone_asset_dict.items(), key=lambda d:d[1]['update_time'], reverse=True)
            sorted_id_list = [item[0] for item in sorted_list]
            back_id_list = sorted_id_list[(page_index-1)*page_size:page_index*page_size]
            #print sorted_id_list, back_id_list
            for id in back_id_list:
                ready_list.append(zone_asset_dict[id])
    elif album_id == -1: #所有
        zone_asset_dict = fetch_zone_asset(res_type)
        public_like_dict = fetch_public_like(request.user.id, res_type)
        for key in public_like_dict.keys():
            zone_asset_dict[key]['is_like'] = 1
            zone_asset_dict[key]['update_time'] = public_like_dict[key]['update_time']
        
        if is_like:
            auth_like_dict = fetch_auth_asset(request.user.id, res_type=2, is_like=1)  #个人音频类型是2
            
            if len(public_like_dict) + len(auth_like_dict) < LIKE_BACK_LEAST:    #需要被喜欢数量
                recommend_id_list = fetch_public_recommend(res_type, public_like_dict.keys(), LIKE_BACK_LEAST-len(public_like_dict)-len(auth_like_dict))
            else: recommend_id_list = []
            like_asset_dict = {}
            for key in public_like_dict.keys():
                like_asset_dict[key] = zone_asset_dict[key]
            for key in recommend_id_list:
                like_asset_dict[key] = zone_asset_dict[key]
                like_asset_dict[key]['is_like'] = 0
            like_asset_dict.update(auth_like_dict)
            total_count = len(like_asset_dict)
            
            sorted_list = sorted(like_asset_dict.items(), key=lambda d:(d[1]['is_like'], d[1]['update_time']), reverse=True)
            sorted_id_list = [item[0] for item in sorted_list]
            back_id_list = sorted_id_list[(page_index-1)*page_size:page_index*page_size]
            #print sorted_id_list, back_id_list
            for id in back_id_list:
                ready_list.append(like_asset_dict[id])
        else:
            auth_asset_dict = fetch_auth_asset(request.user.id, res_type=2, is_like=0)  #个人音频类型是2
            all_asset_dict = zone_asset_dict.copy()
            all_asset_dict.update(auth_asset_dict)
            total_count = len(all_asset_dict)
            
            sorted_list = sorted(all_asset_dict.items(), key=lambda d:d[1]['update_time'], reverse=True)
            sorted_id_list = [item[0] for item in sorted_list]
            back_id_list = sorted_id_list[(page_index-1)*page_size:page_index*page_size]
            #print sorted_id_list, back_id_list
            for id in back_id_list:
                ready_list.append(all_asset_dict[id])
    elif album_id == 0:  #个人
        auth_asset_dict = fetch_auth_asset(request.user.id, res_type=2, is_like=is_like)  #个人音频类型是2
        total_count = len(auth_asset_dict)
        
        sorted_list = sorted(auth_asset_dict.items(), key=lambda d:d[1]['update_time'], reverse=True)
        sorted_id_list = [item[0] for item in sorted_list]
        back_id_list = sorted_id_list[(page_index-1)*page_size:page_index*page_size]
        #print sorted_id_list, back_id_list
        for id in back_id_list:
            ready_list.append(auth_asset_dict[id])
            
    page_count = int(ceil(total_count/float(page_size)))
    return SuccessResponse({"data":ready_list, "page_index": page_index, "page_count": page_count})


@login_required  
def fetch_video_list(request, param):
    """
        只返回转码成功，
        得到视频列表，公共的，私人的都有
    """
    if param.has_key("is_like"): is_like = int(param.is_like)
    else: is_like = 0
    if param.has_key("album_id"): album_id = int(param.album_id)
    else: album_id = 0
    if param.has_key("page_index"): page_index = int(param.page_index)
    else: page_index = 1
    if param.has_key("page_size"): page_size = int(param.page_size)
    else: page_size = 20
    
    ready_list = []
    res_type=6  #视频
    if album_id == -2:    #公开
        zone_asset_dict = fetch_zone_asset(res_type)
        total_count = len(zone_asset_dict)
        public_like_dict = fetch_public_like(request.user.id, res_type)
        for key in public_like_dict.keys():
            zone_asset_dict[key]['is_like'] = 1
            zone_asset_dict[key]['update_time'] = public_like_dict[key]['update_time']
        
        if is_like:
            if len(public_like_dict) < LIKE_BACK_LEAST:
                recommend_id_list = fetch_public_recommend(res_type, public_like_dict.keys(), LIKE_BACK_LEAST-len(public_like_dict))
            else: recommend_id_list = []
            like_asset_dict = {}
            for key in public_like_dict.keys():
                like_asset_dict[key] = zone_asset_dict[key]
            for key in recommend_id_list:
                like_asset_dict[key] = zone_asset_dict[key]
                like_asset_dict[key]['is_like'] = 0
            total_count = len(like_asset_dict)
            
            sorted_list = sorted(like_asset_dict.items(), key=lambda d:(d[1]['is_like'], d[1]['update_time']), reverse=True)
            sorted_id_list = [item[0] for item in sorted_list]
            back_id_list = sorted_id_list[(page_index-1)*page_size:page_index*page_size]
            #print sorted_id_list, back_id_list
            for id in back_id_list:
                ready_list.append(like_asset_dict[id])
        else:
            total_count = len(zone_asset_dict)
            
            sorted_list = sorted(zone_asset_dict.items(), key=lambda d:d[1]['update_time'], reverse=True)
            sorted_id_list = [item[0] for item in sorted_list]
            back_id_list = sorted_id_list[(page_index-1)*page_size:page_index*page_size]
            #print sorted_id_list, back_id_list
            for id in back_id_list:
                ready_list.append(zone_asset_dict[id])
    elif album_id == -1: #所有
        zone_asset_dict = fetch_zone_asset(res_type)
        public_like_dict = fetch_public_like(request.user.id, res_type)
        for key in public_like_dict.keys():
            zone_asset_dict[key]['is_like'] = 1
            zone_asset_dict[key]['update_time'] = public_like_dict[key]['update_time']

        if is_like:
            auth_like_dict = fetch_auth_asset(request.user.id, res_type=3, is_like=1)  #个人视频类型是3
            
            if len(public_like_dict) + len(auth_like_dict) < LIKE_BACK_LEAST:    #需要被喜欢数量
                recommend_id_list = fetch_public_recommend(res_type, public_like_dict.keys(), LIKE_BACK_LEAST-len(public_like_dict)-len(auth_like_dict))
            else: recommend_id_list = []
            like_asset_dict = {}
            for key in public_like_dict.keys():
                like_asset_dict[key] = zone_asset_dict[key]
            for key in recommend_id_list:
                like_asset_dict[key] = zone_asset_dict[key]
                like_asset_dict[key]['is_like'] = 0
            like_asset_dict.update(auth_like_dict)
            total_count = len(like_asset_dict)
            
            sorted_list = sorted(like_asset_dict.items(), key=lambda d:(d[1]['is_like'], d[1]['update_time']), reverse=True)
            sorted_id_list = [item[0] for item in sorted_list]
            back_id_list = sorted_id_list[(page_index-1)*page_size:page_index*page_size]
            #print sorted_id_list, back_id_list
            for id in back_id_list:
                ready_list.append(like_asset_dict[id])
        else:
            auth_asset_dict = fetch_auth_asset(request.user.id, res_type=3, is_like=0)  #个人视频类型是3
            all_asset_dict = zone_asset_dict.copy()
            all_asset_dict.update(auth_asset_dict)
            total_count = len(all_asset_dict)
            
            sorted_list = sorted(all_asset_dict.items(), key=lambda d:d[1]['update_time'], reverse=True)
            sorted_id_list = [item[0] for item in sorted_list]
            back_id_list = sorted_id_list[(page_index-1)*page_size:page_index*page_size]
            #print sorted_id_list, back_id_list
            for id in back_id_list:
                ready_list.append(all_asset_dict[id])
    elif album_id == 0:  #个人
        auth_asset_dict = fetch_auth_asset(request.user.id, res_type=3, is_like=is_like)  #个人视频类型是3
        total_count = len(auth_asset_dict)
        
        sorted_list = sorted(auth_asset_dict.items(), key=lambda d:d[1]['update_time'], reverse=True)
        sorted_id_list = [item[0] for item in sorted_list]
        back_id_list = sorted_id_list[(page_index-1)*page_size:page_index*page_size]
        #print sorted_id_list, back_id_list
        for id in back_id_list:
            ready_list.append(auth_asset_dict[id])
            
    page_count = int(ceil(total_count/float(page_size)))
    return SuccessResponse({"data":ready_list, "page_index": page_index, "page_count": page_count})



@login_required    
def fetch_picture_list(request, param):
    """
        得到图片列表，私人的，公共的都有
    """
    if param.has_key("album_id"): album_id = int(param.album_id)
    else: album_id = 0
    if param.has_key("is_like"): is_like = int(param.is_like)
    else: is_like = 0
    if param.has_key("page_index"): page_index = int(param.page_index)
    else: page_index = 1
    if param.has_key("page_size"): page_size = int(param.page_size)
    else: page_size = 20
    
    ready_list = []
    res_type=7  #图片
    if album_id == -2:    #公开
        zone_asset_dict = fetch_zone_asset(res_type)
        public_like_dict = fetch_public_like(request.user.id, res_type)
        for key in public_like_dict.keys():
            if key not in zone_asset_dict:
                continue
            zone_asset_dict[key]['is_like'] = 1
            zone_asset_dict[key]['update_time'] = public_like_dict[key]['update_time']
        
        if is_like:
            if len(public_like_dict) < LIKE_BACK_LEAST:
                recommend_id_list = fetch_public_recommend(res_type, public_like_dict.keys(), LIKE_BACK_LEAST-len(public_like_dict))
            else: recommend_id_list = []
            like_asset_dict = {}
            for key in public_like_dict.keys():
                like_asset_dict[key] = zone_asset_dict[key]
            for key in recommend_id_list:
                like_asset_dict[key] = zone_asset_dict[key]
                like_asset_dict[key]['is_like'] = 0
            total_count = len(like_asset_dict)
            
            sorted_list = sorted(like_asset_dict.items(), key=lambda d:(d[1]['is_like'], d[1]['update_time']), reverse=True)
            sorted_id_list = [item[0] for item in sorted_list]
            back_id_list = sorted_id_list[(page_index-1)*page_size:page_index*page_size]
            #print sorted_id_list, back_id_list
            for id in back_id_list:
                ready_list.append(like_asset_dict[id])
        else:
            total_count = len(zone_asset_dict)
            
            sorted_list = sorted(zone_asset_dict.items(), key=lambda d:d[1]['update_time'], reverse=True)
            sorted_id_list = [item[0] for item in sorted_list]
            back_id_list = sorted_id_list[(page_index-1)*page_size:page_index*page_size]
            #print sorted_id_list, back_id_list
            for id in back_id_list:
                ready_list.append(zone_asset_dict[id])
    elif album_id == -1: #所有，全部
        zone_asset_dict = fetch_zone_asset(res_type)
        public_like_dict = fetch_public_like(request.user.id, res_type)
        for key in public_like_dict.keys():
            if key not in zone_asset_dict:
                continue
            zone_asset_dict[key]['is_like'] = 1
            zone_asset_dict[key]['update_time'] = public_like_dict[key]['update_time']
        
        if is_like:
            auth_like_dict = fetch_auth_asset(request.user.id, 1, 1)  #个人图片类型是1
            
            if len(public_like_dict) + len(auth_like_dict) < LIKE_BACK_LEAST:    #需要被喜欢数量
                recommend_id_list = fetch_public_recommend(res_type, public_like_dict.keys(), LIKE_BACK_LEAST-len(public_like_dict)-len(auth_like_dict))
            else: recommend_id_list = []
            
            like_asset_dict = {}
            for key in recommend_id_list:
                like_asset_dict[key] = zone_asset_dict[key]
                like_asset_dict[key]['is_like'] = 0
            for key in public_like_dict.keys():
                if key not in like_asset_dict:
                    continue
                like_asset_dict[key] = zone_asset_dict[key]
            like_asset_dict.update(auth_like_dict)
            total_count = len(like_asset_dict)
            
            sorted_list = sorted(like_asset_dict.items(), key=lambda d:(d[1]['is_like'], d[1]['update_time']), reverse=True)
            sorted_id_list = [item[0] for item in sorted_list]
            back_id_list = sorted_id_list[(page_index-1)*page_size:page_index*page_size]
            #print sorted_id_list, back_id_list
            for id in back_id_list:
                ready_list.append(like_asset_dict[id])
        else:
            auth_asset_dict = fetch_auth_asset(request.user.id, res_type=1, is_like=0)  #个人图片类型是1
            all_asset_dict = zone_asset_dict.copy()
            all_asset_dict.update(auth_asset_dict)
            total_count = len(all_asset_dict)
            
            sorted_list = sorted(all_asset_dict.items(), key=lambda d:d[1]['update_time'], reverse=True)
            sorted_id_list = [item[0] for item in sorted_list]
            back_id_list = sorted_id_list[(page_index-1)*page_size:page_index*page_size]
            #print sorted_id_list, back_id_list
            for id in back_id_list:
                ready_list.append(all_asset_dict[id])
    elif album_id == 0:  #所有个人相册
        where_clause = "user_id=%d and res_type=1 and status=1" % request.user.id
        cursor = connections[DB_READ_NAME].cursor()
        sql = "select count(*) from auth_asset where %s" % where_clause
        #print sql
        cursor.execute(sql)
        row = cursor.fetchone()
        if row: total_count = row[0]
        
        order_by = "update_time desc"
        if is_like:
            order_by = "is_like desc," + order_by
        sql = "select id,res_title,res_path,img_large_path,img_medium_path,img_small_path,is_like,update_time from auth_asset where %s" % where_clause
        sql += " order by %s LIMIT %s, %s" % (order_by, (page_index-1)*page_size, page_size)
        #print sql
        cursor = connections[DB_READ_NAME].cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        for row in rows:
            data_dict = {}
            data_dict["id"] = row[0]
            data_dict["title"] = row[1]
            data_dict["url"] = MEDIA_URL + row[2]
            data_dict["large"] = MEDIA_URL + row[3] if row[3] else ""
            data_dict["medium"] = MEDIA_URL + row[4] if row[4] else ""
            data_dict["small"] = MEDIA_URL + row[5] if row[5] else ""
            data_dict["is_like"] = row[6]
            data_dict["update_time"] = row[7].strftime("%Y-%m-%d %H:%M:%S")
            data_dict["is_public"] = 0
            ready_list.append(data_dict)
        cursor.close()
    else:  #个人相册，其他ID是相册ID
        where_clause = "user_id=%d and res_type=1 and status=1 and album_id=%d" % (request.user.id, album_id)
        cursor = connections[DB_READ_NAME].cursor()
        sql = "select count(*) from auth_asset where %s" % where_clause
        #print sql
        cursor.execute(sql)
        row = cursor.fetchone()
        if row: total_count = row[0]
        
        order_by = "update_time desc"
        if is_like:
            order_by = "is_like desc," + order_by
        sql = "select id,res_title,res_path,img_large_path,img_medium_path,img_small_path,is_like,update_time from auth_asset where %s" % where_clause
        sql += " order by %s LIMIT %s, %s" % (order_by, (page_index-1)*page_size, page_size)
        #print sql
        cursor = connections[DB_READ_NAME].cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        for row in rows:
            data_dict = {}
            data_dict["id"] = row[0]
            data_dict["title"] = row[1]
            data_dict["url"] = MEDIA_URL + row[2]
            data_dict["large"] = MEDIA_URL + row[3] if row[3] else ""
            data_dict["medium"] = MEDIA_URL + row[4] if row[4] else ""
            data_dict["small"] = MEDIA_URL + row[5] if row[5] else ""
            data_dict["is_like"] = row[6]
            data_dict["update_time"] = row[7].strftime("%Y-%m-%d %H:%M:%S")
            data_dict["is_public"] = 0
            ready_list.append(data_dict)
        cursor.close()
    page_count = int(ceil(total_count/float(page_size)))
    return SuccessResponse({"data":ready_list, "page_index": page_index, "page_count": page_count})


@login_required    
def fetch_scrawl_list(request, param):
    """
        得到涂鸦列表
    """
    if param.has_key("is_like"): is_like = int(param.is_like)
    else: is_like = 0
    if param.has_key("page_index"): page_index = int(param.page_index)
    else: page_index = 1
    if param.has_key("page_size"): page_size = int(param.page_size)
    else: page_size = 20

    ready_list = [] 
    auth_asset_dict = fetch_auth_asset(request.user.id, res_type=4, is_like=is_like)  #个人涂鸦类型是4
    total_count = len(auth_asset_dict)
    page_count = int(ceil(total_count/float(page_size)))
    
    sorted_list = sorted(auth_asset_dict.items(), key=lambda d:d[1]['update_time'], reverse=True)
    sorted_id_list = [item[0] for item in sorted_list]
    back_id_list = sorted_id_list[(page_index-1)*page_size:page_index*page_size]
    #print sorted_id_list, back_id_list
    for id in back_id_list:
        ready_list.append(auth_asset_dict[id])
    return SuccessResponse({"data":ready_list, "page_index": page_index, "page_count": page_count})





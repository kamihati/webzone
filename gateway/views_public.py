#coding: utf-8
'''
Created on 2014-4-14

@author: Administrator
'''
import os
from math import ceil
from django.db import connection, connections
from WebZone.settings import DB_READ_NAME

from WebZone.conf import ZONE_RES_STYLE, ZONE_RES_TYPE

from WebZone.settings import MEDIA_URL

from utils.enum import zone_res_type_name, zone_res_style_name
from utils.decorator import login_required

from diy.models import ZoneAsset, ZoneAssetTemplate
from gateway import SuccessResponse, FailResponse


@login_required
def get_public_url(request, id):
    try: zone_asset = ZoneAsset.objects.get(id=id)
    except(ZoneAsset.DoesNotExist): return FailResponse(u'资源ID(%s)不存在' % id)
    
    #非公共资源，只能自己图书馆下的用户可以使用
    if zone_asset.library:
        if zone_asset.library <> request.user.library:
            return FailResponse(u'没有权限')

    data_dict = {"id":id}
    #data_dict["origin"] = request.build_absolute_uri(MEDIA_URL + zone_asset.res_path)
    data_dict["origin"] = MEDIA_URL + zone_asset.res_path
    if zone_asset.res_type in (1,2,3,4):   #only image resource has this property
        #data_dict["large"] = request.build_absolute_uri(MEDIA_URL + zone_asset.img_large_path)
        #data_dict["medium"] = request.build_absolute_uri(MEDIA_URL + zone_asset.img_medium_path)
        #data_dict["small"] = request.build_absolute_uri(MEDIA_URL + zone_asset.img_small_path)
        data_dict["large"] = MEDIA_URL + zone_asset.img_large_path
        data_dict["medium"] = MEDIA_URL + zone_asset.img_medium_path
        data_dict["small"] = MEDIA_URL + zone_asset.img_small_path
    if zone_asset.res_type == 3:    #画框需要带mask层
        img_mask_path = '%s_mask%s' % (os.path.splitext(zone_asset.res_path))
        #data_dict["mask"] = request.build_absolute_uri(MEDIA_URL + img_mask_path)
        data_dict["mask"] = MEDIA_URL + img_mask_path
    return SuccessResponse(data_dict)


@login_required  
def get_zone_list(request, type_id=0, style_id=0, page_index=1, page_size=20):
    """
        现已弃用:2014-06-24
    """
    if request.user.library: where_clause = "(library_id is null or library_id=%d)" % request.user.library.id
    else: where_clause = "library_id is null"
    if type_id <> 0:
        if ZONE_RES_TYPE.has_key(type_id): where_clause += " and res_type=%d" % type_id
        else: return FailResponse(u'不存在的资源类型:%d' % type_id)
    if style_id <> 0:
        if ZONE_RES_STYLE.has_key(style_id): where_clause += " and res_style=%d" % style_id
        else: return FailResponse(u'不存在的资源风格:%d' % style_id)
    
    where_clause += " and status=1"
    cursor = connections[DB_READ_NAME].cursor()
    sql = "select count(*) from zone_asset where %s" % where_clause
    #print sql
    cursor.execute(sql)
    row = cursor.fetchone()
    count = 0
    if row: count = row[0]
    page_count = int(ceil(count/float(page_size)))
    
    sql = "select id,res_title,res_type,res_style,res_path,img_large_path,img_medium_path,img_small_path,create_time,width,height,mask_path From zone_asset where %s order by create_time DESC LIMIT %s, %s" % (where_clause, (page_index-1)*page_size, page_size)
    #print sql
    cursor = connection.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    
    data_lists = []
    for row in rows:
        data_dict = {}
        data_dict["id"] = row[0]
        data_dict["title"] = row[1]
        data_dict["type_id"] = row[2]
        data_dict["type_name"] = zone_res_type_name(data_dict["type_id"])
        data_dict["style_id"] = row[3]
        data_dict["style_name"] = zone_res_style_name(data_dict["style_id"])
        #data_dict["origin"] = request.build_absolute_uri(MEDIA_URL + row[4])
        data_dict["origin"] = MEDIA_URL + row[4]
        if data_dict["type_id"] in (1,2,3,4):   #only image resource has this property
            data_dict["width"] = row[9]
            data_dict["height"] = row[10]
            #data_dict["large"] = request.build_absolute_uri(MEDIA_URL + row[5])
            #data_dict["medium"] = request.build_absolute_uri(MEDIA_URL + row[6])
            #data_dict["small"] = request.build_absolute_uri(MEDIA_URL + row[7])
            data_dict["large"] = MEDIA_URL + row[5]
            data_dict["medium"] = MEDIA_URL + row[6]
            data_dict["small"] = MEDIA_URL + row[7]
        if data_dict["type_id"] == 3:    #画框需要带mask层
            img_mask_path = '%s_mask%s' % (os.path.splitext(row[4]))
            #data_dict["mask"] = request.build_absolute_uri(MEDIA_URL + img_mask_path)
            data_dict["mask"] = MEDIA_URL + img_mask_path
        data_dict["create_time"] = row[8].strftime("%Y-%m-%d %H:%M:%S")
        data_lists.append(data_dict)
    cursor.close()
    return SuccessResponse({"data":data_lists, "page_index": page_index, "page_count": page_count})


@login_required  
def get_bg_list(request, style_id=0, page_index=1, page_size=20):
#     if request.user.library: where_clause = "(library_id is null or library_id=%d)" % request.user.library.id
#     else: where_clause = "library_id is null"
#     where_clause += " and res_type=1"
    where_clause = "res_type=1 and status=1"
    try: style_id = int(style_id)
    except: style_id = 0
    if style_id <> 0:
        if ZONE_RES_STYLE.has_key(style_id): where_clause += " and res_style=%d" % style_id
        else: return FailResponse(u'不存在的资源风格:%s' % style_id)
        
    cursor = connections[DB_READ_NAME].cursor()
    sql = "select count(*) from zone_asset where %s" % where_clause
    #print sql
    cursor.execute(sql)
    row = cursor.fetchone()
    count = 0
    if row: count = row[0]
    page_count = int(ceil(count/float(page_size)))
    
    sql = "select id,res_title,res_style,width,height,img_large_path,img_small_path From zone_asset where %s order by create_time DESC LIMIT %s, %s" % (where_clause, (page_index-1)*page_size, page_size)
    #print sql
    cursor = connection.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    
    data_lists = []
    for row in rows:
        data_dict = {}
        data_dict["id"] = row[0]
        data_dict["title"] = row[1]
        data_dict["style_id"] = row[2]
        data_dict["style_name"] = zone_res_style_name(data_dict["style_id"])
        data_dict["width"] = row[3]
        data_dict["height"] = row[4]
        #data_dict["url"] = request.build_absolute_uri(MEDIA_URL + row[5])
        #data_dict["small"] = request.build_absolute_uri(MEDIA_URL + row[6])
        data_dict["url"] = MEDIA_URL + row[5]
        data_dict["small"] = MEDIA_URL + row[6]
        data_lists.append(data_dict)
    cursor.close()
    return SuccessResponse({"data":data_lists, "page_index": page_index, "page_count": page_count})

@login_required  
def get_bg_list2(request, param):
    '''背景列表，需要根据单双页显示背景，以前接口还保留过渡 2014-08-15'''
    if param.has_key("style_id"): style_id = param.style_id
    else: style_id = 0
    if param.has_key("page_type"): page_type = param.page_type
    else: page_type = 0
    if param.has_key("page_index"): page_index = param.page_index
    else: page_index = 1
    if param.has_key("page_size"): page_size = param.page_size
    else: page_size = 20
    
    where_clause = "res_type=1 and status=1"
    if page_type <> 0 :
        where_clause += " and (page_type=%s or page_type=0)" % page_type
    try: style_id = int(style_id)
    except: style_id = 0
    if style_id <> 0:
        if ZONE_RES_STYLE.has_key(style_id): where_clause += " and res_style=%d" % style_id
        else: return FailResponse(u'不存在的资源风格:%s' % style_id)
        
    cursor = connections[DB_READ_NAME].cursor()
    sql = "select count(*) from zone_asset where %s" % where_clause
    #print sql
    cursor.execute(sql)
    row = cursor.fetchone()
    count = 0
    if row: count = row[0]
    page_count = int(ceil(count/float(page_size)))
    
    sql = "select id,res_title,res_style,width,height,img_large_path,img_small_path,page_type From zone_asset where %s order by create_time DESC LIMIT %s, %s" % (where_clause, (page_index-1)*page_size, page_size)
    #print sql
    cursor.execute(sql)
    rows = cursor.fetchall()
    
    data_lists = []
    from manager.views import zone_page_name
    for row in rows:
        data_dict = {}
        data_dict["id"] = row[0]
        data_dict["title"] = row[1]
        data_dict["style_id"] = row[2]
        data_dict["style_name"] = zone_res_style_name(data_dict["style_id"])
        data_dict["width"] = row[3]
        data_dict["height"] = row[4]
        #data_dict["url"] = request.build_absolute_uri(MEDIA_URL + row[5])
        #data_dict["small"] = request.build_absolute_uri(MEDIA_URL + row[6])
        data_dict["url"] = MEDIA_URL + row[5]
        data_dict["small"] = MEDIA_URL + row[6]
        data_dict["page_name"] = zone_page_name(row[7])
        data_lists.append(data_dict)
    cursor.close()
    return SuccessResponse({"data":data_lists, "page_index": page_index, "page_count": page_count})

@login_required  
def get_decorator_list(request, style_id=0, page_index=1, page_size=20):
#     if request.user.library: where_clause = "(library_id is null or library_id=%d)" % request.user.library.id
#     else: where_clause = "library_id is null"
#     where_clause += " and res_type=2"
    where_clause = "res_type=2 and status=1"
    if style_id <> 0:
        if ZONE_RES_STYLE.has_key(style_id): where_clause += " and res_style=%d" % style_id
        else: return FailResponse(u'不存在的资源风格:%d' % style_id)
        
    cursor = connections[DB_READ_NAME].cursor()
    sql = "select count(*) from zone_asset where %s" % where_clause
    #print sql
    cursor.execute(sql)
    row = cursor.fetchone()
    count = 0
    if row: count = row[0]
    page_count = int(ceil(count/float(page_size)))
    
    sql = "select id,res_title,res_style,width,height,img_medium_path,img_small_path From zone_asset where %s order by create_time DESC LIMIT %s, %s" % (where_clause, (page_index-1)*page_size, page_size)
    #print sql
    cursor.execute(sql)
    rows = cursor.fetchall()
    
    data_lists = []
    for row in rows:
        data_dict = {}
        data_dict["id"] = row[0]
        data_dict["title"] = row[1]
        data_dict["style_id"] = row[2]
        data_dict["style_name"] = zone_res_style_name(data_dict["style_id"])
        data_dict["width"] = row[3]
        data_dict["height"] = row[4]
        #data_dict["url"] = request.build_absolute_uri(MEDIA_URL + row[5])
        #data_dict["small"] = request.build_absolute_uri(MEDIA_URL + row[6])
        data_dict["url"] = MEDIA_URL + row[5]
        data_dict["small"] = MEDIA_URL + row[6]
        data_lists.append(data_dict)
    cursor.close()
    return SuccessResponse({"data":data_lists, "page_index": page_index, "page_count": page_count})


@login_required  
def get_frame_list(request, style_id=0, page_index=1, page_size=20):
#     if request.user.library: where_clause = "(library_id is null or library_id=%d)" % request.user.library.id
#     else: where_clause = "library_id is null"
#     where_clause += " and res_type=3"
    where_clause = "res_type=3 and status=1"
    if style_id <> 0:
        if ZONE_RES_STYLE.has_key(style_id): where_clause += " and res_style=%d" % style_id
        else: return FailResponse(u'不存在的资源风格:%d' % style_id)
        
    cursor = connections[DB_READ_NAME].cursor()
    sql = "select count(*) from zone_asset where %s" % where_clause
    #print sql
    cursor.execute(sql)
    row = cursor.fetchone()
    count = 0
    if row: count = row[0]
    page_count = int(ceil(count/float(page_size)))
    
    sql = "select id,res_title,res_style,res_path,mask_path,width,height,img_medium_path,img_small_path From zone_asset where %s order by create_time DESC LIMIT %s, %s" % (where_clause, (page_index-1)*page_size, page_size)
    #print sql
    cursor.execute(sql)
    rows = cursor.fetchall()
    
    data_lists = []
    for row in rows:
        if not row[3] or not row[4]:
            continue
        data_dict = {}
        data_dict["id"] = row[0]
        data_dict["title"] = row[1]
        data_dict["style_id"] = row[2]
        data_dict["style_name"] = zone_res_style_name(data_dict["style_id"])
        data_dict["url"] = MEDIA_URL + row[3]
        data_dict["mask"] = MEDIA_URL + row[4]
        data_dict["width"] = row[5]
        data_dict["height"] = row[6]
        #data_dict["medium"] = MEDIA_URL + row[7]
        data_dict["small"] = MEDIA_URL + row[8]
        data_lists.append(data_dict)
    cursor.close()
    return SuccessResponse({"data":data_lists, "page_index": page_index, "page_count": page_count})

@login_required  
def get_template_list(request, style_id=0, page_index=1, page_size=20):
#     if request.user.library: where_clause = "(library_id is null or library_id=%d)" % request.user.library.id
#     else: where_clause = "library_id is null"
#     where_clause += " and res_type=4"
    where_clause = "res_type=4 and status=1"
    if style_id <> 0:
        if ZONE_RES_STYLE.has_key(style_id): where_clause += " and res_style=%d" % style_id
        else: return FailResponse(u'不存在的资源风格:%d' % style_id)
    
    cursor = connections[DB_READ_NAME].cursor()
    sql = "select count(*) from zone_asset where %s" % where_clause
    #print sql
    cursor.execute(sql)
    row = cursor.fetchone()
    count = 0
    if row: count = row[0]
    page_count = int(ceil(count/float(page_size)))
    
    sql = "select id,res_title,res_style,img_small_path,page_count,width,height From zone_asset where %s order by create_time DESC LIMIT %s, %s" % (where_clause, (page_index-1)*page_size, page_size)
    #print sql
    cursor.execute(sql)
    rows = cursor.fetchall()
    
    data_lists = []
    for row in rows:
        data_dict = {}
        data_dict["id"] = row[0]
        data_dict["title"] = row[1]
        data_dict["style_id"] = row[2]
        data_dict["style_name"] = zone_res_style_name(data_dict["style_id"])
        #data_dict["small"] = request.build_absolute_uri(MEDIA_URL + row[3])
        data_dict["small"] = MEDIA_URL + row[3]
        data_dict["page_count"] = row[4]
        data_dict["width"] = row[5]
        data_dict["height"] = row[6]
        data_lists.append(data_dict)
    cursor.close()
    return SuccessResponse({"data":data_lists, "page_index": page_index, "page_count": page_count})


@login_required  
def get_template_list2(request, type_id=0, class_id=0, page_index=1, page_size=20):
    """
    2014-07-11新接口，旧接口临时过渡，还需要使用
        据作品分类查模板列表
    edit: kamihati 2015/5/29    返回值中增加所属作品id
    edit: kamihati 2015/6/8 返回值增加size_id
    """
    #     if request.user.library: where_clause = "(library_id is null or library_id=%d)" % request.user.library.id
    #     else: where_clause = "library_id is null"
    print 'get_template_list2.param='
    print type_id, class_id
    type_id = int(type_id)
    class_id = int(class_id)
    page_index = int(page_index)
    page_size = int(page_size)
    where_clause = "res_type=4 and status=1"
    # from gateway.views_opus import check_opus_type
    # check_result = check_opus_type(type_id, class_id)
    # if check_result <> "ok": return FailResponse(check_result)
    if type_id <> 0:
        where_clause += " and type_id=%s" % type_id
    if class_id <> 0:
        where_clause += " and class_id=%s" % class_id
    
    cursor = connections[DB_READ_NAME].cursor()
    sql = "select count(*) from zone_asset where %s" % where_clause
    #print sql
    cursor.execute(sql)
    row = cursor.fetchone()
    count = 0
    if row: count = row[0]
    page_count = int(ceil(count/float(page_size)))
    sql = "select id,res_title,res_style,img_small_path,page_count,width,height,opus_id,size_id " \
          "From zone_asset where %s " \
          "order by create_time DESC " \
          "LIMIT %s, %s" % (where_clause, (page_index-1) * page_size, page_size)

    cursor.execute(sql)
    rows = cursor.fetchall()
    data_lists = []
    for row in rows:
        data_dict = {}
        data_dict["id"] = row[0]
        data_dict["title"] = row[1]
        data_dict["style_id"] = row[2]
        data_dict["style_name"] = zone_res_style_name(data_dict["style_id"])
        #data_dict["small"] = request.build_absolute_uri(MEDIA_URL + row[3])
        data_dict["small"] = MEDIA_URL + row[3]
        data_dict["page_count"] = row[4]
        data_dict["width"] = row[5]
        data_dict["height"] = row[6]
        data_dict['opus_id'] = row[7]
        data_dict['size_id'] = row[8]
        data_lists.append(data_dict)

    cursor.close()
    return SuccessResponse({"data":data_lists, "page_index": page_index, "page_count": page_count})


def get_system_template(request, param=dict()):
    '''
    获取系统分类的模板
    editor: kamihati 2015/6/16
    :param request:
    :param param:
    :return:
    '''
    page_index = int(param.page_index) if param.has_key('page_index') else 1
    page_size = int(param.page_size) if param.has_key('page_size') else 8
    # 默认读预告模版
    opus_type = int(param.opus_type) if param.has_key('opus_type') else 59

    from utils.db_handler import get_sql_data
    from activity.fruit_handler import n_opus_type
    where_clause = "res_type=4 and status=1 AND type_id=%s" % opus_type

    sql = "select count(*) from zone_asset where %s" % where_clause
    row = get_sql_data(sql)
    count = 0
    if row:
        count = row[0][0]
    page_count = int(ceil(count/float(page_size)))

    sql = "select id,res_title,res_style,img_small_path,page_count,width,height,opus_id,size_id " \
          "From zone_asset where %s " \
          "order by create_time DESC " \
          "LIMIT %s, %s" % (where_clause, (page_index-1) * page_size, page_size)
    print sql
    rows = get_sql_data(sql)

    data_lists = []
    for row in rows:
        data_dict = {}
        data_dict["id"] = row[0]
        data_dict["title"] = row[1]
        data_dict["style_id"] = row[2]
        data_dict["style_name"] = zone_res_style_name(data_dict["style_id"])
        #data_dict["small"] = request.build_absolute_uri(MEDIA_URL + row[3])
        data_dict["small"] = MEDIA_URL + row[3]
        data_dict["page_count"] = row[4]
        data_dict["width"] = row[5]
        data_dict["height"] = row[6]
        data_dict['opus_id'] = row[7]
        data_dict['size_id'] = row[8]
        data_lists.append(data_dict)
    return SuccessResponse(dict(data=data_lists, page_index=page_index, page_count=page_count))


@login_required  
def get_audio_list(request, page_index=1, page_size=20):
#     if request.user.library: where_clause = "(library_id is null or library_id=%d)" % request.user.library.id
#     else: where_clause = "library_id is null"
#     where_clause += " and res_type=5"
    where_clause = "res_type=5 and status=1"

    cursor = connections[DB_READ_NAME].cursor()
    sql = "select count(*) from zone_asset where %s" % where_clause
    #print sql
    cursor.execute(sql)
    row = cursor.fetchone()
    count = 0
    if row: count = row[0]
    page_count = int(ceil(count/float(page_size)))
    
    sql = "select id,res_title,res_path,codec_status From zone_asset where %s order by create_time DESC LIMIT %s, %s" % (where_clause, (page_index-1)*page_size, page_size)
    #print sql
    cursor.execute(sql)
    rows = cursor.fetchall()
    
    data_lists = []
    for row in rows:
        data_dict = {}
        data_dict["id"] = row[0]
        data_dict["title"] = row[1]
        #data_dict["url"] = request.build_absolute_uri(MEDIA_URL + row[2])
        data_dict["url"] = MEDIA_URL + row[2]
        data_dict["codec_status"] = row[3]  #转码状态：0:正在转码，1:转码成功，-1:转码失败
        data_lists.append(data_dict)
    cursor.close()
    return SuccessResponse({"data":data_lists, "page_index": page_index, "page_count": page_count})


@login_required  
def get_video_list(request, page_index=1, page_size=20):
#     if request.user.library: where_clause = "(library_id is null or library_id=%d)" % request.user.library.id
#     else: where_clause = "library_id is null"
#     where_clause += " and res_type=6"
    where_clause = "res_type=6 and status=1"

    cursor = connections[DB_READ_NAME].cursor()
    sql = "select count(*) from zone_asset where %s" % where_clause
    #print sql
    cursor.execute(sql)
    row = cursor.fetchone()
    count = 0
    if row: count = row[0]
    page_count = int(ceil(count/float(page_size)))
    
    sql = "select id,res_title,res_path,codec_status From zone_asset where %s order by create_time DESC LIMIT %s, %s" % (where_clause, (page_index-1)*page_size, page_size)
    #print sql
    cursor.execute(sql)
    rows = cursor.fetchall()
    
    data_lists = []
    for row in rows:
        data_dict = {}
        data_dict["id"] = row[0]
        data_dict["title"] = row[1]
        #data_dict["url"] = request.build_absolute_uri(MEDIA_URL + row[2])
        data_dict["url"] = MEDIA_URL + row[2]
        data_dict["codec_status"] = row[3]  #转码状态：0:正在转码，1:转码成功，-1:转码失败
        data_lists.append(data_dict)
    cursor.close()
    return SuccessResponse({"data":data_lists, "page_index": page_index, "page_count": page_count})


@login_required  
def get_template_info(request, zone_asset_id):
    """
        得到模板的每页的详细信息
        editor: kamihati 2015/6/17
    """
    print 'get_template_info=', zone_asset_id
    try:
        zone_asset = ZoneAsset.objects.get(id=zone_asset_id)
    except(ZoneAsset.DoesNotExist):
        return FailResponse(u'模板ID:%s不存在' % zone_asset_id)

    #非公共资源，只能自己图书馆下的用户可以使用
    #if zone_asset.library:
    #    if zone_asset.library <> request.user.library:
    #        return FailResponse(u'没有权限')
    
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
    template_dict['size_id'] = zone_asset.size_id
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
def get_blank_opus(request, param):
    """
        活动新建封面时用，返回一个空的作品信息，以便创建封面用
    """
    from datetime import datetime
    if param.has_key("title"): title = param.title
    else: title = u"未命名作品"
    opus_info = {}
    opus_info["id"] = 0
    opus_info["user_id"] = 0
    opus_info["title"] = title
    opus_info["brief"] = ""
    opus_info["tags"] = ""
    
    opus_info["create_type"] = 0
    opus_info["read_type"] = 0
    
    opus_info["type_id"] = 0
    opus_info["class_id"] = 0
    opus_info["page_count"] = 1
    opus_info["pages"] = {}
    
    opus_info["pages"]["page_index"] = 1
    opus_info["pages"]["media"] = 0
    opus_info["pages"]["orign"] = 0
    opus_info["pages"]["small"] = 0
    opus_info["pages"]["json"] = 0
    
    opus_info["is_top"] = 0
    opus_info["grade"] = 0
    
    opus_info["preview_times"] = 0
    opus_info["comment_times"] = 0
    opus_info["praise_times"] = 0
    opus_info["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    opus_info["create_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    opus_info["status"] = 0
    
    opus_info["width"] = 886
    opus_info["height"] = 744
    return SuccessResponse(opus_info)            

@login_required
def new_blank_page(request, param):
    opus_id, page_index, template_id, template_page_index = 0, 0, 0, 0

    page_dict = {"page_index":page_index}
    page_dict["media"] = 0
    page_dict["orign"] = MEDIA_URL + "blank.jpg"
    page_dict["small"] = MEDIA_URL + "blank_s.jpg"
    page_dict["json"] = MEDIA_URL + "blank.json"
        
    return SuccessResponse({"id":opus_id,"page":page_dict, "page_index":page_index,
                            "json":MEDIA_URL + "blank.json",
                            "url":MEDIA_URL + "blank.jpg", "thumbnail":MEDIA_URL + "blank_s.jpg"})
    




#coding: utf-8
'''
Created on 2014年12月3日

@author: Administrator
'''
from math import ceil
from django.db import connection, connections
from django.core.cache import cache
from WebZone.settings import MEDIA_URL
from WebZone.settings import DB_READ_NAME

from datetime import datetime, date, timedelta
import random
import hashlib

from utils.decorator import login_required
from utils import get_ip

from gateway import SuccessResponse, FailResponse

from activity.models import ActivityList
from activity.models import ActivityOption
from activity.models import ActivityGroup
from activity.models import ActivityFruit
from activity.models import ActivityVote
from activity.models import ActivityGrade
from activity.models import ActivityComment
from activity.models import ActivityPraise
from account.models import AuthUser
from activity.models import ActivityMember
from widget.models import WidgetDistrict

from utils.decorator import print_trace
from diy.models import AuthAsset, AuthOpus

from utils.decorator import print_exec_time
# mark: kamihati 2015/3/26 获取指定id的活动或作品id供amf调用。此处逻辑极其没有效率。亟待调整
from activity.handler import get_activity_for_amf, get_activity_fruit_for_amf

# 获取查询活动和作品的混合分页方法
from activity.handler import search_activity

def get_activity_district_id(activity_id):
    cache_key = "gateway.views_activity.get_activity_district_id:%d" % activity_id
    id_list = cache.get(cache_key, [])
    if not id_list:
        cursor = connections[DB_READ_NAME].cursor()
        sql = "select DISTINCT(district_id) From activity_fruit where activity_id=%d and status=2" % activity_id
        cursor.execute(sql)
        rows = cursor.fetchall()
        for row in rows:
            if not row[0]: continue
            district_id_str = str(row[0])
            while len(district_id_str) > 0:
                district_id = int(district_id_str)
                if id_list.count(district_id) == 0:
                    id_list.append(district_id)
                district_id_str = district_id_str[:len(district_id_str)-2]
        cache.set(cache_key, id_list)
    return ','.join([str(i) for i in id_list])
    

@login_required
def get_province_list(request, param):
    if param.has_key("activity_id"): activity_id = int(param.activity_id)
    else: activity_id = 0   #为零时返回所有省

    cursor = connections[DB_READ_NAME].cursor()
    sql = "select id,name From widget_district where parent_id=0"
    if activity_id:
        sql += " and id in (%s) order by id" % get_activity_district_id(activity_id)
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()
    data_lists = []
    for row in rows:
        data_lists.append({"id":row[0], "name":row[1]})
    return SuccessResponse(data_lists)

@login_required
def get_city_list(request, param):
    if param.has_key("activity_id"): activity_id = int(param.activity_id)
    else: activity_id = 0   #为零时返回所有市
    if param.has_key("province_id"): province_id = int(param.province_id)
    else: return FailResponse(u"必须传入省ID")
    
    if WidgetDistrict.objects.filter(id=province_id).count() == 0:
        return FailResponse(u"省id不正确")
    
    cursor = connections[DB_READ_NAME].cursor()
    sql = "select id,name From widget_district where parent_id=%d" % province_id
    if activity_id:
        sql += " and id in (%s) order by id" % get_activity_district_id(activity_id)
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()
    data_lists = []
    for row in rows:
        data_lists.append({"id":row[0], "name":row[1]})
    return SuccessResponse(data_lists)

@login_required
def get_county_list(request, param):
    if param.has_key("activity_id"): activity_id = int(param.activity_id)
    else: activity_id = 0   #为零时返回所有县
    if param.has_key("city_id"): city_id = int(param.city_id)
    else: return FailResponse(u"必须传入市ID")
    
    if WidgetDistrict.objects.filter(id=city_id).count() == 0:
        return FailResponse(u"市id不正确")
    
    cursor = connections[DB_READ_NAME].cursor()
    sql = "select id,name From widget_district where parent_id=%d" % city_id
    if activity_id:
        sql += " and id in (%s) order by id" % get_activity_district_id(activity_id)
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()
    data_lists = []
    for row in rows:
        data_lists.append({"id":row[0], "name":row[1]})
    return SuccessResponse(data_lists)    

def get_period(submit_start_time, submit_end_time):
    submit_start_time = datetime.strptime(submit_start_time, "%Y-%m-%d %H:%M:%S")
    submit_end_time = datetime.strptime(submit_end_time, "%Y-%m-%d %H:%M:%S")
    if datetime.now() < submit_start_time: return 0
    elif datetime.now() > submit_end_time: return 2
    else: return 1


@print_trace
@login_required
def fetch_activity_list(request, param):
    """
        得到活动列表
        editor: kamihati 2015/4/14   临时修改给省少儿使用
        editor: kamihati 2015/4/15   省少儿分为两个机构。一个只能看到全国范围的活动。一个只能看到省范围的活动
        editor: kamihati 2015/5/13 数据结果增加系列活动主活动的显示
    """
    is_top = 0
    if param.has_key("is_top"):
        is_top = int(param.is_top)
    page_index = 1
    if param.has_key("page_index"):
        page_index = int(param.page_index)
    page_size = 20
    if param.has_key("page_size"):
        page_size = int(param.page_size)

    type = param.type if param.has_key('type') else ''
    where_clause = "l.status<>-1"
    from library.handler import get_library_by_request
    library = get_library_by_request(request)
    if library is not None and library.is_global == 0:
        where_clause += ' AND l.library_id=%s' % library.id
    # else:
    #    where_clause += ' AND l.library_id=%s' % library
    if is_top:
        where_clause += " and is_top=1"
    if type == 'activity':
        where_clause += ' AND fruit_type<>0'
    elif type == 'series':
        where_clause += ' AND fruit_type=0'

    cursor = connections[DB_READ_NAME].cursor()
    # sql = "select count(*) from activity_list where %s" % where_clause.replace("l.library_id", "library_id")
    sql = "select count(*) from view_search_activity_list where %s" % where_clause.replace("l.library_id", "library_id").replace('l.status', 'status')
    cursor.execute(sql)
    row = cursor.fetchone()
    if row: total_count = row[0]
    else: total_count = 0
    page_count = int(ceil(total_count/float(page_size)))
    sql = "select l.id,l.library_id,user_id,title,submit_start_time,submit_end_time,cover,thumbnail"
    sql += ",fruit_type,can_submit,need_group,can_vote,vote_start_time,vote_end_time"
    sql += ",need_fruit_name,need_fruit_brief,need_author_name,need_author_brief,need_author_sex,need_author_age,need_author_school"
    sql += ",opus_id,sponsor_name,is_top,need_unit,need_district,need_author_telephone,need_author_email,status,scope_list, period,activity_img,link_url,description,sign_up_start_time,sign_up_end_time"
    # sql += " from activity_list l LEFT JOIN activity_option o on l.id=o.activity_id"
    sql += ' from view_search_activity_list l'
    sql += " where %s" % where_clause
    sql += " order by if(is_top<>0, 0, 1),is_top,l.id DESC"
    sql += " LIMIT %s, %s" % ((page_index-1)*page_size, page_size)
    # print sql
    cursor.execute(sql)
    rows = cursor.fetchall()

    back_list = []
    # 导入字符串转日期的方法
    from utils.decorator import format_str_to_datetime, format_datetime_to_str
    for row in rows:
        id = int(row[0])
        library_id = int(row[1])
        user_id = int(row[2])
        title = row[3]

        submit_start_time = format_str_to_datetime(row[4]) if row[4] else ""
        submit_end_time = format_str_to_datetime(row[5]) if row[5] else ""
        cover = MEDIA_URL + row[6] if row[6] else ""
        thumbnail = MEDIA_URL + row[7] if row[7] else ""
        
        #(1,u"新闻播报"),(2,u"电子创作"),(3,u"图片"),(4,u"视频")
        fruit_type = int(row[8])
        can_submit = int(row[9])
        need_group = int(row[10])
        can_vote = int(row[11])
        vote_start_time = format_str_to_datetime(row[12]) if row[12] else ""
        vote_end_time = format_str_to_datetime(row[13]) if row[13] else ""

        need_fruit_name = int(row[14]) if row[14] else 0
        need_fruit_brief = int(row[15]) if row[15] else 0
        need_author_name = int(row[16]) if row[16] else 0
        need_author_brief = int(row[17]) if row[17] else 0
        need_author_sex = int(row[18]) if row[18] else 0
        need_author_age = int(row[19]) if row[19] else 0
        need_author_school = int(row[20]) if row[20] else 0

        # editor: kamihati 2015/6/16  当仅有一个作品存在时（一般为活动预告）赋值。供客户端直接打开作品
        # 否则置为0.客户端点击活动图标后打开作品列表
        opus_id = 0
        if ActivityFruit.objects.filter(activity_id=id, status=2).count() == 1:
            opus_id = ActivityFruit.objects.filter(activity_id=id, status=2)[0].opus_id
        sponsor_name = row[22] if row[22] else ""
        is_top = int(row[23]) if row[23] else 0
        need_unit = int(row[24]) if row[24] else 0
        need_district = int(row[25]) if row[25] else 0
        
        need_author_telephone = int(row[26]) if row[26] else 0
        need_author_email = int(row[27]) if row[27] else 0
        status = int(row[28]) if row[28] else 0
        scope_list = row[29]
        period = int(row[30]) if row[30] else 0
        if row[31]:
            activity_img = '/media/' + str(row[31])
        else:
            activity_img = ''
        link_url = row[32]
        description = row[33]
        signup_start_time = format_str_to_datetime(row[34]) if row[34] else ""
        signup_end_time = format_str_to_datetime(row[35]) if row[35] else ""
        # now_period = get_period(submit_start_time, submit_end_time)
        # if now_period <> period:
        #    sql = "update activity_list set period=%d where id=%d" % (now_period, id)
        #    cursor.execute(sql)

        activity_dict = {"id": id, "library_id": library_id, "user_id": user_id, "title": title, "cover": cover, "thumbnail": thumbnail}
        activity_dict["submit_start_time"] = format_datetime_to_str(submit_start_time) if submit_start_time else ''
        activity_dict["submit_end_time"] = format_datetime_to_str(submit_end_time) if submit_end_time else ''
        activity_dict["library_name"] = get_lib_name(library_id)
        activity_dict["fruit_type"] = fruit_type
        # editor: kamihati 2015/6/8 此处从数据库中取出的值目前并不精确。后面会单独判断
        #activity_dict["can_submit"] = can_submit
        activity_dict["need_group"] = need_group
        activity_dict["can_vote"] = can_vote
        activity_dict["vote_start_time"] = format_datetime_to_str(vote_start_time) if vote_start_time else ''
        activity_dict["vote_end_time"] = format_datetime_to_str(vote_end_time) if vote_end_time else ''
        
        activity_dict["need_fruit_name"] = need_fruit_name
        activity_dict["need_fruit_brief"] = need_fruit_brief
        activity_dict["need_author_name"] = need_author_name
        activity_dict["need_author_brief"] = need_author_brief
        activity_dict["need_author_sex"] = need_author_sex
        activity_dict["need_author_age"] = need_author_age
        activity_dict["need_author_school"] = need_author_school
        
        activity_dict["opus_id"] = opus_id
        activity_dict["sponsor_name"] = sponsor_name
        activity_dict["is_top"] = is_top
        activity_dict["need_unit"] = need_unit
        activity_dict["need_district"] = need_district
        
        activity_dict["need_author_telephone"] = need_author_telephone
        activity_dict["need_author_email"] = need_author_email
        activity_dict["status"] = status
        activity_dict["scope_list"] = scope_list
        activity_dict["period"] = 0
        activity_dict['activity_img'] = activity_img
        activity_dict['link_url'] = '/media/' + link_url if link_url else ''
        activity_dict['type'] = 'activity'
        if fruit_type == 0:
            activity_dict['type'] = 'series'
        activity_dict['description'] = description
        # editor: kamihati 2015/6/8   增加能否报名和能否投稿两个参数供客户端使用
        # 是否能够报名
        activity_dict['can_signup'] = 0
        activity_dict['signup_start_time'] = format_datetime_to_str(signup_start_time) if signup_start_time else ''
        activity_dict['signup_end_time'] = format_datetime_to_str(signup_end_time) if signup_end_time else ''
        if signup_end_time != '' and signup_start_time != '':
            if signup_start_time < datetime.now() and signup_end_time > datetime.now():
                activity_dict['can_signup'] = 1

        # 是否能够投稿
        activity_dict['can_submit'] = 0
        if submit_end_time != '' and submit_start_time != '':
            if submit_start_time < datetime.now() and submit_end_time > datetime.now():
                activity_dict['can_submit'] = 1

        if need_group:
            group_names = ""
            sql = "select id,group_name From activity_group where activity_id=%d ORDER BY update_time DESC" % id
            cursor.execute(sql)
            group_rows = cursor.fetchall()
            for group_row in group_rows:
                group_names += "" if len(group_names) == 0 else ";"
                group_names += "%d,%s" % (int(group_row[0]), group_row[1])
            activity_dict["group_names"] = group_names
        back_list.append(activity_dict)
    return SuccessResponse({"data": back_list, "page_index": page_index, "page_count": page_count})


@login_required    
def fetch_activity_info(request, param):
    """
        得到活动列表
    """
    if param.has_key("activity_id"): activity_id = int(param.activity_id)
    else: return FailResponse(u"必须传入活动ID")
    try:
        activity_list = ActivityList.objects.get(id=activity_id)
        activity_option = ActivityOption.objects.get(activity_id=activity_list.id)
    except:
        return FailResponse(u"活动ID不正确  (%d)，请检查重输!" % activity_id)
    
    info = {}
    info["id"] = activity_list.id
    info["library_id"] = activity_list.library_id
    info["library_name"] = get_lib_name(activity_list.library_id)
    
    info["user_id"] = activity_list.user_id
    info["title"] = activity_list.title
    info["submit_start_time"] = activity_list.submit_start_time.strftime("%Y-%m-%d %H:%M:%S") if activity_list.submit_start_time else ""
    info["submit_end_time"] = activity_list.submit_end_time.strftime("%Y-%m-%d %H:%M:%S") if activity_list.submit_end_time else ""
    info["cover"] = MEDIA_URL + activity_list.cover if activity_list.cover else ""
    info["thumbnail"] = MEDIA_URL + activity_list.thumbnail if activity_list.thumbnail else ""
    
    #(1,u"新闻播报"),(2,u"电子创作"),(3,u"图片"),(4,u"视频")
    info["fruit_type"] = activity_list.fruit_type
    info["can_submit"] = activity_list.can_submit
    info["need_group"] = activity_list.need_group
    info["can_vote"] = activity_list.can_vote
    info["vote_start_time"] = activity_list.vote_start_time.strftime("%Y-%m-%d %H:%M:%S") if activity_list.vote_start_time else ""
    info["vote_end_time"] = activity_list.vote_end_time.strftime("%Y-%m-%d %H:%M:%S") if activity_list.vote_end_time else ""
    
    info["need_fruit_name"] = activity_option.need_fruit_name
    info["need_fruit_brief"] = activity_option.need_fruit_brief
    info["need_author_name"] = activity_option.need_author_name
    info["need_author_brief"] = activity_option.need_author_brief
    info["need_author_sex"] = activity_option.need_author_sex
    info["need_author_age"] = activity_option.need_author_age
    info["need_author_school"] = activity_option.need_author_school
    
    info["opus_id"] = activity_list.opus_id
    info["sponsor_name"] = activity_list.sponsor_name if activity_list.sponsor_name else ""
    info["is_top"] = activity_list.is_top
    info["need_unit"] = activity_list.need_unit
    info["need_district"] = activity_list.need_district
    info["need_author_telephone"] = activity_option.need_author_telephone
    info["need_author_email"] = activity_option.need_author_email
    info["status"] = activity_list.status
    info["scope_list"] = activity_list.scope_list
    info["period"] = activity_list.period
    now_period = get_period(info["submit_start_time"], info["submit_end_time"]) #预告，进行中，已结束
    
    cursor = connections[DB_READ_NAME].cursor()
    if now_period <> info["period"]:
        sql = "update activity_list set period=%d where id=%d" % (now_period, activity_list.id)
        cursor.execute(sql)
        info["period"] = now_period
    
    if activity_list.need_group:
        group_names = ""
        sql = "select id,group_name From activity_group where activity_id=%d ORDER BY update_time DESC" % activity_list.id
        cursor.execute(sql)
        group_rows = cursor.fetchall()
        for group_row in group_rows:
            group_names += "" if len(group_names) == 0 else ";"
            group_names += "%d,%s" % (int(group_row[0]), group_row[1])
        info["group_names"] = group_names

    return SuccessResponse(info)


def get_lib_name(lib_id):
    cache_key = "gateway.views_activity.get_lib_name"
    lib_name_dict = cache.get(cache_key, {})
    if not lib_name_dict:
        cursor = connections[DB_READ_NAME].cursor()
        sql = "select id,lib_name from library"
        cursor.execute(sql)
        rows = cursor.fetchall()
        for row in rows:
            id = int(row[0])
            lib_name = row[1]
            lib_name_dict[id] = lib_name
        cache.set(cache_key, lib_name_dict)
    if lib_name_dict.has_key(lib_id):
        return lib_name_dict[lib_id]
    else:
        return u"未知机构名称"

def get_unit_name(unit_id):
    cache_key = "gateway.views_activity.get_unit_name"
    unit_name_dict = cache.get(cache_key, {})
    if not unit_name_dict:
        cursor = connections[DB_READ_NAME].cursor()
        sql = "select id,unit_name from activity_unit"
        cursor.execute(sql)
        rows = cursor.fetchall()
        for row in rows:
            id = int(row[0])
            unit_name = row[1]
            unit_name_dict[id] = unit_name
        cache.set(cache_key, unit_name_dict)
    if unit_name_dict.has_key(unit_id):
        return unit_name_dict[unit_id]
    else:
        return u"未知报送单位"

def get_group_name(group_id):
    cache_key = "gateway.views_activity.get_group_name"
    group_name_dict = cache.get(cache_key, {})
    if not group_name_dict:
        cursor = connections[DB_READ_NAME].cursor()
        sql = "select id,group_name from activity_group"
        cursor.execute(sql)
        rows = cursor.fetchall()
        for row in rows:
            id = int(row[0])
            unit_name = row[1]
            group_name_dict[id] = unit_name
        cache.set(cache_key, group_name_dict)
    if group_name_dict.has_key(group_id):
        return group_name_dict[group_id]
    else:
        return u"未知分组"
    
def get_district_name(district_id):
    cache_key = "gateway.views_activity.get_district_name:%s" % district_id
    district_dict = cache.get(cache_key, {})
    if not district_dict:
        sql = "select id, parent_id, name From widget_district"
        cursor = connections[DB_READ_NAME].cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        for row in rows:
            id = int(row[0])
            parent_id = int(row[1])
            name = row[2]
            district_dict[id] = {"parent_id":parent_id, "name":name}
        cache.set(cache_key, district_dict)
    district_name = district_dict[district_id]['name']
    parent_id = district_dict[district_id]['parent_id']
    while parent_id:
        district_name = district_dict[parent_id]['name'] + "-" + district_name
        parent_id = district_dict[parent_id]['parent_id']
    return district_name


def get_asset_dict(asset_id, fruit_type):
    cursor = connections[DB_READ_NAME].cursor()
    #(3,u"图片"),(4,u"视频")
    sql = "select id,res_path,img_large_path,img_small_path,codec_status from auth_asset where id=%s" % asset_id
    cursor.execute(sql)
    row = cursor.fetchone()
    asset_dict = {}
    if row and row[0]:
        if fruit_type == 3:   #图片
            #id = int(row[0])
            url = MEDIA_URL + row[2]
            small = MEDIA_URL + row[3]
            codec_status = ""
        elif fruit_type == 4:   #视频
            #id = int(row[0])
            url = MEDIA_URL + row[1]
            small = MEDIA_URL + row[3]
            codec_status = int(row[4])
        asset_dict["small"] = small
        asset_dict["url"] = url
        asset_dict["codec_status"] = codec_status
    return asset_dict

def get_opus_dict(opus_id):
    cursor = connections[DB_READ_NAME].cursor()
    #(3,u"图片"),(4,u"视频")
    sql = "select img_small_path from auth_opus_page where auth_opus_id=%s and page_index=1" % opus_id
    cursor.execute(sql)
    row = cursor.fetchone()
    opus_dict = {}
    if row and row[0]:
        opus_dict["small"] = MEDIA_URL + row[0]
    sql = "select id,preview_times,comment_times,praise_times from auth_opus where id=%s" % opus_id
    cursor.execute(sql)
    row = cursor.fetchone()
    if row and row[0]:
        #id = int(row[0])
        opus_dict["preview_times"] = int(row[1])
        opus_dict["comment_times"] = int(row[2])
        opus_dict["praise_times"] = int(row[3])
    return opus_dict


@print_trace    
@login_required    
def fetch_activity_fruit_list(request, param):
    """
        获取活动作品列表
        editor: kamihati 2015/4/30  解决搜索不出结果的问题
    """
    if param.has_key("activity_id"): activity_id = int(param.activity_id)
    # else: return FailResponse(u"必须传入活动ID")
    
    if param.has_key("is_top"): is_top = int(param.is_top)
    else: is_top = 0
    if param.has_key("group_id"): group_id = int(param.group_id)
    else: group_id = 0
    if param.has_key("district_id"): district_id = int(param.district_id)
    else: district_id = 0
    if param.has_key("order_by"): order_by_id = int(param.order_by)
    else: order_by_id = 0
    
    if param.has_key("page_index"): page_index = int(param.page_index)
    else: page_index = 1
    if param.has_key("page_size"): page_size = int(param.page_size)
    else: page_size = 20
    if param.has_key("search_text"): search_text = param.search_text
    else: search_text = ""

    if order_by_id not in (0, 1, 2):
        return FailResponse(u"排序选项:%s不正确" % order_by_id)
    
    try: activity_list = ActivityList.objects.get(id=activity_id)
    except(ActivityList.DoesNotExist): return FailResponse(u"不存在的活动ID")
    
    #发表的，或者当前用户上传且未删除的
    if request.user.is_staff or request.user.is_superuser:
        where_clause = u"(a.status=2 or a.status=1 or (a.status>=-1 and a.user_id=%s))" % request.user.id
    else:
        where_clause = u"(a.status=2 or (a.status>=-1 and a.user_id=%s))" % request.user.id
    where_clause += u" and a.activity_id=%d" % activity_id
    if group_id: where_clause += u" and group_id=%d" % group_id
    if district_id: where_clause += u" and district_id like '%d%%'" % district_id
    
    if is_top:
        where_clause += u" and a.is_top=1"
    if search_text:
        where_clause += u" and (a.fruit_name LIKE '%%%s%%' or a.author_name LIKE '%%%s%%' or a.school_name LIKE '%%%s%%' or a.number LIKE '%%%s%%'  or b.lib_name LIKE '%%%s%%')" % (search_text, search_text, search_text, search_text, search_text)
    # 原版本在此处未对编码做转换导致hashlib.md5函数报错
    # editor: kamihati 2015/4/30  修正
    where_md5 = hashlib.md5(where_clause.encode('utf8')).hexdigest()
    cursor = connections[DB_READ_NAME].cursor()
    
    #opus_type:(0,u"fruit_type作品"),(3,u"活动预告"),(4,u"活动结果")
    order_by = "order by a.opus_type DESC, a.status ASC, a.is_top DESC"
    fruit_id_list = []
    if order_by_id == 0:    #随机排序
        session_fruit_key = "gateway.fetch_activity_fruit_list.opus_id"
        session_fruit_md5 = "gateway.fetch_activity_fruit_list.md5"
        all_id_list = request.session.get(session_fruit_key, [])
        old_where_md5 = request.session.get(session_fruit_md5, None)
        if not all_id_list or (where_md5 <> old_where_md5):
            #print "not found cache"
            all_id_list = []
            sql = "select a.id,a.opus_type from activity_fruit a INNER JOIN library b ON b.id=a.library_id where %s " % where_clause
            cursor.execute(sql)
            rows = cursor.fetchall()
            top_id_list = []
            for row in rows:
                if not row: continue
                fruit_id = int(row[0])
                all_id_list.append(fruit_id)
                opus_type = int(row[1])
                if opus_type == 3:  #活动预告
                    top_id_list.insert(0, fruit_id)
                elif opus_type == 4:    #活动结果
                    top_id_list.append(fruit_id)
            random.shuffle(all_id_list)
            #活动预告，活动结果两项提到前边 2015-01-15
            for top_id in top_id_list:
                all_id_list.remove(top_id)
                all_id_list.insert(0, top_id)
            request.session[session_fruit_key] = all_id_list
            request.session[session_fruit_md5] = where_md5
            
        start_index = (page_index-1)*page_size
        if start_index<0: start_index = 0
        end_index = start_index + page_size
        fruit_id_list = all_id_list[start_index:end_index]
        #print "story_list", story_list
    elif order_by_id == 1:  #1:人气（投票数）
        if activity_list.fruit_type == 2:
            order_by += ",o.preview_times DESC"
        elif activity_list.can_vote:
            order_by += ",vote DESC"
        else:
            order_by += ",a.preview_times DESC"
    elif order_by == 2:  # 2:上传时间
        order_by += ",a.update_time DESC"

    sql = u"select count(*) from activity_fruit a inner join library b ON b.id=a.library_id where %s" % where_clause
    cursor.execute(sql)
    row = cursor.fetchone()
    if row: total_count = row[0]
    else: total_count = 0
    page_count = int(ceil(total_count/float(page_size)))
    
    sql = u"select a.id,a.library_id,a.user_id,number,group_id,auth_asset_id,district_id,unit_id,opus_id"
    sql += u",fruit_name,fruit_brief,author_name,author_brief,author_sex,author_age,school_name"
    sql += u",author_telephone,author_email,score,vote,a.is_top"
    # 由于出现了o.grade为null报错的情况故暂时取消
    # if activity_list.fruit_type == 2:
    #    sql += u",o.grade,o.preview_times,o.comment_times,o.praise_times"
    # else:
    sql += u",a.grade,a.preview_times,a.comment_times,a.praise_times"
    sql += u",a.width,a.height,a.update_time,a.status,a.opus_type From activity_fruit a"
    sql += ' INNER JOIN library b ON b.id=a.library_id '
    if activity_list.fruit_type == 2:
        sql += " LEFT JOIN auth_opus o on o.id=a.opus_id"
    if order_by == 0:
        sql += u" where a.id in (%s)" % ",".join([str(i) for i in fruit_id_list])
    else:
        sql += u" where %s" % where_clause
        sql += u" %s LIMIT %s, %s" % (order_by, (page_index-1)*page_size, page_size)

    cursor.execute(sql)
    rows = cursor.fetchall()
    
    back_list = []
    for row in rows:
        id = int(row[0])
        library_id = int(row[1])
        user_id = int(row[2])
        number = row[3]
        group_id = int(row[4]) if row[4] else 0
        auth_asset_id = int(row[5]) if row[5] else 0
        district_id = int(row[6]) if row[6] else 0
        unit_id = int(row[7]) if row[7] else 0
        opus_id = int(row[8]) if row[8] else 0
        
        fruit_name = row[9]
        fruit_brief = row[10]
        author_name = row[11]
        author_brief = row[12]
        author_sex = int(row[13]) if row[13] else -1
        author_age = int(row[14]) if row[14] else 0
        school_name = row[15] if row[15] else ""
        
        author_telephone = row[16] if row[16] else ""
        author_email = row[17] if row[17] else ""
        score = int(row[18])
        vote = int(row[19])
        is_top = int(row[20])
        grade = int(row[21])
        preview_times = int(row[22])
        comment_times = int(row[23])
        praise_times = int(row[24])
        
        width = int(row[25])
        height = int(row[26])
        update_time = row[27].strftime("%Y-%m-%d %H:%M:%S")
        status = row[28]
        opus_type = row[29] #(0,u"fruit_type作品"),(3,u"活动预告"),(4,u"活动结果")
        
        activity_opus_dict = {"id":id, "library_id":library_id, "user_id":user_id, "number":number, "group_id":group_id, "auth_asset_id":auth_asset_id}
        activity_opus_dict["library_name"] = get_lib_name(library_id)
        activity_opus_dict["group_name"] = get_group_name(group_id)
        
        activity_opus_dict["district_id"] = district_id
        activity_opus_dict["district_name"] = get_district_name(district_id) if district_id else ""
        activity_opus_dict["unit_id"] = unit_id
        activity_opus_dict["unit_name"] = get_unit_name(unit_id)
        activity_opus_dict["opus_id"] = opus_id
        
        activity_opus_dict["fruit_name"] = fruit_name
        activity_opus_dict["fruit_brief"] = fruit_brief
        activity_opus_dict["author_name"] = author_name
        activity_opus_dict["author_brief"] = author_brief
        activity_opus_dict["author_sex"] = author_sex
        activity_opus_dict["author_age"] = author_age
        activity_opus_dict["school_name"] = school_name
        
        activity_opus_dict["author_telephone"] = author_telephone
        activity_opus_dict["author_email"] = author_email
        activity_opus_dict["score"] = score
        activity_opus_dict["vote"] = vote
        activity_opus_dict["is_top"] = is_top
        activity_opus_dict["grade"] = grade
        activity_opus_dict["preview_times"] = preview_times
        activity_opus_dict["comment_times"] = comment_times
        activity_opus_dict["praise_times"] = praise_times
        
        activity_opus_dict["width"] = width
        activity_opus_dict["height"] = height
        activity_opus_dict["update_time"] = update_time
        activity_opus_dict["status"] = status
        activity_opus_dict["opus_type"] = opus_type
        
        activity_opus_dict["fruit_type"] = activity_list.fruit_type

        if opus_type in (3, 4): #活动预告，活动结果
            path_dict = get_opus_dict(opus_id)
        elif activity_list.fruit_type in (1, 2):    #播报，创作
            path_dict = get_opus_dict(opus_id)
        elif activity_list.fruit_type in (3, 4, 5):    #图片，视频
            path_dict = get_asset_dict(auth_asset_id, activity_list.fruit_type)
        activity_opus_dict.update(path_dict)
        
        activity_opus_dict["can_vote"] = activity_list.can_vote
        back_list.append(activity_opus_dict)
        
    return SuccessResponse({"data":back_list, "page_index": page_index, "page_count": page_count})


@login_required
def preview_fruit(request, param):
    if param.has_key("fruit_id"): fruit_id = int(param.fruit_id)
    else: return FailResponse(u"必须传入活动作品ID")
    
    try: activity_fruit = ActivityFruit.objects.get(id=fruit_id)
    except(ActivityFruit.DoesNotExist): return FailResponse(u"不存在的活动作品ID")
    
    if activity_fruit.status <> 2:
        return FailResponse(u'活动作品不是发表状态')

    activity_fruit.preview_times += 1
    activity_fruit.save()
    
    return SuccessResponse({"id":activity_fruit.id, "preview_times":activity_fruit.preview_times})
    

@login_required
def grade_fruit(request, param):
    if param.has_key("fruit_id"): fruit_id = int(param.fruit_id)
    else: return FailResponse(u"必须传入活动作品ID")
    if param.has_key("grade"): grade = int(param.grade)
    else: grade = 0
    
    if request.user.auth_type == 5: return FailResponse(u'游客不能评级!')
    
    try: activity_fruit = ActivityFruit.objects.get(id=fruit_id)
    except(ActivityFruit.DoesNotExist): return FailResponse(u"不存在的活动作品ID")
    
    if activity_fruit.status <> 2:
        return FailResponse(u'作品不是发表状态，不能评论')
    
    if grade not in range(1, 6):
        return FailResponse(u'分值只能为1-5之间的整数')
    
    if ActivityGrade.objects.filter(activity_fruit_id=activity_fruit.id).count() > 0:
        return FailResponse(u'已经对此活动作品作过评分')
    
    activity_grade = ActivityGrade()
    activity_grade.user_id = request.user.id
    activity_grade.library_id = request.user.library_id
    activity_grade.activity_fruit_id = activity_fruit.id
    activity_grade.grade = grade
    activity_grade.save()
    
    activity_fruit.total_grade += grade
    activity_fruit.grade_times += 1
    activity_fruit.grade = "%.1f" % activity_fruit.total_grade*1.0/activity_fruit.grade_times 
    activity_fruit.save()
    
    return SuccessResponse({"id":activity_fruit.id, "grade":activity_fruit.grade})
    
@login_required
def comment_fruit(request, param):
    if param.has_key("fruit_id"): fruit_id = int(param.fruit_id)
    else: return FailResponse(u"必须传入活动作品ID")
    if param.has_key("comment"): comment = param.comment
    else: return FailResponse(u"必须传入评论内容")
    if len(comment) <= 5:
        return FailResponse(u'评论内容过短')
    
    if len(comment) == 0 or len(comment) > 500:
        return FailResponse(u'评论内容过长')
    
    if request.user.auth_type == 5: return FailResponse(u'游客不能评论!')
    
    try: activity_fruit = ActivityFruit.objects.get(id=fruit_id)
    except(ActivityFruit.DoesNotExist): return FailResponse(u"不存在的活动作品ID")
    
    if activity_fruit.status <> 2:
        return FailResponse(u'活动作品不是发表状态，不能评论')
        
    #if auth_opus.library_id and auth_opus.library_id <> request.user.library_id:
    #   return FailResponse(u'没有权限对此作品进行评论')
    
    activity_comment = ActivityComment()
    activity_comment.user_id = request.user.id
    activity_comment.library_id = request.user.library_id
    activity_comment.activity_fruit_id = activity_fruit.id
    activity_comment.comment = comment
    activity_comment.save()
    
    #发个人消息
#     auth_message = AuthMessage()
#     auth_message.user_id = auth_opus.user_id
#     auth_message.from_user_id = request.user.id
#     auth_message.opus_id = auth_opus.id
#     auth_message.msg_type = 3   #作品评论
#     auth_message.content = comment
#     auth_message.save()
    
    activity_fruit.comment_times += 1
    activity_fruit.save()
    
    return SuccessResponse({"id":activity_fruit.id})      
    

    
@print_exec_time    
@login_required
def get_comment_list(request, param):
    if param.has_key("fruit_id"): fruit_id = int(param.fruit_id)
    else: return FailResponse(u"必须传入活动作品ID")
    if param.has_key("page_index"): page_index = int(param.page_index)
    else: page_index = 1
    if param.has_key("page_size"): page_size = int(param.page_size)
    else: page_size = 20
    
    try: activity_fruit = ActivityFruit.objects.get(id=fruit_id)
    except(ActivityFruit.DoesNotExist): return FailResponse(u"不存在的活动作品ID")
    
    if activity_fruit.status <> 2:
        return FailResponse(u'活动作品不是发表状态，不能得到评论列表')
    
    where_clause = "activity_fruit_id=%s" % fruit_id
    cursor = connections[DB_READ_NAME].cursor()
    sql = "select count(*) from activity_comment where %s" % where_clause
    cursor.execute(sql)
    row = cursor.fetchone()
    count = 0
    if row: count = row[0]
    page_count = int(ceil(count/float(page_size)))
    
    sql = "select c.id,c.user_id,u.nickname,`comment`,create_time,u.avatar_img from activity_comment c LEFT JOIN auth_user u on u.id=c.user_id"
    sql += " where %s order by create_time desc limit %d, %d" % (where_clause, (page_index-1)*page_size, page_size)
    
    cursor.execute(sql)
    rows = cursor.fetchall()
    comm_list = []
    for row in rows:
        if not row: continue
        avatar_img = MEDIA_URL + row[5] if row[5] else ""
        comm_list.append({"id":row[0],"user_id":row[1],"nickname":row[2],"comment":row[3],"create_time":row[4].strftime("%Y-%m-%d %H:%M:%S"),"avatar_img":avatar_img})
        
    return SuccessResponse({"data":comm_list, "page_index":page_index, "page_count":page_count})
    

@print_exec_time
@login_required
def comment_fruit_mongo(request, param):
    if param.has_key("fruit_id"): fruit_id = int(param.fruit_id)
    else: return FailResponse(u"必须传入活动作品ID")
    if param.has_key("comment"): comment = param.comment
    else: return FailResponse(u"必须传入评论内容")
    if len(comment) <= 5:
        return FailResponse(u'评论内容过短')
    
    if len(comment) == 0 or len(comment) > 500:
        return FailResponse(u'评论内容过长')
    
    if request.user.auth_type == 5: return FailResponse(u'游客不能评论!')
    
    try: activity_fruit = ActivityFruit.objects.get(id=fruit_id)
    except(ActivityFruit.DoesNotExist): return FailResponse(u"不存在的活动作品ID")
    
    if activity_fruit.status <> 2:
        return FailResponse(u'活动作品不是发表状态，不能评论')
        
    #if auth_opus.library_id and auth_opus.library_id <> request.user.library_id:
    #   return FailResponse(u'没有权限对此作品进行评论')
    
    from mongodb import ActivityCommentMongo
    activity_comment_moneo = ActivityCommentMongo(library_id=request.user.library_id,fruit_id=fruit_id, user_id=request.user.id)
    activity_comment_moneo.comment = comment
    activity_comment_moneo.save()
    
    #发个人消息
#     auth_message = AuthMessage()
#     auth_message.user_id = auth_opus.user_id
#     auth_message.from_user_id = request.user.id
#     auth_message.opus_id = auth_opus.id
#     auth_message.msg_type = 3   #作品评论
#     auth_message.content = comment
#     auth_message.save()
    
    activity_fruit.comment_times += 1
    activity_fruit.save()
    
    return SuccessResponse({"id":activity_fruit.id})      


@login_required
def get_comment_list_mongo(request, param):
    if param.has_key("fruit_id"): fruit_id = int(param.fruit_id)
    else: return FailResponse(u"必须传入活动作品ID")
    if param.has_key("page_index"): page_index = int(param.page_index)
    else: page_index = 1
    if param.has_key("page_size"): page_size = int(param.page_size)
    else: page_size = 20
    
    try: activity_fruit = ActivityFruit.objects.get(id=fruit_id)
    except(ActivityFruit.DoesNotExist): return FailResponse(u"不存在的活动作品ID")
    
    if activity_fruit.status <> 2:
        return FailResponse(u'活动作品不是发表状态，不能得到评论列表')
    
    from mongodb import ActivityCommentMongo
    count = ActivityCommentMongo.objects.filter(fruit_id=fruit_id).count()
    page_count = int(ceil(count/float(page_size)))
    
    comment_list_mongo = ActivityCommentMongo.objects.filter(fruit_id=fruit_id).order_by("-create_time").skip((page_index-1)*page_size).limit(page_size);
    
    comm_list = []
    uid_dict = {}
    for comment in comment_list_mongo:
        #avatar_img = MEDIA_URL + row[5] if row[5] else ""
        comm_list.append({"user_id":int(comment.user_id),"comment":comment.comment,"create_time":comment.create_time.strftime("%Y-%m-%d %H:%M:%S")})
        uid_dict[str(comment.user_id)] = None
    if len(uid_dict) > 0:
        sql = "select id, nickname, avatar_img from auth_user where id in (%s)" % ','.join(uid_dict.keys())
        cursor = connections[DB_READ_NAME].cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        for row in rows:
            uid = int(row[0])
            nickname = row[1]
            avatar_img = MEDIA_URL + row[2] if row[2] else ""
            for comm in comm_list:
                if comm["user_id"] == uid:
                    comm["nickname"] = nickname
                    comm["avatar_img"] = avatar_img
    
    return SuccessResponse({"data":comm_list, "page_index":page_index, "page_count":page_count})

    
    
@login_required
def praise_fruit(request, param):
    if param.has_key("fruit_id"): fruit_id = int(param.fruit_id)
    else: return FailResponse(u"必须传入活动作品ID")
    
    if request.user.auth_type == 5: return FailResponse(u'游客不能点赞!')
    
    try: activity_fruit = ActivityFruit.objects.get(id=fruit_id)
    except(ActivityFruit.DoesNotExist): return FailResponse(u"不存在的活动作品ID")
    
    if activity_fruit.status <> 2:
        return FailResponse(u'活作品不是发表状态，不能点赞')
    
    if ActivityPraise.objects.filter(user_id=request.user.id, activity_fruit_id=fruit_id).count() > 0:
        return FailResponse(u'已经赞过，不要重复赞')
    
    activity_praise = ActivityPraise()
    activity_praise.user_id = request.user.id
    activity_praise.library_id = request.user.library_id
    activity_praise.activity_fruit_id = activity_fruit.id
    activity_praise.save()
    
    #发个人消息
#     auth_message = AuthMessage()
#     auth_message.user_id = auth_opus.user_id
#     auth_message.from_user_id = request.user.id
#     auth_message.opus_id = auth_opus.id
#     auth_message.msg_type = 4   #作品点赞
#     auth_message.content = u"作品[%s]被用户(%s)赞了。" % (auth_opus.title, request.user.nickname)
#     auth_message.save()
    
    activity_fruit.praise_times += 1
    activity_fruit.save()
    
    return SuccessResponse({"id":activity_fruit.id, "praise_times":activity_fruit.praise_times})     


@print_exec_time
@login_required
def praise_fruit_mongodb(request, param):
    if param.has_key("fruit_id"): fruit_id = int(param.fruit_id)
    else: return FailResponse(u"必须传入活动作品ID")
    
    if request.user.auth_type == 5: return FailResponse(u'游客不能点赞!')
    
    try:
        activity_fruit = ActivityFruit.objects.get(id=fruit_id)
    except(ActivityFruit.DoesNotExist): return FailResponse(u"不存在的活动作品ID")
    
    if activity_fruit.status <> 2:
        return FailResponse(u'活作品不是发表状态，不能点赞')


    from mongodb import ActivityPraiseMongo
    if ActivityPraiseMongo.objects(user_id=request.user.id, fruit_id=fruit_id).count() > 0:
        return FailResponse(u'已经赞过，不要重复赞')

    activity_praise_mongo = ActivityPraiseMongo(library_id=request.user.library_id,fruit_id=fruit_id, user_id=request.user.id)
    activity_praise_mongo.save()
    
    #发个人消息
#     auth_message = AuthMessage()
#     auth_message.user_id = auth_opus.user_id
#     auth_message.from_user_id = request.user.id
#     auth_message.opus_id = auth_opus.id
#     auth_message.msg_type = 4   #作品点赞
#     auth_message.content = u"作品[%s]被用户(%s)赞了。" % (auth_opus.title, request.user.nickname)
#     auth_message.save()
    
    activity_fruit.praise_times += 1
    activity_fruit.save()

    return SuccessResponse({"id":activity_fruit.id, "praise_times":activity_fruit.praise_times})


@login_required
def get_client_ip(request):
    return SuccessResponse(get_ip(request))

@print_exec_time
@login_required
def vote_fruit(request, param):
    if param.has_key("fruit_id"): fruit_id = int(param.fruit_id)
    else: return FailResponse(u"必须传入活动作品ID")
    if param.has_key("ip"): ip = param.ip
    else: return FailResponse(u"非法请求")
    
    if param.has_key("mac"): mac = param.mac
    else: return FailResponse(u"非法请求")
    
    try: activity_fruit = ActivityFruit.objects.get(id=fruit_id)
    except(ActivityFruit.DoesNotExist): return FailResponse(u"不存在的活动作品ID")
    
    if activity_fruit.status <> 2:
        return FailResponse(u'活作品不是发表状态，不能投票')
    
    activity_list = ActivityList.objects.get(id=activity_fruit.activity_id)
    
    if datetime.now() < activity_list.vote_start_time:
        return FailResponse(u"《%s》投票开始时间为%s，请到时再参与投票！" % (activity_list.title, (activity_list.vote_start_time).strftime("%Y-%m-%d")))
    
    if datetime.now() >= activity_list.vote_end_time:
        return FailResponse(u"《%s》投票截止时间为%s，感谢你的参与。" % (activity_list.title, (activity_list.vote_end_time + timedelta(days=-1)).strftime("%Y-%m-%d")))
    
    real_ip = get_ip(request)
    if ip <> real_ip:
        print "ip:", ip, "real_ip:", real_ip
        return FailResponse(u"非法请求2")
    
    referer = request.META.get('REFERER', '')
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    user_limit_count = ActivityVote.objects.filter(create_time__gte=date.today(), user_id=request.user.id).count()
    if user_limit_count >= 10:
        return FailResponse(u"当前登录账号今日投票数超限.")
    
    ip_limit_count = ActivityVote.objects.filter(create_time__gte=date.today(), real_ip=real_ip).count()
    if ip_limit_count >= 50:
        return  FailResponse(u"你的IP(%s)今日投票数超限." % real_ip) 
    
    
    #修改主数据库
    cursor = connection.cursor()
    sql = "update activity_fruit set vote=vote+1 where id=%s and vote=%d" % (fruit_id, activity_fruit.vote)
    if cursor.execute(sql) == 0:
        return FailResponse(u"投票失败，请重试")
    
    activity_vote = ActivityVote()
    activity_vote.library_id = request.user.library_id
    activity_vote.activity_id = activity_fruit.activity_id
    activity_vote.fruit_id = fruit_id
    activity_vote.user_id = request.user.id
    
    activity_vote.real_ip = real_ip
    activity_vote.user_agent = user_agent
    activity_vote.referer =  referer
    activity_vote.mac =  mac
    activity_vote.save()
    return SuccessResponse({"id":fruit_id, "vote":activity_fruit.vote+1}) 


@print_exec_time
@login_required
def vote_fruit_mongo(request, param):
    """
        使用mongodb数据库存储数据
    """
    import re
    from mongodb import ActivityVoteMongo
    
    if param.has_key("fruit_id"): fruit_id = int(param.fruit_id)
    else: return FailResponse(u"必须传入活动作品ID")
    if param.has_key("ip"): ip = param.ip
    else: return FailResponse(u"非法请求")
    
    if param.has_key("mac"): mac = param.mac
    else: return FailResponse(u"非法请求")
    #E0-3F-49-78-10-C8  mac地址必须符合规则
    if len(mac)>0 and not re.match(r'^[0-9a-fA-F]{2}-[0-9a-fA-F]{2}-[0-9a-fA-F]{2}-[0-9a-fA-F]{2}-[0-9a-fA-F]{2}-[0-9a-fA-F]{2}$',mac):
        return FailResponse(u"非法请求")
    
    try: activity_fruit = ActivityFruit.objects.get(id=fruit_id)
    except(ActivityFruit.DoesNotExist): return FailResponse(u"不存在的活动作品ID")
    
    if activity_fruit.status <> 2:
        return FailResponse(u'活作品不是发表状态，不能投票')
    
    activity_list = ActivityList.objects.get(id=activity_fruit.activity_id)
    
    if datetime.now() < activity_list.vote_start_time:
        return FailResponse(u"《%s》投票开始时间为%s，请到时再参与投票！" % (activity_list.title, (activity_list.vote_start_time).strftime("%Y-%m-%d")))
    
    if datetime.now() >= activity_list.vote_end_time:
        return FailResponse(u"《%s》投票截止时间为%s，感谢你的参与。" % (activity_list.title, (activity_list.vote_end_time + timedelta(days=-1)).strftime("%Y-%m-%d")))
    
    real_ip = get_ip(request)
    if ip <> real_ip:
        print "ip:", ip, "real_ip:", real_ip
        return FailResponse(u"非法请求2")
    
    referer = request.META.get('REFERER', '')
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    user_count = ActivityVoteMongo.objects.filter(user_id=request.user.id, create_time__gte=date.today()).count()
    if user_count >= 10:
        return FailResponse(u"当前登录账号今日投票数超限.")
    
    ip_count = ActivityVoteMongo.objects.filter(real_ip=real_ip, create_time__gte=date.today()).count()
    if ip_count >= 50:
        return  FailResponse(u"你的IP(%s)今日投票数超限." % real_ip) 
    
    mac_count = ActivityVoteMongo.objects.filter(mac=mac, create_time__gte=date.today()).count()
    if mac_count >= 20:
        return  FailResponse(u"当前电脑今日投票数超限.")
    
    #修改主数据库
    cursor = connection.cursor()
    sql = "update activity_fruit set vote=vote+1 where id=%s and vote=%d" % (fruit_id, activity_fruit.vote)
    if cursor.execute(sql) == 0:
        return FailResponse(u"投票失败，请重试")
    
    activity_vote_mongo = ActivityVoteMongo(library_id=request.user.library_id, activity_id=activity_fruit.activity_id, fruit_id=fruit_id, user_id=request.user.id)
    activity_vote_mongo.user_agent = user_agent
    activity_vote_mongo.real_ip = real_ip
    activity_vote_mongo.referer = referer
    activity_vote_mongo.mac = mac
    activity_vote_mongo.save()
    return SuccessResponse({"id":fruit_id, "vote":activity_fruit.vote+1})


@print_trace
@login_required
def update_activity(request, param):
    """
        新建活动，修改活动，都是这一个接口
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return FailResponse(u"没有限权!")
    
    if param.has_key("id"): id = int(param.id)
    else: id = 0
    
    if param.has_key("title"): title = param.title
    else: return FailResponse(u"必须传入title")
    if param.has_key("fruit_type"): fruit_type = int(param.fruit_type)
    else: return FailResponse(u"必须传入fruit_type")
    if param.has_key("scope_list"): scope_list = param.scope_list
    else: return FailResponse(u"必须传入scope_list")
    
    if param.has_key("can_submit"): can_submit = int(param.fruit_type)
    else: return FailResponse(u"必须传入can_submit")
    
    if param.has_key("submit_start_time"): submit_start_time = datetime.strptime(param.submit_start_time, "%Y-%m-%d")
    else: return FailResponse(u"必须传入submit_start_time")
    if param.has_key("submit_end_time"): submit_end_time = datetime.strptime(param.submit_end_time, "%Y-%m-%d")
    else: return FailResponse(u"必须传入submit_end_time")

    if param.has_key("need_group"): need_group = int(param.need_group)
    else: return FailResponse(u"必须传入need_group")
    if param.has_key("need_unit"): need_unit = int(param.need_unit)
    else: return FailResponse(u"必须传入need_unit")
    if param.has_key("need_district"): need_district = int(param.need_district)
    else: return FailResponse(u"必须传入need_district")
    
    if param.has_key("can_vote"): can_vote = int(param.can_vote)
    else: return FailResponse(u"必须传入fruit_type")
    if can_vote:
        if param.has_key("vote_start_time"): vote_start_time = datetime.strptime(param.vote_start_time, "%Y-%m-%d")
        else: return FailResponse(u"必须传入vote_start_time")
        if param.has_key("vote_end_time"): vote_end_time = datetime.strptime(param.vote_end_time, "%Y-%m-%d")
        else: return FailResponse(u"必须传入vote_end_time")
    
    if id:
        try:
            activity_list = ActivityList.objects.get(id=id)
        except: return FailResponse(u"需要更新的活动ID不存在")
    else:
        activity_list = ActivityList()
        activity_list.library_id = request.user.library_id
        activity_list.user_id = request.user.id
        activity_list.fruit_type = fruit_type
        activity_list.status = 0
        activity_list.update_time = datetime.now()
        
        activity_option = ActivityOption()
        activity_option.library_id = activity_list.library_id
        activity_option.user_id = activity_list.user_id
        activity_list.save()
        activity_option.activity_id = activity_list.id
        activity_option.save()
    
    activity_list.title = title
    #activity_list.fruit_type = fruit_type
    activity_list.need_group = need_group
    activity_list.need_unit = need_unit
    activity_list.need_district = need_district
    activity_list.update_time = datetime.now()
    activity_list.scope_list = scope_list
    activity_list.submit_start_time = submit_start_time
    activity_list.submit_end_time = submit_end_time
    
    #(1,u"新闻播报"),(2,u"电子创作"),(3,u"图片"),(4,u"视频")
    if activity_list.fruit_type in (2,3,4):
        activity_list.can_submit = can_submit
        activity_list.can_vote = can_vote
        
        if activity_list.can_vote:
            activity_list.vote_start_time = vote_start_time
            activity_list.vote_end_time = vote_end_time
    activity_list.save()
    
    return SuccessResponse({"id":activity_list.id})


@login_required
def update_activity_option(request, param):
    """
        新建活动，修改活动上传参数
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return FailResponse(u"没有限权!")

    if param.has_key("activity_id"): activity_id = int(param.activity_id)
    else: return FailResponse(u"必须传入活动ID")
    
    if param.has_key("need_fruit_name"): need_fruit_name = int(param.need_fruit_name)
    else: return FailResponse(u"必须传入need_fruit_name")
    if param.has_key("need_fruit_brief"): need_fruit_brief = int(param.need_fruit_brief)
    else: return FailResponse(u"必须传入need_fruit_brief")
    
    if param.has_key("need_author_name"): need_author_name = int(param.need_author_name)
    else: return FailResponse(u"必须传入need_author_name")
    if param.has_key("need_author_brief"): need_author_brief = int(param.need_author_brief)
    else: return FailResponse(u"必须传入need_author_brief")
    
    if param.has_key("need_author_sex"): need_author_sex = int(param.need_author_sex)
    else: return FailResponse(u"必须传入need_author_sex")
    if param.has_key("need_author_age"): need_author_age = int(param.need_author_age)
    else: return FailResponse(u"必须传入need_author_age")
    if param.has_key("need_author_school"): need_author_school = int(param.need_author_school)
    else: return FailResponse(u"必须传入need_author_school")
    if param.has_key("need_author_telephone"): need_author_telephone = int(param.need_author_telephone)
    else: return FailResponse(u"必须传入need_author_telephone")
    if param.has_key("need_author_email"): need_author_email = int(param.need_author_email)
    else: return FailResponse(u"必须传入need_author_email")

    try:
        activity_option = ActivityOption.objects.get(activity_id=activity_id)
        activity_list = ActivityList.objects.get(id=activity_id)
        activity_option.update_time = datetime.now()
    except:
        import traceback
        traceback.print_exc()
        return FailResponse(u"活动(%d)选项不存在" % activity_id)
    
    if activity_list.fruit_type == 1:
        return FailResponse(u"新闻播报活动不需要设置上传项")
    
    activity_option.need_fruit_name = need_fruit_name
    activity_option.need_fruit_brief = need_fruit_brief
    
    activity_option.need_author_name = need_author_name
    activity_option.need_author_brief = need_author_brief
    activity_option.need_author_sex = need_author_sex
    activity_option.need_author_age = need_author_age
    
    activity_option.need_author_school = need_author_school
    activity_option.need_author_telephone = need_author_telephone
    activity_option.need_author_email = need_author_email
    activity_option.save()
    
    return SuccessResponse({"activity_id":activity_id})


@login_required
def update_activity_group(request, param):
    """
        新建活动，修改活动分组
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return FailResponse(u"没有限权!")
    
    if param.has_key("group_id"): group_id = int(param.group_id)
    else: group_id = 0
    if not group_id:
        if param.has_key("activity_id"): activity_id = int(param.activity_id)
        else: return FailResponse(u"必须传入活动ID")
    if param.has_key("group_name"): group_name = param.group_name
    else: return FailResponse(u"必须传入group_name")

    if group_id:
        try:
            activity_group = ActivityGroup.objects.get(id=group_id)
            activity_list = ActivityList.objects.get(id=activity_group.activity_id)
            activity_group.update_time = datetime.now()
        except: return FailResponse(u"活动分组ID(%d)不存在" % group_id)
    else:
        try: activity_list = ActivityList.objects.get(id=activity_id)
        except: return FailResponse(u"活动ID不存在")
        if ActivityGroup.objects.filter(activity_id=activity_id).count() > 4:
            return FailResponse(u"每个活动最多只能有四个分组!")
        
        activity_group = ActivityGroup()
        activity_group.library_id = activity_list.library_id
        activity_group.activity_id = activity_list.id
    
    if activity_list.need_group <> 1:
        return FailResponse(u"当前活动设置不需要组组")
    
    activity_group.group_name = group_name
    activity_group.save()
    
    return SuccessResponse({"activity_id":activity_list.id,"id":activity_group.id,"group_name":activity_group.group_name})


@login_required
def update_activity_group_list(request, param):
    """
        新建活动，修改活动分组，支持一次传多个分组
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return FailResponse(u"没有限权!")
    
    if param.has_key("activity_id"): activity_id = int(param.activity_id)
    else: return FailResponse(u"必须传入活动ID")
    if param.has_key("groups"): groups = param.groups
    else: return FailResponse(u"必须传入分组对象")
    
    if len(groups)<2 or len(groups)>4:
        return FailResponse(u"每个活动只能有2-4个分组!")
    
    try: activity_list = ActivityList.objects.get(id=activity_id)
    except: return FailResponse(u"活动ID不存在")
    if activity_list.need_group <> 1:
        return FailResponse(u"当前活动设置不需要分组")

    cur_group_count = ActivityGroup.objects.filter(activity_id=activity_id).count()
    new_group_count = 0
    for group in groups:
        if group.has_key("group_id"): group_id = int(group.group_id)
        else: group_id = 0
        if group_id:
            if ActivityGroup.objects.filter(id=group_id).count() == 0:
                return FailResponse(u"活动分组ID(%d)不存在" % group_id)
        else: new_group_count+=1
        if group.has_key("group_name"):
            group_name = group.group_name.strip()
            if len(group_name) == 0 and group_id:
                new_group_count -= 1
        else: return FailResponse(u"必须传入group_name")
    if cur_group_count + new_group_count>4:
        return FailResponse(u"每个活动最多只能有四个分组!")
    
    back_list = []
    for group in groups:
        if group.has_key("group_id"): group_id = int(group.group_id)
        else: group_id = 0
        group_dict = {"group_id":group_id}
        
        group_name = group.group_name.strip()

        if group_id:
            activity_group = ActivityGroup.objects.get(id=group_id)
            if len(group_name) == 0:
                activity_group.delete()
                continue
            activity_list = ActivityList.objects.get(id=activity_group.activity_id)
            activity_group.update_time = datetime.now()
        else:
            activity_group = ActivityGroup()
            activity_group.library_id = activity_list.library_id
            activity_group.activity_id = activity_list.id
        activity_group.group_name = group_name
        activity_group.save()
        group_dict['group_name'] = group_name
        back_list.append(group_dict)
    
    return SuccessResponse({"activity_id":activity_list.id,"groups":back_list})


def has_activity_signup(request, param):
    '''
    检验用户是否在指定活动报名
    editor: kamihati 2015/6/5
    :param request:
    :param param:
    :return:
    '''
    activity_id = int(param.activity_id) if param.has_key('activity_id') else 0
    if activity_id == 0:
        return FailResponse(u'活动不存在！')
    result = dict(is_signup=0,
                  is_submit=0,
                  is_vote=0)
    if ActivityMember.objects.filter(user_id=request.user.id, activity_id=activity_id).count() > 0:
        result['is_signup'] = 1
    if ActivityFruit.objects.filter(user_id=request.user.id, activity_id=activity_id, status__gt=-1).count() > 0:
        result['is_submit'] = 1
    return SuccessResponse(result)

def sign_activity_member(request, param):
    '''
    活动报名
    editor: kamihati 2015/6/5
    :param request:
    :param param:
    :return:
    '''
    activity_id = int(param.activity_id) if 'activity_id' in param else 0
    # 活动报名状态验证
    activity_obj = ActivityList.objects.filter(id=activity_id)
    if not activity_obj:
        return FailResponse(u'活动不存在！')
    activity_obj = activity_obj[0]
    if activity_obj.status == -1:
        return FailResponse(u'活动已被删除！')
    if activity_obj.sign_up_end_time and activity_obj.sign_up_start_time > datetime.now():
        return FailResponse(u'还未到活动报名时间，敬请期待！')
    if activity_obj.sign_up_end_time and activity_obj.sign_up_end_time < datetime.now():
        return FailResponse(u'活动报名已结束。')

    activity_option = ActivityOption.objects.filter(activity_id=activity_id)
    if not activity_option:
        return FailResponse(u'活动报名信息有误！')
    activity_option = activity_option[0]
    user_obj = request.user

    if ActivityMember.objects.filter(activity_id=activity_id, user_id=user_obj.id).count() > 0:
        return FailResponse(u'报名信息已存在！')
    member = ActivityMember()

    # 作者姓名
    author_name = param.author_name if param.has_key('author_name') else ''
    if activity_option.need_author_name == 1 and author_name == '':
        return FailResponse(u'未填写作者姓名')
    else:
        member.realname = author_name

    # 年龄
    age = int(param.age) if param.has_key('age') else 0
    if age == 0 and activity_option.need_author_age == 1:
        return FailResponse(u'未填写作者年龄！')
    else:
        member.age = age

    # 性别
    sex = int(param.sex) if param.has_key('sex') else 1
    member.sex = sex

    # 学校
    school = param.school if param.has_key('school') else ''
    if activity_option.need_author_school == 1 and school == '':
        return FailResponse(u'未填写学校地址！')
    else:
        member.school = school

    # email
    email = param.email if param.has_key('email') else ''
    if activity_option.need_author_email == 1 and email == '':
        return FailResponse(u'未填写作者email!')
    else:
        member.email = email

    # 电话
    tel = param.author_telephone if param.has_key('author_telephone') else ''
    if activity_option.need_author_email == 1 and tel == '':
        return FailResponse(u'未填写作者电话！')
    else:
        member.telephone = tel

    # 地址
    """
    address = param.address if param.has_key('address') else ''
    if activity_option.need_author_address == 1 and address == '':
        return FailResponse(u'未填写作者地址！')
    else:
        member.address = address
    """

    # 作者简介
    author_brief = param.author_brief if param.has_key('author_brief') else ''
    if activity_option.need_author_brief == 1 and author_brief == '':
        return FailResponse(u'未填写作者简介！')
    else:
        member.description = author_brief

    member.activity_id = activity_id
    member.user_id = user_obj.id
    member.number = get_number(activity_id)
    member.join_time = datetime.now()
    member.status = 0
    member.save()
    activity_obj.sign_up_member_count = ActivityMember.objects.filter(activity_id=activity_id).count()
    activity_obj.save()
    return SuccessResponse(u'报名成功！')


@login_required
def update_activity_fruit(request, param):
    """
        新上传、修改活动作品，可以用户上传，也可以管理员上传
        editor: kamihati 2015/4/9  优化部分代码逻辑 根据客户端调用需求进行改动
        editor: kamihati 2015/6/16 增加对活动预告类型作品的支持
    """
    fruit_id = int(param.fruit_id) if 'fruit_id' in param else 0
    opus_type = int(param.opus_type) if 'opus_type' in param else 0
    activity_id = int(param.activity_id) if 'activity_id' in param else 0
    opus_id = int(param.opus_id) if 'opus_id' in param else 0
    fruit_name = param.fruit_name if param.has_key('fruit_name') else ''
    fruit_brief = param.fruit_brief if param.has_key('fruit_brief') else ''

    if not fruit_id:
        if not activity_id:
            return FailResponse(u"必须传入活动ID")
        # editor: kamihati 2015/6/17 个人中心调用。只有活动id和opus_id。据此获取活动作品id
        if opus_id != 0:
            # 暂定为最近的一条处于驳回和草稿状态的作品
            fruit = ActivityFruit.objects.filter(
                activity_id=activity_id, opus_id=opus_id, status__in=[-1, 0]).order_by("-id")
            if fruit.count() != 0:
                fruit = fruit[0]
                fruit_id = fruit.id

    activity_fruit = ActivityFruit()
    activity_fruit.fruit_name = fruit_name
    activity_fruit.fruit_brief = fruit_brief

    if fruit_id:
        activity_fruit = ActivityFruit.objects.get(id=fruit_id)
        # 驳回和待审核状态才可以修改
        if activity_fruit.status not in (-1, 0):
            return FailResponse(u"作品不能修改，只有未提交的作品才能修改")
        activity_list = ActivityList.objects.get(id=activity_fruit.activity_id)
        activity_option = ActivityOption.objects.get(activity_id=activity_list.id)
        activity_fruit.update_time = datetime.now()
    else:
        activity_list = ActivityList.objects.get(id=activity_id)
        activity_option = ActivityOption.objects.get(activity_id=activity_id)
        activity_fruit.library_id = activity_list.library_id
        activity_fruit.activity_id = activity_list.id
        activity_fruit.opus_type = opus_type
        if ActivityFruit.objects.filter(status__gt=-1, user_id=request.user.id, activity_id=activity_id).count() != 0:
            return FailResponse(u'此活动不允许多次投稿！')

    if activity_list.submit_start_time > datetime.now():
        return FailResponse(u'未到投稿期，不能提交作品。')
    if activity_list.submit_end_time < datetime.now():
        return FailResponse(u"已过投稿期，不能提交作品！")

    if activity_list.fruit_type not in (2, 3, 4):
        return FailResponse(u"当前活动不需要用户上传作品")

    if activity_list.fruit_type in (3, 4):
        if param.has_key("asset_id"): asset_id = int(param.asset_id)
        else: return FailResponse(u"必须传入个人素材asset_id")
        
        try: auth_asset = AuthAsset.objects.get(id=asset_id)
        except(AuthAsset.DoesNotExist): return FailResponse(u"个人素材ID(%s)不正确!" % asset_id)
        
        if auth_asset.status != 1:
            return FailResponse(u"个人素材ID(%s)当前状态不可用!" % asset_id)
        
        if request.user.id != auth_asset.user_id:
            return FailResponse(u"只能选择自己的资源!")
        #auth_asset (1,u"图片"),(2,u"声音"),(3,u"视频"),(4,u"涂鸦")
        #fruit_type fruit_type  (3,u"图片"),(4,u"视频")
        if activity_list.fruit_type == 3 and auth_asset.res_type not in (1, 4):
            return FailResponse(u"个人资料ID不 正确，需要类型为图片!")
        if activity_list.fruit_type == 4 and auth_asset.res_type != 3:
            return FailResponse(u"个人资料ID不 正确，需要类型为视频!")

        activity_fruit.auth_asset_id = auth_asset.id
        activity_fruit.user_id = auth_asset.user_id
        activity_fruit.status = 1
    elif activity_list.fruit_type == 2:
        # 报名时新建作品则预先建立报名作品对象返回给客户端。客户端提交作品信息的时候把这个id一起返回。
        # coder   kamihati   2015/4/9   这逻辑略蛋疼。
        activity_fruit.status = 0
        if opus_id > 0:
            opus = AuthOpus.objects.filter(pk=opus_id)
            if not opus:
                return FailResponse(u'用户作品不存在')
            opus = opus[0]
            activity_fruit.opus_id = opus_id
            activity_fruit.user_id = opus.user.id
            if opus.status == 2:
                activity_fruit.status = 1
        #elif fruit_id == 0:
            # editor: kamihati 2015/6/16 fruit_id==0 opus_id=0 则缺少作品数据。需要抛出异常
        #    return FailResponse(u'未传入作品id')
    activity_fruit.fruit_type = activity_list.fruit_type
    if activity_list.need_district:
        if param.has_key("district_id"): district_id = int(param.district_id)
        else: return FailResponse(u"必须传入活动district_id")
        activity_fruit.district_id = district_id
    if activity_list.need_group:
        if param.has_key("group_id"): group_id = int(param.group_id)
        else: return FailResponse(u"必须传入活动group_id")
        activity_fruit.group_id = group_id

    #     if activity_list.need_unit:
    #         if param.has_key("unit_id"): unit_id = int(param.unit_id)
    #         else: return FailResponse(u"必须传入活动unit_id")
    #         activity_fruit.unit_id = unit_id

    member = ActivityMember.objects.filter(activity_id=activity_id, user_id=request.user.id)
    if not member:
        return FailResponse(u'请先报名！')
    member = member[0]
    # 使用报名信息填充部分活动作品信息
    activity_fruit.author_name = member.realname
    activity_fruit.author_brief = member.description
    activity_fruit.author_sex = member.sex
    activity_fruit.author_age = member.age
    activity_fruit.school_name = member.school
    activity_fruit.author_telephone = member.telephone
    activity_fruit.author_email = member.email
    activity_fruit.number = member.number

    if activity_option.need_fruit_name:
        if param.has_key("fruit_name"): fruit_name = param.fruit_name.strip()
        else: return FailResponse(u"必须传入活动fruit_name")
        activity_fruit.fruit_name = fruit_name
    if activity_option.need_fruit_brief:
        if param.has_key("fruit_brief"): fruit_brief = param.fruit_brief.strip()
        else: return FailResponse(u"必须传入活动fruit_brief")
        activity_fruit.fruit_brief = fruit_brief
    if activity_option.need_author_business == 1:
        unit_name = param['unit_name'] if param.has_key('unit_name') else ''
        if unit_name == '':
            return FailResponse(u'必须传入报名单位名称！')
        activity_fruit.unit_name = unit_name

    activity_fruit.save()
    activity_list.join_member_count = ActivityFruit.objects.filter(activity_id=activity_id, status=2).count()
    activity_list.save()
    return SuccessResponse({"activity_id":activity_list.id, "fruit_id":activity_fruit.id})


def submit_activity_fruit(request, param):
    '''
    editor: kamihati 2015/6/17
    :param request:
    :param param:
    :return:
    '''
    pass


def get_number(activity_id):
    cursor = connections[DB_READ_NAME].cursor()
    sql = "select number from activity_fruit where activity_id=%s ORDER BY number DESC LIMIT 1" % activity_id
    cursor.execute(sql)
    row = cursor.fetchone()
    if row and row[0]:
        cur_id = int(row[0])
    else:
        cur_id = 0
    return str(cur_id+1).zfill(4)
    
@login_required
def apply_activity(request, param):
    """
        提交活动，提交后活动就不充许修改了
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return FailResponse(u"没有限权!")
    
    if param.has_key("id"): id = int(param.id)
    else: return FailResponse(u"必须传入活动ID")
    
    try: activity_list = ActivityList.objects.get(id=id)
    except: return FailResponse(u"活动ID不存在")
    
    if activity_list.status == 1:
        return FailResponse(u"活动已是进行状态，不需要提交！")
    if not (activity_list.opus_id or activity_list.cover):
        return FailResponse(u"请先创建《活动预告》，再申请提交！")

    if request.user.id <> activity_list.user_id:
        return FailResponse(u"只能提交自己创建的活动！")
    
    if activity_list.fruit_type in (2, 3, 4):
        activity_fruit = ActivityFruit.objects.get(activity_id=activity_list.id, opus_type=3) #活动预告
        activity_fruit.status = 2   #发表状态
        auth_opus = AuthOpus.objects.get(id=activity_fruit.opus_id)
        auth_opus.status = 2    #发表状态
    elif activity_list.fruit_type == 1:
        auth_opus = AuthOpus.objects.get(id=activity_list.opus_id)
        auth_opus.status = 2    #发表状态

    activity_list.status = 1
    activity_list.save()
    
    return SuccessResponse({"id":activity_list.id})
    

@login_required
def delete_activity(request, param):
    """
        删除活动，只有未提交的活动才可以删除
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return FailResponse(u"没有限权!")
    
    if param.has_key("id"): id = int(param.id)
    else: return FailResponse(u"必须传入活动ID")
    
    try: activity_list = ActivityList.objects.get(id=id)
    except: return FailResponse(u"活动ID不存在")
    
    if activity_list.status == -1:
        return FailResponse(u"活动已是删除状态，不需要重复删除！")
    elif activity_list.status == 1:
        return FailResponse(u"活动已是进行状态，不能删除！")

    if request.user.id <> activity_list.user_id:
        return FailResponse(u"只能删除自己创建的活动！")
    
    activity_list.status = -1
    activity_list.save()
    
    return SuccessResponse({"id":activity_list.id})


@login_required
def apply_fruit(request, param):
    """
        用户申请提交活动作品，提交后活动作品就不充许修改了，申请后需要管理审核
        editor: kamihati 2015/6/17
    """
    fruit_id = param.fruit_id if param.has_key('fruit_id') else 0
    opus_id = param.opus_id if param.has_key('opus_id') else 0
    activity_id = param.activity_id if param.has_key('activity_id') else 0
    if fruit_id == 0 and opus_id == 0:
        return FailResponse(u"必须传入活动作品id")
    try:
        if fruit_id == 0:
            fruit = ActivityFruit.objects.filter(
                activity_id=activity_id, opus_id=opus_id, status__in=[-1, 0]).order_by("-id")
            if fruit.count() != 0:
                fruit = fruit[0]
                fruit_id = fruit.id
        activity_fruit = ActivityFruit.objects.get(id=fruit_id)
    except:
        return FailResponse(u"活动作品不存在")
    try:
        activity_list = ActivityList.objects.get(id=activity_fruit.activity_id)
    except:
        return FailResponse(u"活动ID不存在")
    
    if activity_list.fruit_type not in (2, 3, 4):
        return FailResponse(u"当前活动不需要用户上传作品")
    """
    from activity.fruit_handler import n_opus_type
    if activity_fruit.opus_type in n_opus_type.split(',') or activity_fruit:   #比赛结果
        if not (request.user.is_staff or request.user.is_superuser):
            return FailResponse(u"没有权限!")
        else:
            activity_fruit.status = 2
            activity_fruit.save()
            return SuccessResponse({"fruit_id":activity_fruit.id})
    """
    if activity_list.submit_end_time.date()<date.today():
        return FailResponse(u"活动已经超过截稿时间（%s）。" % activity_list.submit_end_time.strftime("%Y-%m-%d"))
    
    if activity_fruit.status == 1:
        return FailResponse(u"活动作品已经提交过，不需要重复提交！")
    
    if request.user.id <> activity_fruit.user_id:
        return FailResponse(u"只能提交自己创建的作品！")
    if activity_fruit.status not in (-1, 0):
        return FailResponse(u'只有状态为驳回和草稿状态的作品可以投稿！')
    activity_fruit.status = 1
    if activity_fruit.fruit_type == 2:
        from diy.auth_opus_handler import set_opus_status
        opus = AuthOpus.objects.get(pk=activity_fruit.opus_id)
        if opus.status != 2:
            opus.status = 1
            opus.save()
    activity_fruit.save()
    
    return SuccessResponse({"fruit_id":activity_fruit.id})


@login_required
def delete_fruit(request, param):
    """
        用户删除作品,只有待提交，审核未通过的作品才能删除
    """
    if param.has_key("fruit_id"): fruit_id = int(param.fruit_id)
    else: return FailResponse(u"必须传入活动fruit_id")
    
    try: activity_fruit = ActivityFruit.objects.get(id=fruit_id)
    except: return FailResponse(u"活动作品不存在")
    try: activity_list = ActivityList.objects.get(id=activity_fruit.activity_id)
    except: return FailResponse(u"活动ID不存在")
    
    if activity_fruit.user_id <> request.user.id:
        return FailResponse(u"只能删除自己的活动作品")
    
    if activity_list.fruit_type not in (2, 3, 4):
        return FailResponse(u"当前活动不需要用户上传作品")
    
    if activity_fruit.status not in (-1, 0):
        return FailResponse(u"只能待提交状态的活动作品才能删除！")
    
    from diy.models import AuthOpus, AuthOpusPage
    from WebZone.settings import MEDIA_ROOT
    import os
    import shutil
    from utils import get_user_path
    from gateway.views_opus import delete_opus_ref
    if activity_list.fruit_type == 2:
        if activity_fruit.opus_id:
            auth_opus = AuthOpus.objects.get(id=activity_fruit.opus_id)
            if AuthOpusPage.objects.filter(auth_opus=auth_opus).count() > 0:
                opus_path = get_user_path(request.user, "opus", auth_opus.id)
                opus_absdir = os.path.join(MEDIA_ROOT, opus_path)
                try: shutil.rmtree(opus_absdir)
                except: pass
                
                delete_opus_ref(auth_opus)
                AuthOpusPage.objects.filter(auth_opus=auth_opus).delete()
            auth_opus.delete()
    
    activity_fruit.delete()
    
    return SuccessResponse({"fruit_id":param.fruit_id})


@login_required
def approve_fruit(request, param):
    """
        审核通过、不过通活动作品，不通过的需要用户重新编辑
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return FailResponse(u"没有权限!")
        
    if param.has_key("fruit_id"): fruit_id = int(param.fruit_id)
    else: return FailResponse(u"必须传入活动fruit_id")
    if param.has_key("approve"): approve = int(param.approve)
    else: return FailResponse(u"必须传入活动approve")
    
    try: activity_fruit = ActivityFruit.objects.get(id=fruit_id)
    except: return FailResponse(u"活动作品不存在")
    try: activity_list = ActivityList.objects.get(id=activity_fruit.activity_id)
    except: return FailResponse(u"活动ID不存在")
    
    if activity_fruit.status <> 1:
        return FailResponse(u"活动作品已经审核过，不需要重复审核！")
    
    if approve:
        if activity_list.fruit_type == 2:   #原创比赛
            auth_opus = AuthOpus.objects.get(id=activity_fruit.opus_id)
            if auth_opus.status <> 2:
                auth_opus.status = 2
                auth_opus.save()
        activity_fruit.status = 2  #审核通过
    else:
        activity_fruit.status = -1  #审核未通过
    activity_fruit.save()
    
    return SuccessResponse({"fruit_id":activity_fruit.id})


@print_trace
@login_required
def search_activity_and_fruit(request, params):
    '''
    搜索活动和作品的混合列表
    editor: kamihati  2015/4/15 增加对省少儿图书馆的活动搜索结果的区分（yh.hnsst.org.cn 读取全国。sst.3qdou.com读取本省（本机构））
    :param request:
    :param params:
          params.key    搜索关键字.string
          params.page_index  页码。从1计数
          params.page_size   每页数据数。默认8。
          params.range_type   范围 。0全国  1本机构  2联合
          params.library_id   机构id  。当range_type为2的时候传这个参数
    :return:
           数据字典：
               data_list :  数据结果

               data_count:  数据总数
               page_count:  总页数
               page_index:  页码 从1计数
    '''
    # range_type = int(params.range_type) if params.has_key('range_type') else None
    page_size = int(params.page_size) if params.has_key('page_size') else 8
    page_index = int(params.page_index) if params.has_key('page_index') else 1
    key = params.key if params.has_key('key') else ''
    status = str(params.status) if params.has_key('status') else ''
    # 字符串 。允许值为 空或  activity,fruit,series三者的组合字符串
    type = params.type if params.has_key('type') else ''

    results = dict()
    results['data'] = []
    results['page_index'] = page_index
    data_list, results['data_count'], results['page_count'], results['page_size'] = search_activity(
        page_index - 1, page_size, key,
        status, type, request.get_host().lower(),
        library_id=request.user.library_id)

    for data in data_list:
        data_dict = {}
        '''
        data_dict['id'] = data['id']
        data_dict['title'] = data['title']
        data_dict['library_id'] = data['library_id']
        data_dict['lib_name'] = data['lib_name']
        data_dict['thumbnail'] = MEDIA_URL + data['thumbnail']
        data_dict['activity_status'] = data['activity_status']
        data_dict['start_time'] = data['start_time']
        '''
        if data['nickname'] == '':
            data_dict['id'] = data['id']
            data_dict['title'] = data['title']
            data_dict['library_name'] = data['lib_name']
            data_dict['type'] = 'series'
            data_dict['cover'] = MEDIA_URL + data['thumbnail']
        elif data['activity_name'] == '':
            data_dict = get_activity_for_amf(data['id'])
            data_dict['type'] = 'activity'
            obj = ActivityList.objects.get(id=data['id'])
            # 特殊活动。需要定制输出
            if obj.fruit_type == 5:
                data_dict['link_url'] = '' if not obj.link_url else '/media/' + obj.link_url
                data_dict['activity_img'] =  '' if not obj.activity_img else '/media/' + obj.activity_img
        else:
            data_dict = get_activity_fruit_for_amf(data['id'], int(data['fruit_type']))
            data_dict['type'] = 'fruit'
        '''
        data_dict['fruit_type'] = data['fruit_type']
        data_dict['opus_type'] = data['opus_type']
        '''
        results['data'].append(data_dict)
    return  SuccessResponse(results)


def get_series_activity(request, param):
    '''
    获取系列活动列表
    editor: kamihati 2015/5/12
    :param request:
    :param param:
                page_index:
                page_size:
                series_id
    :return:
    '''
    page_index = int(param.page_index if param.has_key('page_index') else 1)
    page_size = int(param.page_size if param.has_key('page_size') else 8)
    series_id = param.series_id
    # 导入系列活动分页方法
    from activity.series_handler import get_activity_series_pager
    data_list, data_count = get_activity_series_pager(page_index - 1, page_size, series_id)
    result = dict(data=list())
    for data in data_list:
        result['data'].append(get_activity_for_amf(data['id']))
    result['data_count'] = data_count
    result['page_index'] = page_index
    result['page_size'] = page_size
    return SuccessResponse(result)


@print_trace
def get_activity_and_series(request, param):
    '''
    搜索活动与系列活动列表
    editor: kamihati 2015/5/14
    :param request:
    :param param:
             page_index: 页码。从1开始
             page_size: 每页数据数。
             status: 活动状态
    :return:
    '''
    page_index = int(param.page_index if param.has_key('page_index') else 1)
    page_size = int(param.page_size if param.has_key('page_size') else 8)
    status = param.status if param.has_key('status') else ''
    # 导入获取主题活动与系列活动混合列表的方法
    from activity.series_handler import get_activity_and_series_pager
    data_list, data_count = get_activity_and_series_pager(page_index - 1, page_size, status=status)
    result = dict(data=list())
    for data in data_list:
        if data['nickname'] == '':
            result['data'].append(dict(
                id=data['id'],
                title=data['title'],
                cover='/media/' + data['thumbnail'],
                library_name=data['lib_name'],
                type='series',
                activity_count=ActivityList.objects.filter(series_id=data['id']).exclude(status=-1).count()))
        else:
            d = get_activity_for_amf(data['id'])
            d['type'] = 'activity'
            result['data'].append(d)
    result['data_count'] = data_count
    result['page_index'] = page_index
    result['page_size'] = page_size
    return SuccessResponse(result)


def get_activity_fruit_folder(request, param):
    '''
    获取活动下的作品数据概况
    editor: kamihati 2015/6/10  需要获取每类数据的总数和第一个作品的信息
    :param request:
    :param param:
    :return:
    '''
    result = dict()
    activity_id = int(param.activity_id)

    # 活动预告
    result['yugao_type'] = 59
    result['yugao_count'] = ActivityFruit.objects.filter(activity_id=activity_id, status=2, opus_type=59).count()
    result['yugao'] = None
    if result['yugao_count'] != 0:
        yugao = ActivityFruit.objects.filter(activity_id=activity_id, status=2, opus_type=59).order_by("-is_top",
                                                                                                       "-id")[0]
        result['yugao'] = dict(id=yugao.id, title=yugao.fruit_name, opus_id=yugao.opus_id,
                               img='/media/' + yugao.thumbnail if yugao.thumbnail else '')

    # 活动结果
    result['jieguo_type'] = 60
    result['jieguo_count'] = ActivityFruit.objects.filter(activity_id=activity_id, status=2, opus_type=60).count()
    result['jieguo'] = None
    if result['jieguo_count'] != 0:
        jieguo = ActivityFruit.objects.filter(activity_id=activity_id, status=2, opus_type=60).order_by("-is_top",
                                                                                                        "-id")[0]
        result['jieguo'] = dict(id=jieguo.id, title=jieguo.fruit_name, opus_id=jieguo.opus_id,
                                img='/media/' + jieguo.thumbnail if jieguo.thumbnail else '')

    # 活动新闻
    result['xinwen_type'] = 61
    result['xinwen_count'] = ActivityFruit.objects.filter(activity_id=activity_id, status=2, opus_type=61).count()
    result['xinwen'] = None
    if result['xinwen_count'] != 0:
        news = ActivityFruit.objects.filter(activity_id=activity_id, status=2, opus_type=61).order_by("-is_top",
                                                                                                      "-id")[0]
        result['xinwen'] = dict(id=news.id, title=news.fruit_name, opus_id=news.opus_id,
                                img='/media/' + news.thumbnail if news.thumbnail else '')

    # 活动播报
    result['bobao_type'] = 63
    result['bobao_count'] = ActivityFruit.objects.filter(activity_id=activity_id, status=2, opus_type=63).count()
    result['bobao'] = None
    if result['bobao_count'] != 0:
        bobao = ActivityFruit.objects.filter(activity_id=activity_id, status=2, opus_type=63).order_by("-is_top",
                                                                                                       "-id")[0]
        result['bobao'] = dict(id=bobao.id, title=bobao.fruit_name, opus_id=bobao.opus_id,
                               img='/media/' + bobao.thumbnail if bobao.thumbnail else '')

    # 活动通知
    result['tongzhi_type'] = 62
    result['tongzhi_count'] = ActivityFruit.objects.filter(activity_id=activity_id, status=2, opus_type=62).count()
    result['tongzhi'] = None
    if result['tongzhi_count'] != 0:
        tongzhi = ActivityFruit.objects.filter(activity_id=activity_id, status=2, opus_type=62).order_by("-is_top",
                                                                                                         "-id")[0]
        result['tongzhi'] = dict(id=tongzhi.id, title=tongzhi.fruit_name, opus_id=tongzhi.opus_id,
                                 img='/media/' + tongzhi.thumbnail if tongzhi.thumbnail else '')

    # editor: kamihati 2015/6/11  系统分类不显示在活动作品列表中
    # 活动作品
    result['fruit_count'] = ActivityFruit.objects.filter(activity_id=activity_id, status=2, fruit_type__in=[2, 3, 4]
                                                         ).exclude(opus_type__in=[59, 60, 61, 62, 63]).count()
    result['fruit'] = None
    if result['fruit_count'] != 0:
        fruit = ActivityFruit.objects.filter(activity_id=activity_id, status=2, fruit_type__in=[2, 3, 4]
                                             ).exclude(opus_type__in=[59, 60, 61, 62, 63]).order_by("-is_top", "-id")[0]
        result['fruit'] = dict(id=fruit.id, name=fruit.fruit_name,
                               img='/media/' + fruit.thumbnail if fruit.thumbnail else '')
    return SuccessResponse(data=result)


def get_activity_folder_data(request, param):
    '''
    根据活动概览界面的动作获取数据
    editor: kamihati 2015/6/10
    :return:
    '''
    page_index = int(param.page_index) if param.has_key('page_index') else 0
    page_size = int(param.page_size) if param.has_key('page_size') else 8
    order_by = param.order_by if param.has_key('order_by') else ''
    group_id = param.group_id if param.has_key('group_id') else ''
    activity_id = int(param.activity_id)
    # 作品类型。目前只针对。活动预告。结果。新闻。播报。通知。五种。传0则取普通作品
    # editor: kamihati 2015/6/10   对应get_activity_fruit_folder所使用的作品类型
    opus_type = int(param.opus_type)
    # 导入获取活动作品分页的方法
    from activity.fruit_handler import get_activity_fruit_pager
    if opus_type == 0:
        # 取活动的参赛作品
        data_list, data_count = get_activity_fruit_pager(page_index - 1, page_size, activity_id=activity_id,
                                                         n_opus_type=1, order_by=order_by, group_id=group_id)
        data_list = [get_activity_fruit_for_amf(obj['id'], obj['fruit_type']) for obj in data_list]
    else:
        # 取对应类型的系统作品
        data_list, data_count = get_activity_fruit_pager(page_index - 1, page_size, activity_id=activity_id,
                                                         opus_type=opus_type)
        for obj in data_list:
            obj['thumbnail'] = '/media/' + obj['thumbnail'] if obj['thumbnail'] else ''

    # 返回结果字典
    #  ['id', 'lib_name', 'activity_name', 'fruit_name', 'username', 'author_name', 'author_age', 'fruit_type',
    # 'group_name', 'status', 'user_lib_name', 'number', 'opus_id', 'activity_fruit_type', 'group_id']
    return SuccessResponse(
        data=dict(data=data_list, data_count=data_count, page_index=page_index, page_size=page_size,
        activity_id=activity_id, opus_type=opus_type))


def get_activity_status(request, param):
    '''
    editor: kamihati 2015/6/15  查询活动是否可以报名。可以投稿。可以投票
    :param request:
    :param param:
    :return:
    '''
    activity_id = param.activity_id if param.has_key('activity_id') else 0
    activity = ActivityList.objects.get(pk=activity_id)
    # 是否能够报名
    can_apply = 0
    if activity.sign_up_start_time and activity.sign_up_end_time:
        if activity.sign_up_start_time < datetime.now() and activity.sign_up_end_time > datetime.now():
            can_apply = 1
    # 是否能够投稿
    can_submit = 0
    if activity.submit_start_time and activity.submit_end_time:
        if activity.submit_start_time < datetime.now() and activity.submit_end_time > datetime.now():
            can_submit = 1
    # 是否能够投票
    can_vote = 0
    if activity.vote_start_time and activity.vote_end_time:
        if activity.vote_start_time < datetime.now() and activity.vote_end_time > datetime.now():
            is_vote = 1
    return SuccessResponse(data=dict(can_apply=can_apply, can_submit=can_submit, can_vote=can_vote))


def get_fruit_info(request, param):
    '''
    editor: kamihati 2015/6/16 获取活动作品的信息 。暂供活动投稿使用(仅供电子书类的投稿）
    :param request:
    :param param:
               .activity_id
    :return:
    '''
    # fruit_name,teacher,fruit_brief,small,opus_id
    activity_id = int(param.activity_id) if param.has_key('activity_id') else 0
    fruit = ActivityFruit.objects.filter(activity_id=activity_id, user_id=request.user.id, status__in=[-1, 0])
    if fruit.count() == 0:
        return FailResponse(u'没有草稿状态的投稿')
    fruit = fruit[0]
    from diy.models import AuthOpusPage
    page1 = AuthOpusPage.objects.filter(auth_opus_id=fruit.opus_id).order_by("page_index")
    small = ''
    if page1:
        page1 = page1[0]
        small = '/media/' + page1.img_small_path if page1.img_small_path else ''
    return SuccessResponse(dict(fruit_name=fruit.fruit_name,
                                 teacher=fruit.teacher,
                                 fruit_brief=fruit.fruit_brief,
                                 small=small,
                                 opus_id=fruit.opus_id))

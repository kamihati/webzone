# coding=utf8

'''
活动相关操作方法
coder: kamihati 2015/3/25   创建搜索活动分页方法
'''
import  datetime
# 导入缓存对象
from django.core.cache import cache
# 导入多媒体文件url配置
from WebZone.settings import MEDIA_URL
# 导入model数据编辑方法
from utils.db_handler import save_model_data

# 导入网络列表model
from activity.models import ActivityList
# 导入活动背景model
from activity.models import ActivityBackground

# 导入sql查询分页方法
from utils.db_handler import get_pager
# 导入sql查询数据总数的方法
from utils.db_handler import get_data_count
# 导入数据列表转化为dict的方法
from utils.db_handler import rows_to_dict_list
# 导入获取sql执行数据的方法
from utils.db_handler import get_sql_data
# 导入执行sql语句的方法
from utils.db_handler import execute_sql

def search_activity(page_index, page_size, key, status, type, host_str="", **args):
    '''
    搜索活动和活动作品
    :param page_index:  页码。从0开始
    :param page_size:   每页数据数。默认8
    :param key:    搜索关键字。默认为空
    :param status: 活动或所属活动的状态。为空字符则查询所有状态
    :param type:  数据类别。只查询活动则传'activity', 查作品则传'fruit'
    :return: data_list,数据列表, data_count,数据总数, page_count总页数, 'page_size':每页数据数
    coder: kamihati 2015/3/25   搜索指定条件的活动和作品数据。查询较复杂于是写入视图。在这里进行调用分页。
    '''
    results = []
    data_count = 0
    page_count = 1
    where_str = '1=1'
    # editor kamihati 2015/4/28   客户端有这个bug。为了赶时间在服务端对文本框默认文字进行过滤。将来要去掉
    key = key.replace(u'活动/作品/作者/图书馆', '')
    if key != '' and key is not None:
        where_str += ' AND (title LIKE \'%' + key + '%\' OR activity_name LIKE \'%' + key + '%\' OR nickname LIKE \'%' + key + '%\' OR lib_name LIKE \'%' + key + '%\')'
    if status != '':
        where_str += ' AND activity_status=' + status
    if type != '':
        if  type == 'activity':
            where_str += ' AND nickname<>\'\' AND activity_name=\'\''
        elif type == 'fruit':
            where_str += ' AND nickname<>\'\' AND activity_name<>\'\''
        elif type == 'series':
            where_str += ' AND nickname=\'\''

    if 'library_id' in args:
        from library.models import Library
        library = Library.objects.get(id=args['library_id'])
        if library.is_global == 0:
            where_str += " AND library_id=%s" % args['library_id']

    data_list = rows_to_dict_list(
        get_pager('id,title,library_id,lib_name,thumbnail,activity_status,start_time,nickname,activity_name,fruit_type,opus_type,scope_list,activity_img,link_url',
                  'view_search_activity_and_fruit',
                  '',
                  where_str,
                  'ORDER BY id DESC,start_time DESC',
                  page_index, page_size),
        ['id', 'title', 'library_id', 'lib_name', 'thumbnail', 'activity_status', 'start_time', 'nickname', 'activity_name', 'fruit_type', 'opus_type', 'scope_list', 'activity_img', 'link_url'])
    data_count = get_data_count('id', 'view_search_activity_and_fruit', '', where_str)
    page_count = data_count / page_size
    if data_count % page_size > 0:
        page_count += 1
    return  data_list, data_count, page_count, page_size

from utils.db_handler import get_cursor

def get_period(submit_start_time, submit_end_time):
    submit_start_time = datetime.datetime.strptime(submit_start_time, "%Y-%m-%d %H:%M:%S")
    submit_end_time = datetime.datetime.strptime(submit_end_time, "%Y-%m-%d %H:%M:%S")
    if datetime.datetime.now() < submit_start_time: return 0
    elif datetime.datetime.now() > submit_end_time: return 2
    else: return 1

def get_lib_name(lib_id):
    cache_key = "gateway.views_activity.get_lib_name"
    lib_name_dict = cache.get(cache_key, {})
    if not lib_name_dict:
        sql = "select id,lib_name from library"
        rows = get_sql_data(sql)
        for row in rows:
            id = int(row[0])
            lib_name = row[1]
            lib_name_dict[id] = lib_name
        cache.set(cache_key, lib_name_dict)
    if lib_name_dict.has_key(lib_id):
        return lib_name_dict[lib_id]
    else:
        return u"未知机构名称"

def get_activity_for_amf(id):
    ''''
    获取指定的活动数据供amf调用
    :param id:活动id
    :return:
    '''
    sql = "select l.id,l.library_id,user_id,title,submit_start_time,submit_end_time,cover,thumbnail"
    sql += ",fruit_type,can_submit,need_group,can_vote,vote_start_time,vote_end_time"
    sql += ",need_fruit_name,need_fruit_brief,need_author_name,need_author_brief,need_author_sex,need_author_age,need_author_school"
    sql += ",opus_id,sponsor_name,is_top,need_unit,need_district,need_author_telephone,need_author_email,status,scope_list,period,series_id,activity_img,link_url"
    sql += " from activity_list l LEFT JOIN activity_option o on l.id=o.activity_id"
    sql += ' WHERE l.id=%s' % id
    rows = get_sql_data(sql)
    if not rows:
        return dict()
    row = rows[0]
    id = int(row[0])
    library_id = int(row[1])
    user_id = int(row[2])
    title = row[3]
    submit_start_time = row[4].strftime("%Y-%m-%d %H:%M:%S") if row[4] else ""
    submit_end_time = row[5].strftime("%Y-%m-%d %H:%M:%S") if row[5] else ""
    cover = MEDIA_URL + row[6] if row[6] else ""
    thumbnail = MEDIA_URL + row[7] if row[7] else ""

    #(1,u"新闻播报"),(2,u"电子创作"),(3,u"图片"),(4,u"视频")
    fruit_type = int(row[8])
    can_submit = int(row[9])
    need_group = int(row[10])
    can_vote = int(row[11])
    vote_start_time = row[12].strftime("%Y-%m-%d %H:%M:%S") if row[12] else ""
    vote_end_time = row[13].strftime("%Y-%m-%d %H:%M:%S") if row[13] else ""

    # editor : kamihati  2015/4/16     临时改动  。后期需要debugg
    need_fruit_name = 1#int(row[14])
    need_fruit_brief = 1 #int(row[15])
    need_author_name = 1 #int(row[16])
    need_author_brief = 1 #int(row[17])
    need_author_sex = 1 #int(row[18])
    need_author_age = 1 #int(row[19])
    need_author_school = 1 #int(row[20])

    opus_id = int(row[21]) if row[21] else 0
    sponsor_name = row[22] if row[22] else ""
    is_top = int(row[23])
    need_unit = int(row[24])
    need_district = int(row[25])

    need_author_telephone = 1 # int(row[26])
    need_author_email = 1 # int(row[27])
    status = int(row[28])
    scope_list = row[29]
    period = int(row[30])
    series_id = int(row[31])
    activity_img = '/media/%s' % row[32] if row[32] else ''
    link_url = '/media/%s' % row[33] if row[33] else ''
    #now_period = get_period(submit_start_time, submit_end_time)
    #if now_period <> period:
    #    sql = "update activity_list set period=%d where id=%d" % (now_period, id)
    #    execute_sql(sql)

    activity_dict = {"id":id, "library_id":library_id, "user_id":user_id, "title":title, "cover":cover, "thumbnail":thumbnail}
    activity_dict["submit_start_time"] = submit_start_time
    activity_dict["submit_end_time"] = submit_end_time
    activity_dict["library_name"] = get_lib_name(library_id)
    activity_dict["fruit_type"] = fruit_type
    activity_dict["can_submit"] = can_submit
    activity_dict["need_group"] = need_group
    activity_dict["can_vote"] = can_vote
    activity_dict["vote_start_time"] = vote_start_time
    activity_dict["vote_end_time"] = vote_end_time

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
    activity_dict["period"] = period
    activity_dict['series_id'] = series_id
    activity_dict['activity_img'] = activity_img
    activity_dict['link_url'] = link_url
    if fruit_type == 1:
        sql = ""

    if need_group:
        group_names = ""
        sql = "select id,group_name From activity_group where activity_id=%d ORDER BY update_time DESC" % id

        group_rows = get_sql_data(sql)
        for group_row in group_rows:
            group_names += "" if len(group_names) == 0 else ";"
            group_names += "%d,%s" % (int(group_row[0]), group_row[1])
        activity_dict["group_names"] = group_names
    return activity_dict


def get_group_name(group_id):
    cache_key = "gateway.views_activity.get_group_name"
    group_name_dict = cache.get(cache_key, {})
    if not group_name_dict:
        sql = "select id,group_name from activity_group"
        rows = get_sql_data(sql)
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
        rows = get_sql_data(sql)
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


def get_unit_name(unit_id):
    cache_key = "gateway.views_activity.get_unit_name"
    unit_name_dict = cache.get(cache_key, {})
    if not unit_name_dict:
        sql = "select id,unit_name from activity_unit"
        rows = get_sql_data(sql)
        for row in rows:
            id = int(row[0])
            unit_name = row[1]
            unit_name_dict[id] = unit_name
        cache.set(cache_key, unit_name_dict)
    if unit_name_dict.has_key(unit_id):
        return unit_name_dict[unit_id]
    else:
        return u"未知报送单位"


def get_asset_dict(asset_id, fruit_type):
    #(3,u"图片"),(4,u"视频")
    sql = "select id,res_path,img_large_path,img_small_path,codec_status from auth_asset where id=%s" % asset_id
    rows = get_sql_data(sql)
    if not rows:
        return  None
    row = rows[0]
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
        elif fruit_type == 5:
            url = MEDIA_URL + row[1]
            small = MEDIA_URL + row[3]
            codec_status = ""
        asset_dict["small"] = small
        asset_dict["url"] = url
        asset_dict["codec_status"] = codec_status
    return asset_dict

def get_opus_dict(opus_id):
    #(3,u"图片"),(4,u"视频")
    sql = "select img_small_path from auth_opus_page where auth_opus_id=%s and page_index=1" % opus_id
    rows = get_sql_data(sql)
    opus_dict = {}
    if rows:
        opus_dict["small"] = MEDIA_URL + rows[0][0]
    sql = "select id,preview_times,comment_times,praise_times from auth_opus where id=%s" % opus_id
    rows = get_sql_data(sql)
    if rows:
        #id = int(row[0])
        opus_dict["preview_times"] = int(rows[0][1])
        opus_dict["comment_times"] = int(rows[0][2])
        opus_dict["praise_times"] = int(rows[0][3])
    return opus_dict


def get_activity_fruit_for_amf(id, fruit_type):
    '''
    获取活动作品
    :param id: 作品id
    :return:
    '''
    sql = u"select a.id,a.library_id,a.user_id,number,group_id,auth_asset_id,district_id,unit_id,opus_id"
    sql += u",fruit_name,fruit_brief,author_name,author_brief,author_sex,author_age,school_name"
    sql += u",author_telephone,author_email,score,vote,a.is_top"
    if fruit_type == 2:
        sql += u",o.grade,o.preview_times,o.comment_times,o.praise_times"
    else:
        sql += u",a.grade,a.preview_times,a.comment_times,a.praise_times"
    sql += u",a.width,a.height,a.update_time,a.status,a.opus_type,a.activity_id From activity_fruit a"
    if fruit_type == 2:
        sql += " LEFT JOIN auth_opus o on o.id=a.opus_id"
    sql += ' WHERE a.id=%s' % id
    rows = get_sql_data(sql)
    if not rows:
        return dict()
    row = rows[0]

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
    grade = 0 if row[21] is None else int(row[21])
    preview_times = 0 if row[22] is None else int(row[22])
    comment_times = 0 if row[23] is None else int(row[23])
    praise_times = 0 if row[24] is None else int(row[24])

    width = int(row[25])
    height = int(row[26])
    update_time = row[27].strftime("%Y-%m-%d %H:%M:%S")
    status = row[28]
    opus_type = row[29]
    activity_id = int(row[30])

    activity_opus_dict = {"id": id, "library_id": library_id, "user_id": user_id, "number": number, "group_id": group_id, "auth_asset_id": auth_asset_id}
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

    activity_opus_dict["fruit_type"] = fruit_type
    path_dict = dict()
    # 系统作品以及创作类型的作品
    if opus_type in (59, 60, 61, 62 ,63) or fruit_type in (1, 2):
        path_dict = get_opus_dict(opus_id)
    elif fruit_type in (3, 4, 5):
        path_dict = get_asset_dict(auth_asset_id, fruit_type)
    if path_dict:
        activity_opus_dict.update(path_dict)

    act = ActivityList.objects.get(pk=activity_id)
    activity_opus_dict["can_vote"] = act.can_vote
    activity_opus_dict['activity_name'] = act.title
    return activity_opus_dict


def delete_activity_list(id):
    '''
    删除网络活动
    editor: kamihati 2015/4/24  删除活动
    :param id: 活动id
    :return:
    '''
    if ActivityList.objects.filter(pk=id).update(status=-1):
        return  True
    return False


def edit_activity_background(params):
    '''
    编辑活动背景
    :param params:
    :return:
    '''
    return save_model_data(ActivityBackground, params)


def get_activity_pager(page_index, page_size, **args):
    '''
    获取活动的分页数据
    editor: kamihati 2015/5/12
    :param page_index: 页码。从0开始
    :param page_size:
    :param args:
    :return:
    '''
    # 默认取状态不为已删除的机构
    where_str = "a.status<>-1"
    # 如果是系列活动搜索则忽略其他条件的搜索
    if args['series_id'] not in ( '', '0'):
        where_str += ' AND a.series_id=%s' % args['series_id']
    else:
        if args['library_id'] != '':
            where_str += " AND a.library_id=%s" % args['library_id']
        if args['place_type'] != '':
            where_str += " AND a.place_type='%s'" % args['place_type']
        if args['activity_status'] != '':
            where_str += ' AND a.status=%s' % args['activity_status']
        if args['search_text'] != '':
            where_str += ' AND a.title LIKE \'%' + args['search_text'] + '%\''
        if args['fruit_type'] != '':
            where_str += ' AND a.fruit_type=%s' % args['fruit_type']

    data_list = rows_to_dict_list(
        get_pager('a.library_id,b.lib_name,a.id,a.title,a.place_type,a.status,a.sign_up_member_count,a.join_member_count,a.series_id,c.title as series_title,a.is_top,a.fruit_type',
                  'activity_list a',
                  'INNER JOIN library b ON b.id=a.library_id LEFT JOIN activity_series c ON c.id=a.series_id',
                  where_str,
                  'ORDER BY a.id DESC',
                  page_index, page_size),
        ['library_id', 'lib_name', 'id', 'title', 'place_type', 'status', 'sign_up_member_count', 'join_member_count', 'series_id', 'series_title', 'is_top', 'fruit_type'])
    data_count = get_data_count('a.id', 'activity_list a', 'INNER JOIN library b ON b.id=a.library_id LEFT JOIN activity_series c ON c.id=a.series_id', where_str)
    return data_list, data_count


def get_activity_background_pager(page_index, page_size):
    '''
    获取活动背景的翻页数据
    :param page_index: 页码从0开始
    :param page_size: 每页数据
    :return:
    '''
    data_list = rows_to_dict_list(
        get_pager('id,name,origin_path,tag_font_style,tag_font_color,tag_font_size,content_font_style,content_font_color,content_font_size,position,use_num,create_time',
                  'activity_background',
                  '',
                  'status=0',
                  'ORDER BY id DESC',
                  page_index, page_size),
        ['id', 'name', 'origin_path', 'tag_font_style', 'tag_font_color', 'tag_font_size', 'content_font_style', 'content_font_color', 'content_font_size', 'position', 'use_num', 'create_time'])
    data_count = get_data_count('id', 'activity_background', '', '1=1')
    return data_list, data_count


def remove_activity_background(id):
    '''
    移除活动背景
    :param id:  活动背景id
    :return:
    '''
    if ActivityBackground.objects.filter(pk=id).update(status=1):
        return  True
    return  False


def get_activity_by_library(lib_id, **kwargs):
    '''
    获取指定机构的活动列表。
    editor: kamihati 2015/5/25
    :param lib_id:
    :return:
    '''
    if kwargs.has_key('status'):
        return ActivityList.objects.filter(library_id=lib_id, status=kwargs['status']).order_by('-id')
    return ActivityList.objects.filter(library_id=lib_id).exclude(status=-1).order_by('-id')


def get_activity_background_list():
    '''
    获取活动背景列表
    :return:
    '''
    return ActivityBackground.objects.filter(status=0)


def make_activity_option(option_obj, param):
    '''
    根据列表中存在的选项设定选项列表的值
    :param option_obj:
                新建的option对象或要修改的option对象
    :param param:
               list 。需要哪个字段为必选项就把这个字段名写入列表中传进来
    :return:
            保存后的option对象
    '''
    option_obj.need_fruit_name = 1 if 'need_fruit_name' in param else 0
    option_obj.need_fruit_brief = 1 if 'need_fruit_brief' in param else 0
    option_obj.need_author_name = 1 if 'need_author_name' in param else 0
    option_obj.need_author_brief = 1 if 'need_author_brief' in param else 0
    option_obj.need_author_sex = 1 if 'need_author_sex' in param else 0
    option_obj.need_author_age = 1 if 'need_author_age' in param else 0
    option_obj.need_author_school = 1 if 'need_author_school' in param else 0
    option_obj.need_author_telephone = 1 if 'need_author_telephone' in param else 0
    option_obj.need_author_email = 1 if 'need_author_email' in param else 0
    option_obj.need_author_address = 1 if 'need_author_address' in param else 0
    option_obj.need_author_business = 1 if 'need_author_business' in param else 0
    option_obj.save()
    return option_obj


def update_activity_top(id, status):
    '''
    更新活动的置顶/推荐状态
    editor: kamihati 2015/4/24 供活动管理页面使用
    editor: kamihati 2015/6/12  增加对is_top不同顺序进行排序的支持
    :param id:
    :param status:
    :return:
    '''
    activity = ActivityList.objects.get(pk=id)
    is_top = 0
    if status != "0":
        from utils.db_handler import execute_sql
        # 当设置置顶顺序时。更新指定位置后的顺序。由于最多只能指定21个位置。故第22位取消置顶状态
        sql = "UPDATE activity_list SET is_top=0 WHERE is_top=22"
        execute_sql(sql)
        sql = 'UPDATE activity_list SET is_top=is_top+1 WHERE is_top BETWEEN %s AND 21' % status
        execute_sql(sql)
        is_top = status
    activity.is_top = is_top
    activity.save()
    return True


def get_activity_list_by_request(request):
    '''
    根据当前请求上下文获取进行中的活动列表
    editor: kamihati 2015/4/29  供活动管理页面新增活动作品使用
    :param request:
    :return:
    '''
    # 超级管理员可以查询到所有活动。其他角色只能查询到本机构活动
    if request.user.auth_type in (9, 8):
        return ActivityList.objects.filter(status=1)
    return ActivityList.objects.filter(status=1, library_id=request.user.library_id)


def auto_update_activity_list_status(id):
    '''
    根据活动的各种时间改变活动的状态
    editor: kamihati 2015/5/15
    :param id:
    :return:
    '''
    now = datetime.datetime.now()
    activity = ActivityList.objects.get(pk=id)
    # 如果活动状态不正常(已删除等)则不作处理
    if activity.status < 0:
        return
    print activity.sign_up_start_time
    # 报名开始时间已到
    if activity.sign_up_start_time < now:
        # 更新活动状态为已开始
        activity.status = 1 if activity.status == 0 else activity.status
    if activity.place_type == 'net':
        print activity.submit_end_time
        # 投稿时间已结束则更新状态为已结束
        if activity.submit_end_time < now:
            activity.status == 2 if activity.status in (0, 1) else activity.status
    elif activity.place_type == 'place':
        # 如果活动结束时间已过
        if activity.activity_end_time < now:
            activity.status = 2 if activity in (0, 1) else activity.status
    activity.save()


def get_res_type_by_fruit_type(fruit_type):
    '''
    根据活动作品类型获取对应的资源类型
    editor: kamihati 2015/5/20  由于旧版本设计中活动作品类型与资源类型并非一一对应。新版本为与旧版本兼容故写此方法
    将来待优化后此方法应取消；
    :param fruit_type:活动作品类型
    :return:
    '''
    # res_type  ((1,u"图片"),(2,u"声音"),(3,u"视频"),(4,u"涂鸦"),(11,u"故事大王"))
    # editor: kamihati 2015/5/20  返回结果对应res_type
    result = {"1": 0, "2": 0, "3": 1, "4": 3, "5": 0, "6": 2}
    return result[str(fruit_type)]


def set_activity_join_member(activity_id):
    '''
    更新活动的参与人数
    editor: kamihati 2015/6/18
    :param activity_id:
    :return:
    '''
    from activity.models import ActivityFruit
    ActivityList.objects.filter(pk=activity_id).update(
        join_member_count=ActivityFruit.objects.filter(activity_id=activity_id, status_gt=0).count())
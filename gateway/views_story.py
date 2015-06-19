#coding: utf-8
'''
Created on 2014-6-13

@author: Administrator
'''
from math import ceil
import random

from django.db import connection, connections
from WebZone.settings import DB_READ_NAME

from datetime import date, datetime

from WebZone.settings import MEDIA_URL
from utils import get_ip
from utils.decorator import login_required

from gateway import SuccessResponse, FailResponse
from widget.models import WidgetDistrict, WidgetStoryOpus
from widget.models import WidgetStoryVote
import hashlib


@login_required
#@require_POST
def get_province_list(request):
    cursor = connections[DB_READ_NAME].cursor()
    sql = "select id,name From widget_district where parent_id=0 and story_count>0 order by id"
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()
    data_lists = []
    for row in rows:
        data_lists.append({"id":row[0], "name":row[1]})
    return SuccessResponse(data_lists)

@login_required
#@require_POST
def get_city_list(request, province_id):
    if WidgetDistrict.objects.filter(id=province_id).count() == 0:
        return FailResponse(u"省id不正确")
    
    cursor = connections[DB_READ_NAME].cursor()
    sql = "select id,name From widget_district where parent_id=%d and story_count>0 order by id" % province_id
    #print sql
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()
    data_lists = []
    for row in rows:
        data_lists.append({"id":row[0], "name":row[1]})
    return SuccessResponse(data_lists)

@login_required
def get_county_list(request, city_id):
    if WidgetDistrict.objects.filter(id=city_id).count() == 0:
        return FailResponse(u"市id不正确")
    
    cursor = connections[DB_READ_NAME].cursor()
    sql = "select id,name From widget_district where parent_id=%d and story_count>0 order by id" % city_id
    #print sql
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()
    data_lists = []
    for row in rows:
        data_lists.append({"id":row[0], "name":row[1]})
    return SuccessResponse(data_lists)     


@login_required
def get_story_list(request, obj):
    """
    obj:print type(obj)
    print dir(obj)
    <class 'pyamf.ASObject'>
    ['__amf__', '__class__', '__cmp__', '__contains__', '__delattr__', '__delitem__'
    , '__dict__', '__doc__', '__eq__', '__format__', '__ge__', '__getattr__', '__get
    attribute__', '__getitem__', '__gt__', '__hash__', '__init__', '__iter__', '__le
    __', '__len__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__re
    duce_ex__', '__repr__', '__setattr__', '__setitem__', '__sizeof__', '__str__', '
    __subclasshook__', '__weakref__', 'clear', 'copy', 'fromkeys', 'get', 'has_key',
     'items', 'iteritems', 'iterkeys', 'itervalues', 'keys', 'pop', 'popitem', 'setd
    efault', 'update', 'values', 'viewitems', 'viewkeys', 'viewvalues']
    """
    group_id = int(obj.group_id)     #0:所有, 1:学前组, 2:小学组
    district_id = int(obj.district_id)   #0:所有区域    其他:对应区域ID
    search_text = obj.search_text   #可搜索项:作者姓名，作品名称，报送机构名称，选手编号
    order_by_id = int(obj.order_by) #排序    0:默认(随机)    1:人气（投票数）    2:上传时间
    page_index = obj.page_index if obj.has_key("page_index") else 1
    page_size = obj.page_size if obj.has_key("page_size") else 12
    
    if group_id not in (0, 1, 2):
        return FailResponse(u"分组id:%s不正确" % group_id)
    if order_by_id not in (0, 1, 2):
        return FailResponse(u"排序选项:%s不正确" % order_by_id)
    
    cursor = connections[DB_READ_NAME].cursor()
    
    where_clause = "a.codec_status=1 and a.status=1"
    #只能显示本机构的
    #if request.user.library: where_clause += " and o.library_id=%d" % request.user.library_id
    #else: where_clause += " and o.library_id is NULL"
    if group_id <> 0:
        where_clause += " and o.group_id=%d" % group_id
    if district_id <> 0:
        where_clause += " and o.district_id like '%d%%'" % district_id
    if len(search_text) <> 0:
        where_clause += " and (o.story_name like '%%%s%%'" % search_text
        where_clause += " or o.actor_name like '%%%s%%'" % search_text
        where_clause += " or u.name like '%%%s%%'" % search_text
        where_clause += " or au.number like '%%%s%%')" % search_text
    where_md5 = hashlib.md5(where_clause).hexdigest()
    #print where_clause, where_md5
    
    story_list = []
    if order_by_id == 0:    #随机排序
        session_story_key = "gateway.get_story_list.opus_id"
        session_story_md5 = "gateway.get_story_list.md5"
        opus_id_list = request.session.get(session_story_key, [])
        old_where_md5 = request.session.get(session_story_md5, None)
        #opus_id_list = cache.get(session_story_key, [])
        if not opus_id_list or (where_md5 <> old_where_md5):
            #print "not found cache"
            opus_id_list = []
            sql = "select o.id from widget_story_opus o LEFT JOIN auth_asset a on o.auth_asset_id=a.id "
            sql += "LEFT JOIN widget_story_unit u on o.unit_id=u.id "
            sql += "LEFT JOIN auth_user au on o.user_id=au.id "
            sql += "where %s " % where_clause
            cursor.execute(sql)
            rows = cursor.fetchall()
            for row in rows:
                if not row: continue
                opus_id_list.append(int(row[0]))
            random.shuffle(opus_id_list)
            request.session[session_story_key] = opus_id_list
            request.session[session_story_md5] = where_md5
            
        start_index = (page_index-1)*page_size
        if start_index<0: start_index = 0
        end_index = start_index + page_size
        story_list = opus_id_list[start_index:end_index]
        #print "story_list", story_list
    elif order_by_id == 1:  #1:人气（投票数）
        order_by = "ORDER BY o.vote DESC"
    elif order_by_id == 2:  # 2:上传时间
        order_by = "ORDER BY o.update_time DESC"
    
    sql = "select count(*) from widget_story_opus o LEFT JOIN auth_asset a on o.auth_asset_id=a.id "
    sql += "LEFT JOIN widget_story_unit u on o.unit_id=u.id "
    sql += "LEFT JOIN auth_user au on o.user_id=au.id "
    sql += "where %s" % where_clause
    cursor.execute(sql)
    row = cursor.fetchone()
    count = 0
    if row: count = row[0]
    page_count = int(ceil(count/float(page_size)))
    
    if order_by_id == 0:
        sql = "select o.id,o.user_id,au.number,o.group_id,o.opus_id,o.district_id,o.unit_id,story_name,story_brief,"
        sql += "actor_name,actor_brief,o.sex,o.age,u.telephone,u.email,vote,u.name,u.brief,a.res_path,a.img_small_path "
        sql += "from widget_story_opus o LEFT JOIN auth_asset a on o.auth_asset_id=a.id "
        sql += "LEFT JOIN widget_story_unit u on o.unit_id=u.id "
        sql += "LEFT JOIN auth_user au on o.user_id=au.id "
        sql += "where o.id in (%s)" % ",".join([str(i) for i in story_list])
        #print "get_story_list:sql", sql
    else:
        sql = "select o.id,o.user_id,au.number,o.group_id,o.opus_id,o.district_id,o.unit_id,story_name,story_brief,"
        sql += "actor_name,actor_brief,o.sex,o.age,u.telephone,u.email,vote,u.name,u.brief,a.res_path,a.img_small_path "
        sql += "from widget_story_opus o LEFT JOIN auth_asset a on o.auth_asset_id=a.id "
        sql += "LEFT JOIN widget_story_unit u on o.unit_id=u.id "
        sql += "LEFT JOIN auth_user au on o.user_id=au.id "
        sql += "where %s " % where_clause
        sql += "%s LIMIT %s, %s" % (order_by, (page_index-1)*page_size, page_size)
    #print sql
    cursor.execute(sql)
    rows = cursor.fetchall()
    story_lists = []
    if order_by_id == 0:
        story_temp_dict = {}
    for row in rows:
        if not row: continue
        story_dict = {}
        story_dict["id"] = int(row[0])
        story_dict["user_id"] = row[1]
        story_dict["number"] = row[2]
        story_dict["group_id"] = row[3]
        story_dict["opus_id"] = row[4]
        story_dict["district_id"] = row[5]
        story_dict["unit_id"] = row[6]
        story_dict["story_name"] = row[7]
        story_dict["story_brief"] = row[8]
        story_dict["actor_name"] = row[9]
        story_dict["actor_brief"] = row[10]
        story_dict["sex"] = row[11]
        story_dict["age"] = row[12]
        story_dict["telephone"] = row[13]
        story_dict["email"] = row[14]
        story_dict["vote"] = row[15]
        story_dict["unit_name"] = row[16]
        story_dict["unit_brief"] = row[17]
        story_dict["res_path"] = MEDIA_URL + row[18]
        story_dict["img_small_path"] = MEDIA_URL + row[19]
        if order_by_id == 0:
            story_temp_dict[story_dict["id"]] = story_dict
        else:
            story_lists.append(story_dict)
    if order_by_id == 0:    #随机排序
        for story_id in story_list:
            story_lists.append(story_temp_dict[story_id])
        del story_temp_dict
    return SuccessResponse({"data":story_lists, "page_index": page_index, "page_count": page_count})


from utils.decorator import print_exec_time
@print_exec_time
@login_required
def vote_story(request, story_id):
    dt_end = datetime.strptime("2014-08-21", "%Y-%m-%d")
    dt_now = datetime.now()
    if dt_now>= dt_end:
        return FailResponse(u"投票截止时间为8-20 24:00，当前时间：%s，故事达人投票已截止，感谢你的参与。" % dt_now.strftime("%Y-%m-%d %H:%M:%S"))
        
    try: widget_story_opus = WidgetStoryOpus.objects.get(id=story_id)
    except: return FailResponse(u"作品ID:%s不存在" % story_id)
    
    real_ip = get_ip(request)
    
    referer = request.META.get('REFERER', '')
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    if referer.find('t=') > 0:
        try:
            t1 = int(referer[referer.find('t=')+2:referer.find('t=')+12])
            import time
            if int(time.time()) - t1 > 5*60:
                #print "referer:time_limited", int(time.time() * 1000), t1, real_ip, widget_story_opus.id
                return FailResponse(u"请通过官方网址:http://www.hnsst.org.cn的链接，或者直接下载客户端进行投票")
        except:
            import traceback
            traceback.print_exc()
    elif referer.find('http') >= 0:
        return FailResponse(u"请通过官方网址:http://www.hnsst.org.cn的链接，或者直接下载客户端进行投票")
    
    user_limit_count = WidgetStoryVote.objects.filter(create_time__gte=date.today(), user_id=request.user.id).count()
    if user_limit_count >= 10:
        return  FailResponse(u"当前登录账号今日投票数超限.")
    
    ip_limit_count = WidgetStoryVote.objects.filter(create_time__gte=date.today(), real_ip=real_ip).count()
    if ip_limit_count >= 50:
        return  FailResponse(u"你的IP(%s)今日投票数超限." % real_ip) 
    
#    if referer <> "app:/Main.swf":
#         agent_referer_limit_count = WidgetStoryVote.objects.filter(story_opus_id=widget_story_opus.id, user_agent=user_agent, referer=referer, create_time__gte=date.today()).count()
#         if agent_referer_limit_count >= 50:
#             print "referer:agent_referer_limit_count:", user_agent, widget_story_opus.id, real_ip
#             return  FailResponse(u"请遵守大赛规则，每IP每天限投10票。")
#         agent_limit_count = WidgetStoryVote.objects.filter(story_opus_id=widget_story_opus.id, user_agent=user_agent, create_time__gte=date.today()).count()
#         if agent_limit_count >= 250:
#             print "referer:agent_limit_count:", user_agent, widget_story_opus.id, real_ip
#             return  FailResponse(u"请遵守大赛规则，每IP每天限投10票。")
#     else:
#         agent_referer_limit_count = WidgetStoryVote.objects.filter(story_opus_id=widget_story_opus.id, user_agent=user_agent, referer=referer, create_time__gte=date.today()).count()
#         if agent_referer_limit_count >= 1000:
#             print "referer:agent_referer_limit_count:", user_agent, widget_story_opus.id, real_ip
#             return  FailResponse(u"请遵守大赛规则，每IP每天限投10票。")
    
    cursor = connections[DB_READ_NAME].cursor()
    sql = "update widget_story_opus set vote=vote+1 where id=%s and vote=%d" % (story_id, widget_story_opus.vote)
    #print sql
    if cursor.execute(sql) == 0:
        return FailResponse(u"投票失败，请重试")
    
    widget_story_vote = WidgetStoryVote()
    widget_story_vote.library_id = widget_story_opus.library_id
    widget_story_vote.story_opus = widget_story_opus
    widget_story_vote.user_id = request.user.id
    
    widget_story_vote.real_ip = real_ip
    widget_story_vote.user_agent = user_agent
    #widget_story_vote.http_cooike =  request.META.get('HTTP_COOKIE','')
    widget_story_vote.referer =  referer
    
    #widget_story_vote.accept =  request.META.get('HTTP_ACCEPT', '')
    #widget_story_vote.accept_language =  request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    #widget_story_vote.accept_encoding =  request.META.get('HTTP_ACCEPT_ENCODING', '')
    
    #md5_str = widget_story_vote.user_agent + widget_story_vote.referer + widget_story_vote.accept + widget_story_vote.accept_language + widget_story_vote.accept_encoding
    #widget_story_vote.md5 = hashlib.md5(md5_str).hexdigest()
    widget_story_vote.vote = widget_story_opus.vote+1
    widget_story_vote.save()
    return SuccessResponse({"id":story_id, "vote":widget_story_opus.vote+1}) 











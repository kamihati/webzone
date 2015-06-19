#coding: utf-8
'''
Created on 2014-6-13

@author: Administrator
'''
import os
import json
from math import ceil
from django.shortcuts import render
from django.http import HttpResponse

import traceback
from datetime import datetime

from django.db import connection, connections
from WebZone.settings import DB_READ_NAME
from PIL import Image, ImageDraw, ImageFont
from StringIO import StringIO

from WebZone.settings import MEDIA_ROOT, MEDIA_URL
from WebZone.conf import ALLOWED_VIDEO_EXTENSION,ALLOWED_VIDEO_UPLOAD_SIZE
from diy.models import AuthAsset, AuthAssetShare, AuthAssetRef
from diy.models import AuthOpus, AuthOpusPage
from account.models import AuthUser
from utils import get_ip
# Create your views here.

from utils.decorator import login_manager_required

#from django.views.decorators.http import require_http_methods
from django.views.decorators.http import require_POST
from gateway import FailResponse, SuccessResponse
from widget.models import WidgetDistrict, WidgetStoryUnit, WidgetStoryOpus
from utils import get_user_path

from manager import add_manager_action_log


@login_manager_required
#@require_POST
def get_new_number(request):
    return HttpResponse(new_number())

def new_number():
    """
        得到账号的一个新的编码
    """
    cursor = connections[DB_READ_NAME].cursor()
    #sql = "select number From auth_user order by id desc limit 1"
    sql = "select max(number) from auth_user"
    cursor.execute(sql)
    row = cursor.fetchone()
    number = row[0]
    max_number = int(number)+1 if number else 1
    return '%04d' % max_number
    
@login_manager_required
#@require_POST
def get_province_list(request):
    cursor = connections[DB_READ_NAME].cursor()
    sql = "select id,name From widget_district where parent_id=0 order by id"
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()
    data_lists = []
    for row in rows:
        data_lists.append({"id":row[0], "name":row[1]})
    return HttpResponse(SuccessResponse(data_lists))


@login_manager_required
#@require_POST
def get_city_list(request):
    try: province_id = int(request.REQUEST['id'])
    except: return HttpResponse(FailResponse(u"先选择省"))
    print province_id
    if WidgetDistrict.objects.filter(id=province_id).count() == 0:
        return HttpResponse(FailResponse(u"省id不正确"))
    
    cursor = connections[DB_READ_NAME].cursor()
    sql = "select id,name From widget_district where parent_id=%d order by id" % province_id
    print sql
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()
    data_lists = []
    for row in rows:
        data_lists.append({"id":row[0], "name":row[1]})
    return HttpResponse(SuccessResponse(data_lists))       


@login_manager_required
#@require_POST
def get_county_list(request):
    try: city_id = int(request.REQUEST['id'])
    except: return HttpResponse(FailResponse(u"先选择市"))
    print city_id
    if WidgetDistrict.objects.filter(id=city_id).count() == 0:
        return HttpResponse(FailResponse(u"市id不正确"))
    
    cursor = connections[DB_READ_NAME].cursor()
    sql = "select id,name From widget_district where parent_id=%d order by id" % city_id
    #print sql
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()
    data_lists = []
    for row in rows:
        data_lists.append({"id":row[0], "name":row[1]})
    return HttpResponse(SuccessResponse(data_lists))     


@login_manager_required
#@require_POST
def get_unit_list(request):
    district_id = request.REQUEST.get("id", None)
    
    if request.user.library_id:
        where_clause = "library_id=%d" % request.user.library_id
    else:
        where_clause = "library_id is null"
        
    cursor = connections[DB_READ_NAME].cursor()
    if district_id and district_id<>"0":
        sql = "select id,name From widget_story_unit where %s and district_id like '%s%%' order by id" % (where_clause, district_id)
    else:
        sql = "select id,name From widget_story_unit where %s order by id" % where_clause
    print sql
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()
    data_lists = []
    for row in rows:
        data_lists.append({"id":row[0], "name":row[1]})
    return HttpResponse(SuccessResponse(data_lists))       

@login_manager_required
#@require_POST
def story_unit_list(request):

    page_index = int(request.POST.get('page_index', 1))
    page_size = int(request.POST.get('page_size', 15))
    search_text = request.POST.get('search_text',"")

    if request.user.library_id:
        where_clause = "u.library_id=%d" % request.user.library_id
    else:
        where_clause = "u.library_id is null"
        if search_text != "":
            where_clause = "u.library_id is null and u.name = '%s'" % search_text



        
    cursor = connections[DB_READ_NAME].cursor()
    sql = "select count(*) from widget_story_unit u where %s" % where_clause
    print sql
    cursor.execute(sql)
    row = cursor.fetchone()
    count = 0
    if row: count = row[0]
    page_count = int(ceil(count/float(page_size)))
    
    sql = "select u.id,u.name unit_name,d.name district_name,brief,contact,telephone,email,u.story_count,update_time,district_id from widget_story_unit u LEFT JOIN widget_district d on d.id=u.district_id where %s order by update_time DESC LIMIT %s, %s" % (where_clause, (page_index-1)*page_size, page_size)
    cursor.execute(sql)
    rows = cursor.fetchall()
    
    data_lists = []
    for row in rows:
        data_dict = {}
        data_dict["id"] = row[0]
        data_dict["unit_name"] = row[1]
        data_dict["district_name"] = row[2]
        data_dict["brief"] = row[3]
        data_dict["contact"] = row[4]
        data_dict["telephone"] = row[5]
        data_dict["email"] = row[6]
        data_dict["story_count"] = row[7]
        data_dict["update_time"] = row[8].strftime("%Y-%m-%d %H:%M:%S")
        data_dict["district_id"] = row[9]
        data_lists.append(data_dict)
    cursor.close()
    return HttpResponse(json.dumps({"data":data_lists, "page_index": page_index, "page_count": page_count}))

@login_manager_required
def story_unit(request):
    """
        报送单位管理
    """
    if request.method == "GET":
        return render(request, "manager/story_unit.html", {"index":7, "sub_index":1})
    elif request.method == "POST":
        try:
            unit_id = int(request.REQUEST['unit_id'])
            district_id = int(request.REQUEST['id'])
            name = request.REQUEST["name"]
            contact = request.REQUEST["contact"]
            telephone = request.REQUEST["telephone"]
            email = request.REQUEST["email"]
            brief = request.REQUEST["brief"]
        except:
            traceback.print_exc()
            return HttpResponse(FailResponse(u"参数错误"))
        
        if unit_id:
            action_name = u"修改"
            try: widget_story_unit = WidgetStoryUnit.objects.get(id=unit_id)
            except: return HttpResponse(FailResponse(u"错误的单位ＩＤ，不能修改"))
        else:
            action_name = u"新增"
            widget_story_unit = WidgetStoryUnit()
        widget_story_unit.library = request.user.library
        widget_story_unit.district_id = district_id
        widget_story_unit.name = name
        widget_story_unit.contact = contact
        widget_story_unit.telephone = telephone
        widget_story_unit.email = email
        widget_story_unit.brief = brief
        widget_story_unit.save()
        
        #WidgetStoryOpus.objects.filter(unit_id=widget_story_unit.id)
        sql = "update widget_story_opus set district_id=%d where unit_id=%d" % (widget_story_unit.district_id, widget_story_unit.id)
        print sql
        cursor = connection.cursor()
        cursor.execute(sql)
        
        #记录日志
        add_manager_action_log(request, u'%s%s“故事达人”的报送单位(%s)的详细资料' % (request.user, action_name, widget_story_unit.name))
        return HttpResponse(SuccessResponse(u"报送单们资料更新完毕."))

@login_manager_required
def delete_unit(request):
    try: unit_id = int(request.REQUEST["id"])
    except: return HttpResponse(FailResponse(u"参数错误"))
    
    try: widget_story_unit = WidgetStoryUnit.objects.get(id=unit_id)
    except: return HttpResponse(FailResponse(u"错误的单位ＩＤ"))
    
    if request.user.library <> widget_story_unit.library:
        return HttpResponse(FailResponse(u"没有权限，只能本馆管理员才能删除"))
    
    widget_story_unit.delete()
    
    #记录日志
    add_manager_action_log(request, u'%s删除了“故事达人”的报送单位(%s)' % (request.user, widget_story_unit.name))
    return HttpResponse(SuccessResponse(u"删除成功"))
    
@login_manager_required
def story_opus(request):
    """
        添加选手作品
    """
    if request.method == "GET":
        story_opus_id = request.REQUEST.get('id', None)
        story_opus = None
        if story_opus_id:
            try: story_opus = WidgetStoryOpus.objects.get(id=story_opus_id)
            except: pass
        return render(request, "manager/story_opus.html", {"index":7, "sub_index":2, "story_opus":story_opus})
    elif request.method == "POST":
        try:
            unit_id = int(request.REQUEST["sel_unit"])    #报送单位ID
            story_name = request.REQUEST["story_name"].strip()
            story_brief = request.REQUEST["story_brief"].strip()
            actor_name = request.REQUEST["actor_name"].strip()
            actor_brief = request.REQUEST["actor_brief"].strip()
            group_id = int(request.REQUEST["rdo_group"])
            sex = int(request.REQUEST["rdo_sex"])
            age = request.REQUEST["age"]
            school_name = request.REQUEST["school_name"].strip()
            telephone = request.REQUEST["telephone"].strip()
            email = request.REQUEST["email"].strip()
            
            story_file = request.FILES.get("story_file", None)
            
            hid_story_id = request.REQUEST["hid_story_id"]
            #print group_id, sex
        except:
            #traceback.print_exc()
            return HttpResponse(u"参数错误")

        try: widget_story_unit = WidgetStoryUnit.objects.get(id=unit_id)
        except: return HttpResponse(u"必须选择报送单位")
        if not hid_story_id and not story_file:
            return HttpResponse(u'必须上传视频文件')
        
        is_change_district = False #改变作品的区域
        action_name = u"新上传"
        if hid_story_id:
            action_name = u"修改"
            try:
                widget_story_opus = WidgetStoryOpus.objects.get(id=hid_story_id)
                
                if widget_story_opus.unit_id <> widget_story_unit.id:
                    is_change_district = True
                    story_unit = WidgetStoryUnit.objects.get(id=widget_story_opus.unit_id)
                    #更新所在区域，上报单位拥有作品数量
                    update_story_count(story_unit, -1)
                
                widget_story_opus.district_id = widget_story_unit.district_id
                widget_story_opus.unit_id = unit_id
                widget_story_opus.group_id = group_id
                widget_story_opus.story_name = story_name
                widget_story_opus.story_brief = story_brief
                widget_story_opus.actor_name = actor_name
                widget_story_opus.actor_brief = actor_brief
                widget_story_opus.sex = sex
                widget_story_opus.age = age
                widget_story_opus.school_name = school_name
                widget_story_opus.telephone = telephone
                widget_story_opus.email = email
                widget_story_opus.update_time = datetime.now()
                widget_story_opus.save()
                
                auth_asset = widget_story_opus.auth_asset
                if story_file:
                    ext = os.path.splitext(story_file.name)[1]
                    if ext.lower() not in ALLOWED_VIDEO_EXTENSION:
                        return HttpResponse(u"只充许上传视频文件(%s)" % ';'.join(ALLOWED_VIDEO_EXTENSION))
                    if story_file.size > ALLOWED_VIDEO_UPLOAD_SIZE:
                        return HttpResponse(u'文件超过最大充许大小')
                    
                    #注意，视频上传到管理员的目录里，　不是注册用户的目录里
                    asset_res_path = "%s/%d" % (get_user_path(request.user, auth_asset.res_type), auth_asset.id)
                    if not os.path.exists(os.path.join(MEDIA_ROOT, asset_res_path)):
                        os.makedirs(os.path.join(MEDIA_ROOT, asset_res_path))
                    auth_asset.origin_path = '%s/origin%s' % (asset_res_path, ext)
                    auth_asset.res_path = '%s/%d.flv' % (asset_res_path, auth_asset.id)
                    auth_asset.img_large_path = '%s/l.jpg' % asset_res_path #存视频截图的原图
                    auth_asset.img_small_path = '%s/s.jpg' % asset_res_path
                    f = open(os.path.join(MEDIA_ROOT, auth_asset.origin_path), "wb")    #待转码状态
                    for chunk in story_file.chunks():
                        f.write(chunk)
                    f.close()
                    auth_asset.codec_status = 0 #更新视频了，需要重新转码
                    auth_asset.status = 1
                    auth_asset.save()
                
                auth_user = widget_story_opus.user
                auth_user.set_password(telephone.strip().lower())   #修改密码
                auth_user.save()
                
                auth_opus_page = AuthOpusPage.objects.get(auth_opus_id=widget_story_opus.opus_id, page_index=1)
                
                #更新作品背景
                update_story_opus(auth_user, auth_asset, widget_story_opus, auth_opus_page, widget_story_unit)
            except:
                traceback.print_exc()
                return HttpResponse(u"故事ID不存在")
        else:
            auth_asset = AuthAsset()
            auth_asset.library = request.user.library
            auth_asset.user = request.user
            auth_asset.res_title = story_name
            auth_asset.res_type = 11    #故事大王专题
            auth_asset.status = -1  #未上传成功前，先状态为-1
            auth_asset.ref_times = 1
            auth_asset.share_times = 1
            auth_asset.save()   #得到ID
            if story_file:
                filename, ext = os.path.splitext(story_file.name)
                if ext.lower() not in ALLOWED_VIDEO_EXTENSION:
                    return HttpResponse(u"只充许上传视频文件(%s)" % ';'.join(ALLOWED_VIDEO_EXTENSION))
                if story_file.size > ALLOWED_VIDEO_UPLOAD_SIZE:
                    return HttpResponse(u'文件超过最大充许大小')
                
                #注意，视频上传到管理员的目录里，　不是注册用户的目录里
                asset_res_path = "%s/%d" % (get_user_path(request.user, auth_asset.res_type), auth_asset.id)
                if not os.path.exists(os.path.join(MEDIA_ROOT, asset_res_path)):
                    os.makedirs(os.path.join(MEDIA_ROOT, asset_res_path))
                auth_asset.origin_path = '%s/origin%s' % (asset_res_path, ext)
                auth_asset.res_path = '%s/%d.flv' % (asset_res_path, auth_asset.id)
                auth_asset.img_large_path = '%s/l.jpg' % asset_res_path #存视频截图的原图
                auth_asset.img_small_path = '%s/s.jpg' % asset_res_path
                f = open(os.path.join(MEDIA_ROOT, auth_asset.origin_path), "wb")    #待转码状态
                for chunk in story_file.chunks():
                    f.write(chunk)
                f.close()
                auth_asset.status = 1
                auth_asset.save()
            
            widget_story_opus = WidgetStoryOpus()
            widget_story_opus.library = request.user.library
            widget_story_opus.auth_asset = auth_asset
            widget_story_opus.district_id = widget_story_unit.district_id
            widget_story_opus.unit_id = unit_id
            widget_story_opus.group_id = group_id
            widget_story_opus.story_name = story_name
            widget_story_opus.story_brief = story_brief
            widget_story_opus.actor_name = actor_name
            widget_story_opus.actor_brief = actor_brief
            widget_story_opus.sex = sex
            widget_story_opus.age = age
            widget_story_opus.school_name = school_name
            widget_story_opus.telephone = telephone
            widget_story_opus.email = email
            widget_story_opus.save()
            
            #自动生成一个会员，账号是telephone，密码是111111
            auth_user = AuthUser()
            auth_user.number = new_number()
            auth_user.username = "gsdw%s" % auth_user.number
            auth_user.set_password(telephone.strip().lower())
            auth_user.library_id = 1    #省少儿图书馆id
            auth_user.nickname = actor_name
            auth_user.realname = actor_name
            auth_user.auth_type = 11    #故事大王会员
            auth_user.sex = sex
            auth_user.telephone = telephone
            auth_user.school = school_name
            auth_user.email = email
            auth_user.reg_ip = get_ip(request)
            auth_user.last_ip = auth_user.reg_ip
            auth_user.save()
            #把资源共享给新建用户
            auth_asset_share = AuthAssetShare()
            auth_asset_share.auth_asset = auth_asset
            auth_asset_share.user = auth_user
            auth_asset_share.save()
            
            #用默认故事大王模板，直接创建作品
            auth_opus = AuthOpus()
            auth_opus.user = auth_user
            auth_opus.library_id = 1    #省少儿图书馆id
            auth_opus.title = widget_story_opus.story_name
            auth_opus.brief = widget_story_opus.story_brief
            auth_opus.show_type = 101   #故事大王大赛的风格
            auth_opus.type_id = 2   #才艺展示
            auth_opus.class_id = 24    #讲故事
            auth_opus.page_count = 1
            auth_opus.width = 1812
            auth_opus.height = 870
            auth_opus.status = 1    #待审核    自动转码成功后，转为已发表状态
            auth_opus.save()
            #创建资源的引用表
            auth_asset_ref = AuthAssetRef()
            auth_asset_ref.auth_asset = auth_asset
            auth_asset_ref.user = auth_user
            auth_asset_ref.auth_opus = auth_opus
            auth_asset_ref.page_index = 1
            auth_asset_ref.res_type = auth_opus.type_id
            auth_asset_ref.save()
            
            opus_res_path = get_user_path(auth_user, "opus", auth_opus.id)
            auth_opus_page = AuthOpusPage()
            auth_opus_page.auth_opus = auth_opus
            auth_opus_page.page_index = 1
            auth_opus_page.is_multimedia = 1
            auth_opus_page.auth_asset_list = int(auth_asset.id)
            #auth_opus_page.json = ""
            auth_opus_page.json_path = "%s/1.json" % opus_res_path
            auth_opus_page.img_path = "%s/1.jpg" % opus_res_path
            auth_opus_page.img_small_path = "%s/1_s.jpg" % opus_res_path
            auth_opus_page.save()
            
            widget_story_opus.user_id = auth_user.id    #自动创建用户ＩＤ
            widget_story_opus.opus_id = auth_opus.id    #自动创建作品ID
            widget_story_opus.save()
            update_story_opus(auth_user, auth_asset, widget_story_opus, auth_opus_page, widget_story_unit)
            
        #更新所在区域，上报单位拥有作品数量
        if hid_story_id and is_change_district:    #旧作品，但更新作品区域的话
            update_story_count(widget_story_unit, 1)
        else: update_story_count(widget_story_unit, 1)  #新作品
        
        #记录日志
        add_manager_action_log(request, u'%s%s了“故事达人”作品【%s】' % (request.user, action_name, widget_story_opus.story_name))
        
        return render(request, "manager/story_opus.html", {"index":7, "sub_index":2, "result":"ok", "username":auth_user.username, "password":auth_user.telephone.strip().lower()})

def update_story_count(widget_story_unit, count):
    widget_story_unit.story_count += count
    widget_story_unit.save()
    
    widget_district = WidgetDistrict.objects.get(id=widget_story_unit.district_id)
    widget_district.story_count += count
    widget_district.save()
    new_district_id = str(widget_district.id)[:-2]
    while len(new_district_id)>=2:
        inherit_district = WidgetDistrict.objects.get(id=new_district_id)
        inherit_district.story_count += count
        inherit_district.save()
        new_district_id = new_district_id[:-2]

def update_story_opus(auth_user, auth_asset, widget_story_opus, auth_opus_page, widget_story_unit):
    json_file = open(os.path.join(MEDIA_ROOT, "gsdw/1.json"), 'r')
    img_file = open(os.path.join(MEDIA_ROOT, "gsdw/1.jpg"), "rb")
    json_data = json_file.read()
    json_file.close()
    
    json_data = json_data.replace("{video_url}", MEDIA_URL + auth_asset.res_path)
    json_data = json_data.replace("{video_id}", str(auth_asset.id))
    json_data = json_data.replace("{story_name}", widget_story_opus.story_name)
    json_data = json_data.replace("{actor_name}", widget_story_opus.actor_name)
    json_data = json_data.replace("{sex}", u"男" if widget_story_opus.sex==1 else u"女")
    json_data = json_data.replace("{age}", str(widget_story_opus.age))
    json_data = json_data.replace("{school_name}", widget_story_opus.school_name)
    json_data = json_data.replace("{unit_name}", widget_story_unit.name)
    json_data = json_data.replace("{number}", auth_user.number)
    #print json_data
    asset_res_path = get_user_path(auth_user, "opus", widget_story_opus.opus_id)
    if not os.path.exists(os.path.join(MEDIA_ROOT, asset_res_path)):
        os.makedirs(os.path.join(MEDIA_ROOT, asset_res_path))
    
    json_data = json_data.encode('utf-8')
    auth_opus_page.json = json_data
    auth_opus_page.save()
    open(os.path.join(MEDIA_ROOT, auth_opus_page.json_path), "w").write(json_data)
    
    img_data = img_file.read()
    img_file.close()
    img = Image.open(StringIO(img_data))
    from WebZone.conf import fonts
    from WebZone.settings import FONT_ROOT
    font_file = fonts[1]["font"]
    font_file = os.path.join(FONT_ROOT, font_file)
    #print font_file 
    dr = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_file, 32)
    dr.text((1389,174), widget_story_opus.story_name, fill="#000000", font=font)
    dr.text((1392,227), widget_story_opus.actor_name, fill="#000000", font=font)
    dr.text((1390,285), u"男" if widget_story_opus.sex==1 else u"女", fill="#000000", font=font)
    dr.text((1392,344), str(widget_story_opus.age), fill="#000000", font=font)
    dr.text((1394,399), widget_story_opus.school_name, fill="#000000", font=font)
    dr.text((1466,458), auth_user.number, fill="#000000", font=font)
    
    if len(widget_story_unit.name) > 9:
        dr.text((1466,519), widget_story_unit.name[:9], fill="#000000", font=font)
        dr.text((1466,580), widget_story_unit.name[9:], fill="#000000", font=font)
    else:
        dr.text((1466,519), widget_story_unit.name, fill="#000000", font=font)
    img.save(os.path.join(MEDIA_ROOT, auth_opus_page.img_path))

    
@login_manager_required
def story_list(request):
    """
        选手作品列表
    """
    if request.method == "GET":
        return render(request, "manager/story_list.html", {"index":7, "sub_index":3})
    elif request.method == "POST":
        try:
            unit_id = int(request.REQUEST.get('sel_unit', 0))   #上报单位ID
            search_text = request.REQUEST.get('search_text', None)  #故事标题
            page_index = int(request.POST.get('page_index', 1))
            page_size = int(request.POST.get('page_size', 15))
        except:
            traceback.print_exc()
            return HttpResponse(FailResponse(u"参数错误"))
        
        if request.user.library_id:
            where_clause = "o.library_id=%d" % request.user.library_id
        else:
            where_clause = "o.library_id is null"
        if unit_id:
            if WidgetStoryUnit.objects.filter(id=unit_id).count() == 1:
                where_clause += " and unit_id=%d" % unit_id
            else: return HttpResponse(FailResponse(u"报送单位不存在"))
        if search_text:
            where_clause += " and story_name like '%%%s%%'" % search_text if where_clause else "story_name like '%%%s%%'" % search_text
            
        cursor = connections[DB_READ_NAME].cursor()
        sql = "select count(*) from widget_story_opus o where %s" % where_clause
        print sql
        cursor.execute(sql)
        row = cursor.fetchone()
        count = 0
        if row: count = row[0]
        page_count = int(ceil(count/float(page_size)))
        
        sql = "select o.id,u.name,story_name,actor_name,o.sex,age,school_name,o.telephone,vote,o.create_time,a.res_path,a.img_large_path,a.img_small_path,a.codec_status,username,number"
        sql += " from widget_story_opus o LEFT JOIN widget_story_unit u on o.unit_id=u.id LEFT JOIN auth_asset a on a.id=o.auth_asset_id LEFT JOIN auth_user on auth_user.id=o.user_id"
        sql += " where a.status=1"
        if where_clause: sql += " and %s order by create_time desc LIMIT %s, %s" % (where_clause, (page_index-1)*page_size, page_size)
        else: sql += " order by create_time desc LIMIT %s, %s" % ((page_index-1)*page_size, page_size)
        print sql
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        data_lists = []
        for row in rows:
            data_dict = {}
            data_dict["id"] = row[0]
            data_dict["unit_name"] = row[1]
            data_dict["story_name"] = row[2]
            data_dict["actor_name"] = row[3]
            data_dict["sex"] = row[4]
            data_dict["age"] = row[5]
            data_dict["school_name"] = row[6]
            data_dict["telephone"] = row[7]
            data_dict["vote"] = row[8]
            data_dict["create_time"] = row[9].strftime("%Y-%m-%d %H:%M:%S")
            data_dict["res_path"] = MEDIA_URL + row[10]
            data_dict["img_large_path"] = MEDIA_URL + row[11]
            data_dict["img_small_path"] = MEDIA_URL + row[12]
            data_dict["codec_status"] = codec_name(row[13])
            data_dict["res_path"] = row[10]
            data_dict["username"] = row[14]
            data_dict["number"] = row[15]
            data_lists.append(data_dict)
        cursor.close()
        return HttpResponse(json.dumps({"data":data_lists, "page_index": page_index, "page_count": page_count}))

def codec_name(codec_status):
    if codec_status == 0:
        return u"正在转码"
    elif codec_status == 1:
        return u"成功"
    elif codec_status == -1:
        return u"失败"

@login_manager_required
@require_POST
def delete_story(request):
    try: story_opus_id = request.REQUEST['id']
    except: return HttpResponse(u"参数错误")
    
    try:
        widget_story_opus = WidgetStoryOpus.objects.get(id=story_opus_id)
        widget_story_unit = WidgetStoryUnit.objects.get(id=widget_story_opus.unit_id)
        widget_district = WidgetDistrict.objects.get(id=widget_story_unit.district_id)
    except: return HttpResponse(u"不存在的故事ＩＤ")
    
    log_content = u"%s删除了“故事达人”的作品：【%s】" % (request.user, widget_story_opus.story_name)
    
    auth_asset = widget_story_opus.auth_asset
    auth_user = widget_story_opus.user
    
    AuthAssetShare.objects.filter(auth_asset_id=auth_asset.id).delete()
    AuthAssetRef.objects.filter(auth_asset_id=auth_asset.id).delete()
    AuthOpusPage.objects.filter(auth_opus_id=widget_story_opus.opus_id).delete()
    auth_opus = AuthOpus.objects.filter(id=widget_story_opus.opus_id)
#     if auth_asset.ref_times > 0:
#         return HttpResponse(u'资源有(%s)个相关引用，不能删除' % auth_asset.ref_times)
#     if auth_asset.share_times > 0:
#         return HttpResponse(u'资源有(%s)个相关共享，不能删除' % auth_asset.ref_times)
    
    auth_asset_dir = '%s/%d' % (get_user_path(auth_asset.user, auth_asset.res_type), auth_asset.id)
    auth_asset_absdir = os.path.join(MEDIA_ROOT, auth_asset_dir)
    print "auth_asset_absdir", auth_asset_absdir
    __import__('shutil').rmtree(auth_asset_absdir)
    
#     opus_path = get_user_path(auth_opus.user, "opus", auth_opus.id)
#     opus_abspath = os.path.join(MEDIA_ROOT, opus_path)
#     print "opus_abspath", opus_abspath
#     __import__('shutil').rmtree(opus_abspath)
    #用户全删除，需要删除整个用户的目录，不仅仅是作品
    user_path = 'user/%d/%s/%d' % (auth_user.library.id, auth_user.date_joined.strftime("%Y"), auth_user.id)
    user_abspath = os.path.join(MEDIA_ROOT, user_path)
    print "user_abspath", user_abspath
    __import__('shutil').rmtree(user_abspath)
    
    auth_user.delete()
    auth_opus.delete()
    
    widget_story_opus.delete()
    auth_asset.delete()
    widget_story_unit.story_count -= 1
    widget_story_unit.save()
    widget_district.story_count -= 1
    widget_district.save()
    
    #记录日志
    add_manager_action_log(request, log_content)
    return HttpResponse('ok')

    
    
    
    
    
    
    
    
    
    
    
    
    
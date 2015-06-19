# coding=utf-8
import os
import json
from math import ceil
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Max

import traceback

from django.db import connection, connections
from datetime import datetime

from WebZone.settings import MEDIA_ROOT, MEDIA_URL
from WebZone.conf import ALLOWED_IMG_EXTENSION,ALLOWED_IMG_UPLOAD_SIZE
from WebZone.conf import ALLOWED_SOUND_EXTENSION,ALLOWED_SOUND_UPLOAD_SIZE
from WebZone.conf import ALLOWED_VIDEO_EXTENSION,ALLOWED_VIDEO_UPLOAD_SIZE
from diy.models import ZoneAsset, ZoneAssetTemplate
from diy.models import AuthOpus, AuthOpusPage
from account.models import AuthUser
from account.models import AuthMessage
from library.models import Library
from utils import get_tile_image_name
from utils import get_new_filename
from utils import get_library, get_zone_asset
from utils import get_ip, get_lib_path
from utils.enum import zone_res_type_name, zone_res_style_name
# Create your views here.

from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from utils.decorator import REDIRECT_FIELD_NAME

from utils.decorator import manager_required
from utils import fmt_str as F

#from django.views.decorators.http import require_http_methods
from django.views.decorators.http import require_POST
from gateway import FailResponse, SuccessResponse
#from utils.enum import opus_type_name, opus_class_name, opus_status_name
from utils.enum import opus_status_name

from widget.models import WidgetOpusClassify, WidgetOpusSize
from widget.models import WidgetPageSize
from widget.models import WidgetGas

from WebZone.conf import OPUS_SIZE
from utils import get_small_size
from manager import add_manager_action_log


from WebZone.settings import DB_READ_NAME

def get_asset_path(request, res_type=1):
    return get_lib_path(request.user.library, res_type)


def login(request, redirect_field_name=REDIRECT_FIELD_NAME):
    redirect_to = request.REQUEST.get(redirect_field_name, '/manager2/')

    if request.method == "GET":
        if request.session.get('manager_login', False) and request.user.is_active and request.user.auth_type in (1, 2):
            return HttpResponseRedirect(redirect_to)
        return render(request, "manager/login.html")
    elif request.method == "POST":
        try:
            username = request.REQUEST["username"].strip().lower()
            password = request.REQUEST["password"].strip()
            print username, password
        except:
            return render(request, "manager/login.html", {"error":u"参数错误"})

        try:
            login_user = authenticate(username=username, password=password)
            print '%s lgoin .success' % username
        except Exception,e :
            print e
            return render(request, "manager/login.html", {"error":u"用户名或密码错误，请检查后重新输入"})

        if login_user is None:
            return render(request, "manager/login.html", {"error":u"用户名或密码错误，请检查后重新输入"})

        if not login_user.is_active:
            return render(request, "manager/login.html", {"error":u"你的账号(%s)已被封，解封请联系管理员" % username})
        '''
        if login_user.library:
            if login_user.library.host <> request.get_host().lower():
                return HttpResponse(u"<h1>非法的登录请求!</h1><br>请通过自己所属的登录网页:<a href='http://%s/manager/login/'>http://%s/manager/login/</a>进行登录!" % (login_user.library.host, login_user.library.host))
        else:
            if request.get_host().lower() not in  ("yh.3qdou.com", "10.0.0.177:8000","127.0.0.1:8000","localhost:8000"):
                return HttpResponse(u"<h1>非法的登录请求!</h1><br>请通过自己所属的登录网页:<a href='http://yh.3qdou.com/manager/login/'>http://yh.3qdou.com/manager/login/</a>进行登录!")

        request.session['last_ip'] = login_user.last_ip
        request.session['last_login'] = login_user.last_login.strftime("%Y-%m-%d %H:%M:%S") if login_user.last_login else ""
        if  login_user.library and login_user.library.expire_time:
            if login_user.library.expire_time <= datetime.now():
                return render(request, "manager/login.html", {"error":u"您的机构已到期，请联系管理人员"})
        '''
        #退出当前账号
        auth_logout(request)
        auth_login(request, login_user)
        # print "last_ip", login_user.last_ip, login_user.last_login

        request.session['last_ip'] = login_user.last_ip
        request.session['last_login'] = login_user.last_login.strftime("%Y-%m-%d %H:%M:%S") if login_user.last_login else ""

        auth_type_dict = dict()
        auth_type_dict[0] = u'普通会员'
        auth_type_dict[1] = u'图书馆长'
        auth_type_dict[2] = u'图书馆审核员'
        auth_type_dict[5] = u'游客会员'
        auth_type_dict[8] = u'二级管理员'
        auth_type_dict[9] = u'超级管理员'
        auth_type_dict[11] = u'故事大王会员'
        request.session['level'] = auth_type_dict[login_user.auth_type]
        # 原版本设计。此处非必要且在非缓存存储session的情况下会引起异常故注释 editor: kamihati 2015/4/16
        # request.session['library'] = request.user.library
        
        login_user.last_ip = get_ip(request)
        login_user.login_times += 1
        login_user.save()

        request.session['manager_login'] = True
        from manager import update_group_perms, update_top_perms
        update_group_perms(request)
        update_top_perms(request)
        #记录日志
        log_content = u'%s登陆管理信息系统' % login_user
        # print log_content
        add_manager_action_log(request, log_content)
        # 导入获取用户权限列表的方法
        from account.handler import get_user_permission
        request.session['permission'] = get_user_permission(request.user.id)
        print '%s permission is.......' % username
        print request.session['permission']
        return HttpResponseRedirect(redirect_to)


def logout(request, redirect_field_name=REDIRECT_FIELD_NAME):
    redirect_to = request.REQUEST.get(redirect_field_name, '/manager/login/')
    auth_logout(request)
    from manager import update_group_perms, update_top_perms
    update_group_perms(request, True)
    update_top_perms(request, True)
    request.session['manager_login'] = False
    return HttpResponseRedirect(redirect_to)


def change_self_pass(request):
    if hasattr(request, "session") and request.session.get('manager_login', False) and request.user.is_active and request.user.is_staff:
        try:
            oldpass = request.REQUEST["oldpass"].strip()
            password = request.REQUEST["password"].strip()
        except: return HttpResponse(u"参数错误")
        
        if not request.user.check_password(oldpass):
            return HttpResponse(u"旧密码不正确")
        
        from utils.reg_check import is_password_valid
        if not is_password_valid(password):
            return HttpResponse(u"密码不合规")
            
        request.user.set_password(password)
        request.user.save()
        
        #记录日志
        add_manager_action_log(request, u'%s修改了自己的登录密码' % request.user)
        return HttpResponse("ok")
    else:
        return HttpResponse(u"没有权限，请先登录")

def view_self_log(request):
    '''查看自己的管理员日志'''
    if not (hasattr(request, "session") and request.session.get('manager_login', False) and request.user.is_active and request.user.is_staff):
        return HttpResponseRedirect("/manager/login/")

    try:
        page_index = int(request.REQUEST.get("page_index", 1))
        page_size = int(request.REQUEST.get("page_size", 15))
        #action_name = request.REQUEST.get("username", request.user.username)
    except:
        return HttpResponse(u"参数错误")
    
    cursor = connections[DB_READ_NAME].cursor()
    sql = "select count(*) from manager_action_log where user_id=%d" % request.user.id
    cursor.execute(sql)
    row = cursor.fetchone()
    count = int(row[0]) if row and row[0] else 0
    page_count = int(ceil(count/float(page_size)))
    
    sql = "select id,username,content,ip,action_time,remark from manager_action_log where user_id=%d order by action_time DESC LIMIT %s, %s" % (request.user.id, (page_index-1)*page_size, page_size)
    #print sql
    cursor.execute(sql)
    rows = cursor.fetchall()
    
    data_lists = []
    for row in rows:
        data_dict = {}
        data_dict["id"] = row[0]
        data_dict["username"] = row[1]
        data_dict["content"] = row[2]
        data_dict["ip"] = row[3]
        data_dict["action_time"] = row[4].strftime("%Y-%m-%d %H:%M:%S")
        data_lists.append(data_dict)
    cursor.close()
    return HttpResponse(json.dumps({"data":data_lists, "page_index": page_index, "page_count": page_count}))

def get_role_list(request):
    '''
        只返回自己权限的子集的角色的列表
    '''
    if not (hasattr(request, "session") and request.session.get('manager_login', False) and request.user.is_active and request.user.is_staff):
        return HttpResponseRedirect(u"请先登录")
    
    from manager.models import ManagerAuthGroup
    
    role_list = []
    for item in ManagerAuthGroup.objects.all():
        role_item = {"id":item.id, "name":item.name, "perms":item.perms, "remark":item.remark}
        role_list.append(role_item)
    return HttpResponse(json.dumps(role_list))

@manager_required
def index(request):
    return render(request, "manager/index.html")


@manager_required
def library(request):
    lib_id = request.REQUEST.get('id', 0)
    library = get_library(lib_id)[2]
    if request.method == "GET":
        now = datetime.now()
        return render(request, "manager/library.html", {"index":1, "sub_index":1, "library":library, "lib_id":lib_id,'date_now':'%d-%d-%d'%(now.year+1,now.month,now.day)})
    elif request.method == "POST":
        lib_name = request.POST["lib_name"].lower().strip()
        lib_address = request.POST["lib_address"].lower().strip()
        brief =  request.POST["brief"].lower().strip()
        is_global = host = int(request.POST["rdo_global"])
        expire_time = None
        if not lib_name:
            return HttpResponse(u'图书馆名不能为空')
        if not lib_address:
            return HttpResponse(u'地址不能为空')
        if not brief:
            return HttpResponse(u'简介不能为空')


        if not library:
            username = request.POST["username"].lower().strip()
            nickname = request.POST["nickname"].strip()
            realname = request.POST["realname"].strip()
            telephone = request.POST["telephone"].strip()
            password = request.POST["password"]
            expire_time = request.POST['expire_time']
            #domain = request.POST["domain"].lower().strip()
            host = request.POST["host"].lower().strip()
            try :
                expire_time =  datetime.strptime(expire_time, "%Y-%m-%d")
            except ValueError:
                return  HttpResponse(u'日期不合规')



            print "is_global", is_global
            from utils.lib_check import is_host_valid, is_host_exist
            from utils.lib_check import is_lib_name_valid, is_lib_name_exist
            
            from utils.reg_check import is_username_valid, is_username_exist
            from utils.reg_check import is_nickname_valid, is_nickname_exist
            from utils.reg_check import is_password_valid

            if not username:
                return HttpResponse(u'用户名不能为空')

            if not nickname:
                return HttpResponse(u'昵称不能为空')

            if not telephone:
                return HttpResponse(u"电话号码不能为空")
            # import re
            #
            # if not re.match('\d{3}-\d{8}|\d{4}-\d{7}',telephone):
            #     return HttpResponse(u"请输出正确的电话号码")


            if not is_username_valid(username):
                return HttpResponse(u"用户名(%s)不合规" % username)
            if is_username_exist(username):
                return HttpResponse(u"用户名(%s)已存在" % username)
            
            if not is_nickname_valid(nickname):
                return HttpResponse(u"昵称(%s)不合规" % nickname)
            if is_nickname_exist(username):
                return HttpResponse(u"昵称(%s)已存在" % nickname)

            
            if not is_password_valid(password):
                return HttpResponse(u"密码不合规")



            if not lib_address:
                return HttpResponse(u'地址不能为空')
            if not brief:
                return HttpResponse(u'简介不能为空')

            #if not is_domain_valid(domain) or is_domain_exist(domain):
            #    return HttpResponse(u"二级域名(%s)不合规" % domain)
            if not is_host_valid(host) or is_host_exist(host):
                return HttpResponse(u"自定义域名(%s)不合规" % host)
            if not is_lib_name_valid(lib_name) or is_lib_name_exist(lib_name):
                return HttpResponse(u"图书馆名(%s)不合规" % lib_name)
            
            #新建管理员账号，直接赋值其角色为　“机构管理员”:id=4
            auth_user = AuthUser()
            auth_user.username = username
            auth_user.nickname = nickname
            auth_user.realname = realname
            auth_user.telephone = telephone
            
            auth_user.set_password(password)
            auth_user.reg_ip = get_ip(request)
            auth_user.last_ip = auth_user.reg_ip
            auth_user.last_login = datetime.now()
            
            auth_user.auth_type = 1  #图书馆长
            auth_user.is_staff = 1  #管理员
            auth_user.save()
            #用户加入角色组
            from manager.models import ManagerUserGroup
            manager_user_group = ManagerUserGroup()
            manager_user_group.user = auth_user
            manager_user_group.group_id = 4 #机构管理员
            manager_user_group.save()
            
            library = Library()
            library.user = auth_user
            library.host = host
            library.save()
            
            auth_user.library = library
            auth_user.save()

        library.lib_name = lib_name
        library.lib_address = lib_address
        library.brief = brief
        if expire_time:
            library.expire_time =expire_time
        library.is_global = is_global
        
        hid_logo_path = request.POST["hid_logo_path"]
        hid_swf_path = request.POST["hid_swf_path"]
        if hid_logo_path.find("temp") >= 0:
            ext = os.path.splitext(hid_logo_path)[1]
            
            logo_path = "lib/%d/logo%s" % (library.id, ext)
            logo_abspath =  os.path.join(MEDIA_ROOT, logo_path)
            
            if not os.path.exists(os.path.split(logo_abspath)[0]):
                os.makedirs(os.path.split(logo_abspath)[0])
            open(logo_abspath, "wb").write(open(os.path.join(MEDIA_ROOT, hid_logo_path), "rb").read())
            os.remove(os.path.join(MEDIA_ROOT, hid_logo_path))
            library.logo_path = logo_path
        if hid_swf_path.find("temp") >= 0:
            ext = os.path.splitext(hid_swf_path)[1]
            
            swf_path = "lib/%d/swf%s" % (library.id, ext)
            swf_abspath =  os.path.join(MEDIA_ROOT, swf_path)
            print swf_path, swf_abspath
            
            if not os.path.exists(os.path.split(swf_abspath)[0]):
                os.makedirs(os.path.split(swf_abspath)[0])
            open(swf_abspath, "wb").write(open(os.path.join(MEDIA_ROOT, hid_swf_path), "rb").read())
            os.remove(os.path.join(MEDIA_ROOT, hid_swf_path))
            library.swf_path = swf_path
        library.save()
        
        #记录日志
        add_manager_action_log(request, u'%s新建/更新了机构/图书馆[%s]的基本信息' % (request.user, library.lib_name))
        return render(request, "manager/library.html", {"index":1, "sub_index":1, "result":"ok"})


@manager_required
#@require_POST
def get_library_list(request):
    cursor = connections[DB_READ_NAME].cursor()
    sql = "select id,lib_name From library where status=1 order by create_time DESC"
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()
    data_lists = []
    for row in rows:
        data_lists.append({"id":row[0], "name":row[1]})
    #data_lists.append({"id":0, "name":u"公共图书馆"})
    return HttpResponse(SuccessResponse(data_lists))    


@manager_required
def library_list(request):
    if request.method == "GET":
        return render(request, "manager/library_list.html", {"index":1, "sub_index":2})
    elif request.method == "POST":
        page_index = int(request.POST.get('page_index', 1))
        page_size = int(request.POST.get('page_size', 15))
        search_text = request.POST.get("search_text", "")
        
        cursor = connections[DB_READ_NAME].cursor()
        where_clause = "status=1"
        if search_text: where_clause += " and lib_name like '%%%s%%'" % search_text
        #print where_clause
        sql = "select count(*) from library where %s" % where_clause
        cursor.execute(sql)
        row = cursor.fetchone()
        count = 0
        if row: count = row[0]
        page_count = int(ceil(count/float(page_size)))
        
        sql = "select library.id,user_id,username,domain,lib_name,host,logo_path,create_time,is_global,swf_path,expire_time From library LEFT JOIN auth_user on auth_user.id=library.user_id where %s order by create_time DESC LIMIT %s, %s" % (where_clause, (page_index-1)*page_size, page_size)
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        data_lists = []
        for row in rows:
            id = row[0]
            user_id = row[1]
            username = row[2]
            domain = row[3]
            lib_name = row[4]
            host = row[5]

            logo_path = row[6]
            if not logo_path:
                logo_path = ""
            create_time = row[7]
            expire_time = row[10]
            is_global = u"是" if row[8] else u"否"
            swf_path = row[9]
            data_dict = {"id":id,"user_id":user_id,"username":username,"domain":domain,"lib_name":lib_name,"host":host,"is_global":is_global}
            if  logo_path:
                data_dict["logo_path"] = request.build_absolute_uri(MEDIA_URL + logo_path)
            else:
                data_dict["logo_path"] = ""


            data_dict["create_time"] = create_time.strftime("%Y-%m-%d %H:%M:%S")
            data_dict['expire_time'] = expire_time.strftime("%Y-%m-%d") if expire_time else ""
            data_dict["swf_path"] = swf_path

            data_lists.append(data_dict)
        cursor.close()
        return HttpResponse(json.dumps({"data":data_lists, "page_index": page_index, "page_count": page_count}))

@manager_required
def get_opus_type_list(request):
    parent_id = request.REQUEST.get("id", "0")
    sql = "select id,classify_name from widget_opus_classify where parent_id=%s" % parent_id
    cur = connections[DB_READ_NAME].cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    data_lists = []
    for row in rows:
        data_lists.append({"id":row[0], "name":row[1]})
    return HttpResponse(SuccessResponse(data_lists))    
    
@manager_required
def opus_type_list(request):
    page_index = int(request.POST.get('page_index', 1))
    page_size = int(request.POST.get('page_size', 15))
    search_text = request.POST.get('search_text',"")
    if search_text != "":
        where_clause = "where c1.classify_name = '%s'" % search_text

    else:
        where_clause = ""
    cursor = connections[DB_READ_NAME].cursor()

    sql = "select count(*) from widget_opus_classify c1 %s " % where_clause
    cursor.execute(sql)
    row = cursor.fetchone()
    count = 0
    if row: count = row[0]
    page_count = int(ceil(count/float(page_size)))
    
    sql = "select c1.id,c1.classify_name,c2.classify_name,c1.parent_id,c1.create_type,c1.read_type from widget_opus_classify c1 LEFT JOIN widget_opus_classify c2 on c1.parent_id=c2.id %s LIMIT %s, %s" % (where_clause,(page_index-1)*page_size, page_size)
    cursor.execute(sql)
    rows = cursor.fetchall()
    
    data_lists = []
    for row in rows:
        data_dict = {}
        data_dict["id"] = row[0]
        data_dict["classify_name"] = row[1]
        data_dict["parent_name"] = row[2] if row[2] else ""
        data_dict["parent_id"] = row[3]
        data_dict["create_type_id"] = row[4]
        data_dict["read_type_id"] = row[5]
        data_dict["create_type"] = u"单页" if row[4] == 1 else u"双页"
        data_dict["read_type"] = u"单页" if row[5] == 1 else u"双页"
        data_lists.append(data_dict)
    cursor.close()
    return HttpResponse(json.dumps({"data":data_lists, "page_index": page_index, "page_count": page_count}))

@manager_required
def opus_type(request):
    if request.method == "GET":
        return render(request, "manager/opus_type.html", {"index":1, "sub_index":3})
    elif request.method == "POST":
        try:
            id = int(request.REQUEST['hid_id'])
            parent_id = int(request.REQUEST['parent_id'])
            classify_name = request.REQUEST["classify_name"]
            create_type = int(request.REQUEST['rdo_create'])
            read_type = int(request.REQUEST['rdo_read'])
        except:
            traceback.print_exc()
            return HttpResponse(FailResponse(u"参数错误"))
        
        if parent_id:
            if WidgetOpusClassify.objects.filter(id=parent_id).count() == 0:
                return HttpResponse(FailResponse(u"一级分类错误"))
        if id:
            try: widget_opus_classify = WidgetOpusClassify.objects.get(id=id)
            except: return HttpResponse(FailResponse(u"作品ID不正确"))
        else:
            widget_opus_classify = WidgetOpusClassify()
            if parent_id:
                max_id = WidgetOpusClassify.objects.filter(parent_id=parent_id).aggregate(Max('id')).values()[0]
                print max_id
                widget_opus_classify.id = max_id+1 if max_id else '%d1' % parent_id
                widget_opus_classify.level = WidgetOpusClassify.objects.get(id=parent_id).level + 1
        widget_opus_classify.create_type = create_type
        widget_opus_classify.read_type = read_type
        widget_opus_classify.parent_id = parent_id
        widget_opus_classify.classify_name = classify_name
        widget_opus_classify.save()
        
        #记录日志
        add_manager_action_log(request, u'%s新建/更新了作品分类：[%s]' % (request.user, widget_opus_classify.classify_name))
        return HttpResponse(SuccessResponse("ok"))

@manager_required
def get_opus_size(request):
    return HttpResponse(json.dumps(OPUS_SIZE))
    

@manager_required
def opus_size_list(request):
    page_index = int(request.POST.get('page_index', 1))
    page_size = int(request.POST.get('page_size', 15))
    cursor = connections[DB_READ_NAME].cursor()
    sql = "select count(*) from widget_opus_size"
    cursor.execute(sql)
    row = cursor.fetchone()
    count = 0
    if row: count = row[0]
    page_count = int(ceil(count/float(page_size)))
    
    sql = "select s.id, c.classify_name,screen_width, screen_height, print_width, print_height, origin_width,origin_height, c.id, size_id,s.create_type,s.read_type from widget_opus_size s LEFT JOIN widget_opus_classify c on s.classify_id=c.id LIMIT %s, %s" % ((page_index-1)*page_size, page_size)
    cursor.execute(sql)
    rows = cursor.fetchall()
    
    data_lists = []
    for row in rows:
        data_dict = {}
        data_dict["id"] = row[0]
        data_dict["classify_name"] = row[1]
        data_dict["screen_width"] = row[2]
        data_dict["screen_height"] = row[3]
        data_dict["print_width"] = row[4]
        data_dict["print_height"] = row[5]
        data_dict["origin_width"] = row[6]
        data_dict["origin_height"] = row[7]
        data_dict["classify_id"] = row[8]
        data_dict["size_id"] = row[9]
        data_dict["create_type_id"] = row[10]
        data_dict["read_type_id"] = row[11]
        data_dict["create_type"] = u"单页" if row[10] == 1 else u"双页"
        data_dict["read_type"] = u"单页" if row[11] == 1 else u"双页"
        data_lists.append(data_dict)
    cursor.close()
    return HttpResponse(json.dumps({"data":data_lists, "page_index": page_index, "page_count": page_count}))
    
@manager_required
def opus_size(request):
    if request.method == "GET":
        return render(request, "manager/opus_size.html", {"index":1, "sub_index":4})
    elif request.method == "POST":
        try:
            opus_type_id = request.REQUEST["opus_type_id"]
            size_id = int(request.REQUEST["size_id"])
            hid_id = int(request.REQUEST["hid_id"])
            create_type = int(request.REQUEST['rdo_create'])
            read_type = int(request.REQUEST['rdo_read'])
        except:
            traceback.print_exc()
            return HttpResponse(FailResponse(u"参数错误"))
        
        if WidgetOpusClassify.objects.filter(id=opus_type_id).count() == 0:
            return HttpResponse(FailResponse(u"作品类型不正确"))
        
        size_obj = opus_size_obj(size_id)
        if not size_obj:
            return HttpResponse(FailResponse(u"先选择作品片面类型"))
        
        if hid_id:
            try: widget_opus_size = WidgetOpusSize.objects.get(id=hid_id)
            except: return HttpResponse(FailResponse(u"修改作品版面ID不存在"))
        else:
            widget_opus_size = WidgetOpusSize()
        
        widget_opus_size.create_type = create_type
        widget_opus_size.read_type = read_type
        widget_opus_size.classify_id = opus_type_id
        widget_opus_size.size_id = size_id
        widget_opus_size.screen_width = size_obj[2][0]
        widget_opus_size.screen_height = size_obj[2][1]
        widget_opus_size.print_width = size_obj[3][0]
        widget_opus_size.print_height = size_obj[3][1]
        widget_opus_size.origin_width = size_obj[4][0]
        widget_opus_size.origin_height = size_obj[4][1]
        widget_opus_size.save()
        return HttpResponse(SuccessResponse(u"%s作品版面/画布成功！" % (u"修改" if hid_id else u"新增")))


def opus_page_type_name(type_id):
    if type_id == 1: return u"单页"
    elif type_id == 2: return u"双页"
    elif type_id == 3: return u"单双页"
    else: return u"未知"

@manager_required
def page_size_list(request):
    page_index = int(request.POST.get('page_index', 1))
    page_size = int(request.POST.get('page_size', 15))
    search_text = request.POST.get('search_text',"")
    if search_text != "":
        where_clause = "where name like '%%%s%%'" % search_text
    else :
        where_clause = ""
    cursor = connections[DB_READ_NAME].cursor()
    sql = "select count(*) from widget_page_size %s " % where_clause
    cursor.execute(sql)
    row = cursor.fetchone()
    count = 0
    if row: count = row[0]
    page_count = int(ceil(count/float(page_size)))
    
    sql = "select id,name,screen_width,screen_height,print_width,print_height,origin_width,origin_height,create_type,read_type,res_path,img_small_path From widget_page_size %s LIMIT %s, %s" % (where_clause,(page_index-1)*page_size, page_size)
    cursor.execute(sql)
    rows = cursor.fetchall()
    
    data_lists = []
    for row in rows:
        data_dict = {}
        data_dict["id"] = row[0]
        data_dict["name"] = row[1]
        data_dict["screen_width"] = row[2]
        data_dict["screen_height"] = row[3]
        data_dict["print_width"] = row[4]
        data_dict["print_height"] = row[5]
        data_dict["origin_width"] = row[6]
        data_dict["origin_height"] = row[7]
        data_dict["create_type"] = opus_page_type_name(row[8])
        data_dict["read_type"] = opus_page_type_name(row[9])
        data_dict["create_type_id"] = row[8]
        data_dict["read_type_id"] = row[9]
        data_dict["nickname"] = u"%s*%s：%sx%s（%sx%s）%s" % (data_dict["screen_width"], data_dict["screen_height"], data_dict["print_width"], data_dict["print_height"], data_dict["origin_width"], data_dict["origin_height"], data_dict["create_type"])
        data_dict["res_path"] = row[10] if row[10] else ""
        data_dict["img_small_path"] = MEDIA_URL + row[11] if row[11] else ""
        #data_dict["nickname"] = u"%s*%s：%sx%s（%sx%s）" % (data_dict["screen_width"], data_dict["screen_height"], data_dict["print_width"], data_dict["print_height"], data_dict["origin_width"], data_dict["origin_height"])
        data_lists.append(data_dict)
    cursor.close()
    return HttpResponse(json.dumps({"data":data_lists, "page_index": page_index, "page_count": page_count}))


@manager_required
def page_size(request):
    if request.method == "GET":
        return render(request, "manager/page_size.html", {"index":1, "sub_index":5})
    elif request.method == "POST":
        try:
            hid_id = int(request.REQUEST["hid_id"])
            create_type = int(request.REQUEST['cho_create'])
            read_type = int(request.REQUEST['cho_read'])
            name = request.REQUEST["name"]
            
            screen_width = int(request.REQUEST['screen_w'])
            screen_height = int(request.REQUEST['screen_h'])
            print_width = float(request.REQUEST['print_w'])
            print_height = float(request.REQUEST['print_h'])
            origin_width = int(request.REQUEST['origin_w'])
            origin_height = int(request.REQUEST['origin_h'])
            hid_res_path = request.POST["hid_res_path"]
        except:
            traceback.print_exc()
            return HttpResponse(FailResponse(u"参数错误"))
        
        if len(hid_res_path) == 0:
            return HttpResponse(FailResponse(u"未知错误，请联系管理员"))
    
        if hid_id:
            try: widget_pages_size = WidgetPageSize.objects.get(id=hid_id)
            except: return HttpResponse(FailResponse(u"修改作品页尺寸ID不存在"))
        else:
            widget_pages_size = WidgetPageSize()
            
        ext = os.path.splitext(hid_res_path)[1] #扩展名 
        if ext not in ('.jpg','.jpeg','.png','.gif','.bmp'):
            return HttpResponse(FailResponse(u"上传图片格式不正确:%s" % ext))
        
        widget_pages_size.name = name
        widget_pages_size.create_type = create_type
        widget_pages_size.read_type = read_type
        widget_pages_size.screen_width = screen_width
        widget_pages_size.screen_height = screen_height
        widget_pages_size.print_width = print_width
        widget_pages_size.print_height = print_height
        widget_pages_size.origin_width = origin_width
        widget_pages_size.origin_height = origin_height
        widget_pages_size.save()
        
        if hid_res_path.find("temp") >= 0:  #有新上传文件
            res_type = 21   #作品尺寸图片
            asset_res_path = "%s/%d" % (get_asset_path(request, res_type), widget_pages_size.id)
            if not os.path.exists(os.path.join(MEDIA_ROOT, asset_res_path)):
                os.makedirs(os.path.join(MEDIA_ROOT, asset_res_path))
            widget_pages_size.res_path = "%s/origin%s" % (asset_res_path, ext)
            widget_pages_size.img_small_path = widget_pages_size.res_path.replace("origin", "s")
            open(os.path.join(MEDIA_ROOT, widget_pages_size.res_path), "wb").write(open(os.path.join(MEDIA_ROOT, hid_res_path), "rb").read())
            try: os.remove(os.path.join(MEDIA_ROOT, hid_res_path))
            except: pass

            from PIL import Image
            img = Image.open(os.path.join(MEDIA_ROOT, widget_pages_size.res_path))
            
            #print get_small_size(img.size[0], img.size[1])
            img.thumbnail(get_small_size(img.size[0], img.size[1]), Image.ANTIALIAS)
            img.save(os.path.join(MEDIA_ROOT, widget_pages_size.img_small_path))
            widget_pages_size.save()
        
        #记录日志
        add_manager_action_log(request, u'%s新建/更新了作品页尺寸：[%s(%sx%s)]' % (request.user, widget_pages_size.name, widget_pages_size.print_width, widget_pages_size.print_height))
        return HttpResponse(SuccessResponse(u"%s作品页尺寸成功！" % (u"修改" if hid_id else u"新增")))
    

def opus_size_obj(size_id):
    if size_id not in xrange(1, len(OPUS_SIZE)+1):
        return None
    
    for item in OPUS_SIZE:
        if item[0] == size_id:
            return item
    return None

@manager_required
def  delete_opus_size(request):
    try: id = int(request.REQUEST["id"])
    except: return HttpResponse(FailResponse(u"参数错误"))
    
    try: widget_opus_size = WidgetOpusSize.objects.get(id=id)
    except: return HttpResponse(FailResponse(u"删除对象不存在"))
    
    widget_opus_size.delete()
    return HttpResponse(SuccessResponse(u"作品版面:%d删除成功" % id))
    

@manager_required
def delete_page_size(request):
    try: id = int(request.REQUEST["id"])
    except: return HttpResponse(FailResponse(u"参数错误"))
    
    try: widget_page_size = WidgetPageSize.objects.get(id=id)
    except: return HttpResponse(FailResponse(u"删除对象不存在"))
    
    widget_page_size.delete()
    return HttpResponse(SuccessResponse(u"作品尺寸:%d删除成功" % id))

@manager_required
def asset_list(request):
    if request.method == "GET":
        return render(request, "manager/asset_list.html", {"index":2, "sub_index":3, })
    elif request.method == "POST":
        page_index = int(request.POST.get('page_index', 1))
        page_size = int(request.POST.get('page_size', 15))
        
        where_clause = "status=1"
        if request.user.library_id:
            where_clause += " and library_id=%d" % request.user.library_id
        else:
            where_clause += " and library_id is null"
            
        res_type = int(request.REQUEST.get('type_id', 0))
        res_style = int(request.REQUEST.get('style_id', 0))
        search_text = request.REQUEST.get('search_text', None)
        if res_type:
            where_clause += " and res_type=%d" % res_type
        if res_style:
            where_clause += " and res_style=%d" % res_style
        if search_text:
            where_clause += " and res_title like '%%%s%%'" % search_text
        print where_clause    
        
        cursor = connections[DB_READ_NAME].cursor()
        sql = "select count(*) from zone_asset  where %s" % where_clause
        cursor.execute(sql)
        row = cursor.fetchone()
        count = 0
        if row: count = row[0]
        page_count = int(ceil(count/float(page_size)))
        
        sql = "select id,res_title,res_type,res_style,res_path,img_large_path,create_time,page_count,ref_times,type_id,class_id,page_type From zone_asset where %s order by create_time DESC LIMIT %s, %s" % (where_clause, (page_index-1)*page_size, page_size)
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        data_lists = []
        for row in rows:
            id = row[0]
            res_title = row[1]
            res_type_id = int(row[2])
            res_style_id = row[3]
            res_path = row[4] if row[4] else ""
            img_large_path = row[5] if row[5] else ""
            create_time = row[6]
            
            data_dict = {"id":id,"title":res_title,"type_id":res_type_id,"res_type_name":zone_res_type_name(res_type_id),"style_name":zone_res_style_name(res_style_id)}
            data_dict["url"] = MEDIA_URL + img_large_path if img_large_path else MEDIA_URL + res_path
            data_dict["create_time"] = create_time.strftime("%Y-%m-%d %H:%M:%S")
            data_dict["page_count"] = row[7]
            data_dict["ref_times"] = row[8]
            data_dict["type_id"] = row[9]
            data_dict["class_id"] = row[10]
            data_dict["type_name"] = opus_type_name(row[9])
            data_dict["class_name"] = opus_type_name(row[10])
            data_dict["page_name"] = zone_page_name(row[11])
            data_lists.append(data_dict)
        cursor.close()
        return HttpResponse(json.dumps({"data":data_lists, "page_index": page_index, "page_count": page_count}))

def opus_type_name(type_id):
    try:
        return WidgetOpusClassify.objects.get(id=type_id).classify_name
    except: return u"未知"
    
def zone_page_name(page_id):
    if page_id == 1:
        return u"单页"
    elif page_id == 2:
        return u"双页"
    elif page_id == 0:
        return u"不限"

@manager_required
@require_POST
def delete_asset(request):
    zone_asset = get_zone_asset(request.REQUEST.get('id', None))[2]
    if not zone_asset: return HttpResponse(u"资源不存在")
    
    if zone_asset.library <> request.user.library:
        return HttpResponse(u"没有权限")
    
    if zone_asset.res_type == 4:
        if zone_asset.page_count > 0:
            return HttpResponse(u"模板必须删除完下属页才能删除")
    elif zone_asset.ref_times > 0:
        return HttpResponse(u'资源有(%s)个相关引用，不能删除' % zone_asset.ref_times)
    
    asset_dir = '%s/%d' % (get_asset_path(request, zone_asset.res_type), zone_asset.id)
    asset_absdir = os.path.join(MEDIA_ROOT, asset_dir)
    __import__('shutil').rmtree(asset_absdir)
    zone_asset.delete()
    
    #记录日志
    add_manager_action_log(request, u'%s删除了素材%s[%s]' % (request.user, zone_asset.res_title, zone_res_type_name(zone_asset.res_type)))
    return HttpResponse('ok')



@manager_required
def batch_upload_img(request):
    if len(request.FILES) == 0:
        return HttpResponse(FailResponse(u"请选择图片文件并上传"))
    back_data = []
    mem_files = request.FILES.popitem()[1]
    
    count = 0
    file_names = ""
    for mem_file in mem_files:
        filename, ext = os.path.splitext(mem_file.name)
        if ext.lower() not in ALLOWED_IMG_EXTENSION:
            continue
        if mem_file.size > ALLOWED_IMG_UPLOAD_SIZE:
            continue
        
        count += 1
        file_names += "," + filename if len(file_names)>0 else filename
        
        res_path = "temp/%s/%s%s" % (datetime.now().strftime("%Y-%m-%d"), filename, ext)
        res_path = get_new_filename(MEDIA_ROOT, res_path)   #有重名文件，则重命名新文件
        res_abspath =  os.path.join(MEDIA_ROOT, res_path)
        
        if not os.path.exists(os.path.split(res_abspath)[0]):
            os.makedirs(os.path.split(res_abspath)[0])
        f = open(res_abspath, "wb")
        for chunk in mem_file.chunks():
            f.write(chunk)
        f.close()
        back_data.append({"path":res_path, "filename": filename})
    
    #记录日志
    add_manager_action_log(request, u'%s批量上传了[%s]张图片(%s)' % (request.user, count, file_names))
    return HttpResponse(SuccessResponse(back_data))



def ajax_upload_file(request):
    '''
    上传文件
    editor: kamihati 2015/5/7
    :param request:
    :return:
    '''
    print len(request.FILES), request.FILES
    if len(request.FILES) == 0:
        return HttpResponse(FailResponse(u"请选择文件并上传"))
    elif len(request.FILES) > 1:
        return HttpResponse(FailResponse(u"一次只能上传一个文件"))

    mem_file = request.FILES.popitem()[1][0]
    filename, ext = os.path.splitext(mem_file.name)

    res_path = "temp/%s/%s%s" % (datetime.now().strftime("%Y-%m-%d"), filename, ext)
    res_path = get_new_filename(MEDIA_ROOT, res_path)   #有重名文件，则重命名新文件
    res_abspath =  os.path.join(MEDIA_ROOT, res_path)

    if not os.path.exists(os.path.split(res_abspath)[0]):
        os.makedirs(os.path.split(res_abspath)[0])
    f = open(res_abspath, "wb")
    for chunk in mem_file.chunks():
        f.write(chunk)
    f.close()

    return HttpResponse(SuccessResponse({"path":res_path, "filename": filename}))



@manager_required
def ajax_upload_img(request):
    print len(request.FILES), request.FILES
    if len(request.FILES) == 0:
        return HttpResponse(FailResponse(u"请选择图片文件并上传"))
    elif len(request.FILES) > 1:
        return HttpResponse(FailResponse(u"一次只能上传一个图片文件"))
    
    mem_file = request.FILES.popitem()[1][0]
    filename, ext = os.path.splitext(mem_file.name)
    if ext.lower() not in ALLOWED_IMG_EXTENSION:
        return HttpResponse(FailResponse(u"只充许上传图片文件(%s)" % ';'.join(ALLOWED_IMG_EXTENSION)))
    if mem_file.size > ALLOWED_IMG_UPLOAD_SIZE:
        return HttpResponse(FailResponse(u'文件超过最大充许大小'))

    res_path = "temp/%s/%s%s" % (datetime.now().strftime("%Y-%m-%d"), filename, ext)
    res_path = get_new_filename(MEDIA_ROOT, res_path)   #有重名文件，则重命名新文件
    res_abspath =  os.path.join(MEDIA_ROOT, res_path)
    
    if not os.path.exists(os.path.split(res_abspath)[0]):
        os.makedirs(os.path.split(res_abspath)[0])
    f = open(res_abspath, "wb")
    for chunk in mem_file.chunks():
        f.write(chunk)
    f.close()

    return HttpResponse(SuccessResponse({"path":res_path, "filename": filename}))

@manager_required
def ajax_upload_json(request):
    if len(request.FILES) == 0:
        return HttpResponse(FailResponse(u"请选择json文件并上传"))
    elif len(request.FILES) > 1:
        return HttpResponse(FailResponse(u"一次只能上传一个json文件"))
    
    mem_file = request.FILES.popitem()[1][0]
    filename, ext = os.path.splitext(mem_file.name)
    if ext.lower() not in (".json", ".txt"):
        return HttpResponse(FailResponse(u"只充许上传图片文件(%s)" % ';'.join((".json", ".txt"))))
    if mem_file.size > 1024*100:
        return HttpResponse(FailResponse(u'文件超过最大充许大小(100K)'))

    res_path = "temp/%s/%s%s" % (datetime.now().strftime("%Y-%m-%d"), filename, ext)
    res_path = get_new_filename(MEDIA_ROOT, res_path)   #有重名文件，则重命名新文件
    res_abspath =  os.path.join(MEDIA_ROOT, res_path)
    
    if not os.path.exists(os.path.split(res_abspath)[0]):
        os.makedirs(os.path.split(res_abspath)[0])
    f = open(res_abspath, "wb+")
    for chunk in mem_file.chunks():
        f.write(chunk)
    f.seek(0)
    json_data = f.read()
    f.close()
    #os.remove(res_abspath)
    
    try: json.loads(json_data)
    except: return HttpResponse(FailResponse(u"非法的json文件"))
    return HttpResponse(SuccessResponse(json_data))

@manager_required
def ajax_upload_audio(request):
    if len(request.FILES) == 0:
        return HttpResponse(FailResponse(u"请选择音频文件并上传"))
    elif len(request.FILES) > 1:
        return HttpResponse(FailResponse(u"一次只能上传一个音频文件"))
    
    mem_file = request.FILES.popitem()[1][0]
    filename, ext = os.path.splitext(mem_file.name)
    print filename, ext
    if ext.lower() not in ALLOWED_SOUND_EXTENSION:
        return HttpResponse(FailResponse(u"只充许上传音频文件(%s)" % ';'.join(ALLOWED_SOUND_EXTENSION)))
    if mem_file.size > ALLOWED_SOUND_UPLOAD_SIZE:
        return HttpResponse(FailResponse(u'文件超过最大充许大小'))

    res_path = "temp/%s/%s%s" % (datetime.now().strftime("%Y-%m-%d"), filename, ext)
    res_path = get_new_filename(MEDIA_ROOT, res_path)   #有重名文件，则重命名新文件
    res_abspath =  os.path.join(MEDIA_ROOT, res_path)
    
    if not os.path.exists(os.path.split(res_abspath)[0]):
        os.makedirs(os.path.split(res_abspath)[0])
    f = open(res_abspath, "wb")
    for chunk in mem_file.chunks():
        f.write(chunk)
    f.close()
    
    return HttpResponse(SuccessResponse({"path":res_path, "filename": filename}))

@manager_required
def ajax_upload_video(request):
    if len(request.FILES) == 0:
        return HttpResponse(FailResponse(u"请选择视频文件并上传"))
    elif len(request.FILES) > 1:
        return HttpResponse(FailResponse(u"一次只能上传一个视频文件"))
    
    mem_file = request.FILES.popitem()[1][0]
    filename, ext = os.path.splitext(mem_file.name)
    if ext.lower() not in ALLOWED_VIDEO_EXTENSION:
        return HttpResponse(FailResponse(u"只充许上传视频文件(%s)" % ';'.join(ALLOWED_VIDEO_EXTENSION)))
    if mem_file.size > ALLOWED_VIDEO_UPLOAD_SIZE:
        return HttpResponse(FailResponse(u'文件超过最大充许大小'))

    res_path = "temp/%s/%s%s" % (datetime.now().strftime("%Y-%m-%d"), filename, ext)
    res_path = get_new_filename(MEDIA_ROOT, res_path)   #有重名文件，则重命名新文件
    res_abspath =  os.path.join(MEDIA_ROOT, res_path)
    
    if not os.path.exists(os.path.split(res_abspath)[0]):
        os.makedirs(os.path.split(res_abspath)[0])
    f = open(res_abspath, "wb")
    for chunk in mem_file.chunks():
        f.write(chunk)
    f.close()
    
    return HttpResponse(SuccessResponse({"path":res_path, "filename": filename}))            


@manager_required
def batch_asset(request):
    if request.method == "GET":
        return render(request, "manager/batch_asset.html", {"index":2, "sub_index":1})

from utils.decorator import print_trace
@print_trace    
@manager_required
def asset(request):
    if request.method == "GET":
        zone_asset = get_zone_asset(request.REQUEST.get('id', None))[2]
        return render(request, "manager/asset.html", {"index":2, "sub_index":2, "asset":zone_asset})
    elif request.method == "POST":
        action_name = u"新增"
        zone_asset = get_zone_asset(request.REQUEST.get('asset_id', None))[2]
        if zone_asset: action_name = u"修改"
        
        res_type = int(request.POST["rdo_type"])
        page_type_id = int(request.POST["page_type_id"])
        page_type_id = int(request.POST["page_type_id"])
        layout_type_id = int(request.POST["layout_type_id"])
        if res_type not in (1,2,3,4,5,6,7,8):
            return HttpResponse(FailResponse(u"资源类型不正确，请检查重新输入！"))
        res_title = request.POST["title"]
        
        if not zone_asset:
            zone_asset = ZoneAsset()
            zone_asset.status = -1  #新作品，未上传成功前，先状态为-1
        zone_asset.user = request.user
        zone_asset.library = request.user.library
        zone_asset.res_title = res_title
        zone_asset.res_type = res_type
        zone_asset.page_type = page_type_id
        zone_asset.layout_type_id = layout_type_id
        if res_type in (1,2,3,4,7,8):
            zone_asset.res_style = int(request.POST["sel_style"])    #声音和视频没有风格
        zone_asset.save()   #得到ID
        
        asset_res_path = "%s/%d" % (get_asset_path(request, res_type), zone_asset.id)
        if not os.path.exists(os.path.join(MEDIA_ROOT, asset_res_path)):
            os.makedirs(os.path.join(MEDIA_ROOT, asset_res_path))
        
        from PIL import Image
        hid_mask_path = request.POST["hid_mask_path"]
        if hid_mask_path.find("temp") >= 0:  #有新上传文件
            if res_type == 3:   #画框
                hid_mask_path = request.POST["hid_mask_path"]
                if len(hid_mask_path) == 0:
                    return HttpResponse(FailResponse(u"未知错误，请联系管理员2"))
                
                if not zone_asset.mask_path:
                    zone_asset.mask_path = "%s/%d/mask%s" % (get_asset_path(request, res_type), zone_asset.id, os.path.splitext(hid_mask_path)[1])

                open(os.path.join(MEDIA_ROOT, zone_asset.mask_path), "wb").write(open(os.path.join(MEDIA_ROOT, hid_mask_path), "rb").read())
                #os.remove(os.path.join(MEDIA_ROOT, hid_mask_path))
            elif res_type == 8:   #特效
                ext_mask = os.path.splitext(hid_mask_path)[1]
                zone_asset.img_large_path = "%s/l%s" % (asset_res_path, ext_mask)
                zone_asset.img_medium_path = "%s/m%s" % (asset_res_path, ext_mask)
                zone_asset.img_small_path = "%s/s%s" % (asset_res_path, ext_mask)
                
                img = Image.open(os.path.join(MEDIA_ROOT, hid_mask_path))
                
                open(os.path.join(MEDIA_ROOT, zone_asset.img_large_path), "wb").write(open(os.path.join(MEDIA_ROOT, hid_mask_path), "rb").read())
                
                if img.size[0] > 950 or img.size[1] > 950:
                    img.thumbnail((950,950), Image.ANTIALIAS)
                    img.save(os.path.join(MEDIA_ROOT, zone_asset.img_large_path))
                
                if img.size[0] > 600 or img.size[1] > 600:
                    img.thumbnail((600,600), Image.ANTIALIAS)
                    img.save(os.path.join(MEDIA_ROOT, zone_asset.img_medium_path))
                else:
                    zone_asset.img_medium_path = zone_asset.img_large_path
                
                img.thumbnail(get_small_size(img.size[0], img.size[1]), Image.ANTIALIAS)
                img.save(os.path.join(MEDIA_ROOT, zone_asset.img_small_path))
                
            os.remove(os.path.join(MEDIA_ROOT, hid_mask_path))
                
        hid_res_path = request.POST["hid_res_path"]
        if len(hid_res_path) == 0:
            return HttpResponse(FailResponse(u"未知错误，请联系管理员"))
        ext = os.path.splitext(hid_res_path)[1] #扩展名 .swf等
        if hid_res_path.find("temp") >= 0:  #有新上传文件
            if res_type in (1, 2, 3, 4, 7):
                zone_asset.res_path = "%s/origin%s" % (asset_res_path, ext)
                if ext.lower() not in (".swf"):
                    zone_asset.img_large_path = zone_asset.res_path.replace("origin", "l")
                    zone_asset.img_medium_path = zone_asset.res_path.replace("origin", "m")
                    zone_asset.img_small_path = zone_asset.res_path.replace("origin", "s")
                elif ext.lower() in (".swf"): #都可以上传swf文件
                    zone_asset.img_large_path = zone_asset.res_path
                    zone_asset.img_medium_path = zone_asset.res_path
                    zone_asset.img_small_path = zone_asset.res_path
                open(os.path.join(MEDIA_ROOT, zone_asset.res_path), "wb").write(open(os.path.join(MEDIA_ROOT, hid_res_path), "rb").read())
            elif res_type == 5: #声音
                zone_asset.origin_path = "%s/origin%s" % (asset_res_path, ext)
                zone_asset.res_path = "%s/%d.mp3" % (asset_res_path, zone_asset.id)
                open(os.path.join(MEDIA_ROOT, zone_asset.origin_path), "wb").write(open(os.path.join(MEDIA_ROOT, hid_res_path), "rb").read())
            elif res_type == 6: #视频
                zone_asset.origin_path = "%s/origin%s" % (asset_res_path, ext)
                zone_asset.res_path = "%s/%d.flv" % (asset_res_path, zone_asset.id)
                zone_asset.img_large_path = "%s/l.jpg" % asset_res_path  #存视频截图的原图
                zone_asset.img_small_path = "%s/s.jpg" % asset_res_path
                open(os.path.join(MEDIA_ROOT, zone_asset.origin_path), "wb").write(open(os.path.join(MEDIA_ROOT, hid_res_path), "rb").read())
            elif res_type == 8: #特效
                zone_asset.res_path = "%s/origin%s" % (asset_res_path, ext)
                open(os.path.join(MEDIA_ROOT, zone_asset.res_path), "wb").write(open(os.path.join(MEDIA_ROOT, hid_res_path), "rb").read())

            try: os.remove(os.path.join(MEDIA_ROOT, hid_res_path))
            except: pass
            
            if res_type in (1,2,3,4,7): #三个等级图片缩放
                if res_type == 8 or ext.lower() not in (".swf"):
                    img = Image.open(os.path.join(MEDIA_ROOT, zone_asset.res_path))
                    zone_asset.width = img.size[0]
                    zone_asset.height = img.size[1]
    
                    if img.size[0] > 950 or img.size[1] > 950:
                        img.thumbnail((950,950), Image.ANTIALIAS)
                        img.save(os.path.join(MEDIA_ROOT, zone_asset.img_large_path))
                    else:
                        zone_asset.img_large_path = zone_asset.res_path
                    
                    if img.size[0] > 600 or img.size[1] > 600:
                        img.thumbnail((600,600), Image.ANTIALIAS)
                        img.save(os.path.join(MEDIA_ROOT, zone_asset.img_medium_path))
                    else:
                        zone_asset.img_medium_path = zone_asset.res_path
    
                    img.thumbnail(get_small_size(img.size[0], img.size[1]), Image.ANTIALIAS)
                    img.save(os.path.join(MEDIA_ROOT, zone_asset.img_small_path))
            zone_asset.status = 1
            zone_asset.save()
        
        #记录日志
        add_manager_action_log(request, u'%s%s了公共素材[%s(%s)]' % (request.user, action_name, zone_asset.res_title, zone_res_type_name(res_type)))
        return HttpResponse(SuccessResponse(request.POST.get("div_id", 0)))


@manager_required
def template_asset(request):
    try:
        hid_id = int(request.POST["hid_id"])
        res_title = request.POST["title"]
        type_id = request.POST["type_id"]
        class_id = request.POST["class_id"]
        hid_res_path = request.POST["hid_res_path"]
        
        size_id = int(request.POST["size_id"])
        create_type = request.POST["rdo_create"]
        read_type = request.POST["rdo_read"]
    except:
        traceback.print_exc()
        return HttpResponse(u"参数错误")
    if len(hid_res_path) == 0:
        return HttpResponse(u"未知错误，请联系管理员")
    
    try: widget_page_size = WidgetPageSize.objects.get(id=size_id)
    except: return HttpResponse(u"请选择模板尺寸")
    
    res_type = 4
    if hid_id:
        try: zone_asset = ZoneAsset.objects.get(id=hid_id)
        except: return HttpResponse(u"修改模板ID不存在")
    else:
        zone_asset = ZoneAsset()
        zone_asset.user = request.user
        zone_asset.library = request.user.library
        zone_asset.res_type = res_type #模板
        zone_asset.status = -1  #未上传成功前，先状态为-1
        zone_asset.save()   #得到ID
    
    zone_asset.res_title = res_title
    zone_asset.type_id = type_id
    zone_asset.class_id = class_id
    zone_asset.create_type = create_type
    zone_asset.read_type = read_type
    zone_asset.size_id = size_id
    zone_asset.width = widget_page_size.screen_width
    zone_asset.height = widget_page_size.screen_height
    
    ext = os.path.splitext(hid_res_path)[1] #扩展名 .swf等
    if hid_res_path.find("temp") >= 0:  #有新上传文件
        asset_res_path = "%s/%d" % (get_asset_path(request, res_type), zone_asset.id)
        if not os.path.exists(os.path.join(MEDIA_ROOT, asset_res_path)):
            os.makedirs(os.path.join(MEDIA_ROOT, asset_res_path))
            zone_asset.res_path = "%s/origin%s" % (asset_res_path, ext)
        if ext.lower() in (".swf"): #都可以上传swf文件
            zone_asset.img_large_path = zone_asset.res_path
            zone_asset.img_medium_path = zone_asset.res_path
            zone_asset.img_small_path = zone_asset.res_path
        else:
            zone_asset.img_large_path = zone_asset.res_path.replace("origin", "l")
            zone_asset.img_medium_path = zone_asset.res_path.replace("origin", "m")
            zone_asset.img_small_path = zone_asset.res_path.replace("origin", "s")
            open(os.path.join(MEDIA_ROOT, zone_asset.res_path), "wb").write(open(os.path.join(MEDIA_ROOT, hid_res_path), "rb").read())
        try: os.remove(os.path.join(MEDIA_ROOT, hid_res_path))
        except: pass
        
        if ext.lower() not in (".swf"):
            from PIL import Image
            img = Image.open(os.path.join(MEDIA_ROOT, zone_asset.res_path))

            if img.size[0] > 950 or img.size[1] > 950:
                img.thumbnail((950,950), Image.ANTIALIAS)
                img.save(os.path.join(MEDIA_ROOT, zone_asset.img_large_path))
            else:
                zone_asset.img_large_path = zone_asset.res_path
            
            if img.size[0] > 600 or img.size[1] > 600:
                img.thumbnail((600,600), Image.ANTIALIAS)
                img.save(os.path.join(MEDIA_ROOT, zone_asset.img_medium_path))
            else:
                zone_asset.img_medium_path = zone_asset.res_path

            img.thumbnail(get_small_size(img.size[0], img.size[1]), Image.ANTIALIAS)
            img.save(os.path.join(MEDIA_ROOT, zone_asset.img_small_path))
        zone_asset.status = 1
    zone_asset.save()
    
    #记录日志
    action_name = u"新增"
    if hid_id: action_name = u"修改"
    add_manager_action_log(request, u'%s%s了模板[%s]的基本信息' % (request.user, action_name, zone_asset.res_title))
    return HttpResponse("ok")    

def auth_type_name(auth_type_id):
    if auth_type_id == 0:
        return u"普通会员"
    elif auth_type_id == 1:
        return u"图书馆管理员"
    elif auth_type_id == 2:
        return u"图书馆审核员"
    elif auth_type_id == 9:
        return u"超级管理员"
    else:
        return u"未知类型:%d" % auth_type_id


@manager_required
def user_list(request):
    if request.method == "GET":
        return render(request, "manager/user_list.html", {"index":4, "sub_index":1})
    elif request.method == "POST":
        if request.user.library_id:
            where_clause = "library_id=%d" % request.user.library_id
        else:
            where_clause = "library_id is null"
            
        auth_type = int(request.REQUEST.get("auth_type", 0))
        if auth_type not in (0, 2):  #普通会员, 审核员
            return HttpResponse(u"参数错误")
        
        where_clause += " and auth_type=%d" % auth_type  #普通会员
        print where_clause
        
        page_index = int(request.POST.get('page_index', 1))
        page_size = int(request.POST.get('page_size', 15))

        search_type = int(request.REQUEST.get('search_type', 0))
        search_text = request.REQUEST.get('search_text', None)
        if search_text:
            if search_type == 1:
                where_clause += " and id=%s" % search_text
            elif search_type == 2:
                where_clause += " and username like '%%%s%%'" % search_text
            elif search_type == 3:
                where_clause += " and nickname like '%%%s%%'" % search_text
        print where_clause  
        
        cursor = connections[DB_READ_NAME].cursor()
        sql = "select count(*) from auth_user where %s" % where_clause
        cursor.execute(sql)
        row = cursor.fetchone()
        count = 0
        if row: count = row[0]
        page_count = int(ceil(count/float(page_size)))
        
        sql = "select id,username,auth_type,library_id,nickname,telephone,qq,email,avatar_img,is_active,login_times,last_ip,last_login,date_joined From auth_user where %s order by date_joined DESC LIMIT %s, %s" % (where_clause, (page_index-1)*page_size, page_size)
        print sql
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        data_lists = []
        for row in rows:
            data_dict = {}
            data_dict["id"] = row[0]
            data_dict["username"] = row[1]
            data_dict["auth_type"] = auth_type_name(row[2])
            #data_dict["library_id"] = row[3]
            data_dict["nickname"] = row[4]
            data_dict["telephone"] = F(row[5])
            data_dict["qq"] = F(row[6])
            data_dict["email"] = F(row[7])
            data_dict["avatar_img"] = request.build_absolute_uri(MEDIA_URL + get_tile_image_name(row[8], 'l')) if row[8] else ""
            data_dict["is_active"] = row[9]
            #data_dict["login_times"] = row[10]
            #data_dict["last_ip"] = row[11]
            #data_dict["last_login"] = row[12].strftime("%Y-%m-%d %H:%M:%S")
            data_dict["date_joined"] = row[13].strftime("%Y-%m-%d %H:%M:%S")
            data_lists.append(data_dict)
        cursor.close()
        return HttpResponse(json.dumps({"data":data_lists, "page_index": page_index, "page_count": page_count}))
    
@manager_required
@require_POST
def change_user_active(request):
    try:
        uid = int(request.REQUEST["uid"])
        is_active = int(request.REQUEST["status"])
    except: return HttpResponse(u"参数错误")
    
    try: auth_user = AuthUser.objects.get(id=uid)
    except(AuthUser.DoesNotExist): return HttpResponse(u"用户不存在")
    
    if is_active not in (0, 1): return HttpResponse(u"参数错误2")
    
    if not request.user.is_superuser:
        if auth_user.library <> request.user.library:
            return HttpResponse(u"没有权限")
        
    
    auth_user.is_active = is_active
    auth_user.save()
    
    return HttpResponse("ok")


@manager_required
@require_POST
def reset_user_password(request):
    try: uid = int(request.REQUEST["uid"])
    except: return HttpResponse(FailResponse(u"参数错误"))
    
    try: auth_user = AuthUser.objects.get(id=uid)
    except(AuthUser.DoesNotExist): return HttpResponse(FailResponse(u"用户不存在"))
    
    if auth_user.library <> request.user.library:
        return HttpResponse(FailResponse(u"没有权限"))
    
    import string
    from random import choice
    newpass = ''.join([choice(string.digits) for _ in xrange(6)])
    auth_user.set_password(newpass)
    auth_user.save()
    
    return HttpResponse(SuccessResponse(newpass))    
    
@manager_required    
def auditor(request):
    if request.method == "GET":
        return render(request, "manager/auditor.html", {"index":3, "sub_index":1})
    elif request.method == "POST":
        uid = int(request.REQUEST.get("uid", 0))
        username = request.REQUEST.get("username", "").strip().lower()
        if uid: #取消审核员资格
            try: auth_user = AuthUser.objects.get(id=uid)
            except: return HttpResponse(u"用户不存在")
            if auth_user.auth_type <> 2: return HttpResponse(u"用户不是审核员")
            if auth_user.library_id <> request.user.library_id: return HttpResponse(u"用户不是当前图书馆下的审核员，没有权限")
            auth_user.auth_type = 0 #转为普通用户
            auth_user.save()
            return HttpResponse("ok")
        else:   #新增审核员
            try:
                auth_user = AuthUser.objects.get(username=username)
                if auth_user.auth_type == 2:
                    return HttpResponse(u"该用户已经是审核员")
                if not auth_user.is_active:
                    return HttpResponse(u"该用户被封号")
                if auth_user.library_id <> request.user.library_id:
                    return HttpResponse(u"必须是当前图书馆下的普通会员，才能转为《审核员》！")
                auth_user.auth_type = 2 #转为审核员
                auth_user.save()
                return HttpResponse("ok")
            except: return HttpResponse(u"用户不存在")
            
        


@manager_required    
def auditor_list(request):
    if request.method == "GET":
        return render(request, "manager/auditor_list.html", {"index":4, "sub_index":2})
    elif request.method == "POST":
        if request.user.library_id:
            where_clause = "library_id=%d" % request.user.library_id
        else:
            where_clause = "library_id is null"
        print where_clause
        
        page_index = int(request.POST.get('page_index', 1))
        page_size = int(request.POST.get('page_size', 15))
        
        cursor = connections[DB_READ_NAME].cursor()
        sql = "select count(*) from auth_user where %s" % where_clause
        cursor.execute(sql)
        row = cursor.fetchone()
        count = 0
        if row: count = row[0]
        page_count = int(ceil(count/float(page_size)))
        
        sql = "select id,username,auth_type,library_id,nickname,telephone,qq,email,avatar_img,is_active,login_times,last_ip,last_login,date_joined From auth_user where %s order by date_joined DESC LIMIT %s, %s" % (where_clause, (page_index-1)*page_size, page_size)
        print sql
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        data_lists = []
        for row in rows:
            data_dict = {}
            data_dict["id"] = row[0]
            data_dict["username"] = row[1]
            data_dict["auth_type"] = auth_type_name(row[2])
            #data_dict["library_id"] = row[3]
            data_dict["nickname"] = row[4]
            data_dict["telephone"] = F(row[5])
            data_dict["qq"] = F(row[6])
            data_dict["email"] = F(row[7])
            data_dict["avatar_img"] = request.build_absolute_uri(MEDIA_URL + get_tile_image_name(row[8], 'l')) if row[8] else ""
            data_dict["is_active"] = row[9]
            #data_dict["login_times"] = row[10]
            #data_dict["last_ip"] = row[11]
            #data_dict["last_login"] = row[12].strftime("%Y-%m-%d %H:%M:%S")
            data_dict["date_joined"] = row[13].strftime("%Y-%m-%d %H:%M:%S")
            data_lists.append(data_dict)
        cursor.close()
        return HttpResponse(json.dumps({"data":data_lists, "page_index": page_index, "page_count": page_count}))


@manager_required    
def notice(request):
    from widget.models import WidgetNotice
    
    notice_id = request.REQUEST.get('id', None)
    if notice_id:
        try:widget_notice = WidgetNotice.objects.get(id=notice_id)
        except(WidgetNotice.DoesNotExist): widget_notice = None
    else: widget_notice = None
    
    if request.method == "GET":
        return render(request, "manager/notice.html", {"index":5, "sub_index":1, "notice":widget_notice})
    elif request.method == "POST":
        expire_time = request.REQUEST["expire_time"]
        content = request.REQUEST["content"]
        
        expire_time = datetime.strptime(expire_time, "%Y-%m-%d")
        
        if not widget_notice:
            widget_notice = WidgetNotice()
            widget_notice.user = request.user
            widget_notice.library = request.user.library
            widget_notice.create_time = datetime.now()
        widget_notice.expire_time = expire_time
        widget_notice.content = content
        widget_notice.save()
        
        return render(request, "manager/notice.html", {"index":5, "sub_index":1, "result":"ok"})


def notice_status_name(status_id):
    if status_id == 0:
        return u"待审核"
    elif status_id == 1:
        return u"可用"
    elif status_id == -1:
        return u"已删除"
    else:
        return u"未知"
    
@manager_required    
def notice_list(request):
    if request.method == "GET":
        return render(request, "manager/notice_list.html", {"index":5, "sub_index":2})
    elif request.method == "POST":

        search_text = request.POST.get('search_text',"")
        where_clause = ""
        if request.user.library_id:
            if search_text != "":
                where_clause = "library_id=%d and content like '%%%s%%'" % (request.user.library_id,search_text)
            else:
                where_clause = "library_id = %d " % request.user.library_id

        else:
            if search_text != "":
                where_clause = "library_id is null and content like '%%%s%%'" % search_text
            else:
                where_clause = "library_id is null"
        print where_clause
        
        page_index = int(request.POST.get('page_index', 1))
        page_size = int(request.POST.get('page_size', 15))
        
        cursor = connections[DB_READ_NAME].cursor()
        sql = "select count(*) from widget_notice where %s" % where_clause
        cursor.execute(sql)
        row = cursor.fetchone()
        count = 0
        if row: count = row[0]
        page_count = int(ceil(count/float(page_size)))
        
        sql = "select id,library_id,content,read_times,expire_time,create_time,status From widget_notice where %s order by create_time DESC LIMIT %s, %s" % (where_clause, (page_index-1)*page_size, page_size)
        print sql
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        data_lists = []
        for row in rows:
            data_dict = {}
            data_dict["id"] = row[0]
            data_dict["library_id"] = row[1] if row[1] else ""
            data_dict["content"] = row[2]
            data_dict["read_times"] = row[3]
            data_dict["expire_time"] = row[4].strftime("%Y-%m-%d")
            data_dict["create_time"] = row[5].strftime("%Y-%m-%d %H:%M:%S")
            data_dict["status_name"] = notice_status_name(row[6])
            data_lists.append(data_dict)
        cursor.close()
        return HttpResponse(json.dumps({"data":data_lists, "page_index": page_index, "page_count": page_count}))
    
    
@manager_required    
def opus_list(request):
    status = int(request.REQUEST.get('status', 1)) #作品状态    1:待审核    2:已发表    -1,0:创作中
    if request.method == "GET":
        if status == 1: sub_index =1
        elif status == 2: sub_index =2
        else: sub_index =3
            
        return render(request, "manager/opus_list.html", {"index":6, "sub_index":sub_index, "status":status})
    elif request.method == "POST":
        if request.user.library_id:
            where_clause = "auth_opus.library_id=%d" % request.user.library_id
        else:
            where_clause = "auth_opus.library_id is null"
            
        #print where_clause
        
        if status == 0: where_clause += " and status in (-1, 0)"
        else: where_clause += " and status=%d" % status
        print where_clause
        page_index = int(request.POST.get('page_index', 1))
        page_size = int(request.POST.get('page_size', 15))
        
        cursor = connections[DB_READ_NAME].cursor()
        sql = "select count(*) from auth_opus where %s" % where_clause
        #print sql
        cursor.execute(sql)
        row = cursor.fetchone()
        count = 0
        if row: count = row[0]
        page_count = int(ceil(count/float(page_size)))
        
        sql = "select auth_opus.id,user_id,username,title,type_id,class_id,page_count,is_top,grade,preview_times,comment_times,cover,create_time,status,praise_times From auth_opus LEFT JOIN auth_user on auth_opus.user_id=auth_user.id where %s order by create_time DESC LIMIT %s, %s" % (where_clause, (page_index-1)*page_size, page_size)
        print sql
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        data_lists = []
        for row in rows:
            data_dict = {}
            data_dict["id"] = row[0]
            data_dict["user_id"] = row[1]
            data_dict["username"] = row[2]
            data_dict["title"] = row[3] if row[3] else u"[未命名作品：%d]" % data_dict["id"]
            data_dict["type_name"] = opus_type_name(row[4])
            data_dict["class_name"] = opus_type_name(row[5])
            print data_dict["class_name"]
            data_dict["page_count"] = row[6]
            data_dict["is_top"] = row[7]
            data_dict["grade"] = row[8]
            data_dict["preview_times"] = row[9]
            data_dict["comment_times"] = row[10]
            
            data_dict["create_time"] = row[12].strftime("%Y-%m-%d %H:%M:%S")
            data_dict["status"] = row[13]
            data_dict["status_name"] = opus_status_name(data_dict["status"])
            data_dict["praise_times"] = row[14]
            
            #opus_dir = 'user/%s/%d/opus/%d' % (date_joined.strftime("%Y"), data_dict["user_id"], data_dict["id"])
            cover_image = row[11] if row[11] else get_cover_image(data_dict["id"])
            data_dict["cover"] = request.build_absolute_uri(MEDIA_URL + cover_image)
            data_lists.append(data_dict)
        cursor.close()
        return HttpResponse(json.dumps({"data":data_lists, "page_index": page_index, "page_count": page_count}))


def get_cover_image(opus_id):
    sql = "select img_path from auth_opus_page where auth_opus_id=%d and page_index=1" % opus_id
    cur = connections[DB_READ_NAME].cursor()
    cur.execute(sql)
    row = cur.fetchone()
    cur.close()
    if row and row[0]:
        return row[0]
    else: return ""


def opus(request):
    try:
        opus_id = request.REQUEST.get("id", None)
        auth_opus = AuthOpus.objects.get(id=opus_id)
    except:
        return HttpResponse(u"参数错误")
    if request.method == "GET":
        return render(request, "manager/opus.html",
                      {"index":6, "sub_index":1, "opus":auth_opus, "host": request.get_host(),
                       'backend': 1, 'user_id': request.user.id})


@manager_required
def get_opus_info(request):
    try:
        opus_id = request.REQUEST.get("id", None)
        auth_opus = AuthOpus.objects.get(id=opus_id)
    except:
        return HttpResponse(u"参数错误")
    
    if auth_opus.library <> request.user.library:
        return HttpResponse(u"没有权限")

    from gateway.views_opus import opus_info
    return HttpResponse(json.dumps(opus_info(auth_opus)))

@manager_required
def get_opus_brief(request):
    try:
        opus_id = request.REQUEST.get("id", None)
        auth_opus = AuthOpus.objects.get(id=opus_id)
    except:
        return HttpResponse(u"参数错误")
    
    if auth_opus.library <> request.user.library:
        return HttpResponse(u"没有权限")
    
    return HttpResponse(json.dumps({"title":auth_opus.title, "tags":auth_opus.tags, "brief":auth_opus.brief, "user_id":auth_opus.user_id}))

@manager_required
def opus_gallery(request):
    return render(request, "manager/opus_gallery.html")

@manager_required
def opus_detail(request):
    return render(request, "manager/opus_detail.html")
    
@manager_required    
def audit_opus(request):
    try:
        opus_id = request.REQUEST.get("id", None)
        auth_opus = AuthOpus.objects.get(id=opus_id)
        status = int(request.REQUEST["status"])
    except:
        return HttpResponse(u"参数错误")
    
    if auth_opus.library <> request.user.library:
        return HttpResponse(u"没有权限")
    
    if status not in (-1, 0, 1):
        return HttpResponse(u"参数错误2")
    
    if status in (-1,2) and auth_opus.status <> 1:
        return HttpResponse(u"作品不是待审核状态")
    if status == 0 and auth_opus.status <> 2:
        return HttpResponse(u"作品不是已发表状态")
    
    #发个人消息
    auth_message = AuthMessage()
    auth_message.user_id = auth_opus.user_id
    auth_message.from_user_id = request.user.id
    auth_message.opus_id = auth_opus.id
    if status == -1:    #审核不通过
        action_name = u"审核不通过"
        auth_message.msg_type = 2   #审核不通过
        auth_message.content = u"很遗憾，你的作品[%s]未通过审核" % auth_opus.title
        auth_opus.status = -1
    elif status == 1:
        action_name = u"审核通过"
        auth_message.msg_type = 1   #作品发表消息
        auth_message.content = u"恭喜，你的作品[%s]发表了！" % auth_opus.title
        auth_opus.status = 2    #发表状态
    elif status == 0:
        action_name = u"转为草稿"
        auth_message.msg_type = 5   #作品转为草稿
        auth_message.content = u"注意，你的作品[%s]转为草稿状态了，请重新编辑后再发表！" % auth_opus.title
        auth_opus.status = 0    #草稿状态
    auth_message.save()
    auth_opus.update_time = datetime.now()
    auth_opus.save()
    
    #记录日志
    add_manager_action_log(request, u'%s把作品[%s](%s)了' % (request.user, auth_opus.title, action_name))
    return HttpResponse("ok")


@manager_required    
def top_opus(request):
    try:
        opus_id = request.REQUEST.get("id", None)
        auth_opus = AuthOpus.objects.get(id=opus_id)
        is_top = int(request.REQUEST["is_top"])
    except:
        return HttpResponse(u"参数错误")
    
    if auth_opus.library <> request.user.library:
        return HttpResponse(u"没有权限")
    
    if is_top not in (0, 1):
        return HttpResponse(u"参数错误2")
    
    if auth_opus.is_top == is_top:
        return HttpResponse(u"不需要修改")
    
    action_name = u"取消了置优"
    if is_top == 1: #作品被置优了
        #发个人消息
        action_name = u"置优了"
        auth_message = AuthMessage()
        auth_message.user_id = auth_opus.user_id
        auth_message.from_user_id = request.user.id
        auth_message.opus_id = auth_opus.id
        auth_message.msg_type = 1   #作品发表消息
        auth_message.content = u"恭喜，你的作品[%s]被评为优秀作品！" % auth_opus.title
        auth_message.save()
    auth_opus.update_time = datetime.now()
    auth_opus.is_top = is_top
    auth_opus.save()
    
    #记录日志
    add_manager_action_log(request, u'%s把作品[%s](%s)了' % (request.user, auth_opus.title, action_name))
    return HttpResponse(auth_opus.is_top)


@manager_required
def template_list(request):
    if request.method == "GET":
        return render(request, "manager/template_list.html", {"index":2, "sub_index":4})
    elif request.method == "POST":
        page_index = int(request.POST.get('page_index', 1))
        page_size = int(request.POST.get('page_size', 15))
        
        where_clause = "res_type=4 and status=1"
        if request.user.library_id:
            where_clause += " and library_id=%d" % request.user.library_id
        else:
            where_clause += " and library_id is null"
            
        type_id = int(request.REQUEST.get('type_id', 0))
        class_id = int(request.REQUEST.get('class_id', 0))
        search_text = request.REQUEST.get('search_text', None)
        if type_id:
            where_clause += " and type_id=%d" % type_id
        if class_id:
            where_clause += " and class_id=%d" % class_id
        if search_text:
            where_clause += " and res_title like '%%%s%%'" % search_text
        print where_clause    
        
        cursor = connections[DB_READ_NAME].cursor()
        sql = "select count(*) from zone_asset  where %s" % where_clause
        cursor.execute(sql)
        row = cursor.fetchone()
        count = 0
        if row: count = row[0]
        page_count = int(ceil(count/float(page_size)))
        
        sql = "select id,res_title,res_type,res_style,res_path,img_large_path,create_time,page_count,ref_times,type_id,class_id,create_type,read_type,width,height,size_id From zone_asset where %s order by create_time DESC LIMIT %s, %s" % (where_clause, (page_index-1)*page_size, page_size)
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        data_lists = []
        for row in rows:
            id = row[0]
            res_title = row[1]
            res_type_id = row[2]
            res_style_id = row[3]
            res_path = row[4] if row[4] else ""
            img_large_path = row[5] if row[5] else ""
            create_time = row[6]
            data_dict = {"id":id,"title":res_title,"res_type":res_type_id,"type_name":zone_res_type_name(res_type_id),"style_name":zone_res_style_name(res_style_id)}
            data_dict["res_path"] = res_path
            data_dict["url"] = MEDIA_URL + img_large_path if img_large_path else MEDIA_URL + res_path
            data_dict["create_time"] = create_time.strftime("%Y-%m-%d %H:%M:%S")
            data_dict["page_count"] = row[7]
            data_dict["ref_times"] = row[8]
            data_dict["type_id"] = row[9]
            data_dict["class_id"] = row[10]
            data_dict["type_name"] = opus_type_name(row[9])
            data_dict["class_name"] = opus_type_name(row[10])
            
            data_dict["create_type"] = row[11]
            data_dict["read_type"] = row[12]
            data_dict["create_name"] = opus_page_type_name(row[11])
            data_dict["read_name"] = opus_page_type_name(row[12])
            data_dict["width"] = row[13]
            data_dict["height"] = row[14]
            data_dict["size_id"] = row[15]
            data_lists.append(data_dict)
        cursor.close()
        return HttpResponse(json.dumps({"data":data_lists, "page_index": page_index, "page_count": page_count}))


@manager_required    
def template(request):
    zone_asset = get_zone_asset(request.REQUEST.get('id', None))[2]
    if not zone_asset: return HttpResponse(FailResponse(u"不存在的模板"))
    
    if request.method == "GET":
        return render(request, "manager/template.html", {"index":2, "sub_index":4, "asset":zone_asset})
    elif request.method == "POST":
        page_index = int(request.POST.get('page_index', 1))
        page_size = int(request.POST.get('page_size', 15))
        
        cursor = connections[DB_READ_NAME].cursor()
        where_clause = "zone_asset_id=%d" % zone_asset.id
        sql = "select count(*) from zone_asset_template where %s" % where_clause
        cursor.execute(sql)
        row = cursor.fetchone()
        count = 0
        if row: count = row[0]
        page_count = int(ceil(count/float(page_size)))
        
        sql = "select id,page_index,json_path,img_path,ref_times,create_time From zone_asset_template where %s order by page_index DESC LIMIT %s, %s" % (where_clause, (page_index-1)*page_size, page_size)
        print sql
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        data_lists = []
        for row in rows:
            data_dict = {}
            data_dict["id"] = row[0]
            data_dict["page_index"] = row[1]
            data_dict["json_path"] = request.build_absolute_uri(MEDIA_URL + row[2])
            data_dict["img_path"] = request.build_absolute_uri(MEDIA_URL + row[3])
            data_dict["ref_times"] = row[4]
            data_dict["create_time"] = row[5].strftime("%Y-%m-%d %H:%M:%S")
            data_lists.append(data_dict)
        cursor.close()
        return HttpResponse(SuccessResponse({"data":data_lists, "page_index": page_index, "page_count": page_count}))


@manager_required    
def template_page(request):
    zone_asset = get_zone_asset(request.REQUEST.get('id', None))[2]
    if not zone_asset: return HttpResponse(u"不存在的模板")
    
    if zone_asset.library <> request.user.library:
        return HttpResponse(u"没有权限")
    
    page_index = int(request.GET.get('page_index', 0))
    
    flag = "edit"
    templaete = None
    if page_index == 0:
        page_index = zone_asset.page_count + 1
        flag = "new"    #新建页
    elif page_index > zone_asset.page_count or page_index <=0:
        return HttpResponse(u"不存在的模板页码")
    else:
        try: templaete = ZoneAssetTemplate.objects.get(zone_asset_id=zone_asset.id, page_index=page_index)
        except(ZoneAssetTemplate.DoesNotExist): return HttpResponse(u"不存在的模板页码")
        
    if request.method == "GET":
        return render(request, "manager/template_page.html", {"index":2, "sub_index":4, "asset":zone_asset, "templaete":templaete, "flag":flag, "page_index":page_index})
    elif request.method == "POST":
        json_data = request.POST["json"]
        json_data = json_data.encode('utf=8')
        #print type(json_data)
        try: json.loads(json_data)
        except: return HttpResponse(u"非法的json文件")
        
        if not templaete:
            templaete = ZoneAssetTemplate()   #新建模板页
            templaete.zone_asset = zone_asset
            templaete.page_index = page_index
        res_type = 4    #模板
        #保存json文件
        json_path = "%s/%d/%d.json" % (get_asset_path(request, res_type), zone_asset.id, page_index)
        res_absdir =  os.path.join(MEDIA_ROOT, "assets/%d/%d" % (res_type, zone_asset.id))
        if not os.path.exists(res_absdir):
            os.makedirs(res_absdir)
            
        f = open(os.path.join(MEDIA_ROOT, json_path), "wb")
        f.write(json_data)
        f.close()
        templaete.json = json_data
        templaete.json_path = json_path
        #保存图片文件
        res_path = hid_res_path = request.POST["hid_res_path"]
        if hid_res_path.find("temp") >= 0:
            ext = os.path.splitext(hid_res_path)[1]
            
            res_path = "%s/%d/%d%s" % (get_asset_path(request, res_type), zone_asset.id, page_index, ext)
            #res_abspath =  os.path.join(MEDIA_ROOT, res_path)
            
            open(os.path.join(MEDIA_ROOT, res_path), "wb").write(open(os.path.join(MEDIA_ROOT, hid_res_path), "rb").read())
            os.remove(os.path.join(MEDIA_ROOT, hid_res_path))
            
            from PIL import Image
            img = Image.open(os.path.join(MEDIA_ROOT, res_path))
            img_small_path = get_tile_image_name(res_path, 's')
            img.thumbnail(get_small_size(img.size[0], img.size[1]), Image.ANTIALIAS)
            img.save(os.path.join(MEDIA_ROOT, img_small_path))

            templaete.img_path = res_path
            templaete.img_small_path = img_small_path
        templaete.update_time = datetime.now()
        templaete.save()
        if flag == "new":
            zone_asset.page_count += 1
            zone_asset.save()
        
        #记录日志
        action_name = u"新增"
        if flag == "edit": action_name = u"修改"
        add_manager_action_log(request, u'%s%s了模板[%s]的第(%s)页' % (request.user, action_name, zone_asset.res_title, templaete.page_index))
        return render(request, "manager/template_page.html", {"result":"ok", "index":2, "sub_index":4, "asset":zone_asset})
                

from django.core.cache import cache            
@manager_required    
def delete_template_page(request):
    if cache.get("delete_template_page", None):
        return HttpResponse(request.session["delete_template_page"])
    
    cache.set("delete_template_page", "正在删除模板页", 60)
    try:
        template_page_id = int(request.REQUEST["id"])
        templaete_page = ZoneAssetTemplate.objects.get(id=template_page_id)
    except:
        return HttpResponse(u"参数错误")
    zone_asset = templaete_page.zone_asset
    page_index = templaete_page.page_index
    cache.set("delete_template_page", u"正在删除模板(%s)第%d页" % (zone_asset.res_title, page_index), 60)
    
    if zone_asset.library <> request.user.library:
        return HttpResponse(u"没有权限")

    if os.path.isfile(os.path.join(MEDIA_ROOT, templaete_page.json_path)): os.remove(os.path.join(MEDIA_ROOT, templaete_page.json_path))
    if os.path.isfile(os.path.join(MEDIA_ROOT, templaete_page.img_path)): os.remove(os.path.join(MEDIA_ROOT, templaete_page.img_path))
    if os.path.isfile(os.path.join(MEDIA_ROOT, templaete_page.img_small_path)): os.remove(os.path.join(MEDIA_ROOT, templaete_page.img_small_path))
    
    cur_index = page_index + 1
    last_template_page = templaete_page
    while cur_index <= zone_asset.page_count:
        try: cur_template = ZoneAssetTemplate.objects.get(zone_asset_id=zone_asset.id, page_index=cur_index)
        except(ZoneAssetTemplate.DoesNotExist): continue

        if os.path.isfile(os.path.join(MEDIA_ROOT, cur_template.json_path)):
            os.rename(os.path.join(MEDIA_ROOT, cur_template.json_path), os.path.join(MEDIA_ROOT, last_template_page.json_path))
        if os.path.isfile(os.path.join(MEDIA_ROOT, cur_template.img_path)):
            os.rename(os.path.join(MEDIA_ROOT, cur_template.img_path), os.path.join(MEDIA_ROOT, last_template_page.img_path))
        if os.path.isfile(os.path.join(MEDIA_ROOT, cur_template.img_small_path)):
            os.rename(os.path.join(MEDIA_ROOT, cur_template.img_small_path), os.path.join(MEDIA_ROOT, last_template_page.img_small_path))
        cur_template.page_index = cur_index - 1
        cur_template.json_path = last_template_page.json_path
        cur_template.img_path = last_template_page.img_path
        cur_template.img_small_path = last_template_page.img_small_path
        cur_template.update_time = datetime.now()
        cur_template.save()
        cur_index += 1
        last_template_page = cur_template
    
    templaete_page.delete()
    zone_asset.page_count -= 1
    zone_asset.save()
    
    cache.delete("delete_template_page")
    #记录日志
    add_manager_action_log(request, u'%s删除了模板[%s]的第(%s)页' % (request.user, zone_asset.res_title, page_index))
    return HttpResponse("ok")


from utils.decorator import print_trace
@manager_required
@print_trace
def apply_for_template(request):
    """
        已发表的作品，申请成为模板，只有管理员才有此权限
    """
    from PIL import Image
    opus_id = request.POST.get('opus_id',0)
    opus_id = int(opus_id)
    try: auth_opus = AuthOpus.objects.get(id=opus_id)
    except(AuthOpus.DoesNotExist): return HttpResponse(FailResponse(u"不存在的作品ID:%d" % opus_id))

    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponse(FailResponse(u"只有管理员才能申请作品转为模板"))

    #2014-08-19    管理员可以把所有已发表作品转为模板
#     if auth_opus.user_id <> request.user.id:
#         return HttpResponse(FailResponse(u"不是自己的作品"))

    if auth_opus.status <> 2:
        return HttpResponse(FailResponse(u"只有已发表作品，才能申请转为模板"))

    if ZoneAsset.objects.filter(res_type=4, opus_id=auth_opus.id, status__gte=0).count() > 0:
        return HttpResponse(FailResponse(u"已经转为模板过，如果需要重新转换，请先把旧的模板删除"))

    if cache.get("opus:%s" % request.user.id, None):
        return HttpResponse(FailResponse(cache.get("opus:%s" % request.user.id)))
    cache.set("opus:%s" % request.user.id, u"正在把作品[%s]转为模板，请稍候[%s]" % (auth_opus.title, datetime.now().strftime("%Y-%m-%d %H:%M:%S")), 60)
    # 导入作品转模板的方法
    from diy.handler import opus_to_template
    opus_to_template(opus_id, request.user)
    cache.delete("opus:%s" % request.user.id)
    #记录日志
    log_content = u'%s把作品:[%s]转为了模板' % (request.user.username, auth_opus.title)
    add_manager_action_log(request, log_content)
    return HttpResponse(SuccessResponse({"opus_id":opus_id,"msg":u"作品:%s申请转为模板成功，请在模板列表查看修改!" % auth_opus.title}))

@manager_required
def opus2template(request):
    if request.method == "GET":
        return render(request, "manager/opus2template.html")
    
    #2014-08-19    管理员可以把所有已发表作品转为模板
    #只有后台的超级管理员有权限把所有平台的作品，转为模板
    if request.user.library:
        return HttpResponse(u"只有总后台的管理权，才有权限把作品转为模板")
    
    page_index = int(request.REQUEST.get('page_index',1))
    page_size = 15
    lib_id = int(request.REQUEST.get('lib_id', 0))
    search_text = request.REQUEST.get('search_text',"")
    
    where_clause = "status=2"
    if lib_id: where_clause += " and library_id=%d" % lib_id
    if search_text: where_clause += " and title like '%%%s%%'" % search_text
    
    cursor = connections[DB_READ_NAME].cursor()
    sql = "select count(*) from auth_opus where %s" % where_clause
    print sql
    cursor.execute(sql)
    row = cursor.fetchone()
    count = 0
    if row: count = row[0]
    page_count = int(ceil(count/float(page_size)))
    
    sql = "select id,user_id,library_id,title,type_id,class_id,page_count,update_time from auth_opus where %s order by update_time DESC LIMIT %s, %s" % (where_clause, (page_index-1)*page_size, page_size)
    print sql
    cursor.execute(sql)
    rows = cursor.fetchall()
    
    data_list = []
    for row in rows:
        data_dict = {}
        data_dict["id"] = row[0]
        data_dict["username"] = get_username(row[1])
        data_dict["lib_name"] = library_name(row[2])
        data_dict["title"] = row[3] if row[3] else ""
        data_dict["type_name"] = opus_type_name(row[4])
        data_dict["class_name"] = opus_type_name(row[5])
        data_dict["page_count"] = row[6]
        data_dict["update_time"] = row[7].strftime("%Y-%m-%d %H:%M:%S")
        data_dict["url"] = opus_cover_url(row[0])
        data_list.append(data_dict)
    cursor.close()
        
    return HttpResponse(json.dumps({"data":data_list, "page_index": page_index, "page_count": page_count}))

def library_name(lib_id):
    if lib_id:
        try:
            library = Library.objects.get(id=lib_id)
            return library.lib_name
        except: return u"公共图书馆"
    return u"公共图书馆"

def get_username(uid):
    if uid:
        try:
            user = AuthUser.objects.get(id=uid)
            return user.username
        except: return ""
    return ""

def opus_cover_url(opus_id):
    try: auth_opus = AuthOpus.objects.get(id=opus_id)
    except: return ""
    if auth_opus.cover and len(auth_opus.cover)>0:
        return MEDIA_URL + auth_opus.cover
    auth_opus_page = AuthOpusPage.objects.get(auth_opus_id=opus_id, page_index=1)
    return MEDIA_URL + auth_opus_page.img_path


@manager_required
def private_asset_detail(request,id):
    from WebZone.conf import PERSONAL_RES_TYPE_CHOICES,AUTH_MSG_STATUS
    asset_id = id
    try:
        asset_id = int(id)
    except:
        return HttpResponseRedirect("/manager/mis/c_private_asset/")
    from diy.models import  AuthAsset
    try:
        asset = AuthAsset.objects.filter(id = asset_id)[0]
    except IndexError:
        asset=""



    return render(request,"manager/private_asset_details.html",{'asset':asset,'res_type_list':PERSONAL_RES_TYPE_CHOICES,'asset_msg_type':AUTH_MSG_STATUS})



from utils.decorator import print_trace
@print_trace
@manager_required
def gas_list(request):
    if request.method == "GET":
        return render(request, "manager/gas_list.html", {"index":1, "sub_index":3})
    elif request.method == "POST":
        try:
            id = int(request.REQUEST['hid_id'])
            content = request.REQUEST["content"]
        except:
            traceback.print_exc()
            return HttpResponse(FailResponse(u"参数错误"))
        
        if id:
            try: widget_gas = WidgetGas.objects.get(id=id)
            except(WidgetGas.DoesNotExist): return HttpResponse(FailResponse(u"加油ID不正确"))
        else:
            widget_gas = WidgetGas()
        widget_gas.content = content
        widget_gas.update_time = datetime.now()
        widget_gas.save()
        
        #记录日志
        add_manager_action_log(request, u'%s新建/更新了加油站短文：[%s]' % (request.user, widget_gas.id))
        return HttpResponse(SuccessResponse("ok"))


@manager_required
def get_gas_list(request):
    try:
        page_index = int(request.REQUEST.get("page_index", 1))
        page_size = int(request.REQUEST.get("page_size", 15))
        search_text = request.REQUEST.get("search_text", "")
    except:
        return HttpResponse(u"参数错误")
    
    cursor = connections[DB_READ_NAME].cursor()
    sql = "select count(*) from widget_gas"
    if search_text:
        sql = "select count(*) from widget_gas where content like '%%%s%%'" % search_text
    cursor.execute(sql)
    row = cursor.fetchone()
    count = int(row[0]) if row and row[0] else 0
    page_count = int(ceil(count/float(page_size)))
    
    sql = "select id,type_id,content,view_times,update_time from widget_gas order by update_time DESC LIMIT %s, %s" % ((page_index-1)*page_size, page_size)
    if search_text:
        sql = "select id,type_id,content,view_times,update_time from widget_gas where content like '%%%s%%' order by update_time DESC LIMIT %s, %s" % (search_text, (page_index-1)*page_size, page_size)
    #print sql
    cursor.execute(sql)
    rows = cursor.fetchall()
    
    data_lists = []
    for row in rows:
        data_dict = {}
        data_dict["id"] = row[0]
        data_dict["type_id"] = row[1]
        data_dict["content"] = row[2]
        data_dict["view_times"] = row[3]
        data_dict["update_time"] = row[4].strftime("%Y-%m-%d %H:%M:%S")
        data_lists.append(data_dict)
    cursor.close()
    return HttpResponse(json.dumps({"data":data_lists, "page_index": page_index, "page_count": page_count}))

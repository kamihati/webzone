#coding: utf-8
'''
Created on 2014-7-23

@author: Administrator
'''
import os
import json
from datetime import datetime
from math import ceil

from django.shortcuts import render
from django.http import HttpResponse
from django.core.cache import cache

from django.db import connection, connections
from WebZone.settings import MEDIA_URL, MEDIA_ROOT

from manager import has_permissions

from utils import get_ip
from account.models import AuthUser
from manager.models import ManagerUserGroup
from manager.models import ManagerAuthGroup

from manager import add_manager_action_log
from library.models import Library
from diy.models import ZoneAsset

from manager.views import get_asset_path

from utils.decorator import print_trace
from gateway import FailResponse, SuccessResponse
from WebZone.settings import DB_READ_NAME


@print_trace
def s_role_m(request):
    '''角色管理'''
    if request.method == "GET":
        from manager import get_perms_json
        return render(request, "manager/mis/s_role_m.html", {"znodes":get_perms_json(request)})
    else:
        try:
            hid_role_id = int(request.POST["hid_role_id"])
            role_name = request.POST["role_name"]
            remark = request.POST["remark"]
            role_list = request.REQUEST["role_list"]
        except:
            #traceback.print_exc()
            return HttpResponse(u"参数错误")
        
        if hid_role_id:
            try: manager_auth_group = ManagerAuthGroup.objects.get(id=hid_role_id)
            except: return HttpResponse(u"不存在的角色ID:%d" % hid_role_id)
        else:
            manager_auth_group = ManagerAuthGroup()
            
        manager_auth_group.name = role_name
        manager_auth_group.remark = remark
        manager_auth_group.perms = update_role_list(role_list)
        manager_auth_group.save()
        return HttpResponse("ok")

def update_role_list(role_list):
    print role_list
    from manager import MANAGER_PERMS
    def is_role_exist(r):
        for perm in MANAGER_PERMS:
            if perm['code'] == r:
                return True
        return False
    role_list = role_list.split(',')
    pure_list = ""
    for role in role_list:
        if is_role_exist(role):
            pure_list += ',' + role if len(pure_list)>0 else role
    print pure_list
    return pure_list

def get_role_list(request):
    '''得到所有角色/权限列表'''
    role_list = []
    for item in ManagerAuthGroup.objects.all():
        role_item = {"id":item.id, "name":item.name, "perms":item.perms, "remark":item.remark}
        role_list.append(role_item)
    return HttpResponse(json.dumps(role_list))

def can_role_list(request):
    '''只返回自己权限的子集的角色的列表，总后台管理员需要去掉'''
    role_list = []
    if request.user.library:
        try:
            manager_auth_group = ManagerUserGroup.objects.get(user=request.user).group
        except:
            return HttpResponse(json.dumps(role_list))
            
        for item in ManagerAuthGroup.objects.all():
            if u"总后台" in item.name: continue    #去掉总后台
            if manager_auth_group.id == item.id: continue   #去掉自己的权限
            if is_sub_role(manager_auth_group, item):
                role_item = {"id":item.id, "name":item.name, "perms":item.perms, "remark":item.remark}
                role_list.append(role_item)
    else:
        for item in ManagerAuthGroup.objects.all():
            role_item = {"id":item.id, "name":item.name, "perms":item.perms, "remark":item.remark}
            role_list.append(role_item)
    return HttpResponse(json.dumps(role_list))

def is_sub_role(parent_role, child_role):
    '''
        判断子角色是不是父角色的完全子集
    '''
    perm_list = parent_role.perms.split(',')
    child_perm_list = child_role.perms.split(',')
    for perm in child_perm_list:
        if perm not in perm_list:
            return False
    return True
    

def s_auth_m(request):
    '''权限管理'''
    if request.method == "GET":
        return render(request, "manager/mis/s_auth_m.html")
    elif request.method == "POST":
        try:
            page_index = int(request.REQUEST.get("page_index", 1))
            page_size = int(request.REQUEST.get("page_size", 15))
            search_text = request.REQUEST.get("search_text", "").strip()
        except:
            return HttpResponse(u"参数错误")
        
        cursor = connections[DB_READ_NAME].cursor()
        sql = "select count(*) from manager_user_group ug"
        if search_text:
            sql += " LEFT JOIN auth_user u on u.id=ug.user_id where u.username like '%%%s%%'" % search_text
        cursor.execute(sql)
        row = cursor.fetchone()
        count = int(row[0]) if row and row[0] else 0
        page_count = int(ceil(count/float(page_size)))
        
        sql = "select u.id,u.username,u.library_id,l.lib_name,g.`name`,u.last_login,u.last_ip,u.is_active,u.nickname,u.realname,u.telephone,g.id from manager_user_group ug"
        sql += " LEFT JOIN auth_user u on u.id=ug.user_id"
        sql += " LEFT JOIN manager_auth_group g on g.id=ug.group_id"
        sql += " LEFT JOIN library l on l.id=u.library_id"
        sql += " LIMIT %s,%s" % ((page_index-1)*page_size, page_size)
        if request.user.library:
            sql += " where u.library_id=%d" % request.user.library_id
            if search_text: sql += " and u.username like '%%%s%%'" % search_text
        else:
            if search_text: sql += " where u.username like '%%%s%%'" % search_text
        
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        data_lists = []
        for row in rows:
            data_dict = {}
            data_dict["uid"] = row[0]
            data_dict["username"] = row[1]
            data_dict["lib_id"] = row[2] if row[2] else 0
            data_dict["lib_name"] = row[3] if row[3] else u"总后台"
            data_dict["g_name"] = row[4]
            data_dict["last_login"] = row[5].strftime("%Y-%m-%d %H:%M:%S")
            data_dict["last_ip"] = row[6]
            data_dict["is_active"] = row[7]
            data_dict["nickname"] = row[8]
            data_dict["realname"] = row[9] if row[9] else ""
            data_dict["telephone"] = row[10] if row[10] else ""
            data_dict["gid"] = row[11]
            data_lists.append(data_dict)
        cursor.close()
        return HttpResponse(json.dumps({"data":data_lists, "page_index": page_index, "page_count": page_count}))

@print_trace
def s_auth_a(request):
    '''添加、修改管理员信息'''
    if request.method <> "POST":
        return HttpResponse(u"非法请求")
    
    try:
        hid_id = int(request.POST["hid_id"])    #用户ＩＤ
        
        username = request.POST["username"].lower().strip()
        nickname = request.POST["nickname"].strip()
        realname = request.POST["realname"].strip()
        telephone = request.POST["telephone"].strip()
        password = request.POST["password"]
        
        lib_id = int(request.POST["lib_id"])
        role_id = int(request.POST["role_id"])
    except:
        import traceback
        traceback.print_exc()
        return HttpResponse(u"参数错误")
    
    library = None
    if lib_id:
        try: library = Library.objects.get(id=lib_id)
        except: return HttpResponse(u"图书馆ID不存在")
        
    try:
        manager_auth_group = ManagerAuthGroup.objects.get(id=role_id)
    except:
        return HttpResponse(u"角色ID不存在")
    
    if hid_id:
        try:
            auth_user = AuthUser.objects.get(id=hid_id)
        except:
            return HttpResponse(u"修改的用户ID不存在")
        auth_user.realname = realname
        auth_user.telephone = telephone
        auth_user.save()
        manager_user_group = ManagerUserGroup.objects.get(user=auth_user)
        manager_user_group.group_id = manager_auth_group.id
        manager_user_group.save()
    else:
        auth_user = AuthUser()
        if library:
            auth_user.library = library
        auth_user.username = username
        auth_user.nickname = nickname
        auth_user.realname = realname
        auth_user.telephone = telephone
        
        auth_user.set_password(password)
        auth_user.reg_ip = get_ip(request)
        auth_user.last_ip = auth_user.reg_ip
        auth_user.last_login = datetime.now()
        
        #auth_user.auth_type = 2  #图书馆管理员
        auth_user.is_staff = 1  #管理员
        auth_user.save()
        
        #用户加入角色组
        manager_user_group = ManagerUserGroup()
        manager_user_group.user = auth_user
        manager_user_group.group_id = manager_auth_group.id
        manager_user_group.save()
    
    return HttpResponse('ok')
        

def s_auth_pass(request):
    '''
        修改管理员、下属管理员的密码，随机生成6位数字
    '''
    try:
        uid = int(request.REQUEST["uid"])
    except:
        return HttpResponse(u"参数错误")
    
    try: auth_user = AuthUser.objects.get(id=uid)
    except: return HttpResponse(u"用户不存在")
    
    if request.user.library:
        if request.user.library <> auth_user.library:
            return HttpResponse(u"没有权限")
    
    import string
    chars = string.digits
    from random import choice
    newpass = ''.join([choice(chars) for _ in range(6)])
    auth_user.set_password(newpass)
    auth_user.save()
    
    #记录日志
    log_content = u'%s重置了管理员[%s]的密码' % (request.user.username, auth_user.username)
    add_manager_action_log(request, log_content)

    return HttpResponse(u"密码修改成功，新密码为:%s，请登录后修改" % newpass)        
    
def s_log_user(request):
    '''用户日志'''

    if request.method == "GET":
        return render(request, "manager/mis/s_log_user.html")
    elif request.method == "POST":
        try:
            page_index = int(request.REQUEST.get("page_index", 1))
            page_size = int(request.REQUEST.get("page_size", 15))
            #action_name = request.REQUEST.get("username", request.user.username)

        except:
            return HttpResponse(u"参数错误")
        search_text = request.REQUEST.get('search_text',"")
        search_type = request.REQUEST.get('search_type',"1")
        if search_type ==  '1':
            search_type = 'username'
        else:
            search_type = 'ip'


        if request.user.library_id:
            if search_text != "":
                where_clause = "library_id=%d and %s = '%s'" % (request.user.library_id,search_type,search_text)
            else:
                where_clause = "library_id=%d" % request.user.library_id
        else:
            if search_text != "":
                where_clause = "library_id is null and %s = '%s'" % (search_type,search_text)
            else:
                where_clause = "library_id is null"


        cursor = connections[DB_READ_NAME].cursor()
        sql = "select count(*) from auth_action_log where %s" % where_clause
        cursor.execute(sql)
        row = cursor.fetchone()
        count = int(row[0]) if row and row[0] else 0
        page_count = int(ceil(count/float(page_size)))
        
        sql = "select id,username,content,ip,user_agent,referer,action_time,remark from auth_action_log where %s order by action_time DESC LIMIT %s, %s" % (where_clause, (page_index-1)*page_size, page_size)
        print sql
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        data_lists = []
        for row in rows:
            data_dict = {}
            data_dict["id"] = row[0]
            data_dict["username"] = row[1]
            data_dict["content"] = row[2]
            data_dict["ip"] = row[3]
            #data_dict["user_agent"] = row[4]
            #data_dict["referer"] = row[5]
            data_dict["platform"] = get_platform_info(row[4], row[5])
            data_dict["action_time"] = row[6].strftime("%Y-%m-%d %H:%M:%S")
            data_lists.append(data_dict)
        cursor.close()
        return HttpResponse(json.dumps({"data":data_lists, "page_index": page_index, "page_count": page_count}))

def get_platform_info(user_agent, referer):
    if referer[:4] == 'app:' and referer[-4:] == '.swf':
        return u"云汇客户端"
    elif "Macintosh" in user_agent:
        return "Mac OS"
    elif "Windows NT 5.0" in user_agent:
        return "Windows 2000"
    elif "Windows NT 5.1" in user_agent:
        return "Windows XP"
    elif "Windows NT 5.2" in user_agent:
        return "Windows 2003"
    elif "Windows NT 6.0" in user_agent:
        return "Windows Vista"
    elif "Windows NT 6.1" in user_agent:
        return "Windows 7"
    else:
        return u"待定"

def s_log_manager(request):
    '''管理员日志'''
    if not request.user.library_id:
        super_admin = True
    else:
        super_admin = True
    if request.method == "GET":
        return render(request, "manager/mis/s_log_manager.html",{'is_super_admin':super_admin})
    elif request.method == "POST":
        try:
            page_index = int(request.REQUEST.get("page_index", 1))
            page_size = int(request.REQUEST.get("page_size", 15))
            search_text = request.REQUEST.get('search_text',"")
            search_type = request.REQUEST.get("search_type","1")


            #action_name = request.REQUEST.get("username", request.user.username)
        except ValueError:
            return HttpResponse(u"参数错误")
        if search_type == '1':
            search_type =  'username'
        else:
            search_type = 'ip'
        if request.user.library_id:
            where_clause = "library_id=%d" % request.user.library_id
        else:
            where_clause = "library_id is null"
        if search_text != "":
            where_clause += " and %s = '%s'" % (search_type,search_text)

        cursor = connections[DB_READ_NAME].cursor()
        sql = "select count(*) from manager_action_log where %s" % where_clause
        cursor.execute(sql)
        row = cursor.fetchone()
        count = int(row[0]) if row and row[0] else 0
        page_count = int(ceil(count/float(page_size)))
        
        sql = "select id,username,content,ip,action_time,remark from manager_action_log where %s order by action_time DESC LIMIT %s, %s" % (where_clause, (page_index-1)*page_size, page_size)
        print sql
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

def s_msg_sys(request):
    '''系统消息'''
    from django.db.models import Q
    from WebZone.conf import AUTH_MSG_TYPE
    from account.models import AuthMessage
    msg_type = request.REQUEST.get('type',1)
    search_text = request.REQUEST.get("search_text","")
    search_type = request.REQUEST.get("search_type","1")


    query = Q(msg_type=msg_type)
    if not request.user.library_id :
        message_list = AuthMessage.objects.filter(query).order_by('-create_time')
    else:
        message_list =  AuthMessage.objects.filter(query).order_by("-create_time")
        message_list = [x for x in message_list if x.user.library_id == request.user.library_id]

    if search_text != "":
        if search_type == "1":
            message_list = [x for x in message_list if x.opus.title == search_text]

        else :
            message_list = [x for x in message_list if x.user.username == search_text]
    comment_account =len(message_list)
    content_num = 15

    index_num = 12
    page_f_num = index_num/2
    page_n_num = index_num-page_f_num
    page_account = int((comment_account+content_num-1)/content_num)
    page = request.REQUEST.get('page',1)
    try :
        msg_type = int(msg_type)
        page = int(page)
    except ValueError:
        page = 1
    if page> page_account:
        page = page_account
    if page_account <= 0:
        page = 1
    if page == 0:
        page = 1
    page_list = []
    page_list.append(page)
    page_f_add = 0
    page_n_add = 0
    for x in range(1,page_f_num+1):
        temp = page-x
        if temp >= 1:
            page_list.append(temp)
        else:
            page_n_add +=1

    page_list.reverse()

    for x in range(1,page_n_num):
        temp = page+x
        if temp <= page_account:
            page_list.append(temp)
        else:
            page_f_add += 1

    for x in range(page_f_num+1,page_f_num+page_f_add+1):
        temp = page-x
        if temp >= 1:
            page_list.insert(0,temp)


    for x in range(page_n_num,page_n_num+page_n_add):
        temp = page+x
        if temp <= page_account:
            page_list.append(temp)

    if page<page_account:
        comment_list =message_list[(page-1)*content_num:(page-1)*content_num+content_num]
    else:
        comment_list = message_list[(page-1)*content_num:]
    return render(request, "manager/mis/s_msg_sys.html",{'content_list':comment_list,'page':page,'page_f':page-1,'page_n':page+1,'page_list':page_list,'msg_type_list':AUTH_MSG_TYPE,
                                                         'msg_t':msg_type,'search_text':search_text,'search_type':search_type})

def s_opus_c(request):
    '''作品评论'''
    from diy.models import  AuthOpusComment
    from django.db.models import Q
    search_text = request.REQUEST.get('search_text',"")
    search_type = request.REQUEST.get('search_type',"1")

    select_id = None
    query_type = Q()
    search_col = None
    db = None
    if search_text != "":
        if search_type == "1":
            global  db
            db = AuthUser
            search_col = Q(username = search_text)

        else :
            from diy.models import AuthOpus
            global  db
            db = AuthOpus
            search_col = Q(title = search_text)
        try:
            global select_id
            select_id = db.objects.filter(search_col)[0]
        except IndexError:
            return render(request, "manager/mis/s_opus_c.html",{'comment':[],'page':1,'page_list':[1],'page_f':0,'page_n':2,'search_type':search_type,'search_text':search_text})
        if search_type == "1":
            query_type = Q(user = select_id.id)
        else:
            query_type = Q(auth_opus = select_id.id)


    if (not request.user.library_id):
        query = Q()&query_type
    else:
        query = Q(library_id =request.user.library_id)&query_type

    comment_account = AuthOpusComment.objects.filter(query).count()
    content_num = 15
    index_num = 12
    page_f_num = index_num/2
    page_n_num = index_num-page_f_num
    page_account = int((comment_account+content_num-1)/content_num)
    page = request.REQUEST.get('page',1)
    try :
        page = int(page)
    except ValueError:
        page = 1
    if page> page_account:
        page = page_account
    if page_account <= 0:
        page = 1
    if page == 0:
        page = 1
    page_list = []
    page_list.append(page)
    page_f_add = 0
    page_n_add = 0
    for x in range(1,page_f_num+1):
        temp = page-x
        if temp >= 1:
            page_list.append(temp)
        else:
            page_n_add +=1

    page_list.reverse()

    for x in range(1,page_n_num):
        temp = page+x
        if temp <= page_account:
            page_list.append(temp)
        else:
            page_f_add += 1

    for x in range(page_f_num+1,page_f_num+page_f_add+1):
        temp = page-x
        if temp >= 1:
            page_list.insert(0,temp)


    for x in range(page_n_num,page_n_num+page_n_add):
        temp = page+x
        if temp <= page_account:
            page_list.append(temp)

    if page<page_account:
        comment_list = AuthOpusComment.objects.filter(query).order_by("-create_time")[(page-1)*content_num:(page-1)*content_num+content_num]
    else:
        comment_list = AuthOpusComment.objects.filter(query).order_by("-create_time")[(page-1)*content_num:]

    return render(request, "manager/mis/s_opus_c.html",{'comment':comment_list,'page':page,'page_list':page_list,'page_f':page-1,'page_n':page+1,'search_type':search_type,'search_text':search_text})

def s_msg_friend(request):
    # '''好友留言'''
    return render(request, "manager/mis/s_msg_friend.html")



def l_invite_code(request):
    '''邀请码管理'''
    return render(request, "manager/mis/l_invite_code.html")

def l_ip_c(request):
    '''ip地址控制'''
    return render(request, "manager/mis/l_ip_c.html")


    

def c_private_asset(request):
    '''私有素材管理'''
    if not has_permissions(request, 'c_private_asset'): return HttpResponse(u'没有权限')
    from WebZone.conf import PERSONAL_RES_TYPE_CHOICES
    from diy.models import  AuthAsset
    from django.db.models import Q
    res_t = request.REQUEST.get('res_type',0)
    try:
        res_t = int(res_t)
    except ValueError:
        res_t = 0
    search_text = request.REQUEST.get("search_text","")
    query = Q()
    if (not request.user.library_id):
        if search_text != "":
            query = Q(res_title = search_text)
        else:
            query = Q()
    else:
        if search_text != "":
            query =  Q(library_id =request.user.library_id)&Q(res_title = search_text)
        else:
            query = Q(library_id =request.user.library_id)
    if res_t in [x[0] for x in PERSONAL_RES_TYPE_CHOICES]:
        query = query&Q(res_type = res_t)
    query = query&Q(codec_status = 1)
    comment_account = AuthAsset.objects.filter(query).count()
    content_num = 15
    index_num = 12
    page_f_num = index_num/2
    page_n_num = index_num-page_f_num
    page_account = int((comment_account+content_num-1)/content_num)
    page = request.REQUEST.get('page',1)
    try :
        page = int(page)
    except ValueError:
        page = 1
    if page> page_account:
        page = page_account
    if page_account <= 0:
        page = 1
    if page == 0:
        page = 1
    page_list = []
    page_list.append(page)
    page_f_add = 0
    page_n_add = 0
    for x in range(1,page_f_num+1):
        temp = page-x
        if temp >= 1:
            page_list.append(temp)
        else:
            page_n_add +=1

    page_list.reverse()

    for x in range(1,page_n_num):
        temp = page+x
        if temp <= page_account:
            page_list.append(temp)
        else:
            page_f_add += 1

    for x in range(page_f_num+1,page_f_num+page_f_add+1):
        temp = page-x
        if temp >= 1:
            page_list.insert(0,temp)


    for x in range(page_n_num,page_n_num+page_n_add):
        temp = page+x
        if temp <= page_account:
            page_list.append(temp)


    if page<page_account:
        asset_list = AuthAsset.objects.filter(query).order_by("-create_time")[(page-1)*content_num:(page-1)*content_num+content_num]
    else:
        asset_list = AuthAsset.objects.filter(query).order_by("-create_time")[(page-1)*content_num:]

    return render(request, "manager/mis/c_private_asset.html",{'asset_list':asset_list,'page':page,'page_list':page_list,'page_f':page-1,'page_n':page+1,'res_type_list':PERSONAL_RES_TYPE_CHOICES,'res_t':res_t,'search_text':search_text})




def get_res_json(res_type=1):
    '''
    generate json data for ztree control, 学习平台资源类型列表
    '''
    def update_tree_open():
        for key in res_dict.keys():
            if res_dict[key]['parent_id'] and res_dict[res_dict[key]['parent_id']]['parent_id']:
                id = res_dict[res_dict[key]['parent_id']]['parent_id']
                res_dict[id]['open'] = True
    from django.db import connections
    cursor = connections['KidsLibrarySystem'].cursor()
    sql = "select Res_Id,Res_Name,Res_Code,Res_Parent from Res_Class WHERE Res_MetaId=%s ORDER BY Res_Parent, Res_Id" % res_type
    print sql
    cursor.execute(sql)
    rows = cursor.fetchall()
    res_dict = {}
    for row in rows:
        if not row or not row[0]: continue
        res_id = int(row[0])
        res_name = row[1]
        res_code = row[2]
        res_parent = int(row[3])
        res_dict[res_id] = {"id":res_id, "name":res_name, "code":res_code, "parent_id":res_parent, "open":False}
    update_tree_open()
    
    ztree_json = []
    for key in res_dict.keys():
        ztree_json.append({"id":key, "pId":res_dict[key]['parent_id'], "name":res_dict[key]['name'], "open":res_dict[key]['open']})
    
    return json.dumps(ztree_json)


def l_res_list(request):
    '''资源分类列表'''
    if request.method == "GET":
        return render(request, "manager/mis/l_res_list.html", {"znodes":get_res_json()})
    elif request.method == "POST":
        try:
            lib_id = int(request.REQUEST["lib_id"])
            auth_3qdou_list = request.REQUEST["auth_list"]
        except:
            return HttpResponse(u"参数错误")
        
        try: library = Library.objects.get(id=lib_id)
        except: return HttpResponse(u"图书馆不存在")
        
        print auth_3qdou_list
        auth_3qdou_list = update_3qdou_auth(auth_3qdou_list)
        print auth_3qdou_list
        library.auth_3qdou_list = auth_3qdou_list
        library.save()
        return HttpResponse("ok")


def l_auth_list(request):
    try: lib_id = int(request.REQUEST["lib_id"])
    except: return HttpResponse(u"参数错误")
    
    try: library = Library.objects.get(id=lib_id)
    except: return HttpResponse(u"图书馆不存在")
    
    auth_list = library.auth_3qdou_list if library.auth_3qdou_list else ""
    return HttpResponse(auth_list)    
        
        
def update_3qdou_auth(auth_3qdou_list):
    auth_list = []
    cursor = connections['KidsLibrarySystem'].cursor()
    sql = "select Res_Id, Res_Parent from Res_Class"
    cursor.execute(sql)
    rows = cursor.fetchall()
    res_list = []
    parent_list = []
    for row in rows:
        res_list.append(int(row[0]))
        parent_id = int(row[1])
        if parent_list.count(parent_id) == 0:
            parent_list.append(parent_id)
    for res_id in auth_3qdou_list.split(','):
        if res_list.count(int(res_id))>0 and parent_list.count(int(res_id))==0:
            auth_list.append(res_id)
    return ','.join(auth_list)


#话题开始
@print_trace
def topic_template(request):
    '''话题模板'''
    if not has_permissions(request, 'topic_template'): return HttpResponse(u'没有权限')
    
    if request.method == "GET":
        return render(request, "manager/mis/topic_template.html")
    elif request.method == "POST":
        try:
            hid_id = int(request.REQUEST["hid_id"])
            title = request.REQUEST["title"]
            row_num = int(request.REQUEST["row_num"])
            col_num = int(request.REQUEST["col_num"])
            hid_res_path = request.POST["hid_res_path"]
        except:
            return HttpResponse(u"参数错误")
        
        print hid_res_path
        if len(hid_res_path) == 0:
            return HttpResponse(u"未知错误，请联系管理员")
        
        res_type = 10    #标签模板
        if hid_id:
            try: zone_asset = ZoneAsset.objects.get(id=hid_id)
            except(ZoneAsset.DoesNotExist): return HttpResponse(u"不存在的资源ID:%d" % hid_id)
        else:
            zone_asset = ZoneAsset()
            zone_asset.user_id = request.user.id
            zone_asset.library = request.user.library
            zone_asset.res_type = res_type
            zone_asset.status = -1
            
        zone_asset.res_title = title
        zone_asset.row = row_num
        zone_asset.column = col_num
        zone_asset.save()
        
        asset_res_path = "%s/%d" % (get_asset_path(request, res_type), zone_asset.id)
        if not os.path.exists(os.path.join(MEDIA_ROOT, asset_res_path)):
            os.makedirs(os.path.join(MEDIA_ROOT, asset_res_path))
        
        if hid_res_path.find("temp") >= 0:  #有新上传文件
            ext = os.path.splitext(hid_res_path)[1] #扩展名 
            if ext not in ('.jpg','.jpeg','.png','.gif','.bmp'):
                return HttpResponse(u"上传图片格式不正确:%s" % ext)
        
            zone_asset.res_path = "%s/origin%s" % (asset_res_path, ext)
            zone_asset.img_small_path = zone_asset.res_path.replace("origin", "s")
            open(os.path.join(MEDIA_ROOT, zone_asset.res_path), "wb").write(open(os.path.join(MEDIA_ROOT, hid_res_path), "rb").read())
            try: os.remove(os.path.join(MEDIA_ROOT, hid_res_path))
            except: pass

            from PIL import Image
            img = Image.open(os.path.join(MEDIA_ROOT, zone_asset.res_path))
            
            #print get_small_size(img.size[0], img.size[1])
            from utils import get_small_size
            img.thumbnail(get_small_size(img.size[0], img.size[1]), Image.ANTIALIAS)
            img.save(os.path.join(MEDIA_ROOT, zone_asset.img_small_path))
            zone_asset.status = 1
            zone_asset.save()
        
        #记录日志
        add_manager_action_log(request, u'%s新建/更新了话题模板：[%s(%sx%s)]' % (request.user, zone_asset.res_title, zone_asset.row, zone_asset.column))
        return HttpResponse("ok")


def get_topic_list():
    """
        话题模板的缓存
    """
    cache_key = "manager.misaction.get_topic_list"
    topic_list = cache.get(cache_key, [])
    if not topic_list:
        print "cache not found:get_topic_list"
        cursor = connections[DB_READ_NAME].cursor()
        sql = "select id,res_title,res_path,img_small_path,`row`,`column`,update_time from zone_asset where res_type=10 and status=1"
        #print sql
        cursor.execute(sql)
        rows = cursor.fetchall()
        for row in rows:
            id = int(row[0])
            title = row[1]
            url =  MEDIA_URL + row[2]
            small =  MEDIA_URL + row[3]
            row_num = int(row[4])
            col_num = int(row[5])
            update_time = row[6].strftime("%Y-%m-%d %H:%M:%S")
            topic_list.append({"id":id, "title":title, "url":url, "small":small, "row_num":row_num, "col_num":col_num, "update_time":update_time})
        cache.set(cache_key, topic_list)
    return topic_list
    
           
def topic_template_list(request):
    '''话题模板列表'''
    return HttpResponse(json.dumps(get_topic_list()))


def topic_list(request):
    '''话题列表'''
    if not has_permissions(request, 'topic_list'): return HttpResponse(u'没有权限')
    return render(request, "manager/mis/topic_list.html")

def topic_mark(request):
    '''话题标签'''
    if not has_permissions(request, 'topic_mark'): return HttpResponse(u'没有权限')
    if request.method == "GET":
        return render(request, "manager/mis/topic_mark.html")
    elif request.method == "POST":
        try:
            hid_id = int(request.REQUEST["hid_id"])
            title = request.REQUEST["title"]
            parent_id = int(request.REQUEST["parent_id"])
            hid_res_path = request.POST["hid_res_path"]
        except:
            return HttpResponse(u"参数错误")
        
        print hid_res_path
        if len(hid_res_path) == 0:
            return HttpResponse(u"未知错误，请联系管理员")
        
        
        try: topic_template = ZoneAsset.objects.get(id=parent_id, res_type=10)
        except(ZoneAsset.DoesNotExist): return HttpResponse(u"不存在的话题模板ID:%d" % topic_template)
        
        res_type = 11    #话题标签
        if hid_id:
            try: zone_asset = ZoneAsset.objects.get(id=hid_id)
            except(ZoneAsset.DoesNotExist): return HttpResponse(u"不存在的话题标签ID:%d" % hid_id)
        else:
            zone_asset = ZoneAsset()
            zone_asset.user_id = request.user.id
            zone_asset.library = request.user.library
            zone_asset.res_type = res_type
            zone_asset.status = -1
            
        zone_asset.res_title = title
        zone_asset.row = topic_template.row
        zone_asset.column = topic_template.column
        zone_asset.template_id = topic_template.id
        zone_asset.save()
        
        asset_res_path = "%s/%d" % (get_asset_path(request, res_type), zone_asset.id)
        if not os.path.exists(os.path.join(MEDIA_ROOT, asset_res_path)):
            os.makedirs(os.path.join(MEDIA_ROOT, asset_res_path))
        
        if hid_res_path.find("temp") >= 0:  #有新上传文件
            ext = os.path.splitext(hid_res_path)[1] #扩展名 
            if ext not in ('.jpg','.jpeg','.png','.gif','.bmp'):
                return HttpResponse(u"上传图片格式不正确:%s" % ext)
        
            zone_asset.res_path = "%s/origin%s" % (asset_res_path, ext)
            zone_asset.img_small_path = zone_asset.res_path.replace("origin", "s")
            open(os.path.join(MEDIA_ROOT, zone_asset.res_path), "wb").write(open(os.path.join(MEDIA_ROOT, hid_res_path), "rb").read())
            try: os.remove(os.path.join(MEDIA_ROOT, hid_res_path))
            except: pass

            from PIL import Image
            img = Image.open(os.path.join(MEDIA_ROOT, zone_asset.res_path))
            
            #print get_small_size(img.size[0], img.size[1])
            from utils import get_small_size
            img.thumbnail(get_small_size(img.size[0], img.size[1]), Image.ANTIALIAS)
            img.save(os.path.join(MEDIA_ROOT, zone_asset.img_small_path))
            zone_asset.status = 1
            zone_asset.save()
        
        #记录日志
        add_manager_action_log(request, u'%s新建/更新了话题模板：[%s(%sx%s)]' % (request.user, zone_asset.res_title, zone_asset.row, zone_asset.column))
        return HttpResponse("ok")


def topic_mark_list(request):
    '''话题标签'''
    try:
        page_index = int(request.REQUEST.get("page_index", 1))
        page_size = int(request.REQUEST.get("page_size", 15))
        template_id = int(request.REQUEST["sel_topic"])
        search_text = request.REQUEST.get("search_text", "").strip()
    except:
        import traceback
        traceback.print_exc()
        return HttpResponse(u"参数错误")
    
    where_clause = "res_type=11 and status=1"
    if template_id:
        where_clause += " and template_id=%d" % template_id
    if search_text:
        where_clause += " and res_title like '%%%s%%'" % search_text
    
    cursor = connections[DB_READ_NAME].cursor()
    sql = "select count(*) from zone_asset where %s" % where_clause
    cursor.execute(sql)
    row = cursor.fetchone()
    count = int(row[0]) if row and row[0] else 0
    page_count = int(ceil(count/float(page_size)))
    
    sql = "select id,res_title,res_path,img_small_path,`row`,`column`,template_id,update_time from zone_asset where %s" % where_clause
    sql += " order by update_time desc LIMIT %s,%s" % ((page_index-1)*page_size, page_size)
    #print sql
    cursor.execute(sql)
    rows = cursor.fetchall()
    back_list = []
    for row in rows:
        id = int(row[0])
        title = row[1]
        url =  MEDIA_URL + row[2]
        small =  MEDIA_URL + row[3]
        row_num = int(row[4])
        col_num = int(row[5])
        template_id = int(row[6])
        template_name = get_topic_template_name(template_id)
        update_time = row[7].strftime("%Y-%m-%d %H:%M:%S")
        back_list.append({"id":id, "title":title, "url":url, "small":small, "row_num":row_num, "col_num":col_num, "template_name":template_name, "template_id":template_id,"update_time":update_time})
    return HttpResponse(json.dumps({"data":back_list, "page_index": page_index, "page_count": page_count}))

def get_topic_template_name(template_id):
    topic_list = get_topic_list()
    for topic in topic_list:
        if template_id == topic["id"]:
            return topic["title"]
    return u"未知"

def get_emotion_type_list(request):
    #ZONE_EMOTION_CHOICES = ((1,u"默认"), (2,u"蘑菇头"))
    from WebZone.conf import ZONE_EMOTION_CHOICES
    return HttpResponse(json.dumps(ZONE_EMOTION_CHOICES))

def get_emotion_type_name(type_id):
    #ZONE_EMOTION_CHOICES = ((1,u"默认"), (2,u"蘑菇头"))
    from WebZone.conf import ZONE_EMOTION_CHOICES
    for emotion in ZONE_EMOTION_CHOICES:
        if type_id == emotion[0]:
            return emotion[1]
    return u"未知"

def topic_emotion(request):
    '''话题表情'''
    if not has_permissions(request, 'topic_emotion'): return HttpResponse(u'没有权限')
    if request.method == "GET":
        return render(request, "manager/mis/topic_emotion.html")
    elif request.method == "POST":
        try:
            hid_id = int(request.REQUEST["hid_id"])
            title = request.REQUEST["title"]
            type_id = int(request.REQUEST["type_id"])
            hid_res_path = request.POST["hid_res_path"]
        except:
            return HttpResponse(u"参数错误")
        
        print hid_res_path
        if len(hid_res_path) == 0:
            return HttpResponse(u"未知错误，请联系管理员")
        
        if type_id not in (1, 2):
            return HttpResponse(u"错误的表情分类")
        
        res_type = 12    #话题表情
        if hid_id:
            try: zone_asset = ZoneAsset.objects.get(id=hid_id)
            except(ZoneAsset.DoesNotExist): return HttpResponse(u"不存在的话题表情ID:%d" % hid_id)
        else:
            zone_asset = ZoneAsset()
            zone_asset.user_id = request.user.id
            zone_asset.library = request.user.library
            zone_asset.res_type = res_type
            zone_asset.status = -1
        
        zone_asset.res_title = title
        zone_asset.type_id = type_id
        zone_asset.save()
        
        asset_res_path = "%s/%d" % (get_asset_path(request, res_type), zone_asset.id)
        if not os.path.exists(os.path.join(MEDIA_ROOT, asset_res_path)):
            os.makedirs(os.path.join(MEDIA_ROOT, asset_res_path))
        
        if hid_res_path.find("temp") >= 0:  #有新上传文件
            ext = os.path.splitext(hid_res_path)[1] #扩展名 
            if ext not in ('.jpg','.jpeg','.png','.gif','.bmp'):
                return HttpResponse(u"上传图片格式不正确:%s" % ext)
        
            zone_asset.res_path = "%s/origin%s" % (asset_res_path, ext)
            zone_asset.img_small_path = zone_asset.res_path.replace("origin", "s")
            open(os.path.join(MEDIA_ROOT, zone_asset.res_path), "wb").write(open(os.path.join(MEDIA_ROOT, hid_res_path), "rb").read())
            try: os.remove(os.path.join(MEDIA_ROOT, hid_res_path))
            except: pass

            from PIL import Image
            img = Image.open(os.path.join(MEDIA_ROOT, zone_asset.res_path))
            
            if type_id == 1:
                img.thumbnail((36, 34), Image.ANTIALIAS)
            elif type_id == 2:
                img.thumbnail((45, 45), Image.ANTIALIAS)
            img.save(os.path.join(MEDIA_ROOT, zone_asset.img_small_path))
            zone_asset.status = 1
            zone_asset.save()
        
        #记录日志
        add_manager_action_log(request, u'%s新建/更新了话题表情：[%s]' % (request.user, zone_asset.res_title))
        return HttpResponse("ok")

def topic_emotion_list(request):
    '''各种表情列表'''
    try:
        page_index = int(request.REQUEST.get("page_index", 1))
        page_size = int(request.REQUEST.get("page_size", 15))
        type_id = int(request.REQUEST["sel_topic"])
        search_text = request.REQUEST.get("search_text", "").strip()
    except:
        import traceback
        traceback.print_exc()
        return HttpResponse(u"参数错误")
    
    where_clause = "res_type=12 and status=1"
    if type_id:
        where_clause += " and type_id=%d" % type_id
    if search_text:
        where_clause += " and res_title like '%%%s%%'" % search_text
    
    cursor = connections[DB_READ_NAME].cursor()
    sql = "select count(*) from zone_asset where %s" % where_clause
    cursor.execute(sql)
    row = cursor.fetchone()
    count = int(row[0]) if row and row[0] else 0
    page_count = int(ceil(count/float(page_size)))
    
    sql = "select id,res_title,res_path,img_small_path,type_id,update_time from zone_asset where %s" % where_clause
    sql += " order by update_time desc LIMIT %s,%s" % ((page_index-1)*page_size, page_size)
    #print sql
    cursor.execute(sql)
    rows = cursor.fetchall()
    back_list = []
    for row in rows:
        id = int(row[0])
        title = row[1]
        url =  MEDIA_URL + row[2]
        small =  MEDIA_URL + row[3]
        type_id = int(row[4])
        type_name = get_emotion_type_name(type_id)
        update_time = row[5].strftime("%Y-%m-%d %H:%M:%S")
        back_list.append({"id":id, "title":title, "url":url, "small":small, "type_name":type_name, "type_id":type_id,"update_time":update_time})
    return HttpResponse(json.dumps({"data":back_list, "page_index": page_index, "page_count": page_count}))






    
    
    
    
    
    
    
    
    
    
    
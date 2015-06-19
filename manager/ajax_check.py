#coding: utf-8
'''
Created on 2014-4-3

@author: Administrator
'''
from django.http import HttpResponse
from utils.lib_check import is_domain_valid, is_domain_exist
from utils.lib_check import is_host_valid, is_host_exist
from utils.lib_check import is_lib_name_valid, is_lib_name_exist
from utils.reg_check import is_username_valid, is_username_exist
from utils.reg_check import is_nickname_valid, is_nickname_exist
from utils.reg_check import is_password_valid
from utils.lib_check import is_canbe_curator
from account.models import AuthUser
from library.models import Library


def check_new_username(request):
    try:
        username = request.REQUEST["username"].lower().strip()
    except: return HttpResponse(u"参数错误")
    
    if not is_username_valid(username):
        return HttpResponse(u"用户名不合规")
    if is_username_exist(username):
        return HttpResponse(u"用户名已存在")
    return HttpResponse("ok")

def check_new_nickname(request):
    try:
        nickname = request.REQUEST["nickname"].strip()
    except: return HttpResponse(u"参数错误")
    
    if not is_nickname_valid(nickname):
        return HttpResponse(u"呢称不合规")
    if is_nickname_exist(nickname):
        return HttpResponse(u"呢称已存在")
    return HttpResponse("ok")

def check_password(request):
    try:
        password = request.REQUEST["password"]
    except: return HttpResponse(u"参数错误")
    
    if not is_password_valid(password):
        return HttpResponse(u"密码不合规")
    return HttpResponse("ok")

#新增图书馆长
def check_curator_username(request):
    manager_login =  hasattr(request, "session") and request.session.get('manager_login', False) and request.user.is_active and request.user.auth_type == 9
    if not manager_login:
        return HttpResponse(u"请先登录超级管理员账户")
    try:
        username = request.REQUEST["username"].lower().strip()
    except: return HttpResponse(u"参数错误")

    try: auth_user = AuthUser.objects.get(username=username)
    except(AuthUser.DoesNotExist): return HttpResponse(u"用户名不存在")
    
    if not auth_user.is_active: return HttpResponse(u"用户被封")
    
    if auth_user.auth_type <> 0: return HttpResponse(u"只能普通会员转为图书馆长")   #只能普通会员转为图书馆长
    
    return HttpResponse("ok")


def check_auditor_username(request):
    manager_login =  hasattr(request, "session") and request.session.get('manager_login', False) and request.user.is_active and request.user.auth_type == 1
    if not manager_login:
        return HttpResponse(u"请先登录")
    try: username = request.REQUEST["username"].lower().strip()
    except:
        import traceback
        traceback.print_exc()
        return HttpResponse(u"参数错误1")

    try:
        auth_user = AuthUser.objects.get(username=username)
        if auth_user.auth_type == 2:    #审核员
            return HttpResponse(u"该用户已经是审核员")
        if not auth_user.is_active:
            return HttpResponse(u"该用户被封号")
        if auth_user.library_id <> request.user.library_id:
            return HttpResponse(u"必须是当前图书馆下的普通会员，才能转为《审核员》！")
    except: return HttpResponse(u"用户名不存在")
    
    return HttpResponse("ok")


def check_domain(request):
    try: domain = request.REQUEST["domain"].lower().strip()
    except: return HttpResponse(u"参数错误")
    
    if not is_domain_valid(domain):
        return HttpResponse(u"二级域名不合规，请重新输入")
    
    if is_domain_exist(domain):
        return HttpResponse(u"二级域名已存在，请重新选择")
    
    return HttpResponse("ok")


def check_host(request):
    try: host = request.REQUEST["host"].lower().strip()
    except: return HttpResponse(u"参数错误")
    
    if not is_host_valid(host):
        return HttpResponse(u"自定义域名不合规，请重新输入")
    
    if is_host_exist(host):
        return HttpResponse(u"自定义域名已存在，请重新选择")
    
    return HttpResponse("ok")

from utils.decorator import print_trace
@print_trace
def check_lib_name(request):
    try:
        lib_id = int(request.REQUEST["lib_id"])
        lib_name = request.REQUEST["lib_name"].lower().strip()
    except: return HttpResponse(u"参数错误")
    
    if lib_id:
        try: library = Library.objects.get(id=lib_id)
        except: return HttpResponse(u"图书馆ID不存在")
    
        if library.lib_name == lib_name: return HttpResponse("ok")
    
    if not is_lib_name_valid(lib_name):
        return HttpResponse(u"图书馆名称不合规，请重新输入")
    
    if is_lib_name_exist(lib_name):
        return HttpResponse(u"图书馆名称已存在，请重新选择")
    
    return HttpResponse("ok")

    

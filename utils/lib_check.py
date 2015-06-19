#coding: utf-8
'''
Created on 2014-4-2

@author: Administrator
'''
import re
from account.models import AuthUser
from library.models import Library

def is_canbe_curator(username):
    """
        提供的账号是否可以做为图书馆管理员的登录账号
    """
    try: auth_user = AuthUser.objects.get(username=username)
    except(AuthUser.DoesNotExist): return False
    
    if not auth_user.is_active: return False
    
    if auth_user.auth_type <> 0: return False   #只能普通会员转为图书馆长
    
    if Library.objects.filter(user_id=auth_user.id).count() > 0: return False   #已经是图书馆长了
    
    return True

def is_domain_valid(domain):
    """
        长度为3-20个字符
        可以包含英文，数字-_符号
    """
    if re.match(r'^[\w-]{1,20}$', domain): return True
    return False

def is_domain_exist(domain):
    if Library.objects.filter(domain=domain).count() > 0: return True
    return False


def is_host_valid(host):
    """
        格式为domain.3qdou.com之类
    """
    if re.match(r'^[\w-]+.[\w-]+.[\w-]+$', host): return True
    return False


def is_host_exist(host):
    if Library.objects.filter(host=host).count() > 0: return True
    return False

def is_lib_name_valid(lib_name):
    """
        长度为2-100个字符
        可以包含中文，英文，数字，.@+-_符号
        带有中文，前面需要加u，lib_name需要转换为unicode
    """
    if re.match(ur'^[\w.@+-_\u4e00-\u9fa5]{2,100}$', lib_name): return True
    return False


def is_lib_name_exist(lib_name):
    if Library.objects.filter(lib_name=lib_name).count() > 0: return True
    return False









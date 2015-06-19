#coding: utf-8
'''
Created on 2014-3-28

@author: Administrator
'''
import re
from account.models import AuthUser

def is_username_valid(username):
    """
        长度为3-20个字符
        可以包含英文，数字，.@+-_符号
    """
    if re.match('^[\w.@+-_]{3,20}$', username): return True
    return False

def is_username_exist(username):
    if AuthUser.objects.filter(username=username).count() > 0: return True
    return False

def is_password_valid(password):
    """
    password need 6-20 characters length, don't cotain empty space character
    """
    if re.match(ur'^[\S]{6,20}$', password): return True
    return False

def is_nickname_valid(nickname):
    """
        长度为2-8个字符
        可以包含中文，英文，数字，.@+-_符号
        带有中文，前面需要加u，nickname需要转换为unicode
    """
    if re.match(ur'^[\w.@+-_\u4e00-\u9fa5]{2,8}$', nickname): return True
    return False

def is_nickname_exist(nickname):
    if AuthUser.objects.filter(nickname=nickname).count() > 0: return True
    return False

def is_email_valid(email):
    """
    valid emaill address is a valid address
    """
    if re.match(ur'^w+[-+.]w+)*@w+([-.]w+)*.w+([-.]w+)*$', email): return True
    return False


def normalize_email(email):
    """
    Normalize the address by lowercasing the domain part of the email
    address.
    """
    email = email or ''
    try:
        email_name, domain_part = email.strip().rsplit('@', 1)
    except ValueError:
        pass
    else:
        email = '@'.join([email_name, domain_part.lower()])
    return email




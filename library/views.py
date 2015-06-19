# coding=utf8
from django.shortcuts import render
from django.http import HttpResponse
import json

from utils.decorator import print_trace
# 导入读取数据列表的方法
from utils.db_handler import get_pager
# 导入机构model
from library.models import Library
# 导入读取ztree树所需的数据的方法
from library.handler import get_ztree_library
# 导入创建用户的方法
from account.handler import edit_user


def get_ztree_library(request):
    '''
    返回页面ztree控件所需的数据
    editor: kamihati 2015/5/6
    :param request:
    :return:
    '''
    return HttpResponse(json.dumps(get_ztree_library(request.user.library_id)))


@print_trace
def api_library_edit(request):
    '''
    编辑机构信息
    editor: kamihati 2015/5/6
    :param request:
    :return:
    '''
    library_id = int(request.POST.get('id', '0'))
    lib_name = request.POST.get('lib_name')
    province = request.POST.get('province', '')
    city = request.POST.get('city', '')
    region = request.POST.get('region', '')
    realname = request.POST.get('realname', '')
    nickname = request.POST.get('nickname', '')
    phone = request.POST.get('phone', '')
    email = request.POST.get('email', "")
    lib_address = request.POST.get('address', '')
    buy_code = request.POST.get('buy_code', '')
    username = request.POST.get('username', '')
    password = request.POST.get('password', '')
    annex_temp_path = request.POST.get('annex', '')

    domain = request.POST.get('domain', '')
    logo_path = request.POST.get('logo', '')
    swf_path = request.POST.get('swf', '')
    expire_time = request.POST.get('expire_time', '')

    # 如果为新建机构。则需要新建管理员账户。否则不需要
    lib = None if library_id == 0 else Library.objects.get(pk=library_id)
    user = None if lib is None else lib.user
    param = dict()
    user_param = dict(username=username,
                      password=password,
                      realname=realname,
                      nickname=nickname,
                      phone=phone,
                      email=email,
                      auth_type=1)
    if lib is None:
        # 创建机构管理员
        user = edit_user(user_param)
        if user == -1:
            return HttpResponse("-1")
        param['user'] = user
    else:
        user_param['id'] = user.id
        # 修改机构管理员信息
        user = edit_user(user_param)
        param['id'] = library_id

     # 判断机构名称是否重复
    if Library.objects.filter(lib_name=lib_name).exclude(pk=library_id).count() > 0:
        return HttpResponse("-2")
    # 判断自定义域名是否重复
    if Library.objects.filter(domain=domain).exclude(pk=library_id).count() > 0:
        return  HttpResponse("-3")

    param['lib_name'] = lib_name

    # 根据省市区信息的填写情况判断机构级别
    param['province'] = province
    param['city'] = city
    param['region'] = region
    level = 3
    if region == "":
        level = 2
    elif city == "":
        level = 1
    elif province == "":
        level = 0
    param['level'] = level
    if lib_address != '':
        param['lib_address'] = lib_address
    if buy_code != '':
        param['buy_code'] = buy_code

    if domain != "":
        param['domain'] = domain
        param['host'] = domain
    if expire_time != "":
        param['expire_time'] = expire_time
    if logo_path != "":
        param['logo_temp_path'] = logo_path
    if swf_path != "":
        param['swf_temp_path'] = swf_path
    if annex_temp_path != '':
        param['annex_temp_path'] = annex_temp_path
    # 导入编辑机构信息的方法
    from library.handler import edit_library
    library = edit_library(param, request.user)

    if library.id is None:
        return HttpResponse('fail')
    # 如果为新增机构。则指定管理员帐号的所属机构为机构id
    if library_id == 0:
        user.library = library
        user.save()
    return HttpResponse('ok')


def api_get_region(request):
    '''
    获取机构地区列表
    editor: kamihati 2015/5/8
    :param request:
              request.GET.get('parent_id', 0);   上级地市id
    :return:
    '''
    # 导入获取地区列表的方法
    from library.handler import get_region
    result = [dict(id=obj.id, name=obj.name) for obj in get_region(request.GET.get('parent_id'))]
    return HttpResponse(json.dumps(result))

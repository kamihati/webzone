# coding: utf-8
from django.shortcuts import render
from django.http import HttpResponse
from utils.decorator import print_trace

from library.models import Library
from account.models import AuthUser
from PIL import Image


@print_trace
def api_edit_user(request):
    '''
    编辑用户
    editor: kamihati 2015/5/4
    editor: kamihati 2015/6/15 保存图片后增加缩略图的处理
    :param request:
    :return:
    '''
    param = dict()
    user_id = request.POST.get('user_id', '')
    library_id = request.POST.get('library')
    # 机构
    param['library'] = Library.objects.get(pk=library_id)

    # 真名
    realname = request.POST.get('realname', '')
    if realname != '':
        param['realname'] = realname
    # 电话
    phone = request.POST.get('phone', '')
    if phone != '':
        param['phone'] = phone
    # 昵称
    nickname = request.POST.get('nickname', '')
    if nickname != '':
        param['nickname'] = nickname
    # QQ
    qq = request.POST.get('qq', '')
    if qq != '':
        param['qq'] = qq
    # 密码
    password = request.POST.get("password", '')
    if password != '':
        param['password'] = password
    # 邮件
    email = request.POST.get('email', '')
    if email != '':
        param['email'] = email
    if user_id == '':
        username = request.POST.get('username')
        param['username'] = username
        auth_type = request.POST.get('auth_type')
    else:
        param['id'] = user_id

    # 用户类型。默认为0 普通会员
    auth_type = request.POST.get('auth_type', 0)
    param['auth_type'] = auth_type

    # 年龄
    age = request.POST.get('age', 0)
    param['age'] = age

    # 提示问题
    question = request.POST.get('question', '')
    if question != '':
        param['question'] = question
    # 提示答案
    answer = request.POST.get('answer', '')
    if answer != '':
        param['answer'] = answer

    # 生日
    birthday = request.POST.get('birthday', '')
    if birthday != '':
        param['birthday'] = birthday
    # 个人介绍
    desc = request.POST.get('description', '')
    if desc != '':
        param['description'] = desc

    # 性别
    sex = request.POST.get('sex', -1)
    param['sex'] = sex

    # 学校
    school = request.POST.get('school', '')
    if school != '':
        param['school'] = school

    # 导入编辑用户的方法
    from account.handler import edit_user
    user = edit_user(param)
    if user == -1:
        return HttpResponse("-1")

    # 头像
    avatar = request.POST.get('avatar', '')
    if avatar == '':
        if user_id == "":
            user.avatar_img = 'avatar.png'
    else:
        target_path = "/user/person/%s/avatar" % user.id
        from WebZone.settings import MEDIA_ROOT
        from utils.img_handler import thumbnail_img
        from utils.decorator import move_temp_file
        from utils import get_img_ext
        img = Image.open(MEDIA_ROOT + avatar.replace("/media/", '/'))
        ext = get_img_ext(img)
        l_path = target_path + "_l" + ext
        m_path = target_path + "_m" + ext
        s_path = target_path + "_s" + ext

        thumbnail_img(avatar.replace("/media/", '/'), 300, 300, l_path)
        thumbnail_img(avatar.replace("/media/", '/'), 120, 120, m_path)
        thumbnail_img(avatar.replace("/media/", '/'), 40, 40, s_path)
        user.avatar_img = move_temp_file(avatar.replace("/media/", '/'), target_path)
    user.save()

    # 导入编辑管理员权限的方法
    from account.handler import edit_manager_permission
    target_urls = request.POST.get('target_urls', '')
    edit_manager_permission(user, target_urls.split(","))
    return HttpResponse('ok')


def api_change_password(request):
    '''
    修改自己的密码
    editor: kamihati 2015/5/4
    :param request:
    :return:
    '''
    user_id = request.POST.get('id')
    pwd = request.POST.get('pwd')
    new_pwd = request.POST.get('pwd1')
    # 烦！ kamihati 2015/5/4
    if int(user_id) != request.user.id:
        return HttpResponse(u'呵呵')

    user = AuthUser.objects.get(id=user_id)
    from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
    login_user = authenticate(username=user.username, password=pwd)
    if login_user is None:
        return HttpResponse("-1")
    else:
        login_user.set_password(new_pwd)
        login_user.save()
        return HttpResponse("ok")

def api_del_user(request):
    '''
    删除用户
    editor: kamihati 2015/5/4
    :param request:
    :return:
    '''
    from account.handler import del_user
    if del_user(request.POST.get('id')):
        return HttpResponse('ok')
    return HttpResponse('fail')


@print_trace
def api_get_user_info(request):
    '''
    获取用户的明细信息
    editor: kamihati 2015/5/4
    :param request:
    :return:
    '''
    # 导入获取用户权限的方法
    from account.handler import get_user_permission
    user = AuthUser.objects.get(pk=request.GET.get('id'))
    url_list = get_user_permission(user.id)

    result = dict(id=user.id,
                  library_id=user.library.id,
                  realname=user.realname,
                  nickname=user.nickname,
                  username=user.username,
                  phone=user.telephone,
                  qq=user.qq,
                  email=user.email,
                  urls=url_list,
                  school=user.school,
                  age=user.age,
                  sex=user.sex,
                  question=user.question,
                  answer=user.answer,
                  description=user.description,
                  birthday=str(user.birthday),
                  avatar_img='/media/' + user.avatar_img)
    import json
    return HttpResponse(json.dumps(result))

# coding=utf8

import datetime
from django.http import HttpResponse

from utils.db_handler import get_pager
from utils.db_handler import get_data_count
from utils.db_handler import rows_to_dict_list
# 导入用户model
from account.models import AuthUser
# 导入用户权限表
from account.models import UserPermission

def del_user(id):
    '''
    删除用户(禁用)
    editor:
    :param id:
    :return:
    '''
    if AuthUser.objects.filter(pk=id).update(status=-1):
        return True
    return False

def get_manager_pager(page_index, page_size, **args):
    '''
    获取二级管理员分页数据
    editor: kamihati 2015/5/4  供后台用户管理模块使用
    :param page_index: 页码。从0计数
    :param page_size: 步长。
    :param args:
                  args['content'] 操作内容
    :return:
    '''
    where = u'a.status<>-1 AND a.auth_type=8 '
    if 'key' in args and args['key'] != '':
        where += u' AND (a.username LIKE \'%' + args['key'] + '%\' OR a.realname LIKE \'%' + args['key'] + '%\')'

    data_count = get_data_count('a.id', 'auth_user a', "", where)
    return rows_to_dict_list(
        get_pager('a.id,a.username,a.realname,a.login_times,a.last_login',
                  'auth_user a',
                  '',
                  where,
                  'ORDER BY a.id DESC',
                  page_index,
                  page_size),
        ['id', 'username', 'realname', 'login_times', 'last_login']
    ), data_count


def get_user_pager(page_index, page_size, **args):
    '''
    获取会员分页数据
    editor: kamihati 2015/5/5  供后台用户管理模块使用
    :param page_index: 页码。从0计数
    :param page_size: 步长。
    :param args:
    :return:
    '''
    where = u'a.status<>-1 AND a.auth_type=0 '
    if 'key' in args and args['key'] != '':
        where += u' AND (a.username LIKE \'%' + args['key'] + '%\' OR a.realname LIKE \'%' + args['key'] + '%\' OR a.nickname LIKE \'%' + args['key'] + '%\')'
    if 'library_id' in args and args['library_id'] != '':
        where += ' AND a.library_id=%s' % args['library_id']

    join_str = 'INNER JOIN library b ON b.id=a.library_id'

    data_count = get_data_count('a.id', 'auth_user a', join_str, where)
    return rows_to_dict_list(
        get_pager('a.id,b.lib_name,a.username,a.nickname',
                  'auth_user a',
                  join_str,
                  where,
                  'ORDER BY a.id DESC',
                  page_index,
                  page_size),
        ['id', 'lib_name', 'username', 'nickname']
    ), data_count


def get_person_permission(user_id):
    '''
    获取指定用户的操作权限列表
    editor: kamihati 2015/5/4 供utils.decorator.validate_permission使用
    :param user_id:用户id
    :return:
    '''
    # 导入用户权限记录表
    from account.models import UserPermission
    return UserPermission.objects.filter(user_id=user_id).values_list('target_url')


def edit_user(param):
    '''
    编辑用户数据
    editor: kamihati 2015/5/4
    :param param:
    :return:
    '''
    auth_user = AuthUser()
    if 'id' in param:
        auth_user = AuthUser.objects.get(pk=param['id'])
    else:
        # 判断用户名是否已存在
        if AuthUser.objects.filter(username=param['username']).count() != 0:
            return -1
        auth_user.username = param['username']
    if 'password' in param:
        if param['password'] != '':
            auth_user.set_password(param['password'])
    if 'nickname' in param:
        auth_user.nickname = param['nickname']
    sex = -1 if 'sex' not in param else param['sex']
    if 'sex' in param:
        auth_user.sex = sex
    print param
    if 'email' in param:
        auth_user.email = param['email']
    if 'library' in param:
        auth_user.library = param['library']
    if 'phone' in param:
        auth_user.telephone = param['phone']
    if 'qq' in param:
        auth_user.qq = param['qq']
    if 'realname' in param:
        auth_user.realname = param['realname']
    auth_user.auth_type = param['auth_type']

    if 'age' in param:
        auth_user.age = param['age']

    if 'question' in param:
        auth_user.question = param['question']

    if 'answer' in param:
        auth_user.answer = param['answer']

    if 'birthday' in param:
        auth_user.birthday = param['birthday']

    if 'avatar_img' in param:
        auth_user.avatar_img = param['avatar_img']

    if 'sex' in param:
        auth_user.sex = param['sex']

    if 'school' in param:
        auth_user.school = param['school']

    if 'description' in param:
        auth_user.description = param['description']

    auth_user.save()

    from account.models import AuthNotice
    auth_notice = AuthNotice()
    auth_notice.user = auth_user
    auth_notice.save()

    from diy.models import AuthAlbum
    auth_album = AuthAlbum()
    auth_album.user_id = auth_user.id
    auth_album.type_id = 0  #系统自动生成
    auth_album.album_title = u"默认相册"
    auth_album.status = 1   #可用状态
    auth_album.save()
    return auth_user


def edit_manager_permission(user, target_urls):
    '''
    编辑管理员的权限
    editor: kamihati 2015/5/4
    :param param:
    :return:
    '''
    user_urls = get_user_permission(user.id)
    # 计算差集来确定哪些是需要增加的哪些是需要删除的
    new_urls = set(target_urls).difference(set(user_urls))
    del_urls = set(user_urls).difference(set(target_urls))
    for target_url in new_urls:
        if target_url == "":
            continue
        UserPermission.objects.create(user_id=user.id, target_url=target_url, add_time=datetime.datetime.now())
    for url in del_urls:
        UserPermission.objects.filter(user_id=user.id, target_url=url).delete()


def get_user_permission(user_id):
    '''
    获取用户的权限信息
    editor: kamihati 2015/5/18
    editor: kamihati 2015/6/16 增加机构总管理员的权限设置
    :param user_id:
    :return:
    '''
    user = AuthUser.objects.get(pk=user_id)
    if user.auth_type == 9:
        from WebZone.conf import ADMIN_PERMISSION
        return ADMIN_PERMISSION
    elif user.auth_type == 1:
        from WebZone.conf import LIBRARY_ADMIN_PERMISSION
        return LIBRARY_ADMIN_PERMISSION
    return [obj[0] for obj in UserPermission.objects.filter(user_id=user_id).values_list('target_url')]
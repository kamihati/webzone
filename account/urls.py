# coding=utf8

from django.conf.urls import patterns

urlpatterns = patterns(
    'account',
    # 编辑用户信息
    (r'^api_edit_user/$', 'views.api_edit_user'),
    # 修改密码
    (r'^api_change_password/$', 'views.api_change_password'),
    # 删除用户
    (r'^api_del_user/$', 'views.api_del_user'),
    # 获取用户的明细信息
    (r'^api_get_user_info/$', 'views.api_get_user_info'),
)
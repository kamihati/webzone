# coding=utf8

from django.conf.urls import patterns

urlpatterns = patterns(
    'activity',
    # 编辑活动
    # editor: kamihati 2015/6/10  由于新版设计改动。此api暂时停用。以后可用作参考
    (r'^edit/$', 'views.activity_edit'),
    # 编辑活动第一步
    (r'^api_edit_step1/$', 'views.api_edit_activity_step1'),
    # 编辑活动第二步
    (r'^api_edit_step2/$', 'views.api_edit_activity_step2'),
    # 更新活动的置顶状态
    (r'^update_activity_top/$', 'views.update_activity_top_status'),
    # 删除活动
    (r'^delete_activity/$', 'views.delete_activity'),
    # 获取指定机构下的活动列表
    (r'^get_activity_by_library/$', 'views.get_activity_by_library'),
    # 活动背景编辑（包括添加和删除）
    (r'^background_update/$', 'views.background_update'),
    # 移除活动背景
    (r'^remove_background/$', 'views.remove_background'),
    # 移除活动播报或结果
    (r'^del_news/$', 'views.del_news'),

    # 编辑系列活动
    (r'^activity_series_edit/$', 'views.activity_series_edit'),
    # 获取系列活动列表
    (r'^activity_series_list/$', 'views.activity_series_list'),
    # 更改活动所属系列活动
    (r'^change_activity_series/$', 'views.change_series'),

    # 获取活动分组
    (r'^api_get_activity_group/$', 'group_view.api_get_activity_group'),
    # 编辑活动分组
    (r'^api_edit_activity_group/$', 'group_view.api_edit_activity_group'),
    # 删除活动分组
    (r'^api_delete_activity_group/$', 'group_view.api_delete_activity_group'),

    # 获取活动作品的明细信息
    (r'^api_get_fruit_info/$', 'fruit_view.api_get_activity_fruit_info'),
    # 设置活动作品的状态
    (r'^api_set_fruit_status/$', 'fruit_view.api_set_fruit_status'),
    # 编辑活动作品
    (r'^api_edit_activity_fruit/$', 'fruit_view.api_edit_activity_fruit'),


    # 报名记录
    # 删除报名记录
    (r'^api_del_activity_sign_member/$', 'sign_views.api_del_activity_sign_member'),
)
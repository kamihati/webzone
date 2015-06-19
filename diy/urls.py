# coding: utf-8
'''
Created on 2015/5/7

@author: kamihati
'''
from django.conf.urls import patterns

# 素材相关
urlpatterns = patterns(
    'diy',
    # 设置个人创作的状态
    (r'^api_set_opus_status/$', 'views.api_set_opus_status'),
    # 设置个人创作的置顶状态
    (r'^api_update_opus_top/$', 'views.api_update_opus_top'),
    # 编辑个人创作评论
    (r'^api_edit_opus_comment/$', 'views.api_edit_opus_comment'),
    # 删除个人创作拼伦
    (r'^api_del_opus_comment/$', 'views.api_del_opus_comment'),
    # 更新公共资源的推荐状态
    (r'^api_update_zone_asset_top/$', 'views.api_update_zone_asset_top'),
    # 转换个人创作为模板
    (r'^api_opus_to_template/$', 'views.api_opus_to_template'),
)
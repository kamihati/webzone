# coding: utf-8
'''
Created on 2015/5/7

@author: kamihati
'''
from django.conf.urls import patterns

# 素材相关
urlpatterns = patterns(
   'widget',
    # 编辑指定素材类型
    (r'^api_edit_opus_type/$', 'views.api_edit_opus_type'),
    # 获取指定素材类型
    (r'^api_get_opus_type/$', 'views.api_get_opus_type'),
    # 删除指定素材
    (r'^api_delete_opus_type/$', 'views.api_delete_opus_type'),


    # 删除指定页面尺寸
    (r'^api_delete_widget_page_size/$', 'views.api_del_widget_page_size')
)
# coding: utf-8
'''
Created on 2015/3/20

@author: kamihati
'''
from django.conf.urls import patterns

# 素材相关
urlpatterns = patterns(
   'resources.views',
    # 查看指定素材
    (r'^view/$', 'view_resource_origin'),

    # 增加公共素材类型
    (r'^ajax_create_type/$', 'ajax_create_resource_type'),
    # 增加公共素材风格
    (r'^ajax_create_style/$', 'ajax_create_resource_style'),
    # 增加个人素菜类型
    (r'^ajax_create_type_person/$', 'ajax_create_resource_type_person'),
    # 修改公共素材类型
    (r'^ajax_alter_type/$', 'ajax_alter_resource_type'),
    # 修改个人素菜类型
    (r'^ajax_alter_type_person/$', 'ajax_alter_resource_type_person'),
    # 修改公共素材风格
    (r'^ajax_alter_style/$', 'ajax_alter_resource_style'),
    # 删除素材类型
    (r'^drop_type/$', 'ajax_drop_type'),
    # 删除素材风格
    (r'^drop_style/$', 'ajax_drop_style'),
    # 删除公共素菜类型
    (r'^drop_type_person/$', 'ajax_drop_person_type'),


    # 更新公共素材状态
    (r'^ajax_update_common_status/$', 'update_asset_status'),
    # 删除个人素材
    (r'^drop_person_res/$', 'ajax_del_person_res'),
    # 删除公共素材
    (r'^del_common_resource/$', 'ajax_del_common_res'),
    # 编辑公共素材
    (r'^edit/$', 'api_edit_resource'),

    # 编辑页面尺寸
    (r'^api_size_edit/$', 'api_size_edit'),
    # 获取页面尺寸
    (r'^api_get_widget_page_size', 'api_get_widget_page_size'),
)


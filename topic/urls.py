# coding: utf-8
'''
Created on 2015-3-20
@author:kamihati
'''
from django.conf.urls import patterns, include, url
from django.views.decorators.cache import never_cache
from django.http import HttpResponse


urlpatterns = patterns(
    'topic.views',

    # remote api
    # 话题
    (r'^edit_topic/$', 'edit_topic'),
    # 编辑话题评论
    (r'^edit_remark/$', 'edit_remark'),
    # 搜索话题
    (r'^search_topic_json/$', 'search_topic_list_json'),
    # 更新话题状态
    (r'^update_topic_status/$', 'ajax_update_topic_status'),
    # 更新话题置顶状态
    (r'^update_topic_top/$', 'ajax_update_topic_top'),

    # 评论
    # 获取指定话题评论的信息
    (r'^get_comment_json/$', 'get_comment_by_id'),
    # 删除评论
    (r'^delete_remark/$', 'remove_topic_remark'),

    # 表情
    # 删除话题表情分类
    (r'^del_phiz_type/$', 'remove_phiz_type'),
    # 编辑话题表情分类
    (r'^edit_phiz_type/$', 'edit_phiz_type'),
    # 创建话题表情分类
    (r'^add_phiz_type/$', 'add_phiz_type'),
    # 删除话题表情
    (r'^del_phiz/$', 'remove_phiz'),
    # 编辑话题表情
    (r'^edit_phiz/$', 'edit_phiz'),
    # 创建话题表情
    (r'^add_phiz/$', 'add_phiz'),

    # 话题评论资源
    # 获取指定话题的资源列表
    (r'^topic_resource_detail/$', 'topic_resource_detail'),
    # 获取指定话题评论的资源列表
    (r'^remark_resource_detail/$', 'remark_resource_detail'),
    # 移除话题资源
    (r'^remove_topic_resource/$', 'remove_topic_resource'),
    # 移除评论资源
    (r'^remove_remark_resource/$', 'remove_remark_resource'),
)

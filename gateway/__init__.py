#coding: utf-8
'''
Created on 2014-3-24

@author: Administrator
'''
import json
import re
import os
import logging, traceback
from functools import wraps
from django.utils.decorators import available_attrs
from account.models import AuthUser
from library.models import Library

def json_data(code, data):
    return json.dumps({'code':code, 'data':data})

def SuccessResponse(data=''):
    return json_data(1, data)

def FailResponse(data):
    return json_data(-1, data)

def get_library(library_id):
    try: library_id = int(library_id)
    except: return None
    
    try: library = Library.objects.get(id=library_id)
    except(Library.DoesNotExist): library = None
    return library

def echo(request, data):
    return "echo:%s" % data

import views_auth
import views_diy
import views_opus
import views_personal
import views_public
import views_story
import views_3qdou_new
import views_zone
import views_topic
import views_activity

services = {
    'myservice.echo': echo,
    # could include other functions as well
    
    'AccountService.reg_checkusername': views_auth.reg_checkusername,
    'AccountService.reg_checknickname': views_auth.reg_checknickname,
    'AccountService.register': views_auth.register,
    'AccountService.guest_login': views_auth.guest_login,
    'AccountService.guest_register': views_auth.guest_register,
    'AccountService.login': views_auth.login,
    'AccountService.logout': views_auth.logout,
    'AccountService.get_account': views_auth.get_account,
    'AccountService.update_account': views_auth.update_account,
    'AccountService.change_pass': views_auth.change_pass,
    'AccountService.question': views_auth.question,
    'AccountService.reset_password': views_auth.reset_password,
    
    'DiyService.get_lib_info': views_diy.get_lib_info,  #开始得到图书馆的基本信息
    'DiyService.get_font_list': views_diy.get_font_list,
    # 获取新版字体设计的文本框列表  coder: kamihait 2015/42
    'DiyService.get_new_font_list': views_diy.get_new_font_list,
    'DiyService.get_font_img': views_diy.get_font_img,
    'DiyService.update_avatar': views_diy.update_avatar,
    'DiyService.get_res_url': views_diy.get_res_url,
    'DiyService.get_personal_url': views_diy.get_personal_url,
    'DiyService.get_public_url': views_public.get_public_url,
    
    
    'DiyService.get_zone_type_list': views_diy.get_zone_type_list,
    'DiyService.get_zone_style_list': views_diy.get_zone_style_list,
    'DiyService.get_opus_type_list': views_diy.get_opus_type_list,
    'DiyService.get_opus_class_list': views_diy.get_opus_class_list,
    'DiyService.get_opus_size_list': views_diy.get_opus_size_list,
    # 获取个人作品的所有子类列表
    'DiyService.get_opus_class_child_list': views_diy.get_opus_class_child_list,
    
    'DiyService.get_notice_list': views_diy.get_notice_list,
    'DiyService.get_msg_list': views_diy.get_msg_list,
    'DiyService.get_index_list': views_diy.get_index_list,  #首页作品列表，包含原创和个人分享作品
    
    'DiyService.get_zone_list': views_public.get_zone_list, #all
    'DiyService.get_bg_list': views_public.get_bg_list, #1
    'DiyService.get_bg_list2': views_public.get_bg_list2, #背景列表，需要根据单双页区分
    'DiyService.get_decorator_list': views_public.get_decorator_list,   #2
    'DiyService.get_frame_list': views_public.get_frame_list,   #3
    'DiyService.get_template_list': views_public.get_template_list, #4
    'DiyService.get_template_list2': views_public.get_template_list2, #4
    'DiyService.get_audio_list': views_public.get_audio_list,   #5
    'DiyService.get_video_list': views_public.get_video_list,   #6
    'DiyService.get_template_info': views_public.get_template_info, #得到模板详细信息
    
    'DiyService.get_blank_opus': views_public.get_blank_opus,   #一个空作品的所有信息
    
    'DiyService.like_personal_res': views_zone.like_personal_res,
    'DiyService.like_public_res': views_zone.like_public_res,
    'DiyService.fetch_bg_list': views_zone.fetch_bg_list,
    'DiyService.fetch_decorator_list': views_zone.fetch_decorator_list,
    'DiyService.fetch_frame_list': views_zone.fetch_frame_list,
    'DiyService.fetch_template_list': views_zone.fetch_template_list,
    'DiyService.fetch_template_info': views_zone.fetch_template_info,
    #'DiyService.fetch_mark_list': views_zone.fetch_mark_list,
    #'DiyService.fetch_emotion_list': views_zone.fetch_emotion_list,
    
    
    'DiyService.fetch_audio_list': views_zone.fetch_audio_list,
    'DiyService.fetch_video_list': views_zone.fetch_video_list,
    'DiyService.fetch_picture_list': views_zone.fetch_picture_list, #创作平台，得到相关资源
    'DiyService.fetch_scrawl_list': views_zone.fetch_scrawl_list,   #涂鸦列表

    'DiyService.get_press_list': views_opus.get_press_list,
    'DiyService.get_opus_list': views_opus.get_opus_list,   #个人空间，得到个人作品列表
    'DiyService.get_opus_info': views_opus.get_opus_info,
    'DiyService.view_opus': views_opus.view_opus,
    #'DiyService.get_opus_page_image': views_opus.get_opus_page_image,
    #'DiyService.get_opus_page_json': views_opus.get_opus_page_json,
    
    'DiyService.create_opus': views_opus.create_opus,   #新建作品
    'DiyService.new_opus_page': views_opus.new_opus_page,
    'DiyService.update_opus_page': views_opus.update_opus_page,
    'DiyService.update_opus_info': views_opus.update_opus_info,
    'DiyService.apply_for_press': views_opus.apply_for_press,   #申请发表作品
    'DiyService.apply_for_template': views_opus.apply_for_template, #作品转为模板
    'DiyService.delete_opus': views_opus.delete_opus,       #删除个人作品
    'DiyService.delete_opus_page': views_opus.delete_opus_page,
    'DiyService.change_opus_page': views_opus.change_opus_page,
    'DiyService.copy_opus': views_opus.copy_opus,   #复制作品
    
    #'DiyService.grade_opus': views_opus.grade_opus, #评级某个作品
    #'DiyService.comment_opus': views_opus.comment_opus, #评论某个作品
    #'DiyService.get_comment_list': views_opus.get_comment_list,
    #'DiyService.praise_opus': views_opus.praise_opus, #对某个作品点赞
    
    'DiyService.grade_opus': views_opus.grade_opus_mongo, #评级某个作品
    'DiyService.comment_opus': views_opus.comment_opus_mongo, #评论某个作品
    'DiyService.get_comment_list': views_opus.get_comment_list_mongo,
    'DiyService.praise_opus': views_opus.praise_opus_mongo, #对某个作品点赞
    
    
    'DiyService.create_album': views_personal.create_album,  #创建相册
    'DiyService.get_album_list': views_personal.get_album_list,  #得到相册列表
    #'DiyService.upload_personal_res': views_personal.upload_personal_res,   #不需要这个接口了
    'DiyService.get_personal_res': views_personal.get_personal_res,
    'DiyService.delete_personal_res': views_personal.delete_personal_res,
    'DiyService.delete_album': views_personal.delete_album,
    'DiyService.update_scrawl': views_personal.update_scrawl,   #涂鸦
    'DiyService.get_scrawl_list': views_personal.get_scrawl_list,
    'DiyService.delete_scrawl': views_personal.delete_scrawl,
    'DiyService.update_camera_image': views_personal.update_camera_image,   #摄像头自拍  的没手机自拍？
    
    #故事大王比赛接口
    'StoryService.get_province_list': views_story.get_province_list,
    'StoryService.get_city_list': views_story.get_city_list,
    'StoryService.get_county_list': views_story.get_county_list,
    'StoryService.get_story_list': views_story.get_story_list,
    'StoryService.vote_story': views_story.vote_story,
    
    #学习资源库get_3qdou_catalog
    'DouService.get_3qdou_catalog': views_3qdou_new.get_3qdou_catalog,
    'DouService.get_all_list': views_3qdou_new.get_all_list,  #得到所有资源列表
    'DouService.search_res_list': views_3qdou_new.search_res_list,
    
    'TopicService.get_emotion_type_list': views_topic.get_emotion_type_list,    #得到表情分类
    'TopicService.fetch_topic_template': views_topic.fetch_topic_template,
    'TopicService.fetch_topic_mark': views_topic.fetch_topic_mark,
    'TopicService.fetch_topic_emotion': views_topic.fetch_topic_emotion,
    
    'TopicService.get_topic_classify': views_topic.get_topic_classify,  #得到活题分类列表
    # 创建话题
    'TopicService.update_topic': views_topic.update_topic,
    'TopicService.fetch_topic_info': views_topic.fetch_topic_info,
    'TopicService.join_topic': views_topic.join_topic,
    # 获取话题列表
    'TopicService.fetch_topic_list': views_topic.fetch_topic_list,
    'TopicService.fetch_topic_page': views_topic.fetch_topic_page,
    # 话题点赞
    'TopicService.topic_praise': views_topic.topic_praise,
    # 增加话题评论
    'TopicService.create_topic_remark': views_topic.create_remark,
    # 获取话题评论列表
    'TopicService.get_remark_list': views_topic.get_remark_list,
    # 获取指定话题
    'TopicService.fetch_topic_one': views_topic.fetch_topic_one,

    'ActivityService.get_province_list': views_activity.get_province_list,
    'ActivityService.get_city_list': views_activity.get_city_list,
    'ActivityService.get_county_list': views_activity.get_county_list,
    
    'ActivityService.fetch_activity_list': views_activity.fetch_activity_list,
    'ActivityService.fetch_activity_info': views_activity.fetch_activity_info,
    # 获取活动与系列活动的活动列表
    'ActivityService.search_activity_and_series': views_activity.get_activity_and_series,
    
    'ActivityService.fetch_activity_fruit_list': views_activity.fetch_activity_fruit_list,
    'ActivityService.grade_fruit': views_activity.grade_fruit,
    #'ActivityService.comment_fruit': views_activity.comment_fruit,
    #'ActivityService.get_comment_list': views_activity.get_comment_list,
    'ActivityService.comment_fruit': views_activity.comment_fruit_mongo,
    'ActivityService.get_comment_list': views_activity.get_comment_list_mongo,
    'ActivityService.praise_fruit': views_activity.praise_fruit_mongodb,
    'ActivityService.preview_fruit': views_activity.preview_fruit,
    'ActivityService.get_client_ip': views_activity.get_client_ip,
    #'ActivityService.vote_fruit': views_activity.vote_fruit,
    'ActivityService.vote_fruit': views_activity.vote_fruit_mongo,

    # 搜索活动和作品的混合列表
    'ActivityService.search_activity_and_fruit': views_activity.search_activity_and_fruit,
    # 搜索系列活动列表
    # editor: kamihati 2015/5/13  用户客户端点击系列活动时取出子活动列表
    'ActivityService.get_series_activity': views_activity.get_series_activity,
    'ActivityService.update_activity': views_activity.update_activity,
    'ActivityService.update_activity_option': views_activity.update_activity_option,
    'ActivityService.update_activity_group': views_activity.update_activity_group,
    'ActivityService.update_activity_group_list': views_activity.update_activity_group_list,
    # coder: kamihati 2015/4/8   修改参赛逻辑符合新版要求
    'ActivityService.update_activity_fruit': views_activity.update_activity_fruit,
    'ActivityService.apply_activity': views_activity.apply_activity,
    'ActivityService.delete_activity': views_activity.delete_activity,
    'ActivityService.apply_fruit': views_activity.apply_fruit,
    'ActivityService.delete_fruit': views_activity.delete_fruit,
    'ActivityService.approve_fruit': views_activity.approve_fruit,

    # 活动报名   editor: kamihati 2015//6/5
    'ActivityService.sign_activity_member': views_activity.sign_activity_member,
    # 是否报名 editor: kamihati: 2015/6/5
    'ActivityService.has_activity_signup': views_activity.has_activity_signup,
}


from pyamf.remoting.gateway.django import DjangoGateway
from WebZone.settings import DEBUG
WebZoneGateway = DjangoGateway(services, debug=DEBUG)


#WebZoneGateway = DjangoGateway(services, debug=is_debug, timezone_offset=28800, expose_request=False)






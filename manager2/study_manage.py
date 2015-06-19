# coding=utf8
'''
coder: kamihati 2015/4/1   后台学习平台管理模块页面配置
'''
from django.shortcuts import render


def book_manage(request):
    '''
    图书管理
    :param request:
    :return:
    '''
    return render(request, 'manager2/study/list_tsgl.html')


def video_manage(request):
    '''
    视频管理
    :param request:
    :return:
    '''
    return render(request, 'manager2/study/list_spgl.html')


def music_manage(request):
    '''
    音频管理
    :param request:
    :return:
    '''
    return render(request, 'manager2/study/list_ypgl.html')


def game_manage(request):
    '''
    游戏管理
    :param request:
    :return:
    '''
    return render(request, 'manager2/study/list_yxgl.html')


def res_type_manage(request):
    '''
    资源类型管理
    :param request:
    :return:
    '''
    return render(request, 'manager2/study/list_zylx.html')


def res_channel_manage(request):
    '''
    资源栏目管理
    :param request:
    :return:
    '''
    return  render(request, 'manager2/study/list_zylm.html')
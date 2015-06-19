#coding: utf-8

from django.shortcuts import render
from django.http import HttpResponse

from utils.decorator import print_trace


def api_set_opus_status(request):
    '''
    设置个人创作的状态
    editor: kamihati 2015/5/8
    :param request:
    :return:
    '''
    # 导入状态设置方法
    from diy.handler import set_opus_status
    if set_opus_status(request.POST.get('id'), request.POST.get('status')):
        return HttpResponse('ok')
    return HttpResponse('fail')


@print_trace
def api_update_opus_top(request):
    '''
    设置个人创作的置顶状态
    editor: kamihati 2015/5/8
    :param request:
    :return:
    '''
    # 导入置顶设置方法
    from diy.handler import set_opus_top
    if set_opus_top(request.POST.get('id'), request.POST.get('status')):
        return HttpResponse('ok')
    return HttpResponse('fail')


@print_trace
def api_edit_opus_comment(request):
    '''
    编辑原创作品评论
    editor: kamihati 2015/5/8
    :param request:
    :return:
    '''
    from diy.handler import edit_opus_comment
    if edit_opus_comment(request.POST.get('id'), request.POST.get('content')):
        return HttpResponse('ok')
    return HttpResponse('fail')


@print_trace
def api_del_opus_comment(request):
    '''
    删除原创作品评论
    editor: kamihati 2015/5/8
    :param request:
    :return:
    '''
    from diy.handler import del_opus_comment
    if del_opus_comment(request.POST.get('id')):
        return HttpResponse('ok')
    return HttpResponse('fail')


def api_update_zone_asset_top(request):
    '''
    更新公共资源的推荐状态
    editor: kamihati 2015/5/11
    :param request:
    :return:
    '''
    from diy.handler import update_zone_asset_top
    if update_zone_asset_top(request.POST.get('id'), request.POST.get('top')):
        return HttpResponse('ok')
    return HttpResponse('fail')


@print_trace
def api_opus_to_template(request):
    '''
    转换个人创作为模板
    editor: kamihati 2015/5/15
    :param request:
    :return:
    '''
    # 导入创作转模板方法
    from diy.handler import opus_to_template
    return HttpResponse(opus_to_template(request.POST.get('id'), request.user))

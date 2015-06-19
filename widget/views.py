# coding=utf8
from django.shortcuts import render
from django.http import HttpResponse

from utils.decorator import print_trace

from utils.db_handler import get_json_str


@print_trace
def api_edit_opus_type(request):
    '''
    编辑个人创作分类
    editor: kamihati 2015/5/7
    :param request:
    :return:
    '''
    param = dict()
    id = request.POST.get('id', '')

    name = request.POST.get('name', '')
    if name != '':
        param['classify_name'] = name
    parent_id = int(request.POST.get('parent_id', '0'))
    param['parent_id'] = parent_id
    if id not in ('', '0'):
        param['id'] = id
        # 初次创建设定分类级别
        param['level'] = 1 if parent_id == 0 else 2
    from widget.handler import edit_opus_type
    result = edit_opus_type(param)
    print 'result=', result
    # 分类名称已存在
    if result == -1:
        return HttpResponse('-1')
    elif result:
        return HttpResponse('ok')
    return HttpResponse('fail')


def api_get_opus_type(request):
    '''
    获取个人创作分类
    editor: kamihati 2015/5/7
    :param request:
    :return:
    '''
    parent_id = int(request.GET.get('parent_id', 0))
    from widget.handler import get_opus_type_list
    return HttpResponse(get_json_str(get_opus_type_list(parent_id)))


def api_del_widget_page_size(request):
    '''
    删除创作页面尺寸
    editor: kamihati 2015/5/11
    :param request:
    :return:
    '''
    from widget.handler import del_widget_page_size
    if del_widget_page_size(request.POST.get('id')):
        return HttpResponse('ok')
    return HttpResponse('fail')


def api_delete_opus_type(request):
    '''
    删除个人创作分类
    editor: kamihati 2015/5/7
    :param request:
    :return:
    '''
    from widget.handler import delete_opus_type
    if delete_opus_type(request.POST.get('id')):
        return HttpResponse('ok')
    return HttpResponse('fail')
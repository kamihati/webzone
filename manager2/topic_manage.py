# coding=utf8
from django.shortcuts import render
from django.http import HttpResponse
import json
from utils.decorator import print_trace

from utils.decorator import manager_required
from manager import has_permissions

# 搜索话题
from topic.handler import search_topic_dict
# 更新话题状态
from topic.handler import update_topic_status
# 查询话题评论列表
from topic.handler import search_comment_dict
# 查询话题表情分页数据
from topic.handler import search_emotion_list
# 导入查询机构地区信息的方法
from library.handler import get_region
# 导入机构model
from library.models import Library
# 导入表情类型model
from topic.models import PhizType


@print_trace
@manager_required
def topic_list(request):
    '''
    把查询到的话题数据转为json返回给页面post请求
    请求方法：GET
    参数： page_index:   页码。从0开始计数
           page_count:    步长。
           key:   搜索关键字
    coder by: kamihati   2015/3/16
    '''
    library_id = request.GET.get('library', 0)
    library_id = int(library_id) if library_id != '' else 0
    page_index = int(request.GET.get("page_index", 1))
    page_size = request.GET.get("page_size", 15)
    search_text = request.GET.get('search_text', '')
    from library.handler import get_library_list_by_user
    library_list = get_library_list_by_user(request.user)
    if library_list.count() == 1:
        library_id = library_list[0].id
    data, data_count = search_topic_dict(search_text, page_index - 1, int(page_size), library_id=library_id)
    provinces = get_region(0)
    return render(
        request, 'manager2/topic/topic_list.html',
        {
            'topic_list': data,
            'page_index': page_index,
            'page_size': page_size,
            'data_count': data_count,
            'search_text': search_text,
            'provinces': provinces,
            'librarys': library_list,
            'library_id': int(library_id) if library_id != '' else ''
        })


@print_trace
@manager_required
def ajax_update_topic_status(request):
    '''
    更新话题状态
    参数描述：
          id:话题id
          status: 话题状态 （0：正常，1：被删除）
    coder: kamihati 2015/3/13
    mark: 根据页面需求可能需要更改
    '''
    if update_topic_status(request.POST.get("id"), request.POST.get("status")):
        return HttpResponse('ok')
    return HttpResponse('fail')


@print_trace
@manager_required
def comment_list(request):
    '''
    话题评论的管理页面
    参数描述：
        page_index: 页码。从1计数
        page_size: 每页数据数。默认15.
        tid: 话题id
    '''
    page_index = request.GET.get("page_index", '1')
    page_size = request.GET.get("page_size", 15)
    topic_id = request.GET.get('tid', 0)
    try:
        page_index = int(page_index) - 1
    except:
        page_index = 0
    data, page_count, data_count = search_comment_dict(topic_id, page_index, int(page_size))
    return render(
        request,
        'manager2/topic/comment_list.html',
        {"topic_id": topic_id, "comment_list": data, "page_count": page_count, "page_index": page_index + 1, "page_size": page_size, "data_count": data_count})


def get_comment_by_id(request):
    '''
    获取指定评论的数据
    -------------------
    参数描述:
        id: 评论id
    mark: 未完成
    '''
    id = int(request.GET.get('id', 0))
    data_obj = dict()
    return HttpResponse(json.dumps(data_obj))


def emotion_manage(request):
    '''
    后台话题表情管理
    参数描述：
        search_text: 查询关键字
        page_index: 页码。从1开始计数
        page_size: 每页数据数。默认15
        type_id: 表情类型。默认0为全部
    '''
    search_text = request.GET.get("search_text", "")
    page_index = int(request.GET.get("page_index", 1))
    page_size = int(request.GET.get("page_size", 15))
    type_id = int(request.GET.get('phiz_type', 0))
    data_list, data_count = search_emotion_list(type_id, search_text, page_index -1, page_size)
    print data_list
    return render(
        request,
        'manager2/topic/emotion_manage.html',
        {
            'phiz_type_list': PhizType.objects.filter(status=0),
            'data_list': data_list,
            'data_count': data_count,
            'page_index': page_index,
            'page_size': page_size,
            'search_text': search_text,
            'phiz_type': type_id
        }
    )

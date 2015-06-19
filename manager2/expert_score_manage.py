# coding=utf8

from django.http import HttpResponse
from django.shortcuts import render


def expert_default(request):
    '''
    专家评分管理首页
    :param request:
    :return:
    '''
    results = dict()
    return  render(request, 'manager2/expert_score/list_zjgl.html', results)


def expert_score(request):
    '''
    专家评分页面
    :param request:
    :return:
    '''
    results = dict()
    return  render(request, 'manager2/expert_score/list_pfgl.html', results)


def score_record(request):
    '''
    专家评分结果页面
    :param request:
    :return:
    '''
    results = dict()
    page_index = int(request.GET.get('page_index', 1))
    page_size = int(request.GET.get('page_size', 15))
    library_id = request.GET.get('library', '')
    activity_id = request.GET.get('activity', '')
    # 导入评分结果分页查询
    from activity.fruit_handler import get_fruit_score_pager
    data_list, data_count = get_fruit_score_pager(
        page_index - 1, page_size, library_id=library_id, activity_id=activity_id)
    results['page_index'] = page_index
    results['page_size'] = page_size
    results['library_id'] = int(library_id) if library_id != '' else ''
    results['activity_id'] = activity_id
    results['data_list'] = data_list
    results['data_count'] = data_count
    from library.handler import get_library_list_by_user
    results['library_list'] = get_library_list_by_user(request.user)
    return  render(request, 'manager2/expert_score/list_pfjg.html', results)

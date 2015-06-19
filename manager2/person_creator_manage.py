# coding=utf8

from django.shortcuts import render

# 导入获取个人创作类别的方法
from widget.handler import get_opus_type_list
# 导入获取个人创作分页数据的方法
from diy.handler import get_auth_opus_pager
# 根据当前用户获取机构列表
from library.handler import get_library_list_by_user
# 导入获取个人创作分类的方法
from widget.handler import get_opus_type_list
# 导入获取机构地区信息的方法
from library.handler import get_region

def person_creator_default(request):
    '''
    个人创作管理首页
    editor: kamihati 2015/5/8
    editor: kamihati 2015/6/3  使用新的页面设计
    :param request:
    :return:
    '''
    page_index = request.GET.get('page_index', 1)
    page_index = int(page_index) if page_index != '' else 1
    page_size = int(request.GET.get('page_size', 13))
    key = request.GET.get('search_text', '')
    library_id = request.GET.get('library', '')
    class1_id = request.GET.get('class1', '')
    class2_id = request.GET.get('class2', '')
    begin_time = request.GET.get('begin_time', '')
    end_time = request.GET.get('end_time', '')
    is_activity = request.GET.get('is_activity', '')
    library_list = get_library_list_by_user(request.user)
    if library_list.count() == 1:
        library_id = library_list[0].id
    result = dict()
    result['data_count'] = 0
    result['page_index'] = page_index
    result['page_size'] = page_size
    result['search_text'] = key
    result['data_list'], result['data_count'] = get_auth_opus_pager(
        page_index - 1, page_size, key=key,
        library_id=library_id, class1=class1_id, class2=class2_id,
        is_activity=is_activity, begin_time=begin_time, end_time=end_time)
    result['library_list'] = library_list
    result['class1_list'] = get_opus_type_list(0)
    result['begin_time'] = begin_time
    result['end_time'] = end_time
    result['is_activity'] = is_activity
    result['library_id'] = int(library_id) if library_id != '' else ''
    result['class1_id'] = int(class1_id) if class1_id != '' else ''
    result['class2_id'] = int(class2_id) if class2_id != '' else ''
    # 导入获取指定id的类别列表
    from widget.handler import get_opus_type_list_by_id
    #result['class2_data'] = get_opus_type_list_by_id(class2_id)
    if library_id or class1_id or class2_id or begin_time or end_time or is_activity:
        result['is_detail'] = 1
    return render(request, 'manager2/person_creator/list_gerencz.html', result)

def person_creator_wait(request):
    '''
    个人创作管理--待审核作品
    editor: kamihati 2015/5/8
    :param request:
    :return:
    '''
    page_index = request.GET.get('page_index', 1)
    page_index = int(page_index) if page_index != '' else 1
    page_size = int(request.GET.get('page_size', 13))
    key = request.GET.get('search_text', '')
    library_id = request.GET.get('library', '')
    class1_id = request.GET.get('class1', '')
    class2_id = request.GET.get('class2', '')
    begin_time = request.GET.get('begin_time', '')
    end_time = request.GET.get('end_time', '')
    is_activity = request.GET.get('is_activity', '')
    library_list = get_library_list_by_user(request.user)
    if library_list.count() == 1:
        library_id = library_list[0].id
    result = dict()
    result['page_index'] = page_index
    result['page_size'] = page_size
    result['search_text'] = key
    result['data_list'], result['data_count'] = get_auth_opus_pager(
        page_index - 1, page_size, key=key,
        status=1,
        library_id=library_id, class1=class1_id, class2=class2_id,
        is_activity=is_activity, begin_time=begin_time, end_time=end_time)
    result['library_list'] = library_list
    result['class1_list'] = get_opus_type_list(0)
    result['begin_time'] = begin_time
    result['end_time'] = end_time
    result['is_activity'] = is_activity
    result['library_id'] = int(library_id) if library_id != '' else ''
    result['class1_id'] = int(class1_id) if class1_id != '' else ''
    result['class2_id'] = int(class2_id) if class2_id != '' else ''
    if library_id or class1_id or class2_id or begin_time or end_time or is_activity:
        result['is_detail'] = 1
    return render(request, 'manager2/person_creator/list_gerencz_wait.html', result)


def person_creator_new(request):
    '''
    个人创作管理首页--草稿作品
    editor: kamihati 2015/5/8
    :param request:
    :return:
    '''
    page_index = request.GET.get('page_index', 1)
    page_index = int(page_index) if page_index != '' else 1
    page_size = int(request.GET.get('page_size', 13))
    key = request.GET.get('search_text', '')
    library_id = request.GET.get('library', '')
    class1_id = request.GET.get('class1', '')
    class2_id = request.GET.get('class2', '')
    begin_time = request.GET.get('begin_time', '')
    end_time = request.GET.get('end_time', '')
    is_activity = request.GET.get('is_activity', '')
    library_list = get_library_list_by_user(request.user)
    if library_list.count() == 1:
        library_id = library_list[0].id
    result = dict()
    result['data_count'] = 0
    result['page_index'] = page_index
    result['page_size'] = page_size
    result['search_text'] = key
    result['data_list'], result['data_count'] = get_auth_opus_pager(
        page_index - 1, page_size, key=key,
        status=0,
        library_id=library_id, class1=class1_id, class2=class2_id,
        is_activity=is_activity, begin_time=begin_time, end_time=end_time)
    result['library_list'] = library_list
    result['class1_list'] = get_opus_type_list(0)
    result['begin_time'] = begin_time
    result['end_time'] = end_time
    result['is_activity'] = is_activity
    result['library_id'] = int(library_id) if library_id != '' else ''
    result['class1_id'] = int(class1_id) if class1_id != '' else ''
    result['class2_id'] = int(class2_id) if class2_id != '' else ''
    if library_id or class1_id or class2_id or begin_time or end_time or is_activity:
        result['is_detail'] = 1
    return render(request, 'manager2/person_creator/list_gerencz_new.html', result)


def person_creator_remark(request):
    '''
    个人作品评论管理
    editor: kamihati 2015/5/8   此页面为作品列表。由于与个人创作页面功能重复。决定取消。评论列表由个人创作页面进入
    :param request:
    :return:
    '''
    page_index = int(request.GET.get("page_index", 1))
    page_size = request.GET.get("page_size", 15)
    opus_id = request.GET.get('id', 0)
    print 'opus_id=', opus_id
    from diy.handler import get_opus_comment_pager
    data_list, data_count = get_opus_comment_pager(opus_id, page_index, page_size)
    result = {
        'data_list': data_list,
        'page_index': page_index,
        'page_size': page_size,
        'data_count': data_count}
    return render(request, 'manager2/person_creator/list_gerenpl.html', result)


def person_creator_remark_list(request):
    '''
    个人作品评论列表
    editor: kamihati 2015/5/8
    :param request:
    :return:
    '''
    page_index = int(request.GET.get("page_index", 1))
    page_size = request.GET.get("page_size", 15)
    opus_id = request.GET.get('id', 0)
    # 导入获取mongodb中个人创作评论的数据
    from diy.handler import get_opus_comment_pager
    data_list, data_count = get_opus_comment_pager(opus_id, page_index -1, page_size)
    result = dict(data_list=data_list,
                  data_count=data_count,
                  page_index=page_index,
                  page_size=page_size,
                  opus_id=opus_id)
    return render(request, 'manager2/person_creator/list_gerenpln.html', result)


def person_creator_types(request):
    '''
    个人作品分类管理
    editor: kamihati 2015/5/7
    :param request:
    :return:
    '''
    parent_list = get_opus_type_list(0, is_sys=1)
    result = dict(parent_list=parent_list)
    return render(request, 'manager2/person_creator/list_gerenfl.html', result)

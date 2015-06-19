# coding=utf8
'''
素材管理后台页面
coder: kamihati 2015/3/27
'''
from django.shortcuts import render
from django.http import HttpResponse
# 导入异常输出方法
from utils.decorator import print_trace
# 导入资源分类和资源风格model
from resources.models import ResourceType, ResourceStyle
# 导入资源分类列表和资源风格列表获取方法
from resources.handler import get_resource_type_list, get_resource_style_list
# 导入个人资源分类model
from resources.models import ResourceTypePerson
# 导入获取机构列表方法
from library.handler import get_library_list_by_user
# 导入获取个人资源列表的方法
from resources.handler import get_person_resource_pager
# 导入获取公共资源列表的方法
from resources.handler import get_common_resource_pager
from library.handler import get_library_list_by_user


@print_trace
def resource_type_manage(request):
    '''
    素材分类管理
    :param request:
    :return:
    '''
    # 素材类型列表 公共。个人
    common_res_types, person_res_types = get_resource_type_list()
    # 公共素材风格列表
    common_res_styles = get_resource_style_list()
    results = dict()
    results['common_types'], results['person_types'] = get_resource_type_list()
    results['common_styles'] = common_res_styles
    return render(request, 'manager2/resource/type_manage.html', results)


@print_trace
def person_resource_manage(request):
    '''
    个人素材管理
    :param request:
    :return:
    '''
    # 所有机构列表
    library_list = get_library_list_by_user(request.user)

    results = dict()
    results['library_list'] = library_list
    # 个人素材类型列表
    results['person_types'] = get_resource_type_list(2)

    page_index = int(request.GET.get('page_index', '1'))
    page_size = int(request.GET.get('page_size', '15'))
    key = request.GET.get('key', '')
    library_id = request.GET.get('library_id', '') if library_list.count > 1 else library_list[0].id
    if library_list.count() == 1:
        library_id = library_list[0].id
    type_id = request.GET.get('type_id', '')
    results['key'] = key
    results['library_id'] = int(library_id) if library_id != '' else ''

    results['type_id'] = int(type_id) if type_id != '' else ''
    results['page_index'] = page_index
    results['page_size'] = page_size
    results['data_list'], results['data_count'], results['page_count'] = get_person_resource_pager(page_index - 1,
                                                                                                   page_size,
                                                                                                   key=key,
                                                                                                   library_id=library_id,
                                                                                                   type_id=type_id)
    return  render(request, 'manager2/resource/person_manage.html', results)


@print_trace
def common_resource_manage(request):
    '''
    公共素材管理
    editor: kamihati 2015/5/11
    :param request:
    :return:
    '''
    results = dict()
    results['library_list'] = get_library_list_by_user(request.user)
    # 公共素材类型列表
    results['resource_type'] = get_resource_type_list(1)
    # 公共素材风格列表
    results['resource_style'] = get_resource_style_list()
    page_index = int(request.GET.get('page_index', '1'))
    page_size = int(request.GET.get('page_size', '15'))
    key = request.GET.get('key', '')
    library_id = request.GET.get('library_id', '') if results['library_list'].count() > 1 else results['library_list'][0].id
    type_id = request.GET.get('type_id', '')
    style_id = request.GET.get('style_id', '')
    results['key'] = key
    results['library_id'] = int(library_id) if library_id != '' else ''
    results['type_id'] = int(type_id) if type_id != '' else ''
    results['style_id'] = int(style_id) if style_id != '' else ''
    results['page_index'] = page_index
    results['page_size'] = page_size
    results['data_list'], results['data_count'], results['page_count'] = get_common_resource_pager(
        page_index - 1, page_size,
        key=key, library_id=library_id, type_id=type_id, style_id=style_id)
    from widget.handler import get_page_size_list
    print get_page_size_list()
    results['size_list'] = get_page_size_list()
    return  render(request, 'manager2/resource/common_manage.html', results)


@print_trace
def template_manage(request):
    '''
    模板管理
    editor: kamihati 2015/5/11
    :param request:
    :return:
    '''
    page_index = int(request.GET.get('page_index', 1))
    page_size = int(request.GET.get('page_size', 13))
    key = request.GET.get('key', '')
    library_list = get_library_list_by_user(request.user)
    library_id = request.GET.get('library_id', '') if library_list.count > 1 else library_list[0].id
    class1_id = request.GET.get('class1', '')
    class2_id = request.GET.get('class2', '')
    result = dict()
    result['library_list'] = library_list
    # 导入获取作品门类与子类的方法
    from widget.handler import get_opus_type_list
    result['class1_list'] = get_opus_type_list(0)
    from diy.handler import get_zone_asset_pager
    result['data_list'], result['data_count'] = get_zone_asset_pager(
        page_index - 1, page_size,
        library_id=library_id, type_id=class1_id, class_id=class2_id,
        key=key,
        is_opus=True
    )
    result['key'] = key
    result['page_index'] = page_index
    result['page_size'] = page_size
    result['type_id'] = class1_id
    result['class1_id'] = int(class1_id) if class1_id != '' else ''
    result['class2_id'] = class2_id
    result['library_id'] = int(library_id) if library_id != '' else ''
    return  render(request, 'manager2/resource/template_manage.html', result)


@print_trace
def size_manage(request):
    '''
    作品尺寸管理
    editor: kamihati 2015/5/11
    :param request:
    :return:
    '''
    results = dict()
    results['library_list'] = get_library_list_by_user(request.user)
    # 公共素材类型列表
    results['resource_type'] = get_resource_type_list(1)
    page_index = int(request.GET.get('page_index', '1'))
    page_size = int(request.GET.get('page_size', '15'))
    key = request.GET.get('key', '')
    library_id = request.GET.get('library_id', '') if results['library_list'].count() > 1 else results['library_list'][0].id

    if results['library_list'].count() == 1:
        library_id = results['library_list'][0].id
    results['key'] = key
    results['library_id'] = int(library_id) if library_id != '' else ''
    results['page_index'] = page_index
    results['page_size'] = page_size
    # 导入获取作品尺寸分页数据的方法
    from widget.handler import get_widget_page_size_pager
    results['data_list'], results['data_count'] = get_widget_page_size_pager(
        page_index - 1, page_size, title=key, library_id=library_id)
    return render(request, 'manager2/resource/size_manage.html', results)

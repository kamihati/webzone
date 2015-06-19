# coding=utf8
# editor: kamihati 2015/6/4  后台模板管理

from django.shortcuts import render
from library.handler import get_library_list_by_user

def template_list(request):
    '''
    模板管理
    editor: kamihati 2015/6/4
    :param request:
    :return:
    '''
    page_index = int(request.GET.get('page_index', 1))
    page_size = int(request.GET.get('page_size', 13))
    key = request.GET.get('key', '')
    library_list = get_library_list_by_user(request.user)
    library_id = '' if library_list.count > 1 else library_list[0].id
    class1_id = request.GET.get('class1', '')
    class2_id = request.GET.get('class2', '')
    result = dict()
    # 导入获取作品门类与子类的方法
    from widget.handler import get_opus_type_list
    result['class1_list'] = get_opus_type_list(0, is_sys=1)
    from diy.handler import get_zone_asset_pager
    result['data_list'], result['data_count'] = get_zone_asset_pager(
        page_index - 1, page_size,
        library_id=library_id, type_id=class1_id, class_id=class2_id,
        key=key,
        is_opus=True,
        res_type=4
    )
    result['key'] = key
    result['page_index'] = page_index
    result['page_size'] = page_size
    result['class1_id'] = int(class1_id) if class1_id != '' else ''
    result['class2_id'] = class2_id
    return render(request, 'manager2/opus_temp/list_mbyc.html', result)


def opus_to_template(request):
    '''
    作品转模板
    editor: kamihati 2015/6/4
    :param request:
    :return:
    '''
    page_index = int(request.GET.get('page_index', 1))
    page_size = int(request.GET.get('page_size', 13))
    key = request.GET.get('key', '')
    library_list = get_library_list_by_user(request.user)
    library_id = '' if library_list.count > 1 else library_list[0].id
    class2_id = request.GET.get('class2', '')
    class1_id = request.GET.get('class1', '')
    result = dict()
    # 导入获取作品子类的方法
    from widget.handler import get_opus_type_by_level
    result['class2_list'] = get_opus_type_by_level(1)
    result['class1_list'] = get_opus_type_by_level(0)
    from diy.handler import get_auth_opus_pager
    result['data_list'], result['data_count'] = get_auth_opus_pager(
        page_index - 1, page_size, key=key,
        status=2, library_id=library_id, class2=class2_id, class1=class1_id)
    result['key'] = key
    result['page_index'] = page_index
    result['page_size'] = page_size
    result['class2_id'] = int(class2_id) if class2_id != '' else ''
    result['class1_id'] = int(class1_id) if class1_id != '' else ''
    return render(request, 'manager2/opus_temp/list_mbzp.html', result)


def size_manage(request):
    '''
    尺寸管理
    editor: kamihati 2015/6/4
    :param request:
    :return:
    '''
    page_index = int(request.GET.get('page_index', 1))
    page_size = int(request.GET.get('page_size', 13))
    key = request.GET.get('key', '')
    library_list = get_library_list_by_user(request.user)
    library_id = '' if library_list.count > 1 else library_list[0].id
    class1_id = request.GET.get('class1', '')
    class2_id = request.GET.get('class2', '')
    result = dict()
    # 导入获取作品门类与子类的方法
    from widget.handler import get_opus_type_list
    result['class1_list'] = get_opus_type_list(0)
    # 导入获取作品尺寸分页数据的方法
    from widget.handler import get_widget_page_size_pager
    result['data_list'], result['data_count'] = get_widget_page_size_pager(
        page_index - 1, page_size, title=key, library_id=library_id)
    result['key'] = key
    result['page_index'] = page_index
    result['page_size'] = page_size
    result['class1_id'] = int(class1_id) if class1_id != '' else ''
    result['class2_id'] = class2_id
    return render(request, 'manager2/opus_temp/list_mbcc.html', result)


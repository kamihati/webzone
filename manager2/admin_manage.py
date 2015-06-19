# coding=utf8
import json
from django.shortcuts import render
from django.http import HttpResponse

# 导入获取机构列表的方法
from library.handler import get_library_list
# 导入页面权限验证
from utils.decorator import validate_permission
# 导入获取页面ztree控件使用的library列表
from library.handler import get_ztree_library
# 根据当前用户类型返回不同的机构列表
from library.handler import get_library_list_by_user
# 导入获取机构管理员的方法
from library.handler import get_library_manager
# 导入机构表
from library.models import Library


@validate_permission
def level_2_manager(request):
    '''
    二级管理员管理
    editor: kamihati 2015/5/4
    :param request:
    :return:
    '''
    result = dict()
    # 导入获取二级管理员分页数据的方法
    from account.handler import get_manager_pager
    page_index = int(request.GET.get('page_index', 1))
    page_size = int(request.GET.get('page_size', 15))
    search_text = request.GET.get('search_text', '')
    data_list, data_count = get_manager_pager(page_index - 1, page_size, key=search_text)
    result['page_index'] = page_index
    result['page_size'] = page_size
    result['search_text'] = search_text
    result['data_list'] = data_list
    result['data_count'] = data_count
    # 获取处于可用状态的机构列表
    result['library_list'] = get_library_list_by_user(request.user)
    # 页面机构树选择控件
    # result['znodes'] = json.dumps(get_ztree_library(request.user.library_id, open=False))
    return render(request, 'manager2/admin/list_erjigly.html', result)


def library_manager(request):
    '''
    机构管理员管理
    editor: kamihati 2015/6/16  增加机构总管理员访问的处理
    :param request:
    :return:
    '''
    page_index = int(request.GET.get('page_index', 1))
    page_size = int(request.GET.get('page_size', 15))
    search_text = request.GET.get('search_text', '')
    library_id = request.GET.get('library', '')
    library_status = request.GET.get('library_status', '')
    library_list = get_library_list_by_user(request.user)

    if library_list.count() == 1:
        library_id = library_list[0].id

    result = dict()
    data_list, data_count = get_library_manager(
        page_index-1, page_size, key=search_text,
        library_id=library_id, auth_type=1, library_status=library_status)
    result['data_list'] = data_list
    result['data_count'] = data_count
    result['page_index'] = page_index
    result['page_size'] = page_size
    result['library_id'] = int(library_id) if library_id != '' else ''
    result['library_status'] = library_status
    result['search_text'] = search_text
    result['library_list'] = library_list
    return render(request, 'manager2/admin/list_jigougly.html', result)

def library_edit(request):
    '''
    修改或新增机构信息
    editor: kamihati 2015/5/7
    :param request:
    :return:
    '''
    id = request.GET.get('id', '')
    result = dict()
    if id != '':
        from library.models import Library
        result['library'] = Library.objects.get(pk=id)
        result['expire_time'] = str(result['library'].expire_time.date())
        result['manager'] = result['library'].user
    return  render(request, 'manager2/admin/list_jigou.html', result)


def library_edit2(request):
    '''
    机构信息明细编辑页面
    editor: kamihati 2015/5/7  鉴于明细页面的数据现大都弃用。故此页面暂时搁置
    :param request:
    :return:
    '''
    return render(request, 'manager2/admin/list_jigoux.html', dict())


def library_admin(request):
    '''
    机构普通管理员管理
    editor: kamihati 2015/5/5
    :param request:
    :return:
    '''
    page_index = int(request.GET.get('page_index', 1))
    page_size = int(request.GET.get('page_size', 15))
    search_text = request.GET.get('search_text', '')
    library_id = request.GET.get('id')
    result = dict()
    # auth_type =2为普通管理员
    data_list, data_count = get_library_manager(page_index-1, page_size, key=search_text, library_id=library_id, auth_type=2)
    result['data_list'] = data_list
    result['data_count'] = data_count
    result['page_index'] = page_index
    result['page_size'] = page_size
    result['library_id'] = int(library_id)
    result['library'] = Library.objects.get(pk=library_id)
    result['search_text'] = search_text
    return render(request, 'manager2/admin/list_ptgly.html', result)


def user_manager(request):
    '''
    会员管理
    editor: kamihati 2015/5/5
    :param request:
    :return:
    '''
    result = dict()
    page_index = int(request.GET.get('page_index', 1))
    page_size = int(request.GET.get('page_size', 15))
    search_text = request.GET.get('search_text', '')
    library_id = request.GET.get('library', '')
    library_list = get_library_list_by_user(request.user)
    if library_list.count() == 1:
        library_id = library_list[0].id
    # 导入会员分页数据获取方法
    from account.handler import get_user_pager
    data_list, data_count = get_user_pager(page_index - 1, page_size, library_id=library_id, key=search_text)
    # 导入获取用户活动作品数量的方法
    from activity.fruit_handler import get_user_fruit_count
    # 导入获取用户原创作品数量的方法
    from diy.handler import get_user_opus_count
    for data in data_list:
        # 活动作品总数.获取已发布的
        data['activity_fruit_count'] = get_user_fruit_count(data['id'], 2)
        # 发布中原创作品.获取已发表的
        data['publish_fruit_count'] = get_user_opus_count(data['id'], 2)
        # 待审核作品。为待审核的活动作品与待审核原创作品之和
        data['new_fruit_count'] = get_user_fruit_count(data['id'], 0) + get_user_opus_count(data['id'], 1)

    result['page_index'] = page_index
    result['page_size'] = page_size
    result['search_text'] = search_text
    result['data_list'] = data_list
    result['data_count'] = data_count
    # 获取处于可用状态的机构列表
    result['library_list'] = library_list
    result['library_id'] = library_id if library_id == '' else int(library_id)
    return render(request, 'manager2/admin/list_huiyuan.html', result)


def old_library_manager(request):
    '''
    到期机构管理
    editor: kamihati 2015/5/4
    :param request:
    :return:
    '''
    result = dict()
    page_index = int(request.GET.get('page_index', 1))
    page_size = int(request.GET.get('page_size', 15))
    # 导入机构分页数据获取方法
    from library.handler import get_library_pager
    data_list, data_count = get_library_pager(page_index - 1, page_size, quick_expire=True)
    result = dict(data_list=data_list,
                  data_count=data_count,
                  page_index=page_index,
                  page_size=page_size)
    return render(request, 'manager2/admin/list_daoqi.html', result)

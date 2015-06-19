# coding=utf8
# coder：kamihati 2015/4/1   配置活动比赛创作管理模块各页面

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
import json, datetime

# 导入异常输出方法
from utils.decorator import print_trace
# 导入管理员权限验证
from utils.decorator import manager_required

# 导入datetime格式化为datetime html控件所需格式的方法
from utils.decorator import format_datetime_to_str

# 导入活动model
from activity.models import ActivityList
# 导入播报与结果model
from activity.models import ActivityNews
# 导入活动背景model
from activity.models import ActivityBackground
# 导入活动报名选项表
from activity.models import ActivityOption

# 导入获取机构方法
from library.handler import get_library_list_by_user
# 导入获取活动背景的方法
from activity.handler import get_activity_background_list
# 导入获取供ztree控件使用的地区机构节点数据
from library.handler import get_ztree_library
# 导入获取活动作品分页数据的方法
from activity.fruit_handler import get_activity_fruit_pager
# 导入获取活动分组的方法
from activity.group_handler import get_activity_group


def activity_sign_up_member_list(request):
    '''
    报名成员列表
    editor: kamihati 2015/4/28  活动管理页面点击报名人数进入
    :param request:
    :return:
    '''
    result = dict()
    page_index = int(request.GET.get('page_index', 1))
    page_size = int(request.GET.get('page_size', 15))
    activity_id = request.GET.get('id', '')
    # 导入获取报名记录数据的方法
    from activity.sign_handler import get_sing_member_pager
    data_list, data_count = get_sing_member_pager(page_index - 1, page_size, activity_id=activity_id)
    result['data_list'] = data_list
    result['data_count'] = data_count
    result['page_index'] = page_index
    result['page_size'] = page_size
    result['activity_id'] = activity_id
    return  render(request, "manager2/activity/list_bmrs.html", result)


def activity_join_member_list(request):
    '''
    参与人员列表
    editor: kamihati 2015/4/28  活动管理页面点击参与人数进入
    :param request:
    :return:
    '''
    result = dict()
    page_index = int(request.GET.get('page_index', 1))
    page_size = int(request.GET.get('page_size', 15))
    activity_id = request.GET.get('id', '')
    # 导入获取报名记录数据的方法
    from activity.fruit_handler import get_join_member_pager
    data_list, data_count = get_join_member_pager(page_index - 1, page_size, activity_id=activity_id)
    result['data_list'] = data_list
    result['data_count'] = data_count
    result['page_index'] = page_index
    result['page_size'] = page_size
    result['activity_id'] = activity_id
    return render(request, "manager2/activity/list_cjrs.html", result)


@print_trace
def download_activity_join_member(request):
    '''
    下载制定活动的参与人资料
    editor: kamihati 2015/5/20
    :param request:
    :return:
    '''
    # 导入创建参与人数记录excel文件的方法
    from activity.fruit_handler import create_join_member_excel
    return create_join_member_excel(request.GET.get('id'), 'data.xls')



@manager_required
def edit_activity(request):
    '''
    创建活动
    editor: kamihati 2015/5/15  修改年份不正确导致报错的bug
    :param request:
    :return:
    '''
    # 获取供机构选择控件使用的数据
    ztree_nodes = ""
    page_data = dict()
    id = request.GET.get('id', 0)
    # 需要在页面选中的机构
    checked_library = []
    # 如果id不为0则说明是编辑界面。需要初始化页面控件
    if id != 0:
        activity = ActivityList.objects.get(pk=id)
        page_data['activity'] = activity
        # 初始化input日期控件的值
        page_data['sign_up_begin_time'] = format_datetime_to_str(activity.sign_up_start_time)
        page_data['sign_up_end_time'] = format_datetime_to_str(activity.sign_up_end_time)
        if activity.activity_start_time is not None:
            page_data['activity_start_time'] = format_datetime_to_str(activity.activity_start_time)
        if activity.activity_end_time is not None:
            page_data['activity_end_time'] = format_datetime_to_str(activity.activity_end_time)
        if activity.submit_start_time is not None:
            page_data['submit_start_time'] = format_datetime_to_str(activity.submit_start_time)
        if activity.submit_end_time is not None:
            page_data['submit_end_time'] = format_datetime_to_str(activity.submit_end_time)
        if activity.vote_start_time is not None:
            page_data['vote_start_time'] = format_datetime_to_str(activity.vote_start_time)
        if activity.vote_end_time is not None:
            page_data['vote_end_time'] = format_datetime_to_str(activity.vote_end_time)
        if activity.scope_list not in ('0', '1'):
            checked_library = activity.scope_list.split(",")

        # 活动分组
        page_data['groups'] = get_activity_group(id)
        # 获取活动报名信息
        options = ActivityOption.objects.filter(activity_id=id)
        if options:
            page_data['activity_option'] = options[0]

    # 页面机构树选择控件
    page_data['znodes'] = json.dumps(get_ztree_library(request.user.library_id, checked_library=checked_library))
    # 获取活动背景列表
    page_data['background_list'] = get_activity_background_list()
    return render(request, 'manager2/activity/list_hdwl.html', page_data)


def edit_activity_step1(request):
    '''
    编辑活动第一步
    editor:kamihati 2015/6/9
    :param request:
    :return:
    '''
    page_data = dict()
    id = request.GET.get('id', 0)
    # 需要在页面选中的机构
    checked_library = []
    # 如果id不为0则说明是编辑界面。需要初始化页面控件
    if id != 0:
        activity = ActivityList.objects.get(pk=id)
        page_data['activity'] = activity
        # 活动开始时间（现场活动）
        if activity.activity_start_time is not None:
            page_data['activity_start_time'] = format_datetime_to_str(activity.activity_start_time)
        # 活动结束时间（现场）
        if activity.activity_end_time is not None:
            page_data['activity_end_time'] = format_datetime_to_str(activity.activity_end_time)
        # 投票开始时间(网络）
        if activity.vote_start_time is not None:
            page_data['vote_start_time'] = format_datetime_to_str(activity.vote_start_time)
        # 投票结束时间(网络
        if activity.vote_end_time is not None:
            page_data['vote_end_time'] = format_datetime_to_str(activity.vote_end_time)
    return render(request, 'manager2/activity/list_actives.html', page_data)


def edit_activity_step2(request):
    '''
    编辑活动第二步
    editor:kamihati 2015/6/9
    :param request:
    :return:
    '''
    page_data = dict()
    id = request.GET.get('id', 0)
    # 需要在页面选中的机构
    checked_library = []
    # 如果id不为0则说明是编辑界面。需要初始化页面控件
    if id != 0:
        activity = ActivityList.objects.get(pk=id)
        page_data['activity'] = activity
        # 初始化input日期控件的值
        page_data['sign_up_begin_time'] = format_datetime_to_str(activity.sign_up_start_time)
        page_data['sign_up_end_time'] = format_datetime_to_str(activity.sign_up_end_time)
        # 投稿时间（网络
        if activity.submit_start_time is not None:
            page_data['submit_start_time'] = format_datetime_to_str(activity.submit_start_time)
        # 投稿结束时间（网络
        if activity.submit_end_time is not None:
            page_data['submit_end_time'] = format_datetime_to_str(activity.submit_end_time)

    return render(request, 'manager2/activity/list_activesx.html', page_data)


def activity_list(request):
    '''
    活动列表。对负责范围内的活动进行管理
    editor:  kamihati 2015/4/24
    editor: kamihati 2015/6/5 根据新版设计进行修改
    :param request:
    :return:
    '''
    page_index = int(request.GET.get('page_index', 1))
    page_size = int(request.GET.get('page_size', 9))
    library_id = request.GET.get('library', '')
    place_type = request.GET.get('place_type', '')
    search_status = request.GET.get('activity_status', '')
    search_text = request.GET.get('search_text', '')
    series_id = request.GET.get('series_id', '')
    fruit_type = request.GET.get('fruit_type', '')

    library_list = get_library_list_by_user(request.user)
    if library_list.count() == 1:
        library_id = library_list[0].id

    # 如果是点击系列活动名称的搜索则忽略其他条件的搜索
    if series_id not in ('', '0'):
        page_index = 1
        library_id = ''
        place_type = ''
        search_status = ''
        search_text = ''

    # 导入获取活动列表分页数据的方法
    from activity.handler import get_activity_pager
    data_list, data_count = get_activity_pager(
        page_index - 1, page_size,
        library_id=library_id, place_type=place_type, activity_status=search_status, search_text=search_text,
        series_id=series_id, fruit_type=fruit_type)
    page_data = dict()
    page_data['library_list'] = library_list
    page_data['data_list'] = data_list
    page_data['data_count'] = data_count
    page_data['page_index'] = page_index
    page_data['page_size'] = page_size
    page_data['library_id'] = int(library_id) if library_id != '' else ''
    page_data['place_type'] = place_type
    page_data['search_status'] = search_status
    page_data['search_text'] = search_text
    from activity.series_handler import get_activity_series_list
    page_data['series_list'] = get_activity_series_list(request.user.library.id, 0)
    page_data['series_id'] = int(series_id) if series_id != '' else ''
    page_data['type_list'] = [(2, u"个人创作"), (3,u"图片"), (4, u"视频"), (5, u'特殊'), (6, u'音乐')]
    page_data['fruit_type'] = int(fruit_type) if fruit_type != '' else ''
    return render(request, 'manager2/activity/list_hdlb.html', page_data)


def activity_fruit_manage(request):
    '''
    活动作品管理
    editor: kamihati 2015/4/28
    :param request:
    :return:
    '''
    page_index = int(request.GET.get('page_index', 1))
    page_size = int(request.GET.get('page_size', 15))
    library_id = request.GET.get('library', '')
    activity_id = request.GET.get('activity', '')
    search_text = request.GET.get('search_text', "")
    place_type = request.GET.get('place_type', '')
    data_list, data_count = get_activity_fruit_pager(
        page_index - 1,
        page_size,
        library_id=library_id,
        activity_id=activity_id,
        search_text=search_text,
        place_type=place_type
    )
    # 导入获取当前用户所在机构活动的方法
    from activity.handler import get_activity_list_by_request
    return render(request,
                  'manager2/activity/list_hdzp.html',
                  dict(page_index=page_index,
                       page_size=page_size,
                       data_list=data_list,
                       data_count=data_count,
                       library_id=int(library_id) if library_id != '' else '',
                       activity_id=int(activity_id) if activity_id != '' else '',
                       search_text=search_text,
                       place_type=place_type,
                       library_list=get_library_list_by_user(request.user),
                       activity_list=get_activity_list_by_request(request)))


def news_manage(request):
    '''
    结果与新闻管理
    editor: kamihati 2015/5/12
    :param request:
    :return:
    '''
    page_index = int(request.GET.get('page_index', 1))
    page_size = int(request.GET.get('page_size', 15))
    library_id = int(request.GET.get('library', 0))
    activity_id = int(request.GET.get('activity', 0))
    search_text = request.GET.get('search_text', None)
    # 导入结果与新闻分页数据
    from activity.news_handler import get_activity_news_pager
    data_list, data_count = get_activity_news_pager(
        page_index - 1,
        page_size,
        library_id=library_id,
        activity_id=activity_id,
        search_text=search_text)
    return render(
        request,
        'manager2/activity/list_jggl.html',
        dict(data_list=data_list,
             data_count=data_count,
             page_size=page_size,
             page_index=page_index,
             library_list=get_library_list_by_user(request.user),
             library_id=library_id,
             activity_id=activity_id,
             search_text=search_text))


@print_trace
def news_edit(request):
    '''
    结果与新闻编辑
    editor: kamihati 2015/4/22
    :param request:
              id  为修改。否则为新增
    :return:
    '''
    news_type = int(request.GET.get('news_type', 1))
    id = request.GET.get('id', None)
    news = ActivityNews.objects.get(id=id) if id is not None else None

    if request.POST:
        param = dict()
        if id is None:
            param['user_id'] = request.user.id
        else:
            param['id'] = id
        library_id = request.POST.get('library', None)
        if library_id is not None:
            param['library_id'] = library_id
        activity_id = request.POST.get('activity', None)
        if activity_id is not None:
            param['activity_id'] = activity_id
        news_type = request.POST.get('news_type', None)
        if news_type is not None:
            param['news_type'] = news_type
        title = request.POST.get('title', None)
        if title is not None:
            param['title'] = title
        cover = request.POST.get('cover', '')
        if cover != '':
            param['cover'] = cover
        background = request.POST.get('background', None)
        if background is not None:
            param['background_id'] = background
        content = request.POST.get('content', None)
        if content is not None:
            param['content'] = content
        # 导入结果与新闻编辑方法
        from activity.news_handler import edit_activity_news
        news = edit_activity_news(param)
        return HttpResponse("ok")
    library_list = get_library_list_by_user(request.user)

    return  render(
        request,
        'manager2/activity/edit_activity_news.html',
        dict(news=news,
             news_type=news_type,
             library_list=library_list,
             background_list=get_activity_background_list()))


def news_view(request):
    '''
    播报或结果查看
    :param request:
    :return:
    '''
    id = request.GET.get('id', 0)
    news = ActivityNews.objects.get(pk=id)
    bg = ActivityBackground.objects.get(pk=news.background_id)
    return render(request, 'manager2/activity/view_activity_news.html', {"news": news, "background": bg})


def background_manage(request):
    '''
    活动背景管理
    editor: kamihati 2015/4/29
    :param request:
    :return:
    '''
    page_index = int(request.GET.get('page_index', 1))
    page_size = int(request.GET.get('page_size', 15))

    # 导入获取活动背景的分页页数据方法
    from activity.handler import get_activity_background_pager
    data_list, data_count = get_activity_background_pager(page_index - 1, page_size)
    return render(request,
                  'manager2/activity/list_hdbj.html',
                  dict(data_list=data_list,
                       data_count=data_count,
                       page_index=page_index,
                       page_size=page_size))


def view_activity_fruit(request):
    '''
    查看活动作品
    editor: kamihati 2015/4/29   供活动作品管理页面查看作品用。待完善
    :param request:
    :return:
    '''
    # 导入资源目录
    from WebZone.settings import MEDIA_URL
    from activity.models import ActivityFruit
    fruit = ActivityFruit.objects.get(id=request.GET.get('id'))
    print 'view_activity_fruit.fruit_id=%s, fruit_type=%s' % (fruit.id, fruit.fruit_type)
    if fruit.fruit_type == 1:
        pass
    elif fruit.fruit_type == 2:
        # 个人创作
        # 导入个人创作表
        from diy.models import AuthOpus
        return render(request,
                      "manager2/activity/opus.html",
                      {"index": 6, "sub_index": 1,
                       "opus": AuthOpus.objects.get(id=fruit.opus_id),
                       "host": request.get_host().lower()})
    elif fruit.fruit_type in (3, 4):
        # 照片.视频
        # 导入个人素材表
        from diy.models import AuthAsset
        asset = AuthAsset.objects.get(id=fruit.auth_asset_id)
        return HttpResponseRedirect(MEDIA_URL + asset.res_path)
    elif fruit.fruit_type == 5:
        # 无此种活动的作品
        pass
    return HttpResponse("此作品不能预览。")


def activity_info_list_yugao(request):
    '''
    预告列表管理
    editor: kamihati 2015/6/11
    :param request:
    :return:
    '''
    page_data = dict()
    return render(request, 'manager2/activity/list_actives.html', page_data)


def activity_info_list(request):
    '''
    预告列表管理
    editor: kamihati 2015/6/11
    :param request:
    :return:
    '''
    page_index = int(request.GET.get('page_index', 1))
    page_size = int(request.GET.get('page_size', 8))
    # 页面对应的创作类型id。（由于系统作品必定为个人创作类型。故使用创作类别进行判断  默认活动预告
    page_opus_type = int(request.GET.get('opus_type', 59))
    activity_id = int(request.GET.get('id', 0))
    data_list, data_count = get_activity_fruit_pager(
        page_index - 1, page_size, activity_id=activity_id, opus_type=page_opus_type)
    page_data = dict(data_list=data_list, data_count=data_count, page_index=page_index, page_size=page_size,
                     activity=ActivityList.objects.get(pk=activity_id), opus_type=page_opus_type)
    return render(request, 'manager2/activity/list_activen.html', page_data)


def activity_info_list_fruit(request):
    '''
    info界面作品列表管理
    editor: kamihati 2015/6/11
    :param request:
    :return:
    '''
    page_index = int(request.GET.get('page_index', 1))
    page_size = int(request.GET.get('page_size', 8))
    activity_id = int(request.GET.get('id', 0))
    activity = ActivityList.objects.get(pk=activity_id)
    group_id = request.GET.get('group', '')
    # 默认获取状态为待审核和已通过的作品
    status = request.GET.get('status', '1,2')
    data_list, data_count = get_activity_fruit_pager(
        page_index - 1, page_size, activity_id=activity_id, n_opus_type=1,
        group_id=group_id, status=status)
    page_data = dict(data_list=data_list, data_count=data_count, page_index=page_index, page_size=page_size,
                     activity=activity, group_list=get_activity_group(activity_id),
                     status=status if status != '1,2' else "", group_id=int(group_id) if group_id != '' else '')
    return render(request, 'manager2/activity/list_activen_fruit.html', page_data)


def view_fruit(request):
    '''
    查看作品内容
    editor: kamihati 2015/6/12
    :param request:
    :return:
    '''
    fruit_id = int(request.GET.get('id', 0))
    from activity.models import ActivityFruit
    fruit = ActivityFruit.objects.get(pk=fruit_id)
    if fruit.fruit_type == 1:
        # 旧版本新闻播报类别
        return HttpResponseRedirect("/manager/opus/?id=%s" % fruit.opus_id)
    elif fruit.fruit_type == 2:
        # 个人创作
        return HttpResponseRedirect("/manager/opus/?id=%s" % fruit.opus_id)
    elif fruit.fruit_type in (3, 4):
        # 图片作品,视频作品
        from diy.models import AuthAsset
        asset = AuthAsset.objects.get(pk=fruit.auth_asset_id)
        if fruit.fruit_type == 3:
            # 图片作品直接查看图片
            return HttpResponseRedirect("/media/%s" % asset.img_large_path)
        elif fruit.fruit_type == 4:
            # 视频作品链接到视频地址
            return HttpResponseRedirect("/media/%s" % asset.origin_path)
    elif fruit.fruit_type == 5:
        # 特殊处理。省少儿那些
        return HttpResponse("hnsst")
    else:
        return HttpResponse('null type')


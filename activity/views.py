# coding=utf8

import datetime
from django.http import HttpResponse

# 导入现场活动和网络活动两个model
from activity.models import ActivityList
# 导入活动背景model
from activity.models import ActivityBackground
# 导入活动报名选项model
from activity.models import ActivityOption

# 导入管理员权限验证
from utils.decorator import print_trace
# 导入临时文件文件移动方法
from utils.decorator import move_temp_file
# 导入json返回HttpResponse的方法
from utils.db_handler import get_json_str
# 获取管理员鉴权方法
from utils.decorator import manager_required

# 导入生成activity_option对象的方法
from activity.handler import make_activity_option
# 导入活动状态更新方法
from activity.handler import auto_update_activity_list_status


@print_trace
def background_update(request):
    '''
    活动背景编辑
    :param request:
          id:  ActivityBackground id
          name: 标题
          file: 图片文件。为空则不修改。不为空则保存
          tag_font_style: 标签字体名称
          tag_font_size: 标签字体尺寸
          content_font_style: 内容字体名称
          content_font_size: 内容字体尺寸
    :return:
    '''
    id = int(request.POST.get('id', 0))
    param = dict()
    if id == 0:
        param['user_id'] = request.user.id
    else:
        param['id'] = id
    name = request.POST.get('name', '')
    if name:
        param['name'] = name
    origin_path = request.POST.get('origin', '')
    if origin_path:
        param['origin_path'] = origin_path
    tag_font_style = request.POST.get('tag_font_style', '')
    if tag_font_style:
        param['tag_font_style'] = tag_font_style
    tag_font_color = request.POST.get('tag_font_color', '')
    if tag_font_color:
        param['tag_font_color'] = tag_font_color
    tag_font_size = request.POST.get('tag_font_size', '')
    if tag_font_size:
        param['tag_font_size'] = tag_font_size
    content_font_style = request.POST.get('content_font_style', '')
    if content_font_style:
        param['content_font_style'] = content_font_style
    content_font_color = request.POST.get('content_font_color', '')
    if content_font_color:
        param['content_font_color'] = content_font_color
    content_font_size = request.POST.get('content_font_size', '')
    if content_font_size:
        param['content_font_size'] = content_font_size
    position = request.POST.get('position', '')
    if position:
        param['position'] = position
    # 导入活动背景修改方法
    from activity.handler import edit_activity_background
    bg = edit_activity_background(param)
    if bg.id is not None:
        return  HttpResponse('ok')
    return HttpResponse('fail')


def remove_background(request):
    '''
    移除活动背景
    :param request:
              id:  背景id
    :return:
    '''
    # 导入活动背景移除方法
    from activity.handler import remove_activity_background
    if remove_activity_background(request.POST.get('id', 0)):
        return HttpResponse('ok')
    return HttpResponse('fail')


def edit_activity_news(request):
    '''
    编辑结果与新闻
    :param request:
            不传id为新增否则为修改。
            只修改传递值的字段
    :return:
           执行失败返回0
        执行成功返回对应的结果新闻id
    '''
    # 导入结果与新闻编辑方法
    from activity.news_handler import edit_activity_news
    param = dict()
    id = int(request.POST.get('id', None))
    if id is None:
        param['library_id'] = request.user.library.id
        param['user_id'] = request.user.id
    activity_id = request.POST.get('activity_id', None)
    if activity_id is not None:
        param['activity_id'] = activity_id
    news_type = request.POST.get('news_type', None)
    if news_type is not None:
        param['news_type'] = news_type
    title = request.POST.get('title', None)
    if title is not None:
        param['title'] = title
    background = request.POST.get('background', None)
    if background is not None:
        param['background'] = background
    content = request.POST.get('content', None)
    if content is not None:
        param['content'] = content
    if edit_activity_news(param):
        return HttpResponse('ok')
    return HttpResponse('fail')


@print_trace
def del_news(request):
    '''
    删除播报或结果  ActivityNews
    :param request:
    :return:
    '''
    # 导入删除方法
    from activity.news_handler import remove_activity_news
    if remove_activity_news(request.POST.get("id", 0)):
        return HttpResponse('ok')
    return HttpResponse('fail')


@print_trace
def get_activity_by_library(request):
    '''
    获取指定机构下的活动
    editor: kamihati 2015/5/20
    :param request:
               library_id   机构id
    :return:
    '''
    lib_id = request.GET.get('library_id', 0)
    # 导入获取活动的方法
    from activity.handler import get_activity_by_library
    result = []
    for obj in get_activity_by_library(lib_id):
        d = dict()
        d['id'] = obj.id
        d['name'] = obj.title
        result.append(d)
    return HttpResponse(get_json_str(result))


@print_trace
def activity_series_list(request):
    '''
    获取活动系列的列表
    editor: kamihati 2015/5/20
    :param request:
    :return:
    '''
    from activity.series_handler import get_activity_series_list
    series_list = []
    for obj in get_activity_series_list(request.user.library_id, request.user.id):
        series_list.append(dict(id=obj.id,
                                title=obj.title,
                                cover=obj.cover_path))
    return  HttpResponse(get_json_str(series_list))


@print_trace
def activity_series_edit(request):
    '''
    编辑系列活动
    editor: kamihati 2015/5/11
    :param request:
                id:      系列id
                title:   系列名称
                cover:   封面图临时图片路径
    :return:
    '''
    id = int(request.POST.get('id', 0))
    title = request.POST.get('title', "")
    cover_path = request.POST.get('origin_path', '')
    if title == '':
        # 标题不能为空
        return HttpResponse("-1")
    if id == 0 and cover_path == '':
        # 新建系列活动必须有封面图
        return HttpResponse("-2")
    param = dict(title=title, cover_path="", library_id=request.user.library_id, user_id=request.user.id)
    if id > 0:
        param['id'] = id
    from activity.series_handler import edit_activity_series
    series = edit_activity_series(param)
    if series.id is None:
        # 创建失败
        return  HttpResponse(u"创建失败")
    else:
        if cover_path.find("temp") > -1:
            series.cover_path = move_temp_file(cover_path, '/series/%s/cover' % series.id)
            series.save()
    return  HttpResponse("ok")


@print_trace
def activity_edit(request):
    '''
    编辑活动。
    editor: kamihati 2015/4/24  包括活动的创建与修改
    :param request:
    :return:
    '''
    activity = ActivityList()
    id = request.POST.get('id', 0)
    if id != 0:
        activity = ActivityList.objects.get(id=id)
    else:
        # 新增活动。状态设置为预告中。需要创建活动预告
        activity.status = 0
        activity.user_id = request.user.id
        activity.library_id = request.user.library_id
    activity.title = request.POST.get('title')
    activity.place_type = request.POST.get('place_type')
    activity.series_id = request.POST.get('series_id')

    # 报名开始时间结束时间
    sign_up_begin_time = request.POST.get('sign_up_start_time')
    activity.sign_up_start_time = sign_up_begin_time
    sign_up_end_time = request.POST.get('sign_up_end_time')
    activity.sign_up_end_time = sign_up_end_time

    # 根据举办场所的不同进行不同的处理
    if activity.place_type == 'net':
        #　投稿开始时间结束时间
        submit_start_time = request.POST.get('submit_start_time')
        activity.submit_start_time = submit_start_time
        submit_end_time = request.POST.get('submit_end_time')
        activity.submit_end_time = submit_end_time
        # 投票开始时间结束时间
        vote_start_time = request.POST.get('vote_start_time')
        activity.vote_start_time = vote_start_time
        vote_end_time = request.POST.get('vote_end_time')
        activity.vote_end_time = vote_end_time

        # 活动范围
        activity.scope_list = request.POST.get('scope_list')
        # 评选方式
        activity.vote_type = request.POST.get('vote_type')
        # 投票频率
        activity.vote_step = request.POST.get('vote_step')
        # 作品类型
        activity.fruit_type = request.POST.get('fruit_type')
        # 作品提交限数
        activity.submit_fruit_count = request.POST.get('fruit_count')
    elif activity.place_type == "place":
        # 活动开始时间结束时间
        activity_start_time = request.POST.get('activity_begin_time')
        activity.activity_start_time = activity_start_time
        activity_end_time = request.POST.get('activity_end_time')
        activity.activity_end_time = activity_end_time
        # 最大报名人数
        activity.sign_up_count = request.POST.get('sign_up_count')
    else:
        # 没有其他活动类型。抛出异常
        return HttpResponse("-1")
    description = request.POST.get('description', '')
    activity.description = description
    # 判断标题是否重复
    # if ActivityList.objects.filter(title=activity.title).exclude(pk=id).count() > 0:
    #    return HttpResponse("-2")
    # 活动标签数据
    tag = request.POST.get('tag')
    activity.tag = tag
    activity.save()

    # 设定activity_option 的数据
    options = request.POST.get('activity_option', '')
    a_options = ActivityOption()
    # 如果为activity id =0或者当前活动没有option数据（一般为旧版本生成的数据）则需要初始化一个新的option对象 否则获取现有对象并更新
    if id == 0 or ActivityOption.objects.filter(activity_id=id).count() == 0:
        a_options.library_id = request.user.library_id
        a_options.activity_id = activity.id
        a_options.create_time = datetime.datetime.now()
        a_options.update_time = datetime.datetime.now()
    else:
        a_options = ActivityOption.objects.get(activity_id=id)
    a_options = make_activity_option(a_options, options.split(','))

    # 附件地址。可选
    annex_file = request.POST.get('annex', '')
    if annex_file:
        activity.annex = move_temp_file(annex_file, '/activity/%s/annex' % activity.id)
    #　封面地址。可选
    cover = request.POST.get('cover', '')
    if cover:
        activity.cover = move_temp_file(cover, '/activity/%s/cover' % activity.id)
        activity.thumbnail = activity.cover
    # 活动背景id.可选
    background_id = request.POST.get('background_id', '')
    if background_id != "":
        activity.background_id = background_id
    activity.save()
    # 根据活动时间更新活动状态
    auto_update_activity_list_status(activity.id)
    return HttpResponse("ok")


def api_edit_activity_step1(request):
    '''
    编辑活动的第一步
    editor: kamihati 2015/6/10
    :param request:
    :return:
    '''
    activity = ActivityList()
    id = request.POST.get('id', 0)
    if id != 0:
        activity = ActivityList.objects.get(id=id)
    else:
        # 新增活动。状态设置为编辑中。第二步编辑完成后跳转到活动预告创建
        activity.status = -2
        activity.user_id = request.user.id
        activity.library_id = request.user.library_id
    activity.title = request.POST.get('title')
    activity.place_type = request.POST.get('place_type')
    activity.series_id = request.POST.get('series_id')

    # 根据举办场所的不同进行不同的处理
    if activity.place_type == 'net':
        # 活动范围
        activity.scope_list = request.POST.get('scope_list')
        # 评选方式
        activity.vote_type = request.POST.get('vote_type')
        if activity.vote_type == "1":
            # 网络投票
            # 投票开始时间结束时间
            vote_start_time = request.POST.get('vote_start_time')
            activity.vote_start_time = vote_start_time
            vote_end_time = request.POST.get('vote_end_time')
            activity.vote_end_time = vote_end_time
            # 投票频率
            activity.vote_step = request.POST.get('vote_step')

    elif activity.place_type == "place":
        # 活动开始时间结束时间
        activity_start_time = request.POST.get('activity_begin_time')
        activity.activity_start_time = activity_start_time
        activity_end_time = request.POST.get('activity_end_time')
        activity.activity_end_time = activity_end_time
        # 最大报名人数
        activity.sign_up_count = request.POST.get('sign_up_count')
    else:
        # 没有其他活动类型。抛出异常
        return HttpResponse("fail:-1")
    description = request.POST.get('description', '')
    activity.description = description
    activity.save()

    # 附件地址。可选
    annex_file = request.POST.get('annex', '')
    if annex_file:
        activity.annex = move_temp_file(annex_file, '/activity/%s/annex' % activity.id)
    # 海报地址。可选
    cover = request.POST.get('cover', '')
    if cover:
        activity.cover = move_temp_file(cover, '/activity/%s/cover' % activity.id)
        activity.thumbnail = activity.cover
    activity.save()
    return HttpResponse('ok:%s' % activity.id)


def api_edit_activity_step2(request):
    '''
    编辑活动的第二步
    editor: kamihati 2015/6/10
    :param request:
    :return:
    '''
    activity = ActivityList()
    id = request.POST.get('id')
    activity = ActivityList.objects.get(id=id)

    # 报名开始时间结束时间
    sign_up_begin_time = request.POST.get('sign_up_start_time')
    activity.sign_up_start_time = sign_up_begin_time
    sign_up_end_time = request.POST.get('sign_up_end_time')
    activity.sign_up_end_time = sign_up_end_time
    # 根据举办场所的不同进行不同的处理
    if activity.place_type == 'net':
        #　投稿开始时间结束时间
        submit_start_time = request.POST.get('submit_start_time')
        activity.submit_start_time = submit_start_time
        submit_end_time = request.POST.get('submit_end_time')
        activity.submit_end_time = submit_end_time

        # 投票开始时间结束时间
        vote_start_time = request.POST.get('vote_start_time')
        activity.vote_start_time = vote_start_time
        vote_end_time = request.POST.get('vote_end_time')
        activity.vote_end_time = vote_end_time

        # 作品类型
        activity.fruit_type = request.POST.get('fruit_type')
    activity.save()

    # 设定activity_option 的数据
    options = request.POST.get('activity_option', '')
    a_options = ActivityOption()
    if ActivityOption.objects.filter(activity_id=id).count() == 0:
        a_options.library_id = request.user.library_id
        a_options.activity_id = activity.id
        a_options.create_time = datetime.datetime.now()
        a_options.update_time = datetime.datetime.now()
    else:
        a_options = ActivityOption.objects.get(activity_id=id)
    a_options = make_activity_option(a_options, options.split(','))
    if activity.status == -2:
        # 如果状态为编辑中。则更新为预告中的状态并跳转到预告创建界面
        activity.status = 0
        activity.save()
        return HttpResponse('1:%s' % activity.id)
    return HttpResponse('ok:%s' % activity.id)


def update_activity_top_status(request):
    '''
    更新活动置顶状态
    editor: kamihati 2015/4/24  更新活动的置顶状态
    :param request:
             POST    id: 活动id, status: 0为不置顶 1为置顶
    :return:
    '''
    # 导入活动置顶状态更新方法
    from activity.handler import update_activity_top

    if update_activity_top(request.POST.get("id"), request.POST.get('status')):
        return HttpResponse('ok')
    return HttpResponse('-1')


@manager_required
@print_trace
def delete_activity(request):
    """
    删除活动
    editor: kamihati 2015/4/24   删除活动。供活动管理页面使用
    :param request:
                id
    :return:
    """
    # 导入删除活动的方法
    from activity.handler import delete_activity_list
    if delete_activity_list(request.POST.get('id')):
        return HttpResponse('ok')
    return HttpResponse('fail')


@manager_required
@print_trace
def change_series(request):
    '''
    更改活动所属系列活动（专题转系列）
    editor: kamihati 2015/4/24   用于活动管理页面的专题活动转系列活动
    :param request:
    :return:
    '''
    # 导入活动所属系列活动更新方法
    from activity.series_handler import change_activity_series
    if change_activity_series(request.POST.get("id"), request.POST.get('series_id')):
        return HttpResponse("ok")
    return HttpResponse('-1')

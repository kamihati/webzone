# coding=utf8

from django.http import HttpResponse
from utils.decorator import print_trace

def api_set_fruit_status(request):
    '''
    设置活动作品的状态。
    editor: kamihati 2015/4/29  供后台活动作品管理界面使用
    :param request:
                 POST.get('id')   活动作品id
                POST.get('status') 要更新成的状态
    :return:
    '''
    # 导入更新活动作品状态的方法
    from activity.fruit_handler import set_fruit_status
    if set_fruit_status(request.POST.get('id'), request.POST.get('status')):
        return HttpResponse("ok")
    return HttpResponse("fail")


@print_trace
def api_get_activity_fruit_info(request):
    '''
    获取活动作品的明细信息
    :param request:
    :return:
    '''
    # 导入获取活动作品明细的方法
    from activity.fruit_handler import get_activity_fruit_info
    info = get_activity_fruit_info(request.GET.get('id'))
    # 导入数据转json字符串的方法
    from utils.db_handler import get_json_str
    return HttpResponse(get_json_str(info))


@print_trace
def api_edit_activity_fruit(request):
    '''
    编辑活动作品
    editor: kamihati 2015/4/29  供活动作品管理界面编辑活动作品用
    :param request:
    :return:
    '''
    param = dict()
    id = request.POST.get('id', '')
    param['user_id'] = request.user.id
    param['author_name'] = request.POST.get('author_name')
    param['group_id'] = request.POST.get('group_id')
    param['author_sex'] = int(request.POST.get('author_sex', 0))
    param['author_age'] = int(request.POST.get('author_age', 0))
    param['author_email'] = request.POST.get('author_email', '')
    param['author_telephone'] = request.POST.get('author_telephone', '')
    param['author_address'] = request.POST.get('author_address', '')
    param['school_name'] = request.POST.get('school_name', '')
    param['teacher'] = request.POST.get('teacher', '')
    param['author_brief'] = request.POST.get('author_brief', '')
    param['fruit_brief'] =request.POST.get('fruit_brief', '')
    param['fruit_name'] = request.POST.get('fruit_name')
    activity_id = request.POST.get('activity_id', '')
    fruit_path = request.POST.get('fruit_path', '')
    # 处理上传作品
    if fruit_path != '':
        pass
    # 修改作品信息
    if id not in ('', '0'):
        param['id'] = id
    elif activity_id != '':
        # 新增作品信息
        # 导入获取作品编号的方法
        from activity.fruit_handler import get_fruit_number
        param['number'] = get_fruit_number(activity_id)
        # 导入活动表
        from activity.models import ActivityList
        activity_list = ActivityList.objects.get(pk=activity_id)
        param['fruit_type'] = activity_list.fruit_type
        param['activity_id'] = activity_id
        param['library_id'] = activity_list.library_id
        # 创建用户个人资源
        from diy.models import AuthAsset
        auth_asset = AuthAsset()
        auth_asset.library = request.user.library
        auth_asset.user = request.user
        auth_asset.res_title = param['fruit_name']
        auth_asset.res_type = activity_list.fruit_type
        # 未上传成功前，先状态为-1
        auth_asset.status = -1
        auth_asset.ref_times = 1
        auth_asset.share_times = 1
        auth_asset.save()
        param['auth_asset_id'] = auth_asset.id

        if fruit_path != '':
            import os
            filename, ext = os.path.splitext(fruit_path)
            from utils import get_user_path
            asset_res_path = "%s/%d" % (get_user_path(request.user, auth_asset.res_type), auth_asset.id)
            from WebZone.settings import MEDIA_ROOT
            if not os.path.exists(os.path.join(MEDIA_ROOT, asset_res_path)):
                os.makedirs(os.path.join(MEDIA_ROOT, asset_res_path))
            auth_asset.origin_path = '%s/origin%s' % (asset_res_path, ext)
            auth_asset.res_path = '%s/%d.flv' % (asset_res_path, auth_asset.id)
            auth_asset.img_large_path = '%s/l.jpg' % asset_res_path
            auth_asset.img_small_path = '%s/s.jpg' % asset_res_path
            from utils.decorator import move_temp_file
            move_temp_file(fruit_path, '%s/origin' % asset_res_path)
            auth_asset.status = 1
            auth_asset.save()

    from activity.fruit_handler import edit_activity_fruit
    param['status'] = 2
    fruit = edit_activity_fruit(param)
    if fruit.id is not None:
        return HttpResponse("ok")
    return HttpResponse("fail")

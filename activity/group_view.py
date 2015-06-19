# coding=utf8

import datetime
from django.http import HttpResponse

# 导入活动model
from activity.models import ActivityList

# 导入管理员权限验证
from utils.decorator import print_trace
# 导入json返回HttpResponse的方法
from utils.db_handler import get_json_str
# 获取管理员鉴权方法
from utils.decorator import manager_required
# 导入获取活动分组的方法
from activity.group_handler import get_activity_group
# 导入编辑活动分组的方法
from activity.group_handler import edit_activity_group
# 导入删除活动分组的方法
from activity.group_handler import delete_activity_group


@print_trace
def api_get_activity_group(request):
    '''
    获取指定活动的分组数据
    editor: kamihati 2015/4/27
    :param request:
               GET.   activity:  活动id
    :return:
    '''
    result = []
    for obj in get_activity_group(request.GET.get('activity_id')):
        result.append(dict(id=obj["id"], group_name=obj["group_name"]))
    return HttpResponse(get_json_str(dict(data=result)))


@print_trace
def api_edit_activity_group(request):
    '''
    编辑活动分组
    editor: kamihati 2015/4/27
    :param request:
    :return:
    '''
    param = dict(group_name=request.POST.get('group_name'),
                 library_id=request.user.library_id,
                 activity_id=request.POST.get('activity_id'),
                 update_time=datetime.datetime.now(),
                 create_time=datetime.datetime.now())
    id = request.POST.get('id', 0)
    if id not in ('', 0):
        param['id'] = id
    return HttpResponse(edit_activity_group(param))


def api_delete_activity_group(request):
    '''
    删除活动分组
    editor: kamihati 2015/4/27
    :param request:
    :return:
    '''
    if delete_activity_group(request.POST.get('group_id')):
        return HttpResponse('ok')
    return HttpResponse('-1')


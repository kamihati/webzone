# coding=utf8

# 导入Q用于并列关系查询
from django.db.models import Q

# 导入活动表
from activity.models import ActivityList
# 导入活动报名记录表
from activity.models import ActivityMember
# 导入活动分组表
from activity.models import ActivityGroup

# 导入model数据保存方法
from utils.db_handler import save_model_data


def edit_activity_group(param):
    '''
    编辑活动分组
    :param param:
    :return:
    '''
    # 判断新增是否存在重复的情况
    if ActivityGroup.objects.filter(activity_id=param['activity_id'], group_name=param['group_name']).exclude(status=-1).count() != 0:
        return -1
    group = save_model_data(ActivityGroup, param)
    if group.id is not None:
        return 0


def get_activity_group(activity_id):
    '''
    获取指定活动的分组列表
    editor: kamihati 2015/4/28 暂供活动编辑页面使用
    :param activity_id: 活动id
    :return:
    '''
    return ActivityGroup.objects.filter(activity_id=activity_id).exclude(status=-1).values('id', 'group_name')


def delete_activity_group(group_id):
    '''
    删除指定的活动分组
    :param group_id:  分组id
    :return:
    '''
    from activity.models import ActivityFruit
    # 如果没有作品在分组下。则删除这个分组。
    if ActivityFruit.objects.filter(group_id=group_id).count() == 0:
        ActivityGroup.objects.filter(pk=group_id).delete()
        return True
    #　如果此分组已有作品则隐性删除
    group = ActivityGroup.objects.get(id=group_id)
    activity = ActivityList.objects.get(id=group.activity_id)
    if activity.status > 0:
        # 活动发布以后不允许删除分组。以免分组内的作品丢失
        return -1
    group.status = -1
    group.save()
    return True





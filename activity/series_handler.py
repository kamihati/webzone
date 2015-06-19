# coding=utf8

# 导入Q用于并列关系查询
from django.db.models import Q

# 导入活动表
from activity.models import ActivityList
# 导入活动系列表
from activity.models import ActivitySeries
# 导入model数据保存方法
from utils.db_handler import save_model_data
# 导入sql查询分页方法
from utils.db_handler import get_pager
# 导入sql查询数据总数的方法
from utils.db_handler import get_data_count
# 导入数据列表转化为dict的方法
from utils.db_handler import rows_to_dict_list


def edit_activity_series(param):
    '''
    编辑系列活动
    editor: kamihati 2015/5/12
    :param param:
    :return:
    '''
    if ActivitySeries.objects.filter(title=param['title']):
        return ActivitySeries()
    return save_model_data(ActivitySeries, param)


def get_activity_series_list(library_id, user_id):
    '''
    获取活动列表。
    editor: kamihati 2015/5/12
    :param library_id: 所属机构id。0读取所有
    :return:
    '''
    return  ActivitySeries.objects.filter(Q(library_id=library_id) or Q(user_id=user_id))


def change_activity_series(activity_id, series_id):
    '''
    更改活动所属的系列活动
    editor: kamihati 2015/5/12
    :param activity_id:   活动id
    :param series_id:  系列活动id
    :return:
    '''
    if ActivityList.objects.filter(pk=activity_id).update(series_id=series_id):
        return  True
    return True


def get_activity_series_pager(page_index, page_size, series_id, **args):
    '''
    获取系列活动的下属活动
    editor: kamihati 2015/5/12
    :param page_index:
    :param page_size:
    :param kwargs:
    :return:
    '''
    # 默认取状态不为已删除的机构
    where_str = "status<>-1 AND series_id=%s" % series_id
    data_list = rows_to_dict_list(
        get_pager('id', 'activity_list', '', where_str, 'ORDER BY id DESC', page_index, page_size),
        ['id'])
    data_count = get_data_count('id', 'activity_list', '', where_str)
    return data_list, data_count


def get_activity_and_series_pager(page_index, page_size, **kwargs):
    '''
    获取活动与系列活动的列表
    :param page_index: 从0开始页数
    :param page_size: 每页数据数
    :param kwargs:
              status=    专题活动和系列活动子活动的状态
    :return:
    '''
    where_str = "activity_status<>-1 "
    if kwargs.has_key('status') and kwargs['status'] != '':
        where_str += ' AND activity_status=%s' % kwargs['status']
    data_list = rows_to_dict_list(
        get_pager('DISTINCT id,title,library_id,lib_name,thumbnail,nickname',
                  'view_activity_and_series',
                  '',
                  where_str,
                  'ORDER BY id DESC',
                  page_index, page_size),
        ['id', 'title', 'library_id', 'lib_name', 'thumbnail', 'nickname'])
    data_count = get_data_count('id', 'view_activity_and_series', '', where_str)
    return data_list, data_count

# coding=utf8

# 导入Q用于并列关系查询
from django.db.models import Q

# 导入活动表
from activity.models import ActivityList
# 导入活动报名记录表
from activity.models import ActivityMember

# 导入model数据保存方法
from utils.db_handler import save_model_data
# 导入sql查询分页方法
from utils.db_handler import get_pager
# 导入sql查询数据总数的方法
from utils.db_handler import get_data_count
# 导入数据列表转化为dict的方法
from utils.db_handler import rows_to_dict_list


def get_member_pager(page_index, page_size, **args):
    '''
    获取报名成员列表
    :param page_index:
    :param page_size:
    :param args:
    :return:
    '''
    where = 'n.status<>-1'
    if 'library_id' in args and args['library_id'] != 0:
        where += ' AND n.library_id=%s' % args['library_id']
    if 'activity_id' in args and args['activity_id'] != 0:
        where += ' AND n.activity_id=%s' % args['activity_id']
    if 'search_text' in args:
        if args['search_text'] not in ('', None):
            where += ' AND n.title LIKE \'%' + args['search_text'] + "%\'"

    inner = 'INNER JOIN library l ON l.id=n.library_id INNER JOIN activity_list a ON n.activity_id=a.id'
    data_list = rows_to_dict_list(
        get_pager('n.id,n.library_id,l.lib_name,n.activity_id,a.title as activity_name,n.user_id,n.news_type,n.title,n.content,n.background_id,n.create_time',
                  'activity_news n',
                  inner,
                  where,
                  'ORDER BY n.id DESC',
                  page_index, page_size),
        ['id', 'library_id', 'lib_name', 'activity_id', 'activity_name', 'user_id', 'news_type', 'title', 'content', 'background_id', 'create_time'])
    data_count = get_data_count('n.id', 'activity_news n', inner, where)
    return data_list, data_count

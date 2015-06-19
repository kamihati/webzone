# coding=utf8

'''
对活动播报和活动结果的数据处理
coder: kamihati 2015/4/9
'''

# 导入活动播报和活动结果model
from activity.models import ActivityNews
# 导入活动背景model
from activity.models import ActivityBackground
# 导入model数据保存方法
from utils.db_handler import save_model_data
# 导入sql查询分页方法
from utils.db_handler import get_pager
# 导入sql查询数据总数的方法
from utils.db_handler import get_data_count
# 导入数据列表转化为dict的方法
from utils.db_handler import rows_to_dict_list

def edit_activity_news(params):
    '''
    编辑活动播报和活动结果
    :param params:
    :param id:   0为新增。否则为编辑
    :return:
    '''
    # 增加背景引用数
    if 'background_id' in params:
        bg = ActivityBackground.objects.get(pk=params['background_id'])
        bg.use_num += 1
        bg.save()
    news = save_model_data(ActivityNews, params)


def get_activity_news_pager(page_index, page_size, **args):
    '''
    获取活动背景的翻页数据
    :param page_index: 页码从0开始
    :param page_size: 每页数据
    :return:
    '''
    where = 'n.status=0'
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


def remove_activity_news(id):
    '''
    删除播报或结果
    :param id:
    :return:
    '''
    if ActivityNews.objects.filter(pk=id).update(status=-1):
        return True
    return False

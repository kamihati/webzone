# coding=utf8
# editor: kamihati 2015/5/18  活动作品相关逻辑处理

# 导入活动作品model
from activity.models import ActivityFruit
# 导入活动参与记录表
from activity.models import ActivityMember
# 导入分页方法
from utils.db_handler import get_pager
# 导入数据转dict的方法
from utils.db_handler import rows_to_dict_list
# 导入获取数据条数的放啊分
from utils.db_handler import get_data_count
# 导入model数据保存方法
from utils.db_handler import save_model_data


def get_sing_member_pager(page_index, page_size, **kwargs):
    '''
    获取报名人员分页列表
    editor: kamihati 2015/5/18
    :param page_index:   页码： 0开始
    :param page_size:    每页数据数：
    :param kwargs:  参数
    :return:
    '''
    where = 'a.status<>-1'
    if kwargs.has_key('activity_id') and kwargs['activity_id'] != '':
        where += ' AND a.activity_id=%s' % kwargs['activity_id']
    inner = 'INNER JOIN activity_list b ON b.id=a.activity_id'
    data_list = rows_to_dict_list(
        get_pager('a.id,b.title,a.fruit_name,a.number,a.realname,a.age,a.sex,a.school,a.email,a.telephone,a.address,a.unit_name,a.join_time',
                  'activity_member a',
                  inner,
                  where,
                  'ORDER BY a.id DESC',
                  page_index, page_size),
        ['id', 'title', 'fruit_name', 'number', 'realname', 'age', 'sex', 'school', 'email', 'telephone', 'address', 'unit_name', 'join_time'])
    data_count = get_data_count('a.id', 'activity_member a', inner, where)
    return data_list, data_count


def edit_activity_member(param):
    '''
    增加报名记录
    editor: kamihati 2015/5/18
    :param param:
    :return:
    '''
    from utils.db_handler import save_model_data
    return save_model_data(ActivityMember, param)


def del_activity_sign_member(id):
    '''
    删除报名记录
    editor: kamihati 2015/5/18
    :param id:
    :return:
    '''
    return set_activity_sign_member_status(id, -1)


def set_activity_sign_member_status(id, status):
    '''
    更新报名记录的状态
    editor: kamihati 2015/5/18
    :param id:
    :param status:
    :return:
    '''
    if ActivityMember.objects.filter(pk=id).update(status=status):
        return True
    return False


def edit_activity_sign_member(user, **kwargs):
    '''
    编辑活动报名记录
    editor: kamihati 2015/5/21
    :param user:
    :param kwargs:
    :return:
    '''
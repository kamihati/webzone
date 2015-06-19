# coding=utf8

from utils.db_handler import get_data_count, get_pager
from utils.db_handler import rows_to_dict_list

# 导入用户个人资源表
from diy.models import AuthAsset
# 导入用户个人创作表。个人创作分页表
from diy.models import AuthOpus, AuthOpusPage


def edit_auth_opus(origin_path, user, **kwargs):
    '''
    编辑用户个人创作
    editor: kamihati 2015/5/15
    :param origin_path: 源文件路径
    :param user:   操作人
    :param kwargs: 明细参数
    :return:
    '''
    asset = AuthAsset()


def get_opus_pager(page_index, page_size, **kwargs):
    '''
    获取个人创作列表
    editor: kamihati 2015/6/15  供前台个人中心获取各类创作使用
    editor: kamihati 2015/6/18  修改opus的activity_id获取逻辑。从activity_fruit中取最近的一条。
    :param page_index:
    :param page_size:
    :param kwargs:
    :return:
    '''
    # 不为已删除状态
    where = 'a.status>-2'
    user_id = kwargs['user_id'] if kwargs.has_key('user_id') else 0
    type_id = kwargs['type_id'] if kwargs.has_key('type_id') else ''
    class_id = kwargs['class_id'] if kwargs.has_key('class_id') else 0
    group_str = ' GROUP BY a.id'
    # type_id 为数字则取对应类别的作品。否则取相应条件的作品
    if type_id.isdigit():
        where = 'a.type_id=%s' % type_id
    elif type_id == 'edit':
        # 草稿作品.待审核作品
        where = 'a.status IN (0, 1)'
    elif type_id == 'done':
        # 已审核通过的原创作品
        where = 'a.status=2'
        group_str += ' HAVING activity_fruit_num=0'
    elif type_id == 'activity':
        # 活动作品
        where = 'a.status=2'
        group_str += ' HAVING activity_fruit_num<>0'
    if user_id != 0:
        where += ' AND a.user_id=%s' % user_id
    if class_id != 0:
        where += " AND a.class_id=%d" % class_id

    cols = 'a.id,a.title,a.brief,a.tags,a.type_id,a.class_id,a.thumbnail,a.status,a.show_type,' \
           'a.create_type,a.read_type,a.library_id,c.activity_id,' \
           'a.opus_type,count(b.id) as activity_fruit_num'
    join = 'LEFT JOIN activity_fruit b ON b.opus_id=a.id ' \
           'LEFT JOIN (SELECT id,activity_id,opus_id FROM activity_fruit where user_id=%s ' \
           'ORDER BY id desc limit 1) as c ON c.opus_id=a.id' % user_id

    order_by = 'ORDER BY a.is_top,a.update_time DESC '
    tb_name = 'auth_opus a '

    count_where = where.replace('a.', '')
    if type_id == 'activity':
        count_where = count_where + ' AND id in (SELECT opus_id FROM activity_fruit WHERE user_id=%s AND status>0)' % user_id
    elif type_id == 'done':
        count_where = count_where + ' AND id not in (SELECT opus_id FROM activity_fruit WHERE user_id=%s AND status>0)' % user_id
    data_count = get_data_count('id', 'auth_opus', '', count_where)
    return rows_to_dict_list(
        get_pager(cols, tb_name, join, where, order_by, page_index - 1, page_size, group=group_str),
        ['id', 'title', 'brief', 'tags', 'type_id', 'class_id', 'thumbnail', 'status', 'show_type', 'create_type', 'read_type', 'library_id', 'activity_id', 'opus_type', 'activity_fruit_num']
    ), data_count


def set_opus_status(id, status):
    '''
    设置活动作品的状态
    editor: kamihati 2015/6/17
    :param id:
    :param status:
    :return:
    '''
    if AuthOpus.objects.filter(pk=id).update(status=status):
        return True
    return False


def get_opus_activity_id(opus_id):
    '''
    editor: kamihati 2015/6/18  获取个人创作的activity_id
    :param opus_id:
    :return:
    '''
    from activity.models import ActivityFruit
    fruit_list = ActivityFruit.objects.filter(opus_id=opus_id).order_by("-id")
    if not fruit_list:
        return 0
    return fruit_list[0].activity_id


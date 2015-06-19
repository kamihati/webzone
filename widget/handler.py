# coding=utf8

from utils.db_handler import get_sql_data
from utils.db_handler import save_model_data
from utils.db_handler import get_pager
from utils.db_handler import get_data_count
from utils.db_handler import rows_to_dict_list

# 导入创作分类表
from widget.models import WidgetOpusClassify

def get_opus_type_list(parent_id=0, **kwargs):
    '''
    获取个人创作的分类列表
    editor: kamihati 2015/5/7
    editor: kamihati 2015/6/9 增加对系统分类的支持
    editor: kamihati 2015/6/15 优化查询逻辑
    :param parent_id:父类id
    :return:
    '''
    is_sys = int(kwargs['is_sys']) if kwargs.has_key('is_sys') else 0
    data_list = WidgetOpusClassify.objects.filter(parent_id=parent_id, status__gt=-1, is_sys=is_sys)
    # 当取子类货取系统类别时不判断is_sys
    if parent_id != 0 or is_sys == 1:
        data_list = WidgetOpusClassify.objects.filter(parent_id=parent_id, status__gt=-1)
    return [dict(id=obj.id, name=obj.classify_name, parent_id=obj.parent_id) for obj in data_list]


def get_opus_type_by_level(level=0):
    '''
    获取指定级别的作品类型
    editor: kamihati 2015/6/4
    :param level:
    :return:
    '''
    sql = "SELECT id,classify_name,parent_id from widget_opus_classify WHERE status<>-1 and parent_id=0"
    if level == 1:
        sql = "SELECT id,classify_name,parent_id from widget_opus_classify WHERE status<>-1 and parent_id in " \
              "(SELECT id FROM widget_opus_classify WHERE status<>-1 and  parent_id=0)"
    elif level == 2:
        sql = "SELECT id from widget_opus_classify WHERE status<>-1 and parent_id in " \
              "(SELECT id from widget_opus_classify WHERE status<>-1 and  parent_id in " \
              "(SELECT id FROM widget_opus_classify WHERE status<>-1 and  parent_id=0))"
    rows = get_sql_data(sql)
    data_lists = []
    for row in rows:
        d = dict(id=row[0], name=row[1], parent_id=row[2])
        # 如果是子类。则读出其中所对应的尺寸列表
        if level == 1:
            d['size_list'] = get_opus_type_size_list(row[0])
        data_lists.append(d)
    return data_lists


def get_opus_type_list_by_id(ids):
    '''
    获取指定id的个人创作的分类
    editor: kamihati 2015/5/8
    :param ids  id列表
    :return:
    '''
    if not ids:
        return []
    sql = "select id,classify_name,parent_id from widget_opus_classify where status<>-1 and id in (%s)" % ','.join(ids)
    rows = get_sql_data(sql)
    data_lists = []
    for row in rows:
        d = dict(id=row[0], name=row[1], parent_id=row[2])
        d['size_list'] = get_opus_type_size_list(row[0])
        data_lists.append(d)
    return data_lists




def get_opus_type_size_list(class_id):
    '''
    获取指定个人创作分类对应的尺寸列表
    editor: kamihati 2015/5/7
    :param class_id: 个人创作子类id
    :return:
    '''
    size_list = []
    sql = "select screen_width, screen_height, print_width, print_height, origin_width, origin_height,create_type,read_type from widget_opus_size where classify_id=%d" % class_id
    rows = get_sql_data(sql)
    for row in rows:
        size_list.append({"screen_width": row[0], "screen_height": row[1], "print_width": row[2], "print_height": row[3], "origin_width": row[4], "origin_height": row[5], "create_type": row[6], "read_type": row[7]})
    return size_list


def edit_opus_type(param):
    '''
    编辑个人创作分类
    editor: kamihati 2015/5/7
    :param param:
    :return:
    '''
    param['create_type'] = 1 if 'create_type' not in param else param['create_type']
    param['read_type'] = 1 if 'read_type' not in param else param['read_type']
    id = 0 if 'id' not in param else param['id']
    if WidgetOpusClassify.objects.filter(classify_name=param['classify_name']).exclude(pk=id).count() != 0:
        return -1
    return save_model_data(WidgetOpusClassify, param)


def delete_opus_type(id):
    '''
    删除个人创作分类
    editor: kamihati 2015/5/7
    :param id:
    :return:
    '''
    if WidgetOpusClassify.objects.filter(pk=id).update(status=-1):
        return True
    return False


def get_page_size_list():
    '''
    获取页面尺寸列表
    editor: kamihati 2015/6/8
    :return:
    '''
    from widget.models import WidgetPageSize
    return [
        dict(id=obj.id,
             width=obj.print_width,
             height=obj.print_height)
        for obj in WidgetPageSize.objects.exclude(status=-1).order_by("-id")]

def get_widget_page_size_pager(page_index, page_size, **kwargs):
    '''
    获取页面尺寸的分页数据
    editor: kamihati 2015/5/11 主要供后台作品尺寸管理使用
    :param page_index:
    :param page_size:
    :param kwargs:
    :return:
    '''
    where = "status=1"
    if kwargs.has_key('title') and kwargs['title'] != '':
        where += ' AND name LIKE \'%' + kwargs['title'] + "%\'"
    if kwargs.has_key('library_id') and kwargs['library_id'] != '':
        where += ' AND library_id=%s' % kwargs['library_id']
    join_str = ""

    data_count = get_data_count('id', 'widget_page_size', join_str, where)
    return rows_to_dict_list(
        get_pager('id,name,create_type,read_type,screen_width,screen_height,print_width,print_height,add_time,res_path',
                  'widget_page_size',
                  join_str,
                  where,
                  'ORDER BY id DESC',
                  page_index,
                  page_size),
        ['id', 'name', 'create_type', 'read_type', 'screen_width', 'screen_height', 'print_width', 'print_height', 'add_time', 'res_path']
    ), data_count


def del_widget_page_size(id):
    '''
    删除页面尺寸
    editor: kamihati 2015/5/11 主要供作品尺寸管理使用
    :param id:
    :return:
    '''
    from widget.models import WidgetPageSize
    if WidgetPageSize.objects.filter(pk=id).update(status=-1):
        return True
    return False
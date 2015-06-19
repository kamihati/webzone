# coding=utf8
# 数据库操作公共处理函数集
# coder by: kamihati   2015/3/13
import datetime
import time
from django.db import connection, connections
import json

def get_cursor(db_key='', **args):
    '''
    返回setting定义的数据库连接游标。
    如果未指定使用哪个配置则使用default配置。否则使用制定配置
    :param db_key: 数据库配置名
    :param args:  待扩展的其他参数
    :return:
    '''
    cur = connection.cursor()
    if db_key != '':
        cur = connections[db_key].cursor()
    return cur


def get_sql_data(sql, *arg, **args):
    '''
    读取sql的执行结果
    :param sql: sql语句
    :param arg: 备用参数
    :param args: 备用参数。args.db_key=连接名
    :return:
    '''
    db_key = args['db_key'] if args.has_key('db_key') else ''
    cur = get_cursor(db_key)
    cur.execute(sql)
    results = cur.fetchall()
    cur.close()
    return  results

def execute_sql(sql, *arg, **args):
    '''
    执行sql语句(update.delete等)。慎用。
    :param sql: sql语句
    :param arg: 备用参数
    :param args: 备用参数
    :return:
    '''
    cur = get_cursor()
    cur.execute(sql)
    cur.connection.commit()


def get_json_str(obj):
    '''
    :param dict:要转化为json字符串的对象
    :return:json字符串
    coder: kamihati 2015/3/20
    '''
    return json.dumps(obj)

def get_data_count(cols, table_name, join_str, where_str, **kwargs):
    '''
    获取制定查询条件的表有多少数据
    cols:计数依据的字段。不可为空
    table_name:查询的主表名称。不可为空
    join_str:需要用到联结查询则需要传入这个参数。为联结其他表的sql语句。可为空
    where_str:查询条件。可为空
    '''
    if where_str == '':
        where_str = '1=1'
    group = kwargs['group'] if kwargs.has_key('group') else ''
    sql = 'SELECT COUNT(%s) FROM %s %s WHERE %s %s' % (cols, table_name, join_str, where_str, group)

    # print sql
    cur = get_cursor('db_read')
    cur.execute(sql)
    row = cur.fetchone()
    cur.close()
    return int(row[0])


def get_pager(cols, table_name, join_str, where_str, order_str, pageindex, pagesize, **kwargs):
    '''
    获取分页数据的基础处理方法
    cols:字段列表。如为多表查询需要注意字段重复和设定字段别名的问题。不可为空。
    table_name: 作为查询主表的表名 。如果有别名也要加上。 例如 select * from [tblename t1]。参数为中括号内的部分。 不可为空
    join_str: 如果是多表联结查询需要把联结部分的语句传入。例如： inner join t1 on t1.id=main.id 。可为空字符
    where_str: 查询条件。可为空。 例如 where [....]  order by ... 中括号内的部分.
    order_str: 排序条件。例如 [order by colname asc/desc]。传入中括号内的部分。可为空字符。
    pageindex: 页码。从0开始计数。如页面是第一页需要传入0
    pagesize: 每页需要显示的数据数。
    coder: kamihati  2015/3/16
    kwargs:  可选参数列表
         kwargs.page_erroe_size  误差数。某一页显示的不等于pagesize的长度。用于第一页是与其他数据混合显示的情况
        editor: kamihati 2015/6/9
    editor: kamihati 2015/6/15  优化搜索逻辑。支持分组条件传入
    '''
    if where_str == '':
        where_str = '1=1'
    group = kwargs['group'] if kwargs.has_key('group') else ''
    limit = ''

    # pagesize为0则不分页
    if pagesize != 0:
        limit = 'LIMIT %s,%s' % (pageindex * pagesize, pagesize)
    sql = 'SELECT %s FROM %s %s WHERE %s %s %s %s' % (
        cols, table_name, join_str, where_str, group, order_str, limit)
    # print sql
    cur = get_cursor('db_read')
    cur.execute(sql)
    rows = cur.fetchall()
    cur.close()
    return rows


def rows_to_dict_list(rows, keys):
    '''
    根据指定的key列表把查询出的objects转换为dict
    coder: kamihati 2015/3/16
    '''
    result = []
    for row in rows:
        data_dict = dict()
        for i in range(len(keys)):
            if isinstance(row[i], datetime.datetime):
                data_dict[keys[i]] = row[i].strftime("%Y-%m-%d %H:%M:%S")
            else:
                data_dict[keys[i]] = row[i]
        result.append(data_dict)
    return result


def save_model_data(model_class, param):
    '''
    编辑model数据的公有方法
    editor: kamihati 2015/6/11
    :param model_class:    model类名称
    :param param:    models字段与值的字典
    :return:   bool
    '''
    obj = model_class()
    if 'id' in param:
        obj = model_class.objects.get(pk=param['id'])

    is_change = False
    for key, val in param.iteritems():
        if key == 'id':
            continue
        setattr(obj, key, val)
        if not is_change:
            is_change = True
    if is_change:
        obj.save()
    return obj

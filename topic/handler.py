# coding=utf8
import datetime
import os
import StringIO
from PIL import Image

#　导入多媒体文件url, 路径
from WebZone.settings import MEDIA_URL
# 导入异常输出函数
from utils.decorator import print_trace
# 导入用户上传缩略图的存储方法
from utils.decorator import thumbnail_save

# 导入用户model
from account.models import AuthUser
# 导入话题评论model
from topic.models import TopicRemark, RemarkResource, TopicResource
# 导入话题model
from topic.models import Topic
# 导入话题表情分类models
from topic.models import PhizType
# 导入话题点赞记录表，评论点赞记录表
from topic.models import TopicPraise, RemarkPraise
# 导入资源表
from diy.models import ZoneAsset
# 导入用户创作资源表
from diy.models import AuthOpus

# 导入objects转dict的方法
from utils.db_handler import rows_to_dict_list
# 导入sql语句分页方法
from utils.db_handler import get_pager
# 导入sql语句获取数据总数方法
from utils.db_handler import get_data_count
# 导入获取用户文件存储路径的路径
from utils import get_user_path


'''
话题模块数据操作类
coder: kamihati 2015/3/20
coder: kamihati 2015/3/23 更改非必要的  >   为  !=  ，相对来说  !=  会比 >  执行效率要高。
'''


@print_trace
def search_topic_dict(key, pageindex, pagesize, **param):
    '''
    查询符合条件的话题返回分页数据
    key: 关键字
    pageindex: 数据页码，从0计数
    pagesize: 数据步长。每页需要查到的数据条数
    param: 扩展参数： province, city, region 省市区名称

    coder: kamihati 2015/3/13
    返回结果： data_list, page_count
       data_list :   查询到的objects
       page_count: 根据传入的pagesize计算出的总页数
    coder: kamihati 2015/3/13
    '''
    where = 't.status=0'
    key = key.strip()
    if key != '':
        where += ' AND (t.title LIKE \'%' + key + '%\' OR u.nickname LIKE \'%' + key + '%\' OR t.content LIKE \'%' + key + '%\')'
    library_id = province = city = region = ''
    from library.models import LibraryRegion
    if param is not None:
        province = param['province'] if param.has_key('province') else ''
        city = param['city'] if param.has_key('city') else ''
        region = param['region'] if param.has_key('region') else ''
        library_id = param['library_id'] if param.has_key('library_id') else 0
        if library_id not in (0, ''):
            where += ' AND t.library_id=%s' % library_id
        elif region != '':
            region_name = LibraryRegion.objects.get(id=region).name
            where += ' AND liby.region=\'' + region_name + '\''
        elif city != '':
            city_name = LibraryRegion.objects.get(id=city).name
            where += ' AND liby.city=\'' + city_name + '\''
        elif province != '':
            province_name = LibraryRegion.objects.get(id=province).name
            where += ' AND liby.province=\'' + province_name + '\''
    join_str = 'INNER JOIN auth_user u ON u.id=t.user_id ' \
               'INNER JOIN library liby ON liby.id=t.library_id ' \
               'LEFT JOIN topic_remark d ON d.topic_id=t.id'
    # 初始化数据列表为页面所需格式和数据总数一起返回。页码交给前端计算
    data_count = get_data_count('t.id', 'topic_main t', join_str, where)
    return rows_to_dict_list(
        get_pager(
            't.id,t.user_id,u.nickname, t.library_id,liby.lib_name,t.title,t.content,t.remark_count,'
            't.is_top,t.update_time,t.create_time,t.status,t.praise_count,t.view_count,'
            't.remark_count,t.praise_count,count(DISTINCT d.user_id) as remark_user_count',
            'topic_main t',
            join_str,
            where,
            ' GROUP BY t.id ORDER BY t.id DESC', pageindex, pagesize),
        ['id', 'user_id', 'nickname', 'library_id', 'library_name', 'title', 'content', 'remark_count', 'is_top', 'update_time', 'create_time', 'status', 'praise_count', 'view_count', 'remark_count', 'praise_count', 'remark_user_count']
    ), data_count


def search_comment_dict(topic_id, pageindex, pagesize, **param):
    '''
    查询符合条件的话题评论返回分页数据
    topic_id: 所属话题id
    pageindex: 数据页码，从0计数
    pagesize: 数据步长。每页需要查到的数据条数
    返回结果： data_list, page_count
       data_list :   查询到的objects
       page_count: 根据传入的pagesize计算出的总页数
       data_count: 评论总数
    coder: kamihati 2015/3/17
    '''
    where = 'c.status=0'
    if topic_id not in ('', 0):
        where += ' AND c.topic_id=' + topic_id

    # 初始化数据列表为页面所需格式和页数一起返回
    # mark: 此处可能由于每次翻页都要计算页数而影响页面执行效率。后期考虑优化 kamihati 2015/3/16
    data_count = get_comment_count(topic_id)
    page_count = data_count / pagesize
    if data_count % pagesize != 0:
        page_count += 1
    return rows_to_dict_list(
        get_pager(
            'c.id,c.user_id,u.username,u.nickname,c.create_time,c.content,c.praise_count',
            'topic_remark c',
            'LEFT JOIN auth_user u ON u.id=c.user_id',
            where,
            'ORDER BY c.id DESC', pageindex, pagesize),
        ['id', 'user_id', 'username', 'nickname', 'create_time', 'content', 'praise_count']
    ), page_count, data_count


def delete_remark(id):
    '''
    删除评论（隐藏）
    参数描述：
        id : 评论id
    coder: kamihati 2015/3/20
    '''
    if TopicRemark.objects.filter(pk=id).update(status=1) != 0:
        return True
    return False


def get_comment_count(topic_id):
    '''
    获取话题的评论总数
    参数描述：
        topic_id: 评论所属话题id
    '''
    where = 'status=0'
    if topic_id not in ('', 0):
        where += ' AND topic_id=' + topic_id
    return get_data_count(
        '*',
        'topic_remark',
        '',
        where)


def update_topic_status(id, status):
    '''
    更新话题的状态
    字段描述:
        id: 话题id
        status: 话题状态
    coder: kamihati 2015/3/13
    coder: kamihati 2015/3/20 更改为新版后台的表
    '''
    if Topic.objects.filter(id=id).update(status=status) != 0:
        return True
    return False


def update_topic_top(id, status):
    '''
    更新话题的置顶状态
    字段描述:
        id: 话题id
        status: 置顶状态
    coder: kamihati 2015/3/23
    '''
    if Topic.objects.filter(id=id).update(is_top=status) != 0:
        return True
    return False


def get_emotion_count(type_id, key, **args):
    '''
    获取话题表情的总数
    字段描述:
        type_id: 表情所属分类的id,
        key: 搜索关键字
        args: 其他待扩展的条件
    '''
    where_clause = "res_type=12 and status=1"
    if type_id != 0 and type_id != '':
        where_clause += " and type_id=%d" % type_id
    if key:
        where_clause += " and res_title like '%%%s%%'" % key
    return get_data_count('*', 'zone_asset', '', where_clause)


def search_emotion_list(type_id, key, page_index, page_size, **args):
    '''
    获取话题表情分页数据
    字段描述：
        type_id: 表情类型。默认0为全部
        key: 查询关键字
        page_index: 页码。从0开始计数
        page_size: 每页数据数。默认15
        args: 待拓展的其他参数
    返回结果：
        result: 查询到的数据列表
        data_count: 符合条件的数据总数
    '''
    where_clause = "res_type=12 and status=1"
    if type_id:
        where_clause += " and type_id=%d" % type_id
    if key:
        where_clause += " and (res_title like '%%%s%%' or mark like '%%%s%%')" % key

    # 获取数据列表
    data_list = get_pager(
        'id,res_title,res_path,img_small_path,type_id,update_time,width,height,mark_id',
        'zone_asset',
        '',
        where_clause,
        'order by update_time desc',
        page_index,
        page_size)

    # 获取数据总数
    data_count = get_emotion_count(type_id, key)
    result = list()
    for row in data_list:
        data_dict = dict()
        data_dict['id'] = int(row[0])
        data_dict['title'] = row[1]
        data_dict['url'] = MEDIA_URL + row[2]
        data_dict['small'] = MEDIA_URL + row[3]
        data_dict['type_id'] = int(row[4])
        data_dict['type_name'] = get_emotion_type_name(data_dict['type_id'])
        data_dict['update_time'] = row[5].strftime("%Y-%m-%d %H:%M:%S")
        data_dict['width'] = int(row[6]) if row[6] else 0
        data_dict['height'] = int(row[7]) if row[7] else 0
        data_dict['mark'] = row[8]
        result.append(data_dict)
    return result, data_count


def get_emotion_type_name(id):
    '''
    获取指定话题类型id的名称
    coder: kamihati 2015/3/19
    '''
    phiz_type = PhizType.objects.filter(id=id)
    if phiz_type:
        return phiz_type[0].name
    return u'无类型'


@print_trace
def add_topic_remark(user, topic_id , content, media_data):
    """
    添加评论
    参数描述：
          user: 操作用户
          topic_id : 话题的id，
          content: 评论内容，
          media_data: 评论附件
    coder: kamihati 2015/3/24
    """
    last_remark = TopicRemark.objects.filter(user_id=user.id, topic_id=topic_id).order_by('-id')
    if last_remark:
        last_remark = last_remark[0]
        if (datetime.datetime.now() - last_remark.create_time).seconds < 30:
            # 30秒内不能重复发帖
            return  -1
    remark = TopicRemark.objects.create(user_id=user.id,
                                        library_id=user.library.id,
                                        topic_id=topic_id,
                                        content=content,
                                        create_time=datetime.datetime.now(),
                                        status=0)
    if remark:
        topic = Topic.objects.get(pk=topic_id)
        topic.remark_count += 1
        topic.save()
    # 处理附件
    edit_topic_remark_resource(remark, media_data)



def edit_topic_remark(remark_id, content, media_data):
    """
    编辑评论
    参数描述：
          remark_id : 评论的id，
          content: 评论内容，
          media_data: 评论附件
    coder: kamihati 2015/3/24
    """
    remark = TopicRemark.objects.get(id=remark_id)
    remark.content = content
    remark.update_time = datetime.datetime.now()
    remark.save()
    edit_topic_remark_resource(remark, media_data)


def edit_topic_resource(topic, media_data=[]):
    '''
    编辑话题附件
    :param topic: 话题对象
    :param media_data: 附件列表
    :return:
    coder: kamihati 2015/3/24
    '''
    if not media_data:
        return
    user = AuthUser.objects.get(pk=topic.user_id)
    # 取出现有资源id列表。移除与请求中相同的id。剩下的删除。
    res_ids = [obj[0] for obj in TopicResource.objects.filter(topic_id=topic.id).values_list('id')]
    for data in media_data:
        res_id = int(data['id']) if data.has_key('id') else 0
        res_type = data['type_id'] if data.has_key('type_id') else 0
        thumbnail = data['thumbnail'] if data.has_key('thumbnail') else ''
        if res_id in res_ids:
            res_ids.remove(res_id)
            continue

        res = TopicResource.objects.create(topic_id=topic.id,
                                           res_id=res_id,
                                           type_id=res_type)
        if thumbnail != '':
            res.thumbnail = thumbnail_save(user, thumbnail, 'topic', res.id)
            res.save()
    TopicResource.objects.filter(id__in=res_ids).delete()


def add_topic_praise(topic_id, user_id):
    '''
    增加点赞记录
    :param topic_id:话题id
    :param user_id: 用户id
    :return:
         -1: 当天已投票   1: 成功    0 :未知错误
    coder: kamihati 2015/3/24
    '''
    if TopicPraise.objects.filter(user_id=user_id, topic_id=topic_id, add_date=datetime.datetime.now().date()):
        return -1
    if TopicPraise.objects.create(user_id=user_id, topic_id=topic_id, add_date=datetime.datetime.now().date()):
        topic_obj = Topic.objects.get(id=topic_id)
        topic_obj.praise_count += 1
        topic_obj.save()
        return  1
    return 0


def add_remark_praise(remark_id, user_id):
    '''
    增加点赞记录
    :param topic_id:评论id
    :param user_id: 用户id
    :return:
         -1: 当天已投票   1: 成功    0 :未知错误
    coder: kamihati 2015/3/24
    '''
    if RemarkPraise.objects.filter(user_id=user_id, remark_id=remark_id, add_date=datetime.datetime.now().date()):
        return -1
    if RemarkPraise.objects.create(user_id=user_id, remark_id=remark_id, add_date=datetime.datetime.now().date()):
        topic_obj = TopicRemark.objects.get(id=remark_id)
        topic_obj.praise_count += 1
        topic_obj.save()
        return  1
    return 0


def edit_topic_remark_resource(topic_remark, media_data):
    '''
    编辑话题评论附件
    :param topic_remark: 话题评论对象
    :param media_data: 附件列表 list
    :return:
    '''
    user = AuthUser.objects.get(pk=topic_remark.user_id)
    # 取出现有资源id列表。移除与请求中相同的id。剩下的删除。
    res_ids = [obj[0] for obj in RemarkResource.objects.filter(remark_id=topic_remark.id).values_list('id')]
    for data in media_data:
        res_id = int(data['id']) if data.has_key('id') else 0
        res_type = data['type_id'] if data.has_key('type_id') else 0
        thumbnail = data['thumbnail'] if data.has_key('thumbnail') else ''
        if res_id in res_ids:
            res_ids.remove(res_id)
            continue
        res = RemarkResource.objects.create(remark_id=topic_remark.id,
                                            res_id=res_id,
                                            type_id=res_type)
        if thumbnail:
            res.thumbnail = thumbnail_save(user, thumbnail, 'topic_remark', res.id)
            res.save()


    RemarkResource.objects.filter(id__in=res_ids).delete()


@print_trace
def add_topic(user, title, content, media_data):
    """
    添加话题
    参数描述：
          user: 操作用户
          title: 话题标题
          content: 话题内容，
          media_data: 话题附件
    返回描述：
          (bool, string)    bool表示是否执行成功。string 描述执行结果
    """
    topic = Topic.objects.create(user_id=user.id,
                                 library_id=user.library.id,
                                 content=content,
                                 title=title,
                                 create_time=datetime.datetime.now(),
                                 status=0)
    # 处理附件
    edit_topic_resource(topic, media_data)


@print_trace
def edit_topic(id, user, title, content, media_data):
    """
    编辑话题
    参数描述：
          id: 话题id
          user: 操作用户
          title: 话题标题
          content: 话题内容，
          media_data: 话题附件
    返回描述：
          (bool, string)    bool表示是否执行成功。string 描述执行结果
    """
    topic = Topic.objects.create(id=id,
                 user_id=user.id,
                 library_id=user.library.id,
                 topic_id=id,
                 content=content,
                 title=title,
                 create_time=datetime.datetime.now(),
                 status=0)
    # 处理附件
    edit_topic_resource(topic, media_data)

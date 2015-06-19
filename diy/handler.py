# coding=utf8
import os
from PIL import Image
# 导入获取sql语句查询结果的方法
from utils.db_handler import get_sql_data

# 导入用户原创作品记录表
from diy.models import AuthOpus, AuthOpusPage, ZoneAssetTemplate
# 导入原创作品评论表(mongodb)
from mongodb import AuthOpusCommentMongo
from utils.db_handler import get_pager
from utils.db_handler import get_data_count
from utils.db_handler import rows_to_dict_list
from WebZone.settings import MEDIA_ROOT
from diy.models import ZoneAsset

def get_user_opus_count(user_id, status=None):
    '''
    获取用户的作品数
    editor: kamihati 2015/5/15
    :param user_id:用户id
    :param status: 状态
    :return:
    '''
    if status is None:
        return AuthOpus.objects.filter(user_id=user_id).count()
    return AuthOpus.objects.filter(user_id=user_id, status=status).count()


def get_auth_opus_pager(page_index, page_size, **kwargs):
    '''
    获取用户个人创作分页数据
    editor: kamihati 2015/5/8
    editor: kamihati 2015/6/3 新需求不使用多个类别的查询.修改calss1.calss2为单个值的查询
    :param page_index:页码 。从0开始
    :param page_size:
    :param kwargs:
               kwargs['key'] :  搜索关键字。机构名称。用户名。标题
               kwargs['status'] :  作品状态
               kwargs['library_id']: 机构id,
               kwargs['class_1'] :  门类id。
               kwargs['class_2']:  子类id。
               kwargs['begin_time']: 开始时间  。统一查询创建时间
               kwargs['end_time']: 结束时间。统一查询创建时间
               kwargs['is_activity']: 是否活动作品。
    :return:
    '''
    cols = 'a.id,a.title,b.username,c.classify_name as class1_name,page_count,a.preview_times,a.praise_times,a.comment_times,d.lib_name,a.activity_id,a.is_top,a.create_time,e.classify_name as class2_name,a.update_time'
    # 默认读已发布的作品
    where = 'a.status=2'
    # 如果状态值有效则搜索指定状态
    if 'status' in kwargs and kwargs['status'] != '':
        where = 'a.status=%s' % kwargs['status']

    if 'key' in kwargs and kwargs['key'] != '':
        kwargs['key'] = kwargs['key'].replace(',', u'，').replace('\'', u'‘')
        where += ' AND (a.title LIKE \'%' + kwargs['key'] + '%\' OR b.username LIKE \'%' + kwargs['key'] + '%\' OR d.lib_name LIKE \'%' + kwargs['key'] + '%\')'
    if 'library_id' in kwargs and kwargs['library_id'] != '':
        where += ' AND a.library_id=%s' % kwargs['library_id']
    if 'class1' in kwargs and kwargs['class1'] != '':
        where += ' AND a.type_id=%s' % kwargs['class1']
    if 'class2' in kwargs and kwargs['class2'] != '':
        where += ' AND a.class_id=%s' % kwargs['class2']
    if 'begin_time' in kwargs and kwargs['begin_time'] != '':
        where += ' AND a.create_time>\'%s\'' % kwargs['begin_time']
    if 'end_time' in kwargs and kwargs['end_time'] != '':
        where += ' AND a.create_time<\'%s\'' % kwargs['end_time']
    if 'is_activity' in kwargs and kwargs['is_activity']:
        if kwargs['is_activity'] == '0':
            where += ' AND a.activity_id=0'
        else:
            where += ' AND a.activity_id<>0'
    # editor: kamihati 2015/6/17 过滤已经转换为模板的作品
    where += ' AND a.id not in (SELECT opus_id FROM zone_asset WHERE opus_id is not Null)'
    joni_str = 'INNER JOIN auth_user b ON b.id=a.user_id ' \
               'INNER JOIN widget_opus_classify c ON c.id=a.type_id ' \
               'INNER JOIN library d ON d.id=a.library_id ' \
               'LEFT JOIN widget_opus_classify e ON e.id=a.class_id'
    # 导入分页所需方法
    from utils.db_handler import get_pager
    from utils.db_handler import get_data_count
    from utils.db_handler import rows_to_dict_list
    data_list = rows_to_dict_list(
        get_pager(cols, 'auth_opus a', joni_str, where, 'ORDER BY a.id DESC', page_index, page_size),
        ['id', 'title', 'username', 'class1_name', 'page_count', 'preview_times', 'praise_times', 'comment_times', 'lib_name', 'activity_id', 'is_top', 'create_time', 'class2_name', 'update_time'])
    data_count = get_data_count('a.id', 'auth_opus a', joni_str, where)
    return data_list, data_count


def set_opus_status(id, status):
    '''
    更新个人创作的状态
    editor: kamihati 2015/5/8
    :param id:  个人创作id
    :param status:  要更新的状态
    :return:
    '''
    if AuthOpus.objects.filter(pk=id).update(status=status):
        return True
    return False

def set_opus_top(id, status):
    '''
    更新个人创作的置顶状态
    editor: kamihati 2015/5/8
    :param id:  个人创作id
    :param status:  要更新的状态
    :return:
    '''
    if AuthOpus.objects.filter(pk=id).update(is_top=status):
        return True
    return False


def get_opus_comment_pager(page_index, page_size, opus_id, **kwargs):
    '''
    获取个人创作的评论列表
    editor: kamihati 2015/5/8  此处代码暂时使用旧版本设计。由于牵涉mongo数据库。将来有待优化
    :param page_index: 从0计数
    :param page_size:
    :param opus_id:
    :param kwargs:
    :return:
    '''
    import datetime
    count = AuthOpusCommentMongo.objects(auth_opus_id=opus_id).count()
    import math
    comment_list_mongo = AuthOpusCommentMongo.objects(auth_opus_id=opus_id).order_by("-create_time").skip(page_index * page_size).limit(page_size)
    comm_list = []
    from account.models import AuthUser
    from WebZone.settings import MEDIA_URL
    for comment in comment_list_mongo:
        data = dict(id=comment.id,
                    user_id=int(comment.user_id),
                    comment=comment.comment,
                    create_time=comment.create_time.strftime("%Y-%m-%d %H:%M:%S"))
        user = AuthUser.objects.get(pk=comment.user_id)
        data['lib_name'] = user.library.lib_name
        data['nickname'] = user.nickname
        data['avatar_img'] = MEDIA_URL + user.avatar_img if user.avatar_img else ''
        comm_list.append(data)
    return comm_list, count


def edit_opus_comment(id, content):
    '''
    编辑作品评论
    editor: kamihati 2015/5/8 供后台管理页面使用
    :param id:
    :param content:
    :return:
    '''
    try:
        comment = AuthOpusCommentMongo.objects.get(pk=id)
        comment.comment = content
        comment.save()
        return True
    except Exception as e:
        print e
    return False


def del_opus_comment(id):
    '''
    删除作品评论
    editor: kamihati 2015/5/8
    :param id:
    :return:
    '''
    if AuthOpusCommentMongo.objects.filter(pk=id).delete():
        return True
    return False


def get_zone_asset_pager(page_index, page_size, **kwargs):
    '''
    获取公共资源的分页数据
    editor: kamihati 2015/5/11
    :param page_index:  页码。从0开始
    :param kwargs:
    :return:
    '''
    where = "a.status<>-1"
    if kwargs.has_key('key') and kwargs['key'] != '':
        where += ' AND a.res_title LIKE \'%' + kwargs['key'] + '%\''
    if kwargs.has_key('library_id') and kwargs['library_id'] != '':
        where += ' AND a.library_id=%s' % kwargs['library_id']
    if kwargs.has_key('type_id') and kwargs['type_id'] != '':
        where += ' AND a.type_id=%s' % kwargs['type_id']
    if kwargs.has_key('class_id') and kwargs['class_id'] != '':
        where += ' AND a.class_id=%s' % kwargs['class_id']
    if kwargs.has_key('is_opus'):
        where += ' AND a.opus_id is not null '
    if 'res_type' in kwargs and kwargs['res_type'] != '':
        where += ' AND a.res_type=%s' % kwargs['res_type']

    cols = 'a.id,a.res_title,a.page_count,a.ref_times,a.type_id,a.class_id,b.classify_name as class1_name,c.classify_name as class2_name,a.width,a.height,a.create_type,a.read_type,a.create_time,a.is_recommend,a.opus_id'
    items = ['id', 'res_title', 'page_count', 'ref_times', 'type_id', 'class_id', 'class1_name', 'class2_name', 'width', 'height', 'create_type', 'read_type', 'create_time', 'is_recommend', 'opus_id']
    join_str = "INNER JOIN widget_opus_classify b ON b.id=a.type_id INNER JOIN widget_opus_classify c ON c.id=a.class_id"

    data_count = get_data_count('a.id', 'zone_asset a', join_str, where)
    return rows_to_dict_list(
        get_pager(cols, 'zone_asset a', join_str, where, 'ORDER BY a.id DESC', page_index, page_size),
        items), data_count


def update_zone_asset_top(id, is_recommend):
    '''
    更新公共资源的推荐状态
    editor: kamihati 2015/5/11
    :param id:
    :param top:
    :return:
    '''
    if ZoneAsset.objects.filter(pk=id).update(is_recommend=is_recommend):
        return True
    return False


def opus_to_template(id, user):
    '''
    把个人创作转为模板
    editor: kamihati 2015/5/15  原代码为夏记编写。为方便使用在此处把几处代码整合为一个方法供各模块调用
    :param id:
    :param user:
    :return:
    '''
    if ZoneAsset.objects.filter(opus_id=id, res_type=4).count() > 0:
        return -1
    auth_opus = AuthOpus.objects.get(pk=id)
    #先创建模板封面
    zone_asset = ZoneAsset()
    # 设为3qdou官方机构所有
    from library.models import Library
    zone_asset.library = Library.objects.get(pk=3)
    zone_asset.user_id = user.id
    zone_asset.res_title = auth_opus.title if auth_opus.title else ""
    zone_asset.res_type = 4 #模板
    zone_asset.opus_id = auth_opus.id

    zone_asset.type_id = auth_opus.type_id
    zone_asset.class_id = auth_opus.class_id
    zone_asset.create_type = auth_opus.create_type
    zone_asset.read_type = auth_opus.read_type
    zone_asset.size_id = auth_opus.size_id
    #zone_asset.size_id = auth_opus.size_id
    zone_asset.width = auth_opus.width
    zone_asset.height = auth_opus.height
    zone_asset.page_count = auth_opus.page_count
    #　上传文件失败的，等待自动删除程序删除
    zone_asset.status = -1
    zone_asset.save()

    asset_path = "assets/4/%d" % zone_asset.id
    os.makedirs(os.path.join(MEDIA_ROOT, asset_path))   #创建目录
    page_list = AuthOpusPage.objects.filter(auth_opus_id=auth_opus.id).order_by('page_index')
    if page_list.count() <> auth_opus.page_count:
        return u"作品信息有错，请联系管理员改正"
    for opus_page in page_list:
        ext = os.path.splitext(opus_page.img_path)[1]
        if opus_page.page_index == 1:
            zone_asset.res_path = "%s/origin%s" % (asset_path, ext)
            zone_asset.img_large_path = zone_asset.res_path.replace("origin", "l")
            zone_asset.img_medium_path = zone_asset.res_path.replace("origin", "m")
            zone_asset.img_small_path = zone_asset.res_path.replace("origin", "s")
            zone_asset.save()
            try:
                #copy文件到模板目录
                open(os.path.join(MEDIA_ROOT, zone_asset.res_path), "wb").write(open(os.path.join(MEDIA_ROOT, opus_page.img_path), "rb").read())

                img = Image.open(os.path.join(MEDIA_ROOT, zone_asset.res_path))
                if img.size[0] > 950 or img.size[1] > 950:
                    img.thumbnail((950,950), Image.ANTIALIAS)
                    img.save(os.path.join(MEDIA_ROOT, zone_asset.img_large_path))
                else:
                    zone_asset.img_large_path = zone_asset.res_path
                if img.size[0] > 600 or img.size[1] > 600:
                    img.thumbnail((600,600), Image.ANTIALIAS)
                    img.save(os.path.join(MEDIA_ROOT, zone_asset.img_medium_path))
                else:
                    zone_asset.img_medium_path = zone_asset.res_path
                # 导入获取缩略图尺寸的方法
                from utils.decorator import get_small_size
                img.thumbnail(get_small_size(img.size[0], img.size[1]), Image.ANTIALIAS)
                img.save(os.path.join(MEDIA_ROOT, zone_asset.img_small_path))
            except:
                continue

        import json
        json_data = None
        try:
            json_data = json.loads(opus_page.json)
            if json_data.has_key('childrens'):
                for item in json_data['childrens']:
                    if item['localName'] == 'image':
                        item['photoid'] = -1
                        item['b'] = ''
                        item['m'] = ''
                        item['s'] = ''
                        try: item['o'] = ''
                        except: pass
                    elif item['localName'] == 'music':
                        item['musicId'] = -1
                        item['musicUrl'] = ''
                    elif item['localName'] == 'video':
                        item['videoId'] = -1
                        item['videoUrl'] = ''
            json_data = json.dumps(json_data)
        except Exception as e:
            print 'auth_opus to template  page %s error:' % opus_page.page_index, e

        if json_data is None:
            return u"第%d页的json文件转换错误，请联系管理员" % opus_page.page_index

        templaete = ZoneAssetTemplate()
        templaete.zone_asset_id = zone_asset.id
        templaete.page_index = opus_page.page_index
        templaete.json = json_data
        templaete.json_path = "%s/%d.json" % (asset_path, opus_page.page_index)
        templaete.img_path = "%s/%d%s" % (asset_path, opus_page.page_index, ext)
        templaete.img_small_path = "%s/%d_s%s" % (asset_path, opus_page.page_index, ext)
        templaete.save()
        try:
            #写入文件
            open(os.path.join(MEDIA_ROOT, templaete.img_path), "wb").write(open(os.path.join(MEDIA_ROOT, opus_page.img_path), "rb").read())
            open(os.path.join(MEDIA_ROOT, templaete.img_small_path), "wb").write(open(os.path.join(MEDIA_ROOT, opus_page.img_small_path), "rb").read())
            f = open(os.path.join(MEDIA_ROOT, templaete.json_path), "wb")
            f.write(json_data)
            f.close()
        except Exception as e:
            print 'auth_opus to template  json error:', e
    zone_asset.status = 1  #转换成功，直接使用
    zone_asset.save()
    return zone_asset.id


def get_opus_comment_pager(opus_id, page_index, page_size, **kwargs):
    '''
    editor: kamihati 2015/6/17  获取个人创作的评论列表 .使用mongo_db的数据
    :param request:
    :return:
    '''
    opus = AuthOpus.objects.get(pk=opus_id)

    from mongodb import AuthOpusCommentMongo
    data_count = AuthOpusCommentMongo.objects.filter(auth_opus_id=opus_id).count()
    comment_list_mongo = AuthOpusCommentMongo.objects.filter(auth_opus_id=opus_id).order_by("-create_time").skip(page_index*page_size).limit(page_size)
    comm_list = []
    uid_dict = {}
    from WebZone.settings import MEDIA_URL
    for comment in comment_list_mongo:
        comm_list.append({"user_id":int(comment.user_id),"comment":comment.comment,"create_time":comment.create_time.strftime("%Y-%m-%d %H:%M:%S")})
        uid_dict[str(comment.user_id)] = None
    if len(uid_dict) > 0:
        sql = "select id, nickname, avatar_img from auth_user where id in (%s)" % ','.join(uid_dict.keys())
        rows = get_sql_data(sql)
        for row in rows:
            uid = int(row[0])
            nickname = row[1]
            avatar_img = MEDIA_URL + row[2] if row[2] else ""
            for comm in comm_list:
                if comm["user_id"] == uid:
                    comm["nickname"] = nickname
                    comm["avatar_img"] = avatar_img
    return comm_list, data_count


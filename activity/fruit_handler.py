# coding=utf8
# editor: kamihati 2015/4/27  活动作品相关逻辑处理

import os, datetime
from PIL import Image, ImageDraw, ImageFont
import StringIO
from WebZone.settings import MEDIA_ROOT, MEDIA_URL
from WebZone.conf import fonts
from WebZone.settings import FONT_ROOT

# 导入活动作品model
from activity.models import ActivityFruit
# 导入分页方法
from utils.db_handler import get_pager
# 导入数据转dict的方法
from utils.db_handler import rows_to_dict_list
# 导入获取数据条数的放啊分
from utils.db_handler import get_data_count
# 导入model数据保存方法
from utils.db_handler import save_model_data
from utils import get_user_path

from WebZone.conf import ALLOWED_VIDEO_EXTENSION, ALLOWED_SOUND_EXTENSION, ALLOWED_IMG_EXTENSION
from WebZone.conf import ALLOWED_VIDEO_UPLOAD_SIZE
from utils.decorator import move_temp_file

# 需要过滤掉活动作品中的系统作品类别id
# editor: kamihati 2015/6/11 对应 WidgetOpusClassify
n_opus_type = '59,60,61,62,63'
fruit_opus_type_dict = {59: u'活动预告', 60: u'活动结果', 61: u"活动新闻", 62: u'活动通知', 63:u'活动播报'}
def get_activity_fruit_pager(page_index, page_size, **args):
    '''
    获取活动作品分页信息。
    editor: kamihati 2015/4/27   供后台活动作品管理使用
    editor: kamihati 2015/6/10   增加对系统作品（预告等）的过滤
                      args.n_opus_type 是否需要过滤系统创作分类
                     args.opus_type  为指定的创作类型。目前限定为系统作品使用
                          增加对分组查询的支持
    '''
    # 不显示驳回和已删除状态的活动作品
    where = 'a.status in (1, 2)'
    order_str = 'ORDER BY a.id DESC'
    if args.has_key('n_opus_type') and args['n_opus_type'] == 1:
        where += " AND a.opus_type not in (%s)" % n_opus_type

    if 'opus_type' in args and args['opus_type'] != "":
        where += ' AND a.opus_type=%s' % args['opus_type']

    if 'library_id' in args and args['library_id'] != "":
        where += ' AND a.library_id=%s' % args['library_id']
    if 'activity_id' in args and args['activity_id'] != "":
        where += ' AND a.activity_id=%s' % args['activity_id']
    if 'search_text' in args:
        if args['search_text'] not in ('', None):
            where += ' AND a.fruit_name LIKE \'%' + args['search_text'] + "%\'"
    if args.has_key('place_type') and args['place_type'] != '':
        where += ' AND c.place_type=\'' + args['place_type'] + '\''
    if args.has_key('status') and args['status'] != "":
        where += ' AND a.status IN (%s)' % args['status']
    if args.has_key('group_id') and args['group_id'] != '':
        where += ' AND a.group_id=%s' % args['group_id']
    if args.has_key('order_by') and args['order_by'] != "":
        # 按照人气。投票数。浏览量
        if args['order_by'] == 1:
            order_str = 'ORDER BY vote DESC,preview_times DESC'

    inner = 'INNER JOIN library b ON b.id=a.library_id ' \
            'INNER JOIN activity_list c ON c.id=a.activity_id ' \
            'INNER JOIN auth_user d ON d.id=a.user_id ' \
            'LEFT JOIN activity_group e ON e.id=a.group_id ' \
            'INNER JOIN library f ON f.id=d.library_id '
    data_list = rows_to_dict_list(
        get_pager('a.id,b.lib_name,c.title,a.fruit_name,d.username,a.author_name,a.author_age,a.fruit_type,e.group_name,a.`status`,f.lib_name as user_lib_name,a.number,a.opus_id,c.fruit_type,a.group_id,a.thumbnail',
                  'activity_fruit a',
                  inner,
                  where,
                  order_str,
                  page_index, page_size),
        ['id', 'lib_name', 'activity_name', 'fruit_name', 'username', 'author_name', 'author_age', 'fruit_type', 'group_name', 'status', 'user_lib_name', 'number', 'opus_id', 'activity_fruit_type', 'group_id', 'thumbnail'])
    data_count = get_data_count('a.id', 'activity_fruit a', inner, where)
    return data_list, data_count


def edit_activity_fruit(param):
    '''
    编辑活动作品
    :param param:
    :return:
    '''
    return save_model_data(ActivityFruit, param)


def set_fruit_status(id, status):
    '''
    更新活动作品的状态（-1:删除。0草稿。1待审核。2审核通过）
    editor: kamihati 2015/6/18
    :param id:  作品id
    :param status: 作品要更新成的状态
    :return:
    '''
    fruit = ActivityFruit.objects.get(pk=id)
    if ActivityFruit.objects.filter(pk=id).update(status=status):
        if fruit.opus_id:
            from diy.models import AuthOpus
            opus = AuthOpus.objects.filter(pk=fruit.opus_id)
            if opus:
                opus = opus[0]
                from diy.auth_opus_handler import set_opus_status
                status = int(status)
                if status == -1 and opus.status != 2:
                    # 驳回活动作品时把待审核状态的个人作品置为草稿状态
                    set_opus_status(fruit.opus_id, 0)
                    from activity.handler import set_activity_join_member
                    set_activity_join_member(fruit.activity_id)
                elif status == 2 and opus.status != 2:
                    set_opus_status(fruit.opus_id, 2)
        return True
    return False


def get_activity_fruit_info(id):
    '''
    获取活动作品的明细信息
    editor: kamihati 2015/4/29  供后台活动作品管理查看作品明细使用
    :param id:活动作品id
    :return:
    '''
    fruit = ActivityFruit.objects.get(id=id)
    # 导入活动记录表
    from activity.models import ActivityList
    activity = ActivityList.objects.get(pk=fruit.activity_id)
    # 导入机构标
    from library.models import Library
    library = Library.objects.get(pk=fruit.library_id)
    # 导入用户表
    from account.models import AuthUser
    user = AuthUser.objects.get(pk=fruit.user_id)
    # 导入活动分组表
    from activity.models import ActivityGroup
    groups = ActivityGroup.objects.filter(activity_id=fruit.activity_id)
    group_list = []
    for group in groups:
        is_check = 0
        if fruit.group_id == group.id:
            is_check = 1
        group_list.append(dict(id=group.id, group_name=group.group_name, is_check=is_check))
    result = dict(id=fruit.id,
                  library_id=fruit.library_id,
                  lib_name=library.lib_name,
                  fruit_name=fruit.fruit_name,
                  activity_id=activity.id,
                  activity_name=activity.title,
                  user_id=fruit.user_id,
                  username=user.username,
                  group_id=fruit.group_id,
                  group_list=group_list,
                  author_name=fruit.author_name,
                  author_sex=fruit.author_sex,
                  author_age=fruit.author_age,
                  author_email=fruit.author_email,
                  author_tel=fruit.author_telephone,
                  author_address=fruit.author_address,
                  school_name=fruit.school_name,
                  teacher=fruit.teacher,
                  author_brief=fruit.author_brief,
                  fruit_brief=fruit.fruit_brief)
    return result


def get_user_fruit_count(user_id, status=None):
    '''
    获取用户的活动作品数
    :param user_id:
    :param status:
    :return:
    '''
    if status is None:
        return ActivityFruit.objects.filter(user_id=user_id).count()
    return ActivityFruit.objects.filter(user_id=user_id, status=status).count()


def activity_fruit_temp(temp_path):
    '''
    处理活动作品的临时文件
    editor: kamihati 2015/5/18  由于旧版本设定原因。活动作品的类别与个人作品类别并非一一对应。
      故在此处根据扩展名进行类别判断。并与活动所属活动的类别进行对比。然后分别进行处理
    :param temp_path:  使用ajax_upload上传的临时文件路径
    :return:   auth_user对象
    '''
    # 导入集中声音。图片。视频的文件限制参数
    from WebZone.conf import ALLOWED_IMG_EXTENSION, ALLOWED_SOUND_EXTENSION, ALLOWED_VIDEO_EXTENSION
    # 限制尺寸。应在ajax_upload的时候进行处理。此处暂不作处理
    # from WebZone.conf import ALLOWED_IMG_UPLOAD_SIZE, ALLOWED_SOUND_UPLOAD_SIZE, ALLOWED_VIDEO_UPLOAD_SIZE


def get_fruit_number(activity_id):
    '''
    获取作品号码
    editor: kamihati 2015/5/18  使用旧版本逻辑。但此逻辑在并发情况下可能出现重复。待优化。
    :param activity_id:
    :return:
    '''
    # 导入获取Sql语句数据的方法
    from utils.db_handler import get_sql_data
    sql = "select number from activity_fruit where activity_id=%s AND number<>'' ORDER BY number DESC LIMIT 1" % activity_id
    rows = get_sql_data(sql)
    cur_id = 0
    if len(rows) != 0:
        cur_id = int(rows[0][0])
    return str(cur_id + 1).zfill(4)


def edit_video_fruit(file_path, fruit_type,  *ages, **kwargs):
    '''
    编辑活动作品
    editor: kamihati 2015/5/20
    :param user_id:  添加人
    :param ages:
    :param kwargs:
    :return:
    '''
    from library.models import Library
    from activity.models import ActivityList
    from account.models import AuthUser
    from diy.models import AuthOpus, AuthOpusPage, AuthAssetRef, AuthAsset, AuthAssetShare

    library = Library.objects.get(pk=kwargs['library_id'])
    activity = ActivityList.objects.get(pk=kwargs['activity_id'])
    user = AuthUser.objects.get(pk=kwargs['user_id'])

    # 获取用户资源
    auth_asset = AuthAsset()
    auth_asset.library = library
    auth_asset.user = user
    auth_asset.res_title = kwargs['title']
    # 导入根据fruit_type 得到res_type的方法
    # res_type  ((1,u"图片"),(2,u"声音"),(3,u"视频"))
    from activity.handler import get_res_type_by_fruit_type
    auth_asset.res_type = get_res_type_by_fruit_type(fruit_type)
    auth_asset.status = -1  #未上传成功前，先状态为-1
    auth_asset.ref_times = 1
    auth_asset.share_times = 1
    auth_asset.save()   #得到ID

    auth_opus = AuthOpus()
    if auth_asset.res_type == 1:
        # 声音文件的处理
        pass
    elif auth_asset.res_path == 2:
        # 图片文件的处理
        pass
    elif auth_asset.res_path == 3:
        # 视频文件的处理
        filename, ext = os.path.splitext(file_path)
        if ext.lower() not in ALLOWED_VIDEO_EXTENSION:
            return -1, u"只充许上传视频文件(%s)" % ';'.join(ALLOWED_VIDEO_EXTENSION)

        asset_res_path = "%s/%d" % (get_user_path(user, auth_asset.res_type), auth_asset.id)
        if not os.path.exists(os.path.join(MEDIA_ROOT, asset_res_path)):
            os.makedirs(os.path.join(MEDIA_ROOT, asset_res_path))
        auth_asset.origin_path = '%s/origin%s' % (asset_res_path, ext)
        auth_asset.res_path = '%s/%d.flv' % (asset_res_path, auth_asset.id)
        auth_asset.img_large_path = '%s/l.jpg' % asset_res_path
        auth_asset.img_small_path = '%s/s.jpg' % asset_res_path
        # 需要进行转码
        move_temp_file(file_path, asset_res_path + "/origin")
        auth_asset.status = 1
        auth_asset.save()

        # 视频作品按照原故事达人的模版进行处理

        auth_opus.user = user
        auth_opus.library_id = kwargs['library_id']
        auth_opus.title = kwargs['title']
        auth_opus.brief = kwargs['brief']
        auth_opus.show_type = 101   #故事大王大赛的风格
        auth_opus.type_id = 2   #才艺展示
        auth_opus.class_id = 24    #讲故事
        auth_opus.page_count = 1
        auth_opus.width = 1812
        auth_opus.height = 870
        auth_opus.status = 1    #待审核    自动转码成功后，转为已发表状态
        auth_opus.save()

        #创建资源的引用表
        auth_asset_ref = AuthAssetRef()
        auth_asset_ref.auth_asset = auth_asset
        auth_asset_ref.user = user
        auth_asset_ref.auth_opus = auth_opus
        auth_asset_ref.page_index = 1
        auth_asset_ref.res_type = auth_opus.type_id
        auth_asset_ref.save()

        opus_res_path = get_user_path(user, "opus", auth_opus.id)
        auth_opus_page = AuthOpusPage()
        auth_opus_page.auth_opus = auth_opus
        auth_opus_page.page_index = 1
        auth_opus_page.is_multimedia = 1
        auth_opus_page.auth_asset_list = int(auth_asset.id)
        auth_opus_page.json_path = "%s/1.json" % opus_res_path
        auth_opus_page.img_path = "%s/1.jpg" % opus_res_path
        auth_opus_page.img_small_path = "%s/1_s.jpg" % opus_res_path
        auth_opus_page.save()
        # 制作视频创作
        edit_video_opus(user, auth_asset, auth_opus, auth_opus_page,
                        author_name=kwargs['author_name'],
                        sex=kwargs['sex'],
                        age=kwargs['age'],
                        school_name=kwargs['school_name'],
                        unit_name=kwargs['unit_name'],
                        number=kwargs['number'])


def edit_video_opus(auth_user, auth_asset, auth_opus, auth_opus_page, **kwargs):
    '''
    制作视频作品的播放资源文件
    editor: kamihati 2015/5/20
    :param auth_user:  提交用户
    :param auth_asset:  对应的用户个人素菜
    :param auth_opus:  对应的用户个人作品
    :param auth_opus_page: 对应的用户个人作品分页
    :param widget_story_unit:
    :return:
    '''
    json_file = open(os.path.join(MEDIA_ROOT, "opus_temp/video/1.json"), 'r')
    img_file = open(os.path.join(MEDIA_ROOT, "opus_temp/video/1.jpg"), "rb")
    json_data = json_file.read()
    json_file.close()

    json_data = json_data.replace("{video_url}", MEDIA_URL + auth_asset.res_path)
    json_data = json_data.replace("{video_id}", str(auth_asset.id))
    json_data = json_data.replace("{story_name}", auth_opus.title)
    json_data = json_data.replace("{actor_name}", kwargs['author_name'])
    json_data = json_data.replace("{sex}", u"男" if kwargs['sex'] == 1 else u"女")
    json_data = json_data.replace("{age}", str(kwargs['age']))
    json_data = json_data.replace("{school_name}", kwargs['school_name'])
    json_data = json_data.replace("{unit_name}", kwargs['unit_name'])
    json_data = json_data.replace("{number}", kwargs['number'])
    asset_res_path = get_user_path(auth_user, "opus", auth_opus.opus_id)
    if not os.path.exists(os.path.join(MEDIA_ROOT, asset_res_path)):
        os.makedirs(os.path.join(MEDIA_ROOT, asset_res_path))

    json_data = json_data.encode('utf-8')
    auth_opus_page.json = json_data
    auth_opus_page.save()
    open(os.path.join(MEDIA_ROOT, auth_opus_page.json_path), "w").write(json_data)

    img_data = img_file.read()
    img_file.close()
    img = Image.open(StringIO(img_data))

    font_file = fonts[1]["font"]
    font_file = os.path.join(FONT_ROOT, font_file)
    #print font_file
    dr = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_file, 32)
    dr.text((1389,174), auth_opus.title, fill="#000000", font=font)
    dr.text((1392,227), kwargs['author_name'], fill="#000000", font=font)
    dr.text((1390,285), u"男" if kwargs['sex'] == 1 else u"女", fill="#000000", font=font)
    dr.text((1392,344), str(kwargs['age']), fill="#000000", font=font)
    dr.text((1394,399), kwargs['school_name'], fill="#000000", font=font)
    dr.text((1466,458), kwargs['number'], fill="#000000", font=font)

    if len(kwargs['unit_name']) > 9:
        dr.text((1466,519), kwargs['unit_name'][:9], fill="#000000", font=font)
        dr.text((1466,580), kwargs['unit_name'][9:], fill="#000000", font=font)
    else:
        dr.text((1466,519), kwargs['unit_name'], fill="#000000", font=font)
    img.save(os.path.join(MEDIA_ROOT, auth_opus_page.img_path))


def get_join_member_pager(page_index, page_size, **kwargs):
    '''
    获取活动的参与人数资料
    editor: kamihati 2015/5/20
    :param page_index:
    :param page_size:
    :param activity_id:
    :param kwargs:
    :return:
    '''
    cols = 'a.id,b.title,a.fruit_name,a.number,a.author_name,a.author_age,c.group_name,a.school_name,' \
           'a.author_email,a.author_telephone,a.teacher,a.author_address,d.lib_name'
    tb_name = 'activity_fruit a'
    inner_str = 'INNER JOIN activity_list b ON b.id=a.activity_id ' \
                'LEFT JOIN activity_group c ON c.id=a.group_id ' \
                'INNER JOIN library d on d.id=a.library_id '
    where_str = 'a.status>0 and a.opus_type not IN (%s)' % n_opus_type

    if kwargs.has_key('activity_id') and kwargs['activity_id'] != '':
        where_str += ' AND a.activity_id=%s' % kwargs['activity_id']
    order_str = 'ORDER BY a.id DESC'
    data_list = rows_to_dict_list(
        get_pager(cols, tb_name, inner_str, where_str, order_str, page_index, page_size),
        ['id', 'title', 'fruit_name', 'number', 'author_name', 'author_age', 'group_name', 'school_name',
         'author_email', 'author_telephone', 'teacher', 'author_address', 'lib_name'])
    data_count = get_data_count('a.id', tb_name, inner_str, where_str)
    return data_list, data_count


def create_join_member_excel(activity_id, xls_download_name, **kwargs):
    '''
    制作制定活动的参与人数资料excel
    editor: kamihati 2015/5/20
    :param activity_id:
    :param kwargs:
    :return:
    '''
    data_list, data_count = get_join_member_pager(0, 99999, activity_id=activity_id)
    from utils.decorator import write_excel
    exl_path = "/excel/join_member/%s.xls" % activity_id
    return write_excel(
        data_list, xls_download_name,
        title=['id', u'活动名称', u'作品名称', u'作品编号', u'作者', u'年龄', u'所属分组', u'学校',
               u'邮箱', u'电话', u'指导老师', u'家庭住址', u'机构名称'])


def get_fruit_score_pager(page_index, page_size, **kwargs):
    '''
    获取作品评分记录
    editor:kamihati 2015/5/22
    :param page_index:
    :param page_size:
    :param activity_id:
    :param kwargs:
    :return:
    '''
    cols = 'a.id,a.number,b.lib_name,c.title,a.unit_name,a.fruit_name,a.group_id,d.group_name,a.author_name,a.author_age,a.score,a.score_brief'
    tb_name = 'activity_fruit a'
    inner_str = 'INNER JOIN library b ON b.id=a.library_id ' \
                'INNER JOIN activity_list c ON c.id=a.activity_id ' \
                'INNER JOIN activity_group d ON d.id=a.group_id '
    where_str = 'a.`status`<>-1'
    if kwargs.has_key('activity_id') and kwargs['activity_id'] != '':
        where_str += ' AND a.activity_id=%s' % kwargs['activity_id']
    elif kwargs.has_key('library_id') and kwargs['library_id'] != '':
        where_str += ' AND a.library_id=%s' % kwargs['library_id']

    order_str = 'ORDER BY a.id DESC'
    data_list = rows_to_dict_list(
        get_pager(cols, tb_name, inner_str, where_str, order_str, page_index, page_size),
        ['id', 'number', 'lib_name', 'title', 'unit_name', 'fruit_name', 'group_id', 'group_name', 'author_name', 'author_age', 'score', 'score_brief'])
    data_count = get_data_count('a.id', tb_name, inner_str, where_str)
    return data_list, data_count

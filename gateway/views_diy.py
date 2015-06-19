#coding: utf-8
'''
Created on 2014-3-28

@author: Administrator
'''
import os
from pyamf.amf3 import ByteArray

from datetime import datetime
from PIL import Image
from StringIO import StringIO
from math import ceil

from django.db import connection, connections
from WebZone.settings import DB_READ_NAME

from django.core.cache import cache

from WebZone.conf import fonts, new_fonts
from WebZone.conf import ALLOWED_IMG_EXTENSION
from WebZone.conf import ZONE_RES_STYLE, ZONE_RES_TYPE
from utils.db_handler import get_sql_data


from WebZone.settings import MEDIA_ROOT, MEDIA_URL
from WebZone.settings import FONT_ROOT
from WebZone.settings import FONT_IMG_URL

from utils import get_tile_image_name, get_img_ext
from utils import get_user_path
from utils.decorator import login_required

from diy.models import AuthAsset
from gateway import SuccessResponse, FailResponse
from library.models import Library
# 导入获取静态文件url方法
from utils.decorator import get_host_file_url
# 导入获取公共资源的方法
from diy.zone_asset_handler import get_zone_asset_list
# 导入获取公共资源分页的方法
from diy.zone_asset_handler import get_zone_asset_pager


def get_lib_info(request):
    host = request.get_host()
    #print host
    try:
        lib = Library.objects.get(host=host)
        swf = MEDIA_URL + lib.swf_path if lib.swf_path else ""
        logo = MEDIA_URL + lib.logo_path if lib.logo_path else ""
        back_data = {"id":lib.id, "swf":swf, "logo":logo, "name":lib.lib_name}
        return SuccessResponse(back_data)
    except: return FailResponse(u'不存在的图书馆')

def get_font_list(request):
    '''
    字体列表。（old)
    :param request:
    :return:
    '''
    font_list = []
    for font_key in fonts.keys():
        #img_url = request.build_absolute_uri( FONT_IMG_URL + fonts[font_key]['img'] )
        img_url = FONT_IMG_URL + fonts[font_key]['img']
        #print img_url
        font_list.append({"id":font_key,
                          "label":fonts[font_key]['label'],
                          "url": img_url,
                          })
    return SuccessResponse(font_list)


def get_new_font_list(request):
    '''
    新版字体设计为文本框信息.
    :param request:
    :return:
    coder: kamihati 2015/4/2  由于客户端要求新版字体与上个版本的设计兼容。故新增此接口。上个版本的字体接口不做改动
    '''
    result = []
    for font in new_fonts:
        temp_dict = dict()
        temp_dict['id'] = font['id']
        temp_dict['rect'] = font['rect']
        temp_dict['size'] = font['size']
        temp_dict['label'] = font['label']
        # temp_dict['img'] = get_host_file_url(request, 'new_font/' + font['img'], 'static', '/static/')
        temp_dict['img'] = '/static/new_font/' + font['img'] if font['img'] != '' else ''
        # temp_dict['icon'] = get_host_file_url(request, 'new_font/' + font['icon'], 'static', '/static/')
        temp_dict['icon'] = '/static/new_font/' + font['icon']
        result.append(temp_dict)
    return SuccessResponse(result)


from utils.decorator import print_trace
@print_trace
def get_font_img(request, font):
    print font
    font_id = int(font.id)
    if font_id not in fonts.keys():
        return FailResponse(u'非法的字体请求')
    font_file = fonts[font_id]["font"]
    font_file = os.path.join(FONT_ROOT, font_file) 
    #font_file = font_file.encode('utf-8')
    if not os.path.isfile(font_file):
        return FailResponse(u'字体文件不存在')
    if len(font.content) == 0: font.content = fonts[font_id]["label"]
    
    from utils.txt2img import txt2img

    img = txt2img(font, font_file)
    #img.save("c:\\font.png")
    buf = StringIO()
    img.save(buf, 'png')
    snapshot = ByteArray()
    snapshot.write(buf.getvalue())
    return snapshot

@login_required
def update_avatar(request, image):
    img = Image.open(StringIO(image.getvalue()))
    ext = get_img_ext(img)
    if ext == None:
        return FailResponse(u"只充许上传图片文件(%s)" % ';'.join(ALLOWED_IMG_EXTENSION))
    
    user_path = get_user_path(request.user, "")
    user_abspath = os.path.join(MEDIA_ROOT, user_path)
    if not os.path.exists(user_abspath):
        os.makedirs(user_abspath)

    avatar_img = '%s/%d%s' % (user_path, request.user.id, ext)
    #print avatar_img
    img_large = img.resize((300, 300), Image.ANTIALIAS)
    img_large.save(os.path.join(MEDIA_ROOT, get_tile_image_name(avatar_img, 'l')))
    img_medium = img.resize((120, 120), Image.ANTIALIAS)
    img_medium.save(os.path.join(MEDIA_ROOT, get_tile_image_name(avatar_img, 'm')))
    img_small = img.resize((40, 40), Image.ANTIALIAS)
    img_small.save(os.path.join(MEDIA_ROOT, get_tile_image_name(avatar_img, 's')))
    
    request.user.avatar_img = avatar_img
    request.user.save()
#     return SuccessResponse({'large':request.build_absolute_uri(MEDIA_URL + get_tile_image_name(avatar_img, 'l')),
#                             'medium':request.build_absolute_uri(MEDIA_URL + get_tile_image_name(avatar_img, 'm')),
#                             'small':request.build_absolute_uri(MEDIA_URL + get_tile_image_name(avatar_img, 's'))})
    return SuccessResponse({'large':MEDIA_URL + get_tile_image_name(avatar_img, 'l'),
                            'medium':MEDIA_URL + get_tile_image_name(avatar_img, 'm'),
                            'small':MEDIA_URL + get_tile_image_name(avatar_img, 's')})


@login_required
def get_res_url(request, res_type, res_id, size_type="s"):
    """
    generate the match resource's http uri
    if resource is image, need size_type, get (small, medium, large, origion) photo
    """
    res_type = res_type.lower()
    if res_type not in ('image','sound','video'):
        return FailResponse(u'资源类型(%s)不正确' % res_type)
    return SuccessResponse({'url':'http://10.0.0.177:81/static/images/avatar/default.jpg'})


@login_required
def get_personal_url(request, id):
    try: auth_asset = AuthAsset.objects.get(id=id)
    except(AuthAsset.DoesNotExist): return FailResponse(u'资源ID(%s)不存在' % id)

    data_dict = {"id":id}
    data_dict["origin"] = MEDIA_URL + auth_asset.res_path
    data_dict["res_type"] = auth_asset.res_type
    if auth_asset.res_type == 1:    #照片
        data_dict["large"] = MEDIA_URL + auth_asset.img_large_path
        data_dict["medium"] = MEDIA_URL + auth_asset.img_medium_path
        data_dict["small"] = MEDIA_URL + auth_asset.img_small_path
    return SuccessResponse(data_dict)

    
@login_required    
def get_zone_type_list(request):
    """
        公共资源的类型列表
    """
    return SuccessResponse(ZONE_RES_TYPE)

@login_required
def get_zone_style_list(request):
    """
        公共资源的风格列表
    """
    return SuccessResponse(ZONE_RES_STYLE)

@login_required
def get_opus_type_list(request):
    """
        个人作品的大类型列表
    """
    sql = "select id,classify_name from widget_opus_classify where parent_id=0"
    rows = get_sql_data(sql)
    data_lists = []
    for row in rows:
        data_lists.append({"id":row[0], "name":row[1]})
    return SuccessResponse(data_lists)

@login_required
def get_opus_size_list(request):
    """
        个人作品的尺寸列表
        editor: kamihati 2015/6/16
    """
    sql = "select id,create_type,read_type,screen_width,screen_height,print_width,print_height,origin_width,origin_height,res_path,img_small_path from widget_page_size where status=1"
    rows = get_sql_data(sql)
    data_lists = []
    for row in rows:
        size_dict = {}
        size_dict["id"] = row[0]
        size_dict["create_type"] = row[1]
        size_dict["read_type"] = row[2]
        size_dict["screen_width"] = row[3]
        size_dict["screen_height"] = row[4]
        size_dict["print_width"] = row[5]
        size_dict["print_height"] = row[6]
        size_dict["origin_width"] = row[7]
        size_dict["origin_height"] = row[8]
        size_dict["large"] = MEDIA_URL + row[9] if row[9] else ""
        size_dict["small"] = MEDIA_URL + row[10] if row[10] else ""
        if size_dict["create_type"] == 3 or size_dict["read_type"] == 3:
            import copy
            size_dict1 = copy.copy(size_dict)
            size_dict1["create_type"] = 1
            size_dict1["read_type"] = 1
            data_lists.append(size_dict1)
            size_dict2 = copy.copy(size_dict)
            size_dict2["create_type"] = 2
            size_dict2["read_type"] = 2
            data_lists.append(size_dict2)
        else:
            data_lists.append(size_dict)
    return SuccessResponse(data_lists)

@login_required
def get_opus_class_list(request, param):
    """
        个人作品的小类型列表
        editor: kamihati 2015/6/9 修改实现逻辑以统一获取途径
    """
    parent_id = int(param['type_id']) if param.has_key('type_id') else 0
    is_sys = int(param['is_sys']) if param.has_key('is_sys') else 0
    # 导入获取分类列表的方法
    from widget.handler import get_opus_type_list
    return SuccessResponse(get_opus_type_list(parent_id, is_sys=is_sys))
    """
    sql = "select id,classify_name from widget_opus_classify where status<>-1 AND parent_id=%s" % parent_id
    cur = connections[DB_READ_NAME].cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    data_lists = []
    for row in rows:
        data_lists.append({"id":row[0], "name":row[1], "size_list":opus_size_list(row[0])})
    return SuccessResponse(data_lists)
    """


@login_required
def get_opus_class_child_list(request, parent_id=0):
    '''
    获取个人作品的所有子类列表
    :param request:
    :return:
    coder kamihati 2015/3/30    新版客户端用
    editor: kamihati 2015/6/16 修改此接口实现逻辑。如果是系统分类则有子类
    '''
    from widget.handler import get_opus_type_list
    return SuccessResponse(get_opus_type_list(parent_id=parent_id))


def opus_size_list(opus_type_id):
    size_list = []
    sql = "select screen_width, screen_height, print_width, print_height, origin_width, origin_height,create_type,read_type from widget_opus_size where classify_id=%d" % opus_type_id
    cur = connections[DB_READ_NAME].cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    for row in rows:
        size_list.append({"screen_width":row[0], "screen_height":row[1], "print_width":row[2], "print_height":row[3], "origin_width":row[4], "origin_height":row[5], "create_type":row[6], "read_type":row[7]})
    return size_list


@login_required
def get_notice_list(request, is_detail=0):
    if request.user.library: where_clause = "(library_id is null or library_id=%d)" % request.user.library.id
    else: where_clause = "library_id is null"
    where_clause += " and status=1 and expire_time>='%s'" % datetime.now()
    
    from account.models import AuthNotice
    notices = AuthNotice.objects.filter(user_id=request.user.id)
    if notices:
        read_notice_ids = notices[0].notice_ids
    else:
        read_notice_ids = ""
    if read_notice_ids:
        where_clause += " and id not in (%s)" % read_notice_ids
    count = 0
    back_data = []
    cursor = connections[DB_READ_NAME].cursor()
    if is_detail:
        sql = "select id,content from widget_notice where %s" % where_clause
        cursor.execute(sql)
        rows = cursor.fetchall()
        id_list = ""
        for row in rows:
            if not row: continue
            id_list += ',' + str(row[0]) if len(id_list)>0 else str(row[0])
            notice_dict = {"id":row[0], "content":row[1]}
            back_data.append(notice_dict)
        if id_list:
            sql = "update auth_notice set notice_ids='%s' where user_id=%d" % (new_read_notice(read_notice_ids, id_list), request.user.id)
            #print sql
            cursor.execute(sql)
    else:
        sql = "select count(*) from widget_notice where %s" % where_clause
        cursor.execute(sql)
        row = cursor.fetchone()
        if row: count = row[0]
    return SuccessResponse({"count":count, "data":back_data})

def new_read_notice(read_notice_ids, id_list):
    new_id_list = []
    for id1 in read_notice_ids.split(','):
        if len(str(id1)) == 0: continue
        if new_id_list.count(str(id1)) == 0:
            new_id_list.append(str(id1))
    for id2 in id_list.split(','):
        if len(str(id2)) == 0: continue
        if new_id_list.count(str(id2)) == 0:
            new_id_list.append(str(id2))
    #print new_id_list, id_list
    return ','.join(new_id_list)
    
@login_required
def get_msg_list(request, is_detail=0, page_index=1, page_size=20):
    """
    get personal unread message list
    """
    from gateway.views_opus import get_opus_cover_img
    count = 0
    back_data = []
    cursor = connections[DB_READ_NAME].cursor()
    if is_detail:  #需要详细列表
        sql = "select count(*) from auth_message where user_id=%d and status>0" % request.user.id    
        cursor.execute(sql)
        row = cursor.fetchone()
        if row: count = row[0]
        page_count = int(ceil(count/float(page_size)))
    
        sql = "select m.id,m.opus_id,msg_type,m.content,m.create_time,o.title,o.thumbnail from auth_message m LEFT JOIN auth_opus o on m.opus_id=o.id where m.user_id=%d order by create_time desc limit %d, %d" % (request.user.id, (page_index-1)*page_size, page_size)
        cursor.execute(sql)
        rows = cursor.fetchall()
        #print rows
        #id_list = ""
        for row in rows:
            if not row: continue
            msg_dict = {}
            #id_list += ',' + str(row[0]) if len(id_list)>0 else str(row[0])
            msg_dict["opus_id"] = row[1]
            msg_dict["msg_type"] = row[2]
            msg_dict["content"] = row[3] if row[3] else ""
            msg_dict["create_time"] = row[4].strftime("%Y-%m-%d %H:%M:%S")
            msg_dict["opus_title"] = row[5] if row[5] else ""
            msg_dict["opus_thumbnail"] = row[6] if row[6] else get_opus_cover_img(msg_dict["opus_id"])[1]
            if msg_dict["opus_thumbnail"]: msg_dict["opus_thumbnail"] = MEDIA_URL + msg_dict["opus_thumbnail"]
            back_data.append(msg_dict)
        #if id_list:
            #sql = "update auth_message set status=2,read_time='%s' where id in (%s)" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), id_list)
        sql = "update auth_message set status=2,read_time='%s' where user_id=%d and status=1" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), request.user.id)
        cursor.execute(sql)
        return SuccessResponse({"count":count, "data":back_data, "page_index":page_index, "page_count":page_count})
    else:
        sql = "select count(*) from auth_message where user_id=%d and status=1" % request.user.id    
        cursor.execute(sql)
        row = cursor.fetchone()
        if row: count = row[0]
    return SuccessResponse({"count":count, "data":back_data})
    

@login_required
def get_index_list(request, param):
    """
        得到首页原创作品，学习平台作品列表，按标题排个序吧
    """
    from WebZone.conf import DOU_RES_HOST
    from gateway.views_opus import get_opus_cover_img
    from gateway.views_3qdou_new import asset_type_name

    if param.has_key("page_index"): page_index = int(param.page_index)
    else: page_index = 1
    if param.has_key("page_size"): page_size = int(param.page_size)
    else: page_size = 8

    cache_index_count_key = "gateway.get_index_list.index_count"
    cache_index_list_key = "gateway.get_index_list.index_list"
    index_count = cache.get(cache_index_count_key, None)
    index_list = cache.get(cache_index_list_key, None)

    if index_count == None or index_list == None:
        #先查原创作品
        where_clause = "status=2 and is_top=1"
        if request.user.library:
            if request.user.library.is_global == 1:
                pass
            else:
                where_clause += " and (library_id is null or library_id=%d)" % request.user.library.id
        else: where_clause += " and library_id is null"
        #print where_clause
        cursor = connections[DB_READ_NAME].cursor()
        sql = "select count(*) from auth_opus where %s" % where_clause
        cursor.execute(sql)
        row = cursor.fetchone()
        row_count_opus = 0
        if row: row_count_opus = row[0]
        
        sql = "select id,title,brief,tags,type_id,thumbnail,show_type,create_type,read_type from auth_opus where %s order by update_time desc" % where_clause
        # print sql
        cursor.execute(sql)
        rows = cursor.fetchall()
        opus_list = []
        for row in rows:
            if not row: continue
            opus_dict = {"classify":"opus"}
            opus_dict["id"] = row[0]
            opus_dict["title"] = row[1] if row[1] else u"未命名作品"
            opus_dict["brief"] = row[2]
            opus_dict["tags"] = row[3]
            opus_dict["type_id"] = row[4]
            if row[5]:
                opus_dict["thumbnail"] = MEDIA_URL + row[5]
            else:
                thumbnail_path = get_opus_cover_img(opus_dict["id"])[1]    #第一页缩略图当封面
                if thumbnail_path:
                    opus_dict["thumbnail"] = MEDIA_URL + thumbnail_path
                else:
                    opus_dict["thumbnail"] = ""
            opus_dict["show_type"] = row[6] #活动分类，如故事大王大赛
            opus_dict["create_type"] = row[7]   #单双页
            opus_dict["read_type"] = row[8]        #单双页
            opus_list.append(opus_dict)

        where_clause = "status=1 and is_top=1"
        sql = "select count(*) from dou_asset where %s" % where_clause
        #print sql
        cursor.execute(sql)
        row = cursor.fetchone()
        row_count_dou = 0
        if row: row_count_dou = row[0]
        index_count = row_count_opus + row_count_dou
        
        sql = "select id, guid, type_id, title, series_title, label, description, publisher, page_count, width, height, res_path, thumbnail, extension,file_path,thumb_path from dou_asset"
        sql += " where %s" % where_clause
        #print sql
        cursor.execute(sql)
        rows = cursor.fetchall()
        asset_list = []
        for row in rows:
            if not row: continue
            id = int(row[0])
            guid = row[1]
            type_id = int(row[2])
            title = row[3]
            series_title = row[4]
            label = row[5]
            description = row[6]
            publisher = row[7]
            page_count = int(row[8]) if row[8] else 0
            width = int(row[9]) if row[9] else 0
            height = int(row[10]) if row[10] else 0

            res_path = row[11]
            thumbnail = row[12]
            extension = row[13]
            file_path = row[14]
            thumb_path = row[15]

            asset_dict = {"classify":"dou", "id":id, "guid":guid, "title":title, "series_title":series_title, "label":label, "description":description, "publisher":publisher}
            asset_dict["type_id"] = type_id
            asset_dict["type_name"] = asset_type_name(type_id)
            asset_dict["page_count"] = page_count
            asset_dict["extension"] = extension
            asset_dict["thumbnail"] = '/media/4t/3qdou/' + thumbnail
            if type_id == 2:    #book
                asset_dict["thumbnail"] = '/media/4t/3qdou/cover/book/' + thumbnail
                if page_count == 1: #单页的电子书
                    asset_dict["url"] = '/media/4t/3qdou/book/' + res_path
                    asset_dict["extension"] = 'swf'
                else:
                    asset_dict["extension"] = ''
                    asset_dict["width"] = width
                    asset_dict["height"] = height
                    page_list = []
                    for i in xrange(1, page_count+1):
                        page = {"page":i}
                        page['url'] = '/media/4t/3qdou/book/%s/%d.swf' % (file_path, i)
                        page['thumbnail'] = '/media/4t/3qdou/book/%s/%d.jpg' % (thumb_path, i)
                        page_list.append(page)
                    asset_dict["pages"] = page_list
            elif type_id == 3:  #game
                asset_dict["thumbnail"] = '/media/4t/3qdou/cover/game/' + thumbnail
                asset_dict["url"] = '/media/4t/3qdou/game/' + res_path
            elif type_id == 6:  #video
                asset_dict["thumbnail"] = '/media/4t/3qdou/cover/video/' + thumbnail
                asset_dict["url"] = '/media/4t/3qdou/video/' + res_path

            asset_list.append(asset_dict)
        cursor.close()

        index_list = asset_list + opus_list
        cache.set(cache_index_count_key, index_count, 60)
        cache.set(cache_index_list_key, index_list, 60)

    total_page_count = int(ceil(index_count/float(page_size)))
    if page_index < 1:
        page_index = 1
    #elif page_index > total_page_count: page_index = total_page_count
    #print "total_page_count", total_page_count

    return SuccessResponse({"data": index_list[(page_index-1) * page_size: page_index*page_size], "page_index": page_index, "page_count": total_page_count})


def fetch_effect_list(request, param):
    '''
    获取特效的素材列表
    editor: kamihati 2015/6/9  对客户端获取特效列表进行支持
    :param request:
    :param param:
               *param.page_index.  页码。从1开始  必传
               *param.page_size.   每页数据数。默认0  必传
               param.res_type       资源分类
               param.res_style     资源风格
    :return:
    '''
    page_index = int(param.page_index) if param.has_key('page_index') else 1
    page_size = int(param.page_size) if param.has_key('page_size') else 8
    # editor: kamihati 2015/6/9  特效id目前为8
    res_type = int(param.res_type) if param.has_key('res_type') else 8
    res_style = int(param.res_style) if param.has_key('res_style') else 0
    # 是否优先显示当前用户喜欢的资源  editor: kamihati 2015/6/9
    is_like = int(param.is_like) if param.has_key('is_like') else 0
    data_list, data_count, like_count = get_zone_asset_pager(page_index - 1, page_size, res_type=res_type,
                                                             res_style=res_style, is_like=is_like, req=request)

    return SuccessResponse(dict(
        data=data_list, data_count=data_count, page_index=page_index, page_size=page_size,
        res_type=res_type, res_style=res_style, like_count=like_count,
        page_count=data_count / page_size if data_count % page_size == 0 else data_count / page_size + 1))


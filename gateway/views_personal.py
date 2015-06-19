#coding: utf-8
'''
Created on 2014-4-14

@author: Administrator
'''
from datetime import datetime
import os
from math import ceil
from django.db import connection, connections
from WebZone.settings import DB_READ_NAME

from PIL import Image, ImageOps
from StringIO import StringIO

from WebZone.conf import ALLOWED_IMG_EXTENSION, ALLOWED_IMG_UPLOAD_SIZE

from WebZone.settings import MEDIA_ROOT, MEDIA_URL

from utils import get_img_ext
from utils import get_user_path
from utils.decorator import login_required

from diy.models import AuthAlbum
from diy.models import AuthAsset
from gateway import SuccessResponse, FailResponse



@login_required
def create_album(request, album_title):
    if len(album_title) == 0:
        return FailResponse(u'必须输入相册标题')
    if len(album_title) > 100:
        return FailResponse(u'相册标题超过最大长度')
    
    if AuthAlbum.objects.filter(album_title=album_title).count() > 0:
        return FailResponse(u'相册标题已存在，请重新选择')
    
    auth_album = AuthAlbum()
    auth_album.user = request.user
    auth_album.album_title = album_title
    auth_album.save()
    
    return SuccessResponse(u"相册[%s]创建成功！" % album_title)

@login_required
def get_album_list(request):
    sql = "select id, album_title from auth_album where user_id=%d and status=1" % request.user.id
    cursor = connections[DB_READ_NAME].cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    
    album_list = []
    for row in rows:
        if not row: continue
        album_list.append({"id":row[0], "title":row[1]})
    album_list.append({"id":0, "title":u"默认相册"})
    
    return SuccessResponse(album_list)


def get_camera_album(auth_user):
    """
    报像头自拍相册，如果没有，则创建一个，属于系统相册
    """
    try: auth_album = AuthAlbum.objects.get(user_id=auth_user.id, album_title=u'我的自拍', type_id=0)
    except(AuthAlbum.DoesNotExist):
        auth_album = AuthAlbum()
        auth_album.user_id = auth_user.id
        auth_album.album_title = u'我的自拍'
        auth_album.type_id = 0
        auth_album.save()
    return auth_album


@login_required
def update_camera_image(request, param):
    """
    新建，更新“我的自拍”照片
    """
    if param.has_key("image_data"):
        image_data = param.image_data.getvalue()
    else:
        return FailResponse(u'必须传入图片对象')
    
    if len(image_data) > ALLOWED_IMG_UPLOAD_SIZE:
        return FailResponse(u'文件超过最大充许大小')
    img = Image.open(StringIO(image_data))
    ext = get_img_ext(img)
    if ext == None:
        return FailResponse(u"只充许上传图片文件(%s)" % ';'.join(ALLOWED_IMG_EXTENSION))
    if param.has_key("title"): title = title = param.title
    else: title = datetime.now().strftime("%Y%m%d_%H:%M:%S")

    auth_album = get_camera_album(request.user)
    #print auth_album
    
    if param.has_key("id") and param.id:
        camear_id = param.id
        try: auth_asset = AuthAsset.objects.get(id=camear_id)
        except(AuthAsset.DoesNotExist): return FailResponse(u"请指定要修改的涂鸦的ID")
    else:
        auth_asset = AuthAsset()
        auth_asset.library = request.user.library
        auth_asset.user = request.user
        auth_asset.res_type = 1 #图片
        auth_asset.album_id = auth_album.id
        auth_asset.status = -1
    auth_asset.res_title = title
    auth_asset.save()
    
    asset_res_path = "%s/%d" % (get_user_path(request.user, 'image', auth_album.id), auth_asset.id)
    #print asset_res_path
    asset_res_abspath = os.path.join(MEDIA_ROOT, asset_res_path)
    if not os.path.lexists(asset_res_abspath):
        os.makedirs(asset_res_abspath)  #不存在，则创建文件夹

    auth_asset.res_path = '%s/origin%s' % (asset_res_path, ext)
    auth_asset.img_large_path = auth_asset.res_path.replace("origin", "l")
    auth_asset.img_medium_path = auth_asset.res_path.replace("origin", "m")
    auth_asset.img_small_path = auth_asset.res_path.replace("origin", "s")

    img.save(os.path.join(MEDIA_ROOT, auth_asset.res_path))
    
    origin_size = img.size
    auth_asset.width = origin_size[0]
    auth_asset.height = origin_size[1]
    
    if origin_size[0] > 950 or origin_size[1] > 950:
        img.thumbnail((950,950), Image.ANTIALIAS)
        img.save(os.path.join(MEDIA_ROOT, auth_asset.img_large_path))
    else:
        auth_asset.img_large_path = auth_asset.res_path
    
    if origin_size[0] > 600 or origin_size[1] > 600:
        img.thumbnail((600,600), Image.ANTIALIAS)
        img.save(os.path.join(MEDIA_ROOT, auth_asset.img_medium_path))
    else:
        auth_asset.img_medium_path = auth_asset.img_large_path
    
    im_small = ImageOps.fit(img, (240,190), Image.ANTIALIAS)
    im_small.save(os.path.join(MEDIA_ROOT, auth_asset.img_small_path))
    
    auth_asset.status = 1
    auth_asset.save()
    
    return SuccessResponse({'id':auth_asset.id, 'title':auth_asset.res_title, 
                            'origin':MEDIA_URL + auth_asset.res_path,
                            'large':MEDIA_URL + auth_asset.img_large_path,
                            'medium':MEDIA_URL + auth_asset.img_medium_path,
                            'small':MEDIA_URL + auth_asset.img_small_path})


@login_required
def update_scrawl(request, param):
    """
        新建，更新涂鸦作品
        传入一个param对象参数，对象的成员如下：
        param.id    涂鸦ID，为空时是新建，有值时为更新
        param.title
        param.image_data
    """
    image_data = param.image_data.getvalue()
    if len(image_data) > ALLOWED_IMG_UPLOAD_SIZE:
        return FailResponse(u'文件超过最大充许大小')
    img = Image.open(StringIO(image_data))
    ext = get_img_ext(img)
    if ext == None:
        return FailResponse(u"只充许上传图片文件(%s)" % ';'.join(ALLOWED_IMG_EXTENSION))
    if len(param.title) == 0:
        return FailResponse(u"请输入此涂鸦的标题")

    auth_asset = None
    if param.has_key("id") and param.id:
        scrawl_id = param.id
        try: auth_asset = AuthAsset.objects.get(id=scrawl_id)
        except(AuthAsset.DoesNotExist): return FailResponse(u"请指定要修改的涂鸦的ID")
    else:
        auth_asset = AuthAsset()
        auth_asset.library = request.user.library
        auth_asset.user = request.user
        auth_asset.res_type = 4     #涂鸦
        auth_asset.status = -1
    auth_asset.res_title = param.title
    auth_asset.save()
    
    asset_res_path = "%s/%d" % (get_user_path(request.user, 'scrawl'), auth_asset.id)
    asset_res_abspath = os.path.join(MEDIA_ROOT, asset_res_path)
    if not os.path.lexists(asset_res_abspath):
        os.makedirs(asset_res_abspath)  #不存在，则创建文件夹

    auth_asset.res_path = '%s/origin%s' % (asset_res_path, ext)
    auth_asset.img_large_path = auth_asset.res_path.replace("origin", "l")
    auth_asset.img_medium_path = auth_asset.res_path.replace("origin", "m")
    auth_asset.img_small_path = auth_asset.res_path.replace("origin", "s")

    img.save(os.path.join(MEDIA_ROOT, auth_asset.res_path))
    
    origin_size = img.size
    auth_asset.width = origin_size[0]
    auth_asset.height = origin_size[1]
    
    if origin_size[0] > 950 or origin_size[1] > 950:
        img.thumbnail((950,950), Image.ANTIALIAS)
        img.save(os.path.join(MEDIA_ROOT, auth_asset.img_large_path))
    else:
        auth_asset.img_large_path = auth_asset.res_path
    
    if origin_size[0] > 600 or origin_size[1] > 600:
        img.thumbnail((600,600), Image.ANTIALIAS)
        img.save(os.path.join(MEDIA_ROOT, auth_asset.img_medium_path))
    else:
        auth_asset.img_medium_path = auth_asset.img_large_path
    
    im_small = ImageOps.fit(img, (240,190), Image.ANTIALIAS)
    im_small.save(os.path.join(MEDIA_ROOT, auth_asset.img_small_path))
    
    auth_asset.status = 1
    auth_asset.save()
    
    return SuccessResponse({'id':auth_asset.id, 'title':auth_asset.res_title, 
                            'origin':MEDIA_URL + auth_asset.res_path,
                            'large':MEDIA_URL + auth_asset.img_large_path,
                            'medium':MEDIA_URL + auth_asset.img_medium_path,
                            'small':MEDIA_URL + auth_asset.img_small_path})

@login_required    
def get_scrawl_list(request, param):
    if param.has_key("page_index"): page_index = int(param.page_index)
    else: page_index = 1
    if param.has_key("page_size"): page_size = int(param.page_size)
    else: page_size = 20

    res_type = 4    #涂鸦
    cursor = connections[DB_READ_NAME].cursor()
    where_clause = "user_id=%d and res_type=%d and status=1" % (request.user.id, res_type)
    
    sql = "select count(*) from auth_asset where %s" % where_clause
    cursor.execute(sql)
    row = cursor.fetchone()
    count = 0
    if row: count = row[0]
    page_count = int(ceil(count/float(page_size)))
    
    sql = "select id,album_id,res_title,res_type,res_path,img_large_path,img_medium_path,img_small_path from auth_asset where %s order by create_time desc LIMIT %s, %s" % (where_clause, (page_index-1)*page_size, page_size)
    #print sql
    cursor.execute(sql)
    rows = cursor.fetchall()
    res_lists = []
    for row in rows:
        if not row: continue
        res_dict = {}
        res_dict["id"] = row[0]
        res_dict["album_id"] = row[1]
        res_dict["title"] = row[2]
        res_type = row[3]
        res_dict["res_type"] = personal_res_typename(res_type)
        res_dict["origin"] = MEDIA_URL + row[4]
        res_dict["large"] = MEDIA_URL + row[5]
        res_dict["medium"] = MEDIA_URL + row[6]
        res_dict["small"] = MEDIA_URL + row[7]
        res_lists.append(res_dict)
    return SuccessResponse({"data":res_lists, "page_index": page_index, "page_count": page_count})

@login_required
def delete_scrawl(request, param):
    if param.has_key("id"): scrawl_id = int(param.id)
    else: return FailResponse(u'输入需要删除的涂鸦ID')

    try: auth_asset = AuthAsset.objects.get(id=scrawl_id)
    except(AuthAsset.DoesNotExist): return FailResponse(u"请指定要删除的涂鸦的ID")

    if auth_asset.user_id <> request.user.id: return FailResponse(u'只能删除自己的资源')
    
    if auth_asset.ref_times > 0: return FailResponse(u'资源有(%s)个相关引用，不能删除' % auth_asset.ref_times)
    
    res_type = "scrawl"
    auth_asset_path = "%s/%d" % (get_user_path(request.user, res_type), auth_asset.id)
    #print "auth_asset_path", auth_asset_path
    if os.path.isdir(os.path.join(MEDIA_ROOT, auth_asset_path)):
        __import__('shutil').rmtree(os.path.join(MEDIA_ROOT, auth_asset_path))
    auth_asset.delete()
    return SuccessResponse({"id":scrawl_id})


def get_default_album(user_id):
    #得到某用户的默认相册
    try:
        auth_album = AuthAlbum.objects.get(user_id=user_id, type_id=0, album_title=u"默认相册", status=1)
    except(AuthAlbum.DoesNotExist):
        auth_album = AuthAlbum()
        auth_album.user_id = user_id
        auth_album.type_id = 0  #系统自动生成
        auth_album.album_title = u"默认相册"
        auth_album.status = 1   #可用状态
        auth_album.save()
    except:
        import traceback
        traceback.print_exc()
        auth_album = None
    return auth_album

@login_required
def get_personal_res(request, res_type="all", album_id=0, page_index=1, page_size=20):
    res_type = res_type.lower()
    if res_type not in ('all', 'image','sound','video'):
        return FailResponse(u'资源类型(%s)不正确' % res_type)
    
    share_asset_id = ""
    cursor = connections[DB_READ_NAME].cursor()
    sql = "select auth_asset_id from auth_asset_share where user_id=%d" % request.user.id
    cursor.execute(sql)
    rows = cursor.fetchall()
    for row in rows:
        if not row: continue
        share_asset_id += "," + str(row[0]) if len(share_asset_id)>0 else str(row[0])
    if share_asset_id:
        where_clause = "(user_id=%d or id in (%s)) and status=1" % (request.user.id, share_asset_id)
    else:
        where_clause = "user_id=%d and status=1" % request.user.id
    if res_type == "image":
        if album_id == -1: where_clause += " and res_type=1"  #全部
        elif album_id == 0: #默认相册
            auth_album = get_default_album(request.user.id)
            if auth_album:  #找到默认相册
                where_clause += " and res_type=1 and album_id=%d" % auth_album.id
            else:
                where_clause += " and res_type=1"
        else: where_clause += " and res_type=1 and album_id=%d" % album_id
    elif res_type == "sound": where_clause += " and res_type=2"
    elif res_type == "video":
        #视频需要加上故事大王大赛的视频:11
        where_clause += " and res_type in (3, 11)"
    #print where_clause
    
    sql = "select count(*) from auth_asset where %s" % where_clause
    cursor.execute(sql)
    row = cursor.fetchone()
    count = 0
    if row: count = row[0]
    page_count = int(ceil(count/float(page_size)))
    
    sql = "select id,album_id,res_title,res_type,res_path,img_large_path,img_medium_path,img_small_path,codec_status from auth_asset where %s order by create_time desc LIMIT %s, %s" % (where_clause, (page_index-1)*page_size, page_size)
    #print sql
    cursor.execute(sql)
    rows = cursor.fetchall()
    res_lists = []
    for row in rows:
        if not row: continue
        res_dict = {}
        res_dict["id"] = row[0]
        res_dict["album_id"] = row[1]
        res_dict["album_title"] = personal_album_name(res_dict["album_id"])
        res_dict["title"] = row[2]
        res_type = row[3]
        res_dict["res_type"] = personal_res_typename(res_type)
        #res_dict["origin"] = request.build_absolute_uri(MEDIA_URL + row[4])
        res_dict["origin"] = MEDIA_URL + row[4]
        if res_type == 1:   #only image resource has this property
            #res_dict["large"] = request.build_absolute_uri(MEDIA_URL + row[5])
            #res_dict["medium"] = request.build_absolute_uri(MEDIA_URL + row[6])
            #res_dict["small"] = request.build_absolute_uri(MEDIA_URL + row[7])
            res_dict["large"] = MEDIA_URL + row[5]
            res_dict["medium"] = MEDIA_URL + row[6]
            res_dict["small"] = MEDIA_URL + row[7]
        elif res_type == 2: #音频
            res_dict["codec_status"] = row[8]  #转码状态：0:正在转码，1:转码成功，-1:转码失败
        elif res_type in  (3, 11): #视频截图
            res_dict["codec_status"] = row[8]  #转码状态：0:正在转码，1:转码成功，-1:转码失败
            res_dict["large"] = MEDIA_URL + row[5] if row[5] else ""
            res_dict["small"] = MEDIA_URL + row[7] if row[7] else ""
        res_lists.append(res_dict)
    return SuccessResponse({"data":res_lists, "page_index": page_index, "page_count": page_count})


def personal_res_typename(res_type_id):
    if res_type_id == 1:
        return "image"
    elif res_type_id == 2:
        return "sound"
    elif res_type_id in (3, 11):
        return "video"
    elif res_type_id == 4:
        return "scrawl"
    else: return None


def personal_album_name(album_id):
    if album_id == 0: return u"默认相册"
    elif album_id == -1: return u"全部"
    elif album_id == -2: return u"公共图片"
    
    try:
        auth_album = AuthAlbum.objects.get(id=album_id)
        return auth_album.album_title
    except(AuthAlbum.DoesNotExist): return u"未知相册"


@login_required
def delete_personal_res(request, asset_id):
    """
        删除个人资源，直接删除文件和表，不保存
    """
    try: auth_asset = AuthAsset.objects.get(id=asset_id)
    except(AuthAsset.DoesNotExist): return FailResponse(u'资源ID(%s)不存在' % asset_id)
    
    if auth_asset.user_id <> request.user.id: return FailResponse(u'只能删除自己的资源')
    
    if auth_asset.ref_times > 0: return FailResponse(u'资源有(%s)个相关引用，不能删除' % auth_asset.ref_times)
    if auth_asset.share_times > 0: return FailResponse(u'资源有(%s)个分享，不能删除' % auth_asset.ref_times)
    
    if auth_asset.res_type == 1:
        res_type = "image"
    elif auth_asset.res_type == 2:
        res_type = "sound"
    elif auth_asset.res_type == 3:
        res_type = "video"
    elif auth_asset.res_type == 4:
        res_type = "scrawl"
    if auth_asset.res_type == 1: #图片资源
        auth_asset_path = "%s/%d" % (get_user_path(request.user, res_type, auth_asset.album_id), auth_asset.id)
    else:
        auth_asset_path = "%s/%d" % (get_user_path(request.user, res_type), auth_asset.id)
    print "auth_asset_path", auth_asset_path
    if os.path.isdir(os.path.join(MEDIA_ROOT, auth_asset_path)):
        __import__('shutil').rmtree(os.path.join(MEDIA_ROOT, auth_asset_path))
    auth_asset.delete()
    return SuccessResponse({"id":asset_id})

        
@login_required
def delete_album(request, album_id):
    """
        删除个人相册，只能删除空的相册
    """
    try: auth_album = AuthAlbum.objects.get(id=id)
    except(AuthAsset.DoesNotExist): return FailResponse(u'相册ID(%s)不存在' % id)
    
    if auth_album.user_id <> request.user.id: return FailResponse(u'只能删除自己的相册')
    
    if AuthAsset.objects.filter(album_id=id).count() > 0:
        return FailResponse(u'不能删除非空的相册')
    
    auth_album.delete()
    return SuccessResponse({"id":auth_album.id})
    


# coding=utf8
from PIL import Image, ImageOps
import os

from utils import get_user_path
from WebZone.settings import MEDIA_ROOT
from diy.models import AuthAsset


def edit_auth_asset(origin_path, user, **kwargs):
    '''
    创建用户的个人资源
    editor: kamihati 2015/5/15
    :param origin_path:  原始文件路径
    :param user:  用户
    :param kwargs:  明细参数
    :return:
    '''
    res_title = kwargs['res_title']
    res_type = kwargs['res_type']
    # 如果指定状态则使用否则为可用
    status = kwargs['status'] if kwargs.has_key('status') else 1
    auth_asset = AuthAsset()
    auth_asset.library = user.library
    auth_asset.user = user
    auth_asset.res_title = res_title
    auth_asset.status = status
    auth_asset.save()
    ext = os.path.splitext(origin_path)[1]
    if res_type == "image":
        from diy.models import AuthAlbum
        album_id = kwargs['album_id'] if kwargs.has_key('album_id') else 0
        if album_id == 0:
            from diy.album_handler import get_default_album
            auth_album = get_default_album(user.id)
            if auth_album:
                album_id = auth_album.id
        elif AuthAlbum.objects.filter(id=album_id).count() == 0:
            return u'相册ID:%d不存在' % album_id
        auth_asset.album_id = album_id
        auth_asset.res_type = 1 #图片资源
        asset_res_path = "%s/%d" % (get_user_path(user, res_type, album_id), auth_asset.id)
        asset_res_abspath = os.path.join(MEDIA_ROOT, asset_res_path)
        os.makedirs(asset_res_abspath)  #创建文件夹
        auth_asset.res_path = '%s/origin%s' % (asset_res_path, ext)
        auth_asset.img_large_path = auth_asset.res_path.replace("origin", "l")
        auth_asset.img_medium_path = auth_asset.res_path.replace("origin", "m")
        auth_asset.img_small_path = auth_asset.res_path.replace("origin", "s")
        img = Image.open(origin_path)
        origin_size = img.size
        auth_asset.width = origin_size[0]
        auth_asset.height = origin_size[1]

        if origin_size[0] > 950 or origin_size[1] > 950:
            img.thumbnail((950,950), Image.ANTIALIAS)
            img.save(os.path.join(MEDIA_ROOT, auth_asset.img_large_path))
        else:
            open(os.path.join(MEDIA_ROOT, auth_asset.img_large_path), "wb").write(open(os.path.join(MEDIA_ROOT, auth_asset.res_path), "rb").read())

        if origin_size[0] > 600 or origin_size[1] > 600:
            img.thumbnail((600,600), Image.ANTIALIAS)
            img.save(os.path.join(MEDIA_ROOT, auth_asset.img_medium_path))
        else:
            open(os.path.join(MEDIA_ROOT, auth_asset.img_medium_path), "wb").write(open(os.path.join(MEDIA_ROOT, auth_asset.res_path), "rb").read())

        im_small = ImageOps.fit(img, (240,190), Image.ANTIALIAS)
        im_small.save(os.path.join(MEDIA_ROOT, auth_asset.img_small_path))

        auth_asset.status = 1
        auth_asset.save()
    elif res_type == "sound":
        auth_asset.res_type = 2 #声音资源
        asset_res_path = "%s/%d" % (get_user_path(user, res_type), auth_asset.id)
        asset_res_abspath = os.path.join(MEDIA_ROOT, asset_res_path)
        auth_asset.origin_path = '%s/origin%s' % (asset_res_path, ext)
        auth_asset.res_path = '%s/%d.mp3' % (asset_res_path, auth_asset.id)
        auth_asset.status = 1
        auth_asset.save()
    elif res_type == "video":
        auth_asset.res_type = 3 #视频资源
        asset_res_path = "%s/%d" % (get_user_path(user, res_type), auth_asset.id)
        asset_res_abspath = os.path.join(MEDIA_ROOT, asset_res_path)
        #创建文件夹
        if not os.path.exists(asset_res_abspath):
            os.makedirs(asset_res_abspath)

        auth_asset.origin_path = '%s/origin%s' % (asset_res_path, ext)
        auth_asset.res_path = '%s/%d.flv' % (asset_res_path, auth_asset.id)
        auth_asset.img_large_path = '%s/l.jpg' % asset_res_path #存视频截图的原图
        auth_asset.img_small_path = '%s/s.jpg' % asset_res_path
        auth_asset.status = 1
        auth_asset.save()
    return auth_asset.id
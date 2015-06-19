# Create your views here.
#coding: utf-8
'''
Created on 2014-3-26

@author: Administrator
'''
from django.http import HttpResponse
from WebZone.settings import MEDIA_ROOT, MEDIA_URL
from WebZone.conf import ALLOWED_IMG_EXTENSION, ALLOWED_IMG_UPLOAD_SIZE
from WebZone.conf import ALLOWED_SOUND_EXTENSION, ALLOWED_SOUND_UPLOAD_SIZE
from WebZone.conf import ALLOWED_VIDEO_EXTENSION, ALLOWED_VIDEO_UPLOAD_SIZE
import os
from PIL import Image, ImageOps

from diy.models import AuthAlbum
from diy.models import AuthAsset
# 导入异常输出方法
from utils.decorator import print_trace

from django.core.cache import cache
from widget.models import WidgetGas

from gateway import SuccessResponse, FailResponse
from utils.decorator import login_web_required
from utils import get_user_path


def test(request):
    if cache.get("test", None):
        return HttpResponse("caching time: %s" % cache.get("test"))
    cache.set("test", "hello, world", 60)
    return HttpResponse("cache now")
    a = request.REQUEST["a"]
    return HttpResponse("ok" +a)

def test_done(request):
    if cache.get("test", None):
        cache.delete("test")
        return HttpResponse("cache deleted")
    return HttpResponse("no cache")


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


@print_trace
@login_web_required
def upload_personal_res(request):
    if len(request.FILES) == 0:
        return HttpResponse(FailResponse(u"请选择文件并上传"))
    elif len(request.FILES) > 1:
        return HttpResponse(FailResponse(u"一次只能上传一个文件"))
    res_title = request.REQUEST.get("res_title", None)
    res_type = request.REQUEST.get("res_type", "image").lower()
    album_id = int(request.REQUEST.get("album_id", 0))
    #print res_title, res_type, album_id
    if res_type not in ('image','sound','video'):
        return HttpResponse(FailResponse(u'资源类型(%s)不正确' % res_type))
    mem_file = request.FILES.popitem()[1][0]
    filename, ext = os.path.splitext(mem_file.name)
    if res_title == None: res_title = filename
    auth_asset = AuthAsset()
    auth_asset.library = request.user.library
    auth_asset.user = request.user
    auth_asset.res_title = res_title
    auth_asset.status = -1
    auth_asset.save()
    print 'begin.upload.res_type=', res_type
    if res_type == "image":
        if album_id == 0:
            auth_album = get_default_album(request.user.id)
            if auth_album:
                album_id = auth_album.id
            else:
                return HttpResponse(FailResponse(u'系统异常，请联系管理员'))
        elif AuthAlbum.objects.filter(id=album_id).count() == 0:
            return HttpResponse(FailResponse(u'相册ID:%d不存在' % album_id))
        auth_asset.album_id = album_id
        auth_asset.res_type = 1 #图片资源
        if ext.lower() not in ALLOWED_IMG_EXTENSION:
            return HttpResponse(FailResponse(u"只充许上传图片文件(%s)" % ';'.join(ALLOWED_IMG_EXTENSION)))
        if mem_file.size > ALLOWED_IMG_UPLOAD_SIZE:
            return HttpResponse(FailResponse(u'文件超过最大充许大小'))
        asset_res_path = "%s/%d" % (get_user_path(request.user, res_type, album_id), auth_asset.id)
        asset_res_abspath = os.path.join(MEDIA_ROOT, asset_res_path)
        os.makedirs(asset_res_abspath)  #创建文件夹
        auth_asset.res_path = '%s/origin%s' % (asset_res_path, ext)
        auth_asset.img_large_path = auth_asset.res_path.replace("origin", "l")
        auth_asset.img_medium_path = auth_asset.res_path.replace("origin", "m")
        auth_asset.img_small_path = auth_asset.res_path.replace("origin", "s")
        f = open(os.path.join(MEDIA_ROOT, auth_asset.res_path), "wb")
        for chunk in mem_file.chunks():
            f.write(chunk)
        f.close()

        img = Image.open(os.path.join(MEDIA_ROOT, auth_asset.res_path))
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
        print 'image .upload  successs..'
        return HttpResponse(SuccessResponse({'id':auth_asset.id, 'title':auth_asset.res_title, 
                                'large':MEDIA_URL + auth_asset.img_large_path,
                                'medium':MEDIA_URL + auth_asset.img_medium_path,
                                'small':MEDIA_URL + auth_asset.img_small_path}))
    elif res_type == "sound":
        auth_asset.res_type = 2 #声音资源
        if ext.lower() not in ALLOWED_SOUND_EXTENSION:
            return HttpResponse(FailResponse(u"只充许上传音频文件(%s)" % ';'.join(ALLOWED_SOUND_EXTENSION)))
        if mem_file.size > ALLOWED_SOUND_UPLOAD_SIZE:
            return HttpResponse(FailResponse(u'文件超过最大充许大小'))

        asset_res_path = "%s/%d" % (get_user_path(request.user, res_type), auth_asset.id)
        asset_res_abspath = os.path.join(MEDIA_ROOT, asset_res_path)
        #创建文件夹
        if not os.path.exists(asset_res_abspath):
            os.makedirs(asset_res_abspath)
        
        auth_asset.origin_path = '%s/origin%s' % (asset_res_path, ext)
        auth_asset.res_path = '%s/%d.mp3' % (asset_res_path, auth_asset.id)
        
        f = open(os.path.join(MEDIA_ROOT, auth_asset.origin_path), "wb")
        # mark: kamihati 2015/4/7  由于本地没有音视频编码服务所以暂时以原文件存储。上线后取消
        f_res = open(os.path.join(MEDIA_ROOT, auth_asset.res_path), "wb")
        for chunk in mem_file.chunks():
            f.write(chunk)
            f_res.write(chunk)
        f.close()
        f_res.close()
        auth_asset.status = 1
        auth_asset.save()
        print 'sound .upload  successs..'
        return HttpResponse(SuccessResponse({'id':auth_asset.id, 'title':auth_asset.res_title, 'url':MEDIA_URL + auth_asset.res_path}))
    elif res_type == "video":
        auth_asset.res_type = 3 #视频资源
        if ext.lower() not in ALLOWED_VIDEO_EXTENSION:
            return HttpResponse(FailResponse(u"只充许上传视频文件(%s)" % ';'.join(ALLOWED_VIDEO_EXTENSION)))
        if mem_file.size > ALLOWED_VIDEO_UPLOAD_SIZE:
            return HttpResponse(FailResponse(u'文件超过最大充许大小'))
        
        asset_res_path = "%s/%d" % (get_user_path(request.user, res_type), auth_asset.id)
        asset_res_abspath = os.path.join(MEDIA_ROOT, asset_res_path)
        #创建文件夹
        if not os.path.exists(asset_res_abspath):
            os.makedirs(asset_res_abspath)
        
        auth_asset.origin_path = '%s/origin%s' % (asset_res_path, ext)
        auth_asset.res_path = '%s/%d.flv' % (asset_res_path, auth_asset.id)
        auth_asset.img_large_path = '%s/l.jpg' % asset_res_path #存视频截图的原图
        auth_asset.img_small_path = '%s/s.jpg' % asset_res_path
        f = open(os.path.join(MEDIA_ROOT, auth_asset.origin_path), "wb")
        for chunk in mem_file.chunks():
            f.write(chunk)
        f.close()
        
        auth_asset.status = 1
        auth_asset.save()
        print 'video .upload  successs..'
        return HttpResponse(SuccessResponse({'id':auth_asset.id, 'title':auth_asset.res_title, 'url':MEDIA_URL + auth_asset.res_path}))
    else:
        return HttpResponse(FailResponse(u'参数错误'))


from api import txt2img            
def gas_station(request):
    from random import choice
    from WebZone.settings import FONT_ROOT
    from WebZone.conf import fonts
    from StringIO import StringIO
    font_id = 7
    font_size = 22
    width = 190
    height = 480
    font_color = (201, 67, 0)
    
    cache_gas_dict_key = "api.gas_station.gas_dict"
    gas_dict = cache.get(cache_gas_dict_key, {})
    if not gas_dict:
        print "not found cache gas_dict"
        for widget_gas in WidgetGas.objects.filter(status=1):
            gas_dict[widget_gas.id] = widget_gas.content
        cache.set(cache_gas_dict_key, gas_dict)

    gas_id = int(request.REQUEST.get('id', 0))
    if gas_id not in gas_dict.keys():
        gas_id = None
    if not gas_id:
        gas_id = choice(gas_dict.keys())
        
    cache_gas_img_key = "api.gas_station.gas_img:%d" % gas_id
    buf_img = cache.get(cache_gas_img_key, None)
    if not buf_img:
        print "not found cache img", gas_id
        font_file = os.path.join(FONT_ROOT, fonts[font_id]["font"])
        font_file = font_file.encode('utf-8')
        #print font_file, type(font_file)
        if not os.path.isfile(font_file):
            return HttpResponse(u'字体文件不存在')
        
        content = gas_dict[gas_id]
        wiget_gas = WidgetGas.objects.get(id=gas_id)
        wiget_gas.view_times += 1
        wiget_gas.save()
        print 'gas_id=', gas_id
        # print content
        # print content.split('\r')
        img = txt2img(font_file, content, font_size, font_color, width, height, "center")
        #img.save("c:\\font1.png")
        buf = StringIO()
        img.save(buf, 'png')
        del img
        buf_img = buf.getvalue()
        cache.set(cache_gas_img_key, buf_img)
    return HttpResponse(buf_img, mimetype="image/png")


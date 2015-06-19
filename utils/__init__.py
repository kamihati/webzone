#coding: utf-8
import os
from WebZone.conf import THUMBNAIL_SIZE

from library.models import Library
from django.core.cache import cache


def get_lib_path(library, res_type=1):
    """
        图书馆资源路径前缀规则：lib/图书馆id/assets/资源类型, lib/assets/资源类型
        资源类型有：1,2,3,4,5,6    ((1,u"背景"),(2,u"装饰"),(3,u"画框"),(4,u"模板"),(5,u"声音"),(6,u"视频"))
        作品尺寸图片：21
    """
    if library:
        return "lib/%s/assets/%s" % (library.id, res_type)
    else:
        return "assets/%s" % res_type
    
def get_user_path(user, res_type="image", sub_id=0):
    """
        个人资源路径前缀规则：user/图书馆id/用户注册年/用户id/资源类型, user/用户注册年/用户id/资源类型
        资源类型有：image,sound,video,opus
    """
    if user.library:
        if res_type in ("image", "opus"):   #相册有相册ＩＤ，　作品有作品ＩＤ
            return 'user/%d/%s/%d/%s/%d' % (user.library.id, user.date_joined.strftime("%Y"), user.id, res_type, sub_id)
        elif res_type == "":
            return 'user/%d/%s/%d' % (user.library.id, user.date_joined.strftime("%Y"), user.id)
        else:
            return 'user/%d/%s/%d/%s' % (user.library.id, user.date_joined.strftime("%Y"), user.id, res_type)
    else:
        if res_type in ("image", "opus"):   #相册有相册ＩＤ，　作品有作品ＩＤ
            return 'user/%s/%d/%s/%d' % (user.date_joined.strftime("%Y"), user.id, res_type, sub_id)
        elif res_type == "":
            return 'user/%s/%d' % (user.date_joined.strftime("%Y"), user.id)
        else:
            return 'user/%s/%d/%s' % (user.date_joined.strftime("%Y"), user.id, res_type)

def get_ip(request):
    ip_list = ""
    if request.META.has_key('X_REAL_IP'):
        ip_list =  request.META['X_REAL_IP']
    elif request.META.has_key('HTTP_X_FORWARD_FOR'):
        ip_list =  request.META['HTTP_X_FORWARD_FOR']
    elif request.META.has_key('REMOTE_ADDR'):
        ip_list =  request.META['REMOTE_ADDR']
    else:
        ip_list = "127.0.0.1"
    if ip_list.find(',') > 0:
        return ip_list.split(',')[0]
    return ip_list


def get_new_filename(path, full_filename):
    """
    return a valid filename, increase by 1
    """
    index = 1
    new_filename = full_filename
    filename, extension = os.path.splitext(full_filename)
    new_filepath = os.path.join(path, new_filename)
    #print "get_new_filename", new_filepath, os.path.isfile(new_filepath)
    while os.path.isfile(new_filepath):
        new_filename = '%s(%d)%s' % (filename, index, extension)
        new_filepath = os.path.join(path, new_filename)
        index += 1
    return new_filename


def get_tile_image_name(image_name, pyramid="s", extension=None):
    """
    return three kind of image file name: small:s, medium:m, large:l, origin
    """
    if image_name == None or image_name == "":
        return ""
    if pyramid not in ('s','m','l'):
        return None
    if extension == None:
        extension = image_name[image_name.rfind('.'):]
    prefix_name = image_name[:image_name.rfind('.')]
    return "%s_%s%s" % (prefix_name, pyramid, extension)


def get_img_ext(image):
    """
    get the right image extension, not by filename
    return None if not a valid image format
    """
    if image.format == "JPEG": return '.jpg'
    elif image.format == "PNG": return '.png'
    elif image.format == "GIF": return '.gif'
    elif image.format == "BMP": return '.bmp'
    else:
        print "get_img_ext:error:unknow imgage type", image.format
        return None
    

def get_age(birthday):
    if birthday == None or birthday == "":
        return 0
    from datetime import date
    
    #return u"%d岁%d月%d天" % (10, 2, 3)
    #from math import ceil
    #return ceil((date.today() - birthday).days/365.0)
    return date.today().year - birthday.year

    
def get_library(library_id):
    """
    return a tuple
    """
    try: library_id = int(library_id)
    except: return 0, "", None
    
    try:
        library = Library.objects.get(id=library_id)
        return library.id, library.lib_name, library
    except(Library.DoesNotExist): return 0, "", None

def get_lib_name(lib_id):
    """
    return library name by id
    """
    cache_key = "utils.get_lib_name"
    lib_dict = cache.get(cache_key, {})
    if not lib_dict:
        for lib in Library.objects.all():
            lib_dict[lib.id] = lib.lib_name
        cache.set(cache_key, lib_dict)
    if lib_dict.has_key(int(lib_id)):
        return lib_dict[int(lib_id)]
    else:
        return u"未找到馆名"


def get_zone_asset(zone_asset_id):
    """
    return a tuple, judge the id is validate
    """
    try: zone_asset_id = int(zone_asset_id)
    except: return 0, "", None
    
    from diy.models import ZoneAsset
    try:
        zone_asset = ZoneAsset.objects.get(id=zone_asset_id)
        return zone_asset.id, zone_asset.res_title, zone_asset
    except(ZoneAsset.DoesNotExist): return 0, "", None
    

def fmt_str(meta_data):
    """
    convert None or other empty data to ""
    """
    if meta_data == None or meta_data == "":
        return ""
    return meta_data

def rmtree2(dir):
    for root, dirs, files in os.walk(dir, topdown=False):
        print root, dirs, files
        for name in files:
            print name
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(dir)
    
    
def idlist2dict(id_list):
    """
    id_list: "1,2,3,4,5,6,1,2,1,3,1"
    output: {1:4,2:2:3:2,4:1,5:1,6:1}
    """
    id_list = id_list.split(',')
    id_dict = {}
    for id in id_list:
        if not id: continue
        id = int(id)
        if id_dict.has_key(id): id_dict[id] += 1
        else: id_dict[id] = 1
    return id_dict
    

def get_small_size(width, height):
    """
        需求：生成240,190的小图时，不要裁剪，需要计算下缩略图大小（用函数Image.thumbnail）
    """
    #print width, height
    if float(height)/width > float(THUMBNAIL_SIZE[1])/THUMBNAIL_SIZE[0]:
        from math import ceil
        w = int(ceil(float(width)*THUMBNAIL_SIZE[1]/height))
        #print w
        return (w, THUMBNAIL_SIZE[1])
    else:
        return (THUMBNAIL_SIZE[0], THUMBNAIL_SIZE[0])
    

import json
from django.http import HttpResponse
def json_response(obj):
    '''
    像客户端发送json字符串流
    :param 数据辞典等:  对象
    :return:
    '''
    return HttpResponse(json.dumps(obj))


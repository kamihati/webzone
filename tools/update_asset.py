#coding: utf-8
'''
Created on 2014-4-11

@author: Administrator
'''

import sys;
sys.path.insert(0, '..')
#sys.path.append('/www/website/')

import os
#使用django的数据库
os.environ['DJANGO_SETTINGS_MODULE'] = 'WebZone.settings'
from diy.models import AuthAsset
from diy.models import ZoneAsset
from PIL import Image, ImageOps
from WebZone.settings import MEDIA_ROOT


class resize_image():
    def __init__(self):
        self.large_size = (950, 950)
        self.medium_size = (600, 600)
        self.small_size = (240, 190)
        self.rename_frame()
        
    def resize_personal(self):
        for auth_asset in AuthAsset.objects.all():
            res_path_abspath = os.path.join(MEDIA_ROOT, auth_asset.res_path)
            if os.path.isfile(res_path_abspath):
                img_large_abspath = os.path.join(MEDIA_ROOT, auth_asset.img_large_path)
                img_medium_abspath = os.path.join(MEDIA_ROOT, auth_asset.img_medium_path)
                img_small_abspath = os.path.join(MEDIA_ROOT, auth_asset.img_small_path)
                print img_small_abspath
                
                img = Image.open(res_path_abspath)
                origin_size = img.size
                if origin_size[0] > self.large_size[0] or origin_size[1] > self.large_size[1]:
                    img.thumbnail(self.large_size, Image.ANTIALIAS)
                    img.save(img_large_abspath)
                    origin_size = img.size
                
                if origin_size[0] > self.medium_size[0] or origin_size[1] > self.medium_size[1]:
                    img.thumbnail(self.medium_size, Image.ANTIALIAS)
                    img.save(img_medium_abspath)
                
                im_small = ImageOps.fit(img, self.small_size, Image.ANTIALIAS)
                im_small.save(img_small_abspath)
    
    def resize_zone(self):
        index = 0
        for zone_asset in ZoneAsset.objects.all():
            index += 1
            print "begin", index, zone_asset.id, zone_asset.res_path
            prefix = zone_asset.res_path[:zone_asset.res_path.rfind('/')]
            file_name = zone_asset.res_path[zone_asset.res_path.rfind('/')+1:]
            filename, ext = os.path.splitext(file_name)
            res_path_abspath = os.path.join(MEDIA_ROOT, zone_asset.res_path)
            if os.path.isfile(res_path_abspath):
                if filename.find('origin') == -1:
                    zone_asset.res_path = "%s/origin%s" % (prefix, ext)
                    open(os.path.join(MEDIA_ROOT, zone_asset.res_path), "wb").write(open(os.path.join(MEDIA_ROOT, res_path_abspath), "rb").read())
                    #os.remove(os.path.join(MEDIA_ROOT, res_path_abspath))
                if zone_asset.res_type in (1,2,3,4):
                    if ext.lower() in (".swf"): #都可以上传swf文件
                        zone_asset.img_large_path = zone_asset.res_path
                        zone_asset.img_medium_path = zone_asset.res_path
                        zone_asset.img_small_path = zone_asset.res_path
                    else:
                        zone_asset.img_large_path = zone_asset.res_path.replace("origin", "l")
                        zone_asset.img_medium_path = zone_asset.res_path.replace("origin", "m")
                        zone_asset.img_small_path = zone_asset.res_path.replace("origin", "s")
                
                if zone_asset.res_type in (1,2,3,4) and ext.lower() not in (".swf"): #三个等级图片缩放
                    img = Image.open(os.path.join(MEDIA_ROOT, zone_asset.res_path))
                    zone_asset.width = img.size[0]
                    zone_asset.height = img.size[1]
    
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
    
                    im_small = ImageOps.fit(img, (240,190), Image.ANTIALIAS)
                    im_small.save(os.path.join(MEDIA_ROOT, zone_asset.img_small_path))
                zone_asset.save()
                print "end", index, zone_asset.id, zone_asset.res_path
    
    def rename_frame(self):
        index = 0
        for zone_asset in ZoneAsset.objects.filter(res_type=3, id__lte=294).all():
            index += 1
            print "begin", index, zone_asset.id, zone_asset.mask_path
            prefix = zone_asset.res_path[:zone_asset.mask_path.rfind('/')]
            file_name = zone_asset.res_path[zone_asset.mask_path.rfind('/')+1:]
            filename, ext = os.path.splitext(file_name)
            res_path_abspath = os.path.join(MEDIA_ROOT, zone_asset.mask_path)
            if os.path.isfile(res_path_abspath):
                if filename.find('mask') == -1:
                    zone_asset.mask_path = "%s/mask%s" % (prefix, ext)
                    open(os.path.join(MEDIA_ROOT, zone_asset.mask_path), "wb").write(open(os.path.join(MEDIA_ROOT, res_path_abspath), "rb").read())
                    zone_asset.save()
                print "end", index, zone_asset.id, zone_asset.mask_path
if __name__ == "__main__":
    resize_image()
    
    
    
    
    
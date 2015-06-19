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
from PIL import Image, ImageOps
from WebZone.settings import MEDIA_ROOT


class resize_personal_image():
    def __init__(self):
        self.large_size = (1024, 1024)
        self.medium_size = (600, 600)
        self.small_size = (220, 165)
        self.resize()
    
    def resize(self):
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

if __name__ == "__main__":
    resize_personal_image()
    
    
    
    
    
#coding: utf-8
'''
Created on 2014-7-9

@author: Administrator
'''

import sys;
sys.path.insert(0, '..')
#sys.path.append('/www/website/')

import os
#使用django的数据库
os.environ['DJANGO_SETTINGS_MODULE'] = 'WebZone.settings'
from diy.models import AuthAsset, ZoneAsset, ZoneAssetTemplate, AuthOpus, AuthOpusPage
from PIL import Image
from WebZone.settings import MEDIA_ROOT
from utils import get_small_size


class ProduceThumbnail():
    def __init__(self):
        from WebZone.conf import THUMBNAIL_SIZE
        self.small_size = THUMBNAIL_SIZE
        #self.auth_asset()
        #self.zone_asset()
        self.zone_asset_template()
        #self.auth_opus_page()
    
    def auth_asset(self):
        for auth_asset in AuthAsset.objects.filter(res_type=1): #只处理个人相册的图片，故事大王大赛
            res_path_abspath = os.path.join(MEDIA_ROOT, auth_asset.res_path)
            if os.path.isfile(res_path_abspath):
                img_small_abspath = os.path.join(MEDIA_ROOT, auth_asset.img_small_path)
                print img_small_abspath
                
                img = Image.open(res_path_abspath)
                img.thumbnail(get_small_size(img.size[0], img.size[1]), Image.ANTIALIAS)
                img.save(img_small_abspath)
    
    def zone_asset(self):
        for zone_asset in ZoneAsset.objects.filter(res_type__in=(1, 2, 4)): #公共作品的:(1,u"背景"),(2,u"装饰"),(4,u"模板") 模板缩略图
            res_path_abspath = os.path.join(MEDIA_ROOT, zone_asset.res_path)
            ext = os.path.splitext(res_path_abspath)[1].lower()
            if ext not in ('.png', '.jpg', '.gif', '.bmp'):
                print zone_asset.id, ext
            if os.path.isfile(res_path_abspath):
                img_small_abspath = os.path.join(MEDIA_ROOT, zone_asset.img_small_path)
                print img_small_abspath
                
                img = Image.open(res_path_abspath)
                img.thumbnail(get_small_size(img.size[0], img.size[1]), Image.ANTIALIAS)
                img.save(img_small_abspath)
    
    def zone_asset_template(self):
        for zone_asset_template in ZoneAssetTemplate.objects.all():
            res_path_abspath = os.path.join(MEDIA_ROOT, zone_asset_template.img_path)
            if os.path.isfile(res_path_abspath):
                img_small_abspath = os.path.join(MEDIA_ROOT, zone_asset_template.img_small_path)
                print img_small_abspath
                
                img = Image.open(res_path_abspath)
                img.thumbnail(get_small_size(img.size[0], img.size[1]), Image.ANTIALIAS)
                img.save(img_small_abspath)
                
                
    def auth_opus_page(self):
        for auth_opus_page in AuthOpusPage.objects.all():
            res_path_abspath = os.path.join(MEDIA_ROOT, auth_opus_page.img_path)
            if os.path.isfile(res_path_abspath):
                img_small_abspath = os.path.join(MEDIA_ROOT, auth_opus_page.img_small_path)
                print img_small_abspath
                
                img = Image.open(res_path_abspath)
                img.thumbnail(get_small_size(img.size[0], img.size[1]), Image.ANTIALIAS)
                img.save(img_small_abspath)

if __name__ == "__main__":
    ProduceThumbnail()
    
    
    
    
    
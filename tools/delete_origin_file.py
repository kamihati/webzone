#coding: utf-8
'''
Created on 2014-6-10

@author: Administrator
'''
import sys
#sys.path.insert(0, '..')
sys.path.append('/www/wwwroot/')

import os
#使用django的数据库
os.environ['DJANGO_SETTINGS_MODULE'] = 'WebZone.settings'
from WebZone.settings import MEDIA_ROOT
from diy.models import AuthAsset
from diy.models import ZoneAsset



if __name__ == "__main__":
    """
                把转码完，确认无误后的源文件删除掉
    """
    asset_list = AuthAsset.objects.filter(res_type__in=(2,3,11), codec_status=1, origin_del=0)
    for asset in asset_list:
        origin_path = os.path.join(MEDIA_ROOT, asset.origin_path)
        if os.path.isfile(os.path.join(MEDIA_ROOT, origin_path)):
            os.remove(os.path.join(MEDIA_ROOT, origin_path))
            asset.origin_del = 1
            asset.save()
            print os.path.join(MEDIA_ROOT, origin_path)
    asset_list = ZoneAsset.objects.filter(res_type__in=(5,6), codec_status=1, origin_del=0)
    for asset in asset_list:
        origin_path = os.path.join(MEDIA_ROOT, asset.origin_path)
        if os.path.isfile(os.path.join(MEDIA_ROOT, origin_path)):
            os.remove(os.path.join(MEDIA_ROOT, origin_path))
            asset.origin_del = 1
            asset.save()
            os.path.join(MEDIA_ROOT, origin_path)











#coding: utf-8
'''
Created on 2014-6-10

@author: Administrator
'''
from converter import Converter
#from math import ceil, floor
import traceback
from random import choice
import sys
from datetime import datetime
#sys.path.insert(0, '..')
sys.path.append('/www/webzone/')

import os
#使用django的数据库
import WebZone.settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'WebZone.settings'
#from Webzone.settings import MEDIA_ROOT
MEDIA_ROOT = "/www/webzone/media"
from diy.models import AuthAsset
from diy.models import ZoneAsset

from django.db import connection
import shutil
from utils import get_small_size
#from WebZone.conf import THUMBNAIL_SIZE
from PIL import Image

from twisted.internet import reactor

time_out = 60   #单位：秒


class codec_asset():
    def __init__(self):
        self.converter = Converter()
        #self.converter = Converter("D:\\work\\WebZone\\ffmpeg\\ffmpeg.exe", "D:\\work\\WebZone\\ffmpeg\\ffprobe.exe")
        self.run()
        #self.thumb_story_video()
        
    def thumbnail_size(self, width, height):
        size = get_small_size(width, height)
        return "%dx%d" % (size[0], size[1])
        
    def run(self):
        print "run begin:%s" % datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.auth_asset_audio()
    
    def auth_asset_audio(self):
        asset_list = AuthAsset.objects.filter(res_type=2, codec_status=0, status__gte=0)
        for asset in asset_list:
            origin_path = os.path.join(MEDIA_ROOT, asset.origin_path)
            out_path = os.path.join(MEDIA_ROOT, asset.res_path)
            print origin_path, out_path
            info = self.converter.probe(origin_path)
            print info, type(info), dir(info)
            asset.duration = info.format.duration
            try:
                conv = self.converter.convert(origin_path,out_path, {'format':'mp3','audio':{'codec':'mp3','samplerate':11025,'channels':1,'bitrate':32}})
                for timecode in conv:
                    print "Converting (%f) ...\r" % timecode
            except:
                print "auth_asset_audio except convert"
                traceback.print_exc()
                asset.codec_status = -1
                asset.save()
                continue
            asset.codec_status = 1
            asset.save()
        self.auth_asset_video()
        
    
    def auth_asset_video(self):
        asset_list = AuthAsset.objects.filter(res_type__in=(3,11), codec_status=0, status__gte=0)
        for asset in asset_list:
            origin_path = os.path.join(MEDIA_ROOT, asset.origin_path)
            out_path = os.path.join(MEDIA_ROOT, asset.res_path)
            origin_img_path = os.path.join(MEDIA_ROOT, asset.img_large_path)
            thumbnail_path = os.path.join(MEDIA_ROOT, asset.img_small_path)
            print origin_path, out_path, thumbnail_path
            try:
                info = self.converter.probe(origin_path)
                print info.video.video_width, info.video.video_height, info.video.video_fps, info.video.bitrate, info.format.duration
            except:
                print "except thumbnail"
                traceback.print_exc()
                asset.codec_status = -1
                asset.save()
                continue

            asset.video_width = info.video.video_width
            asset.video_height = info.video.video_height
            asset.duration = info.format.duration
            if asset.video_width > 600:
                asset.width, asset.height = self.resize(asset.video_width, asset.video_height)
            else:
                asset.width, asset.height = asset.video_width, asset.video_height
            print asset.width, asset.height
            try:
                conv = self.converter.convert(origin_path,out_path, {'format':'flv',
                                                        'audio':{'codec':'mp3','samplerate':11025,'channels':1,'bitrate':32},
                                                        'video':{'codec':'h264','width':asset.width,'height':asset.height,'qscale ':1}
                                                        })
                                                        #}, timeout=None)
                for timecode in conv:
                    print "Converting (%f) ...\r" % timecode
            except:
                print "except convert"
                traceback.print_exc()
                asset.codec_status = -1
                asset.save()
                continue
                
            thumb_time = choice(xrange(int(asset.duration*0.3), int(asset.duration*0.67)))
            print "thumb_time", thumb_time
            try:
                self.converter.thumbnail(origin_path, thumb_time, origin_img_path, "%dx%d" % (asset.video_width, asset.video_height))
                img = Image.open(origin_img_path)
                img.thumbnail(get_small_size(asset.video_width, asset.video_height), Image.ANTIALIAS)
                img.save(thumbnail_path)
            except:
                print "except thumbnail"
                traceback.print_exc()
                asset.codec_status = -1
                asset.save()
                continue
            asset.codec_status = 1
            asset.save()
            
            if asset.res_type == 11: #故事大王
                sql = "select auth_opus_id, img_small_path from auth_opus_page where page_index=1 and auth_opus_id=(select opus_id from widget_story_opus where auth_asset_id=%d)" % asset.id
                cur = connection.cursor()
                cur.execute(sql)
                row = cur.fetchone()
                if row and row[0]:
                    auth_opus_id  = row[0]
                    opus_page_path = os.path.join(MEDIA_ROOT, row[1])
                    print opus_page_path
                    shutil.copyfile(thumbnail_path, opus_page_path)
                    sql = "update auth_opus set status=11 where id=%d" % auth_opus_id   #故事大王作品状态
                    print sql
                    cur.execute(sql)
                
        self.zone_asset_audio()
        
   
    def thumb_story_video(self):
        asset_list = AuthAsset.objects.filter(res_type=11, codec_status=0, status__gte=0)
        for asset in asset_list:
            origin_path = os.path.join(MEDIA_ROOT, asset.origin_path)
            out_path = os.path.join(MEDIA_ROOT, asset.res_path)
            origin_img_path = os.path.join(MEDIA_ROOT, asset.img_large_path)
            thumbnail_path = os.path.join(MEDIA_ROOT, asset.img_small_path)
            print origin_path, out_path, thumbnail_path
            info = self.converter.probe(origin_path)
            print info.video.video_width, info.video.video_height, info.video.video_fps, info.video.bitrate, info.format.duration
            asset.video_width = info.video.video_width
            asset.video_height = info.video.video_height
            asset.duration = info.format.duration
            if asset.video_width > 600:
                asset.width, asset.height = self.resize(asset.video_width, asset.video_height)
            else:
                asset.width, asset.height = asset.video_width, asset.video_height
            print asset.video_width, asset.video_height, asset.width, asset.height

            thumb_time = choice(xrange(int(asset.duration*0.3), int(asset.duration*0.67)))
            print "thumb_time", thumb_time
            try:
                self.converter.thumbnail(origin_path, thumb_time, origin_img_path, "%dx%d" % (asset.video_width, asset.video_height))
                img = Image.open(origin_img_path)
                img.thumbnail(get_small_size(asset.width, asset.height), Image.ANTIALIAS)
                img.save(thumbnail_path)
            except:
                print "except thumbnail"
                traceback.print_exc()
                asset.codec_status = -1
                asset.save()
                continue
            asset.codec_status = 1
            asset.save()
            
            if asset.res_type == 11: #故事大王
                sql = "select auth_opus_id, img_small_path from auth_opus_page where page_index=1 and auth_opus_id=(select opus_id from widget_story_opus where auth_asset_id=%d)" % asset.id
                cur = connection.cursor()
                cur.execute(sql)
                row = cur.fetchone()
                if row and row[0]:
                    auth_opus_id  = row[0]
                    opus_page_path = os.path.join(MEDIA_ROOT, row[1])
                    print opus_page_path
                    shutil.copyfile(thumbnail_path, opus_page_path)
                    sql = "update auth_opus set status=11 where id=%d" % auth_opus_id   #故事大王作品状态
                    print sql
                    cur.execute(sql)
 
    def zone_asset_audio(self):
        asset_list = ZoneAsset.objects.filter(res_type=5, codec_status=0, status__gte=0)
        for asset in asset_list:
            origin_path = os.path.join(MEDIA_ROOT, asset.origin_path)
            out_path = os.path.join(MEDIA_ROOT, asset.res_path)
            print origin_path, out_path
            info = self.converter.probe(origin_path)
            asset.duration = info.format.duration
            try:
                conv = self.converter.convert(origin_path,out_path, {'format':'mp3','audio':{'codec':'mp3','samplerate':11025,'channels':1,'bitrate':32}})
                for timecode in conv:
                    print "Converting (%f) ...\r" % timecode
            except:
                print "zone_asset_audio except convert"
                traceback.print_exc()
                asset.codec_status = -1
                asset.save()
                continue
            asset.codec_status = 1
            asset.save()
        self.zone_asset_video()
        
    
    def zone_asset_video(self):
        asset_list = ZoneAsset.objects.filter(res_type=6, codec_status=0, status__gte=0)
        for asset in asset_list:
            origin_path = os.path.join(MEDIA_ROOT, asset.origin_path)
            out_path = os.path.join(MEDIA_ROOT, asset.res_path)
            origin_img_path = os.path.join(MEDIA_ROOT, asset.img_large_path)
            thumbnail_path = os.path.join(MEDIA_ROOT, asset.img_small_path)
            print origin_path, out_path, thumbnail_path
            info = self.converter.probe(origin_path)
            print info.video.video_width, info.video.video_height, info.video.video_fps, info.video.bitrate, info.format.duration
            asset.video_width = info.video.video_width
            asset.video_height = info.video.video_height
            asset.duration = info.format.duration
            if asset.video_width > 600:
                asset.width, asset.height = self.resize(asset.video_width, asset.video_height)
            else:
                asset.width, asset.height = asset.video_width, asset.video_height
            print asset.width, asset.height
            try:
                conv = self.converter.convert(origin_path,out_path, {'format':'flv',
                                                        'audio':{'codec':'mp3','samplerate':11025,'channels':1,'bitrate':32},
                                                        'video':{'codec':'h264','width':asset.width,'height':asset.height,'qscale ':1}
                                                        })
                for timecode in conv:
                    print "Converting (%f) ...\r" % timecode
            except:
                print "zone_asset_video except convert"
                traceback.print_exc()
                asset.codec_status = -1
                asset.save()
                continue
                
            thumb_time = choice(xrange(int(asset.duration*0.3), int(asset.duration*0.67)))
            print "thumb_time", thumb_time
            try:
                #self.converter.thumbnail(origin_path, thumb_time, thumbnail_path, self.thumbnail_size(asset.video_width, asset.video_height))
                self.converter.thumbnail(origin_path, thumb_time, origin_img_path, "%dx%d" % (asset.video_width, asset.video_height))
                img = Image.open(origin_img_path)
                img.thumbnail(get_small_size(asset.video_width, asset.video_height), Image.ANTIALIAS)
                img.save(thumbnail_path)
            except:
                print "except thumbnail"
                traceback.print_exc()
                asset.codec_status = -1
                asset.save()
                continue
            asset.codec_status = 1
            asset.save()
        reactor.callLater(time_out, self.run)
        
        
    def resize(self, width, height):
        aspect_ratio = float(height)/width
        aspect_600340 = 340.0/600   #1088:1920    340:600    17:30
        aspect_540300 = 300.0/540   #400:720    300:540   5:9
        
        if aspect_ratio == 0.5625:  #9:16
            return 640, 360
        elif aspect_ratio == 0.8:  #4:5    720 576
            return 600, 480
        elif aspect_ratio == 0.75:  #3:4
            return 600, 450
        elif aspect_ratio == 0.625:  #10:16
            return 600, 375
        elif aspect_ratio == 0.5625:  #9:16
            return 640, 360
        elif aspect_ratio == aspect_600340: #1088:1920    340:600    17:30
            return 600, 340
        elif aspect_ratio == aspect_540300: #400:720    300:540   5:9
            return 540, 300
        else:
            return 600, int(600*aspect_ratio)
    
    
    def delete_origin_file(self):
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
        asset_list = ZoneAsset.objects.filter(res_type__in=(5,6), codec_status=1, origin_del=0)
        for asset in asset_list:
            origin_path = os.path.join(MEDIA_ROOT, asset.origin_path)
            if os.path.isfile(os.path.join(MEDIA_ROOT, origin_path)):
                os.remove(os.path.join(MEDIA_ROOT, origin_path))
                asset.origin_del = 1
                asset.save()
        

if __name__ == "__main__":
    codec_asset()
    reactor.run()











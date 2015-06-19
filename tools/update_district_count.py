#coding: utf-8
'''
Created on 2014-8-8

@author: Administrator
'''
import traceback
from random import choice
import sys
from datetime import datetime
#sys.path.insert(0, '..')
sys.path.append('/www/wwwroot/')

import os
#使用django的数据库
os.environ['DJANGO_SETTINGS_MODULE'] = 'WebZone.settings'
from WebZone.settings import MEDIA_ROOT
from diy.models import AuthAsset
from widget.models import WidgetStoryUnit, WidgetStoryOpus, WidgetDistrict

from django.db import connection


def update_story_count():
    cursor = connection.cursor()
    #同步作品区域
    sql = "UPDATE widget_story_opus set district_id=(select district_id from widget_story_unit where id=widget_story_opus.unit_id)"
    cursor.execute(sql)
    
    #清空所有区域的作品数
    sql = "update widget_district set story_count=0"
    cursor.execute(sql)
    
    #更新报送单位的作品数
    for story_unit in WidgetStoryUnit.objects.all():
        story_count = WidgetStoryOpus.objects.filter(unit_id=story_unit.id).count()
        sql = "update widget_story_unit set story_count=%s where id=%s" % (story_count, story_unit.id)
        print sql
        if story_unit.story_count <> story_count:
            print "different", story_unit.id, story_unit.story_count , story_count
            story_unit.story_count = story_count
            story_unit.save()
    
        #更新所属区域的作品数
        widget_district = WidgetDistrict.objects.get(id=story_unit.district_id)
        widget_district.story_count += story_count
        widget_district.save()
        new_district_id = str(widget_district.id)[:-2]
        while len(new_district_id)>=2:
            inherit_district = WidgetDistrict.objects.get(id=new_district_id)
            inherit_district.story_count += story_count
            inherit_district.save()
            new_district_id = new_district_id[:-2]


if __name__ == "__main__":
    update_story_count()


    

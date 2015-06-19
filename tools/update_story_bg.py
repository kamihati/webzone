#coding: utf-8
'''
Created on 2014-8-8

@author: Administrator
'''
import sys
sys.path.insert(0, '..')
sys.path.append('/www/wwwroot/')
from datetime import datetime

import os
#使用django的数据库
os.environ['DJANGO_SETTINGS_MODULE'] = 'WebZone.settings'
from widget.models import WidgetStoryOpus, WidgetStoryUnit
from diy.models import AuthOpusPage

from utils import get_user_path
from WebZone.settings import MEDIA_ROOT, MEDIA_URL
from StringIO import StringIO

from PIL import Image, ImageDraw, ImageFont

#update_story_opus(auth_user, auth_asset, widget_story_opus, auth_opus_page, widget_story_unit)

def update_story_opus(auth_user, auth_asset, widget_story_opus, auth_opus_page, widget_story_unit):
    json_file = open(os.path.join(MEDIA_ROOT, "gsdw/1.json"), 'r')
    img_file = open(os.path.join(MEDIA_ROOT, "gsdw/1.jpg"), "rb")
    json_data = json_file.read()
    json_file.close()
    
    json_data = json_data.replace("{video_url}", MEDIA_URL + auth_asset.res_path)
    json_data = json_data.replace("{video_id}", str(auth_asset.id))
    json_data = json_data.replace("{story_name}", widget_story_opus.story_name)
    json_data = json_data.replace("{actor_name}", widget_story_opus.actor_name)
    json_data = json_data.replace("{sex}", u"男" if widget_story_opus.sex==1 else u"女")
    json_data = json_data.replace("{age}", str(widget_story_opus.age))
    json_data = json_data.replace("{school_name}", widget_story_opus.school_name)
    json_data = json_data.replace("{unit_name}", widget_story_unit.name)
    json_data = json_data.replace("{number}", auth_user.number)
    #print json_data
    asset_res_path = get_user_path(auth_user, "opus", widget_story_opus.opus_id)
    if not os.path.exists(os.path.join(MEDIA_ROOT, asset_res_path)):
        os.makedirs(os.path.join(MEDIA_ROOT, asset_res_path))
    
    json_data = json_data.encode('utf-8')
    auth_opus_page.json = json_data
    auth_opus_page.save()
    open(os.path.join(MEDIA_ROOT, auth_opus_page.json_path), "w").write(json_data)
    
    img_data = img_file.read()
    img_file.close()
    img = Image.open(StringIO(img_data))
    from WebZone.conf import fonts
    from WebZone.settings import FONT_ROOT
    font_file = fonts[1]["font"]
    font_file = os.path.join(FONT_ROOT, font_file)
    #print font_file 
    dr = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_file, 32)
    dr.text((1389,174), widget_story_opus.story_name, fill="#000000", font=font)
    dr.text((1392,227), widget_story_opus.actor_name, fill="#000000", font=font)
    dr.text((1390,285), u"男" if widget_story_opus.sex==1 else u"女", fill="#000000", font=font)
    dr.text((1392,344), str(widget_story_opus.age), fill="#000000", font=font)
    dr.text((1394,399), widget_story_opus.school_name, fill="#000000", font=font)
    dr.text((1466,458), auth_user.number, fill="#000000", font=font)
    
    if len(widget_story_unit.name) > 9:
        dr.text((1466,519), widget_story_unit.name[:9], fill="#000000", font=font)
        dr.text((1466,580), widget_story_unit.name[9:], fill="#000000", font=font)
    else:
        dr.text((1466,519), widget_story_unit.name, fill="#000000", font=font)
    img.save(os.path.join(MEDIA_ROOT, auth_opus_page.img_path))


if __name__ == "__main__":
    count = 0
    for story_opus in WidgetStoryOpus.objects.all():
        auth_user = story_opus.user
        auth_asset = story_opus.auth_asset
        auth_opus_page = AuthOpusPage.objects.get(auth_opus_id=story_opus.opus_id, page_index=1)
        widget_story_unit = WidgetStoryUnit.objects.get(id=story_opus.unit_id)
        update_story_opus(auth_user, auth_asset, story_opus, auth_opus_page, widget_story_unit)
        count += 1
        print "count", count
        
        
        
        
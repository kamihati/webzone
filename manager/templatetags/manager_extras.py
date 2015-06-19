#coding: utf-8
'''
Created on 2014年8月15日

@author: Administrator
'''
from django import template

register = template.Library()

from widget.models import WidgetOpusClassify
from WebZone.settings import MEDIA_URL
from diy.models import AuthOpus, AuthOpusPage

@register.filter
def opus_type_name(type_id):
    try:
        return WidgetOpusClassify.objects.get(id=type_id).classify_name
    except: return u"未知"

@register.filter
def zone_page_name(page_id):
    if page_id == 1:
        return u"单页"
    elif page_id == 2:
        return u"双页"
    elif page_id == 0:
        return u"不限"
    else:
        return u"未知"
    
@register.filter
def opus_cover_url(opus_id):
    try: auth_opus = AuthOpus.objects.get(id=opus_id)
    except: return ""
    if auth_opus.cover and len(auth_opus.cover)>0:
        return MEDIA_URL + auth_opus.cover
    auth_opus_page = AuthOpusPage.objects.get(auth_opus_id=opus_id, page_index=1)
    return MEDIA_URL + auth_opus_page.img_path
    



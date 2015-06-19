#coding: utf-8
'''
Created on 2014-3-31

@author: Administrator
'''
from WebZone.conf import ZONE_RES_TYPE, ZONE_RES_STYLE

from WebZone.conf import OPUS_TYPE_CHOICES, OPUS_CLASS_CHOICES
from WebZone.conf import OPUS_TYPE, OPUS_CLASS

from WebZone.conf import OPUS_STATUS_CHOICES


def zone_res_type_name(res_type_id):
    """
        公共资源类型
    """
    if ZONE_RES_TYPE.has_key(res_type_id):
        return ZONE_RES_TYPE[res_type_id]
    return u"未知类型"

def zone_res_style_name(res_style_id):
    """
        公共资源风格
    """
    if ZONE_RES_STYLE.has_key(res_style_id):
        return ZONE_RES_STYLE[res_style_id]
    return u"未知风格"



def opus_type_name(opus_type_id):
    """
        个人作品大类
    """
    if opus_type_id == 0:
        return u"未指定"
    if OPUS_TYPE.has_key(opus_type_id):
        return OPUS_TYPE[opus_type_id]
    return u"未知大类"


def opus_class_name(opus_class_id):
    """
        个人作品小类
    """
    if opus_class_id == 0:
        return u"未指定"
    if OPUS_CLASS.has_key(opus_class_id):
        return OPUS_CLASS[opus_class_id]
    return u"未知小类"


def opus_status_name(status_id):
    """
        个人作品发表状态
    """
    for opus_status in OPUS_STATUS_CHOICES:
        if opus_status[0] == status_id:
            return opus_status[1]
    return u"未知状态"





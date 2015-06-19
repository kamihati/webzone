# coding=utf8

import os
from PIL import Image
from utils import get_img_ext

from WebZone.settings import MEDIA_ROOT

def thumbnail_img(oldpath, height, width, newpath, **kwargs):
    '''
    制作图片的缩略图
    editor: kamihati 2015/6/15  制作图片的缩略图
    :param oldpath: 当前文件路径
    :param height: 要缩放的高度
    :param width: 要缩放的宽度
    :param newpath: 要存放缩放文件的目录
    :param kwargs:
    :return:
    '''
    img = Image.open(MEDIA_ROOT + oldpath)
    if not os.path.exists(os.path.dirname(MEDIA_ROOT + newpath)):
        os.makedirs(os.path.dirname(MEDIA_ROOT + newpath))
    img_large = img.resize((width, height), Image.ANTIALIAS)
    img_large.save(MEDIA_ROOT + newpath)




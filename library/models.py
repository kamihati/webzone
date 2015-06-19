#coding: utf-8
'''
Created on 2014-3-24

@author: Administrator

--------------------------------
@coder: kamihati 2015/3/22  增加省市区三个字段
'''

from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from WebZone import settings
# Create your models here.

class Library(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='auth_user_library', verbose_name=u'')
    domain = models.CharField(max_length=20, blank=True, null=True, verbose_name=u"sub domain of 3qdou")
    
    is_global = models.BooleanField(default=False, verbose_name=u"是否可以看全局作品")
    
    lib_name = models.CharField(_('library name'), max_length=255, blank=False, null=False)
    province = models.CharField(max_length=30, null=True, blank=True, verbose_name=u'省名')
    city = models.CharField(max_length=30, null=True, blank=True, verbose_name=u'市名')
    region = models.CharField(max_length=30, null=True, blank=True, verbose_name=u'区名')
    # editor: kamihati 2015/4/17   新增字段。机构级别用于检索
    level = models.SmallIntegerField(default=0, choices=((0, u'全国机构'), (1, u'省级机构'), (2, u'市级机构'), (3, u'区县级机构')), verbose_name=u'机构级别')
    brief = models.CharField(max_length=1000, null=True, blank=True, verbose_name=u"介绍")
    lib_address = models.CharField(_('library address'), max_length=255, blank=True, null=True)
    host = models.CharField(_('library host url'), max_length=255, blank=False)
    logo_path = models.CharField(_('library logo'), max_length=255, null=True, blank=True)
    swf_path = models.CharField(_('library swf file asset'), max_length=255, null=True, blank=True)
    auth_3qdou_list = models.CharField(max_length=1000, null=True, blank=True, verbose_name=u"3qdou少儿空间学习资源权限")
    create_time = models.DateTimeField(_('create time'), default=timezone.now)
    expire_time = models.DateTimeField(_('expire time'), default=timezone.now)

    # status = models.SmallIntegerField(default=1, choices=((0,u"待审核"),(1,u"可用"),(-1,u"已停用")), verbose_name=u"可用状态")
    # 新版设计中机构状态进行变动  coder: kamihati 2015/4/2  与牛淑倩确认
    status = models.SmallIntegerField(default=1, choices=((0,u"试用"),(1,u"使用"),(2, u'过期'),(-1,u"禁用")), verbose_name=u"可用状态")
    buy_code = models.CharField(max_length=100, verbose_name=u'合同编号')
    annex = models.CharField(max_length=255, null=True, verbose_name=u'附件')

    objects = models.Manager()

    def __unicode__(self):
        return u"library"

    class Meta:
        db_table = "library"
        verbose_name = u"机构"


class LibraryRegion(models.Model):
    '''
    机构地区表。随机构信息而更新
    editor: kamihati  2015/4/24  为方便查询。没必要存储全国地市信息。故只存储现有机构所在地信息
    '''
    name = models.CharField(max_length=50, verbose_name=u'名称')
    parent_id = models.IntegerField(default=0, verbose_name=u'父级地市id')
    level = models.SmallIntegerField(choices=((1, u'省'), (2, u'市'), (3, u'县区')), verbose_name=u'级别')

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'library_region'
        verbose_name = u'机构地区表'

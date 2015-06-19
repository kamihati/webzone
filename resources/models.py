# coding=utf8
import datetime
from django.db import models
from account.models import AuthUser

class ResourceType(models.Model):
    '''
    素材分类
    ----------------
    coder: kamihati 2015/3/27
    coder: kamihati 2015/4/6 由于要让类别与老版本兼容。故公共类别与个人类别分两个表存储。取消re_type字段

    '''
    name = models.CharField(max_length=20, verbose_name=u'分类名称')
    user_id = models.IntegerField(null=False, verbose_name=u'创建人id')
    status = models.SmallIntegerField(choices=((0, u'正常'),(1, u'已删除')), default=0, verbose_name=u'状态')
    create_time = models.DateTimeField(default=datetime.datetime.now())

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'resource_type'


class ResourceTypePerson(models.Model):
    '''
    个人素菜分类(  对应auth_asset表的类别)
    coder: kamihati   2015/4/6
    '''
    name = models.CharField(max_length=20, verbose_name=u'分类名称')
    user = models.ForeignKey(AuthUser, verbose_name=u'创建人id')
    status = models.SmallIntegerField(choices=((0, u'正常'), (1, u'已删除')), default=0, verbose_name=u'状态')
    create_time = models.DateTimeField(default=datetime.datetime.now())

    def __unicode__(self):
        return  self.name

    class Meta:
        db_table = 'resource_type_person'


class ResourceStyle(models.Model):
    '''
    素材风格
    coder: kamihati 2015/3/27
    coder: kamihati 2015/4/6   由于个人资源没有风格属性。取消rs_type 字段
    '''
    name = models.CharField(max_length=20, verbose_name=u'风格名称')
    user_id = models.IntegerField(verbose_name=u'创建人id')
    status = models.SmallIntegerField(choices=((0, u'正常'), (1, u'已删除')), default=0, verbose_name=u'状态')
    create_time = models.DateTimeField(default=datetime.datetime.now())

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'resource_style'

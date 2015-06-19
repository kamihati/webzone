#coding: utf-8
from django.db import models
from datetime import datetime

from account.models import AuthUser
from library.models import Library

# Create your models here.
class ManagerAuthGroup(models.Model):
    name = models.CharField(max_length=32, unique=True, verbose_name=u'名称')
    perms = models.TextField(max_length=1000, verbose_name=u'权限列表', help_text=u'逗号分隔的权限代码列表')
    remark = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'说明')
    
    objects = models.Manager()
    
    def __unicode__(self):
        return u"管理员分组：%s" % self.name
    
    class Meta:
        db_table = 'manager_auth_group'
        verbose_name = u'管理分组'
        verbose_name_plural = u'管理分组列表'

class ManagerUserGroup(models.Model):
    user = models.ForeignKey(AuthUser, unique=True, verbose_name=u'用户')
    group = models.ForeignKey(ManagerAuthGroup, unique=False, verbose_name=u'分组')
    
    objects = models.Manager()
    
    def __unicode__(self):
        return u"管理员：%s" % self.user
    
    class Meta:
        db_table = 'manager_user_group'
        verbose_name = u'管理员'
        verbose_name_plural = u'管理员列表'

class ManagerActionLog(models.Model):
    user = models.ForeignKey(AuthUser, unique=False, verbose_name=u'用户')
    library = models.ForeignKey(Library, blank=True, null=True, verbose_name=u"所属图书馆")
    username = models.CharField(max_length=50, null=True, blank=True, verbose_name=u'操作用户名')
    content = models.CharField(max_length=256, blank=True, null=True, verbose_name=u'内容')
    ip = models.IPAddressField(null=True, blank=True, verbose_name=u'操作IP')
    action_time = models.DateTimeField(default=datetime.now, verbose_name=u'时间')
    remark = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'说明')
    status = models.SmallIntegerField(default=0, choices=((0,u"正常"),(1,u"删除")), verbose_name=u'消息类型')
    objects = models.Manager()
    
    def __unicode__(self):
        return u"管理员操作日志：%s" % self.user
    
    class Meta:
        db_table = 'manager_action_log'
        verbose_name = u'管理员操作日志'
        verbose_name_plural = u'管理员操作日志列表'
        
        
        
        
        
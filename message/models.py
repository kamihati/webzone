#coding:utf8
from django.db import models
import datetime


class UserMessage(models.Model):
    '''
    留言信息
    editor: kamihati 2015/5/27
    '''
    post_user_id = models.IntegerField(default=0, verbose_name=u"发送人")
    receive_user_id = models.IntegerField(default=0, verbose_name=u'接受人')
    title = models.CharField(max_length=255, null=False, blank=False, verbose_name=u"标题")
    content = models.CharField(max_length=500, null=False, blank=False, verbose_name=u'内容')
    create_time = models.DateTimeField(default=datetime.datetime.now, verbose_name=u"创建时间")
    status = models.SmallIntegerField(default=0, choices=((-1, u'已删除'), (0, u"未读"), (1, u"已读")), verbose_name=u"可用状态")
    reply_user_id = models.IntegerField(default=0, verbose_name=u'回复人id')
    reply_id = models.IntegerField(default=0, verbose_name=u'所回复的留言id')

    def __unicode__(self):
        return u"留言板"

    class Meta:
        db_table = "user_message"
        verbose_name = u"留言板"

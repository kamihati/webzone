# coding=utf8
'''
话题相关model
create by kamihati   2015/3/17
'''
from django.db import models
import datetime

from WebZone.conf import TOPIC_TYPE_CHOICES


class TopicType(models.Model):
    '''
    话题分类表
    ----------------
    coder: kamihati 2015/3/20

    '''
    name = models.CharField(max_length=20, verbose_name=u'分类名称')
    user_id = models.IntegerField(null=False, verbose_name=u'创建人id')
    create_time = models.DateTimeField(default=datetime.datetime.now())

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'topic_type'


class Topic(models.Model):
    """
        话题表
        -------------------
        coder: kamihati 2015/3/20

    """
    user_id = models.IntegerField(null=False, verbose_name=u"话题创建人ID")
    library_id = models.IntegerField(blank=True, null=True, verbose_name=u"所属图书馆ID")
    title = models.CharField(max_length=255, null=False, blank=False, verbose_name=u"标题")
    content = models.CharField(max_length=500, null=False, blank=False, verbose_name=u'话题内容')
    is_top = models.SmallIntegerField(default=0, choices=((0, u'未置顶'), (1, u'置顶')), verbose_name=u"是否置顶")
    update_time = models.DateTimeField(null=True, verbose_name=u"最后修改时间")
    create_time = models.DateTimeField(default=datetime.datetime.now, verbose_name=u"创建时间")
    status = models.SmallIntegerField(default=0, choices=((0, u"正常"), (1, u"已删除")), verbose_name=u"可用状态")
    praise_count = models.IntegerField(default=0, verbose_name=u"点赞个数")
    view_count = models.IntegerField(default=0, verbose_name=u'浏览量')
    remark_count = models.IntegerField(default=0, verbose_name=u"回复数量")

    def __unicode__(self):
        return u"个人话题"

    class Meta:
        db_table = "topic_main"
        verbose_name = u"个人话题表"
        verbose_name_plural = u"个人话题列表"

    def _add_praise(self):
        '''
        增加点赞数
        coder: kamihati 2015/3/23   供点赞记录插入成功后调用
        '''
        self.praise_count += 1
        self.save()


class TopicPraise(models.Model):
    '''
    话题点赞记录表
    ----------------------------------
    '''
    topic_id = models.IntegerField(verbose_name=u'话题id')
    user_id = models.IntegerField(verbose_name=u'用户id')
    add_date = models.DateField(verbose_name=u'点赞日期', default=datetime.datetime.now().date())

    class Meta:
        db_table = "topic_praise"
        verbose_name = u'话题点赞记录表'


class RemarkPraise(models.Model):
    '''
    话题点赞记录表
    ----------------------------------
    '''
    remark_id = models.IntegerField(verbose_name=u'评论id')
    user_id = models.IntegerField(verbose_name=u'用户id')
    add_date = models.DateField(verbose_name=u'点赞日期', default=datetime.datetime.now().date())

    class Meta:
        db_table = "topic_remark_praise"
        verbose_name = u'评论点赞记录表'



class TopicRemark(models.Model):
    '''
    话题评论记录
    -------------------
    coder: kamihati 2015/3/20
    '''
    user_id = models.IntegerField(null=False, verbose_name=u'评论人id')
    library_id = models.IntegerField(blank=True, null=True, verbose_name=u"所属图书馆ID")
    topic_id = models.IntegerField(null=False, verbose_name=u'被评论的话题id')
    content = models.CharField(max_length=500, null=False, blank=False, verbose_name=u'评论内容')
    update_time = models.DateTimeField(default=datetime.datetime.now, verbose_name=u"最后修改时间")
    create_time = models.DateTimeField(default=datetime.datetime.now, verbose_name=u"创建时间")
    status = models.SmallIntegerField(default=0, choices=((0, u"正常"), (1, u"已删除")), verbose_name=u"可用状态")
    praise_count = models.IntegerField(default=0, verbose_name=u"点赞个数")

    def __unicode__(self):
        return self.content

    class Meta:
        db_table = 'topic_remark'
        verbose_name = u'话题评论记录表'


# 话题附件类别定义
# TOPIC_TYPE_INSERT = ((1, u"表情"), (2, u"图片"), (3, u"音频"), (4, u"视频"), (5, u"作品"))
TOPIC_TYPE_INSERT = ((1, u"图片"), (2, u"音频"), (3, u"视频"), (4, u"作品"))


class TopicResource(models.Model):
    '''
    话题附件记录表
    -------------------------
    coder: kamihati 2015/3/20
    '''
    topic_id = models.IntegerField(null=False, verbose_name=u'所属话题id')
    type_id = models.IntegerField(null=False, choices=TOPIC_TYPE_INSERT, verbose_name=u'附件类别')
    # 目前附件id对应ZoneAsset表
    res_id = models.IntegerField(null=False, verbose_name=u'附件id')
    # 由于资源表已有缩略图字段。这个字段是否需要存在还需讨论
    thumbnail = models.CharField(max_length=100, null=True, verbose_name=u'附件缩略图')

    class Meta:
        db_table = 'topic_resource'
        verbose_name = u'话题附件表'


class PhizType(models.Model):
    '''
    话题表情类别
    话题表情数据存储于   ZoneAsset表res_type=12
    coder: kamihati   2015/3/20
    '''
    name = models.CharField(max_length=15, verbose_name=u"表情类别名称", null=False)
    user_id = models.IntegerField(null=False, verbose_name=u"创建人ID")
    status = models.SmallIntegerField(default=0, choices=((0, u"已禁用"), (1, u"使用中")), verbose_name=u"是否禁用")
    create_time = models.DateTimeField(default=datetime.datetime.now(), verbose_name=u"创建时间")

    def __unicode__(self):
        return self.name

    class Meta:
            db_table = 'topic_phiz_type'
            verbose_name = u'话题表情类别表'


class RemarkResource(models.Model):
    '''
    话题评论附件记录表
    -------------------------
    coder:  2015/3/20
    coder:   kamihati  2015/3/24   修改字段名称 topic_id 为remark_id
    '''
    remark_id = models.IntegerField(null=False, verbose_name=u'所属话题id')
    type_id = models.IntegerField(null=False, choices=TOPIC_TYPE_INSERT, verbose_name=u'附件类别')
    # 目前附件id对应ZoneAsset表
    res_id = models.IntegerField(null=False, verbose_name=u'附件id')
    # 由于资源表已有缩略图字段。这个字段是否需要存在还需讨论
    thumbnail = models.CharField(max_length=100, null=True, verbose_name=u'附件缩略图')

    class Meta:
        db_table = 'topic_remark_resource'
        verbose_name = u'话题评论附件表'
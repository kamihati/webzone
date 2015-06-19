#coding: utf-8
'''
Created on 2014-3-29

@author: Administrator
'''

from django.db import models

from datetime import datetime
from account.models import AuthUser
from WebZone.conf import PERSONAL_RES_TYPE_CHOICES
from WebZone.conf import OPUS_TYPE_CHOICES, OPUS_CLASS_CHOICES
from WebZone.conf import ZONE_RES_STYLE_CHOICES, ZONE_RES_TYPE_CHOICES

from WebZone.conf import OPUS_STATUS_CHOICES, SHOW_TYPE_CHOICES
from WebZone.conf import DOU_ASSET_TYPE
from WebZone.conf import TOPIC_TYPE_CHOICES

from library.models import Library
from django.utils.termcolors import background
from _mysql import NULL
from django.db.models.fields import BLANK_CHOICE_DASH
# Create your models here.


class AuthAlbum(models.Model):
    user = models.ForeignKey(AuthUser, verbose_name=u"用户")
    
    album_title = models.CharField(max_length=100, null=False, blank=False, verbose_name=u"标题")
    #brief = models.CharField(max_length=1000, null=True, blank=True, verbose_name=u"摘要")
    
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    type_id = models.SmallIntegerField(default=1, choices=((1,u"个人相册"),(0,u"系统相册")), verbose_name=u"相册类型")
    status = models.SmallIntegerField(default=1, choices=((0,u"待审核"),(1,u"可用"),(-1,u"删除")), verbose_name=u"可用状态")
    
    objects = models.Manager()
    def __unicode__(self):
        return u"个人相册"
    
    class Meta:
        db_table = "auth_album"
        verbose_name = u"个人相册"
        verbose_name_plural = u"个人相册列表"

class AuthAsset(models.Model):
    """
        个人资源表
    """
    library = models.ForeignKey(Library, blank=True, null=True, verbose_name=u"所属图书馆")
    user = models.ForeignKey(AuthUser, verbose_name=u"资产拥有人")
    album_id = models.IntegerField(default=0, verbose_name=u"所属相册的ID")
    
    res_title = models.CharField(max_length=255, null=True, blank=True, verbose_name=u"标题")
    #brief = models.CharField(max_length=1000, null=True, blank=True, verbose_name=u"摘要")
    # PERSONAL_RES_TYPE_CHOICES = ((1,u"图片"),(2,u"声音"),(3,u"视频"),(4,u"涂鸦"),(11,u"故事大王"))
    res_type = models.SmallIntegerField(default=0, choices=PERSONAL_RES_TYPE_CHOICES, verbose_name=u"个人资源类型")
    
    origin_path = models.CharField(max_length=255, null=True, blank=True, verbose_name=u"音频/视频原始文件路径")
    origin_del = models.BooleanField(default=0, verbose_name=u"标记源文件有没删除")
    video_width = models.SmallIntegerField(default=0, null=True, blank=True, verbose_name=u"视频原始宽度")
    video_height = models.SmallIntegerField(default=0, null=True, blank=True, verbose_name=u"视频原始高度")
    duration = models.FloatField(default=0.0, verbose_name=u"音/视频时长(秒)")
    
    res_path = models.CharField(max_length=255, null=True, blank=True, verbose_name=u"路径")
    width = models.SmallIntegerField(default=0, verbose_name=u"图片/视频的宽度")
    height = models.SmallIntegerField(default=0, verbose_name=u"图片/视频的高度")
    
    img_large_path = models.CharField(max_length=255, null=True, blank=True, verbose_name=u"大图路径")
    img_medium_path = models.CharField(max_length=255, null=True, blank=True, verbose_name=u"中图路径")
    img_small_path = models.CharField(max_length=255, null=True, blank=True, verbose_name=u"小图路径")
    
    ref_times = models.IntegerField(default=0, verbose_name=u"被引用次数")
    share_times = models.IntegerField(default=0, verbose_name=u"分享次数")
    is_like = models.SmallIntegerField(default=0, verbose_name=u"是否喜欢")
    
    update_time = models.DateTimeField(default=datetime.now, verbose_name=u"更新时间")
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    codec_status = models.SmallIntegerField(default=0, choices=((0,u"正在转码"),(1,u"转码成功"),(-1,u"转码失败")), verbose_name=u"转码状态")
    status = models.SmallIntegerField(default=1, choices=((0,u"待审核"),(1,u"可用"),(-1,u"删除")), verbose_name=u"可用状态")
    
    objects = models.Manager()
    
    def __unicode__(self):
        return u"个人资产"
    
    class Meta:
        db_table = "auth_asset"
        verbose_name = u"个人资产"
        verbose_name_plural = u"个人资产列表"


class AuthAssetRef(models.Model):
    """
        个人资源引用计数表，可以做推荐、删除个人资源时检查相关用
    """
    auth_asset = models.ForeignKey(AuthAsset, verbose_name=u"个人资源ID")
    user = models.ForeignKey(AuthUser, verbose_name=u"作品作者")
    auth_opus = models.ForeignKey("AuthOpus", verbose_name=u"引用的作品")
    page_index = models.SmallIntegerField(default=0, verbose_name=u"作品页码")
    
    res_type = models.SmallIntegerField(default=0, choices=PERSONAL_RES_TYPE_CHOICES, verbose_name=u"个人资源类型")
    
    update_time = models.DateTimeField(default=datetime.now, verbose_name=u"更新时间")
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    
    objects = models.Manager()
    
    def __unicode__(self):
        return u"个人资源引用计数"
    
    class Meta:
        db_table = "auth_asset_ref"
        verbose_name = u"个人资源引用计数"
        verbose_name_plural = u"个人资源引用计数列表"


class AuthAssetShare(models.Model):
    """
        个人资源共享表(资源拥有都可以指定自己的哪个资源可以供哪些好友使用)
    """
    auth_asset = models.ForeignKey(AuthAsset, verbose_name=u"个人资源ID")
    user = models.ForeignKey(AuthUser, verbose_name=u"共享用户")

    is_like = models.SmallIntegerField(default=1, verbose_name=u"是否喜欢")
    
    update_time = models.DateTimeField(default=datetime.now, verbose_name=u"更新时间")
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    
    objects = models.Manager()
    
    def __unicode__(self):
        return u"个人资源共享"
    
    class Meta:
        db_table = "auth_asset_share"
        verbose_name = u"个人资源共享表"
        verbose_name_plural = u"个人资源共享表"

# editor: kamihati 2015/6/10 由于类别通过后台进行处理。此变量暂不使用
AUTH_OPUS_TYPE_CHOICES = ((0,u"个人作品"),(1,u"活动播报"),(2,u"个人参赛作品"),(3,u"活动预告"),(4,u"活动结果"),(11,u"机构作品"),(12,u"私密作品"))
class AuthOpus(models.Model):
    """
        个人作品表
        editor: kamihati 2015/6/10
    """
    user = models.ForeignKey(AuthUser, verbose_name=u"作品拥有人")
    library = models.ForeignKey(Library, blank=True, null=True, verbose_name=u"所属图书馆")
    # 作品分类由后台控制。显示widget.models.WidgetOpusClassify 的id
    opus_type = models.SmallIntegerField(default=0, choices=AUTH_OPUS_TYPE_CHOICES, verbose_name=u"作品所属分类")
    activity_id = models.IntegerField(null=True, blank=True, verbose_name=u"活动ID") 

    title = models.CharField(max_length=255, null=True, blank=True, verbose_name=u"标题")
    brief = models.CharField(max_length=1000, null=True, blank=True, verbose_name=u"摘要")
    tags = models.CharField(max_length=255, null=True, blank=True, verbose_name=u"标签")
    template_id = models.SmallIntegerField(null=True, blank=True, verbose_name=u"模板ID")
    
    create_type = models.SmallIntegerField(default=1, choices=((1,u"单页显示"),(2,u"双页显示")), verbose_name=u"创作显示方式")
    read_type = models.SmallIntegerField(default=1, choices=((1,u"单页显示"),(2,u"双页显示")), verbose_name=u"阅读显示方式")
    
    show_type = models.SmallIntegerField(default=0, choices=SHOW_TYPE_CHOICES, verbose_name=u"演示分类")
    type_id = models.SmallIntegerField(default=0, choices=OPUS_TYPE_CHOICES, verbose_name=u"作品类型")
    class_id = models.SmallIntegerField(default=0, choices=OPUS_CLASS_CHOICES, verbose_name=u"作品子分类")
    page_count = models.IntegerField(default=0, verbose_name=u"总页数")
    #multimedia_pages = models.CharField(max_length=500, null=True, blank=True, verbose_name=u"多媒体的页ID")
    #is_press = models.SmallIntegerField(default=0, verbose_name=u"是否发表")
    is_top = models.SmallIntegerField(default=0, verbose_name=u"是否加精/推荐")
    total_grade = models.BigIntegerField(default=0, verbose_name=u"总分数")
    grade_times = models.IntegerField(default=0, verbose_name=u"总评分次数")
    grade = models.FloatField(default=0, verbose_name=u"平均分数")
    preview_times = models.IntegerField(default=0, verbose_name=u"预览次数")
    comment_times = models.IntegerField(default=0, verbose_name=u"评论次数")
    praise_times = models.IntegerField(default=0, verbose_name=u"点赞次数")
    
    width = models.SmallIntegerField(default=0, verbose_name=u"作品宽")
    height = models.SmallIntegerField(default=0, verbose_name=u"作品高")
    
    cover = models.CharField(max_length=255, null=False, blank=False, verbose_name=u"封面")
    thumbnail = models.CharField(max_length=255, null=False, blank=False, verbose_name=u"封面缩略图")
    
    update_time = models.DateTimeField(default=datetime.now, verbose_name=u"最后修改时间")
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    # OPUS_STATUS_CHOICES = ((-3,u"创建失败"),(-2,u"删除标记"),(-1,u"审核未通过"),(0,u"草稿"),(1,u"待审核"),(2,u"已表中"))
    status = models.SmallIntegerField(default=0, choices=OPUS_STATUS_CHOICES, verbose_name=u"可用状态")
    #apply_time = models.DateTimeField(null=True, blank=True, verbose_name=u"申请发表时间")
    #press_time = models.DateTimeField(null=True, blank=True, verbose_name=u"发表时间")
    size_id = models.IntegerField(default=0, verbose_name='size_id')

    objects = models.Manager()
    
    def __unicode__(self):
        return u"个人作品"
    
    class Meta:
        db_table = "auth_opus"
        verbose_name = u"个人作品"
        verbose_name_plural = u"个人作品列表"
        
    
class BlobField(models.Field):
    description = "Blob"
    def db_type(self, connection):
        return 'blob'
    
    
class AuthOpusPage(models.Model):
    auth_opus = models.ForeignKey(AuthOpus, verbose_name=u"作品")
    
    page_index = models.SmallIntegerField(default=0, verbose_name=u"当前页码")
    template_id = models.SmallIntegerField(null=True, blank=True, verbose_name=u"模板ID")
    template_page_index = models.SmallIntegerField(null=True, blank=True, verbose_name=u"对应的模板页码")
    is_multimedia = models.BooleanField(default=False, verbose_name=u"是否多媒体页")
    
    auth_asset_list = models.CharField(max_length=500, verbose_name=u"引用的个人资源ID列表")
    zone_asset_list = models.CharField(max_length=500, verbose_name=u"引用的公共资源ID列表")
    
    json = BlobField(blank=True, null=True, verbose_name=u'json文本')
    json_path = models.CharField(max_length=255, null=True, blank=True, verbose_name=u"json文件路径")
    img_path = models.CharField(max_length=255, null=True, blank=True, verbose_name=u"缩略图路径")
    img_small_path = models.CharField(max_length=255, null=True, blank=True, verbose_name=u"小图路径")
    
    update_time = models.DateTimeField(default=datetime.now, verbose_name=u"更新时间")
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    
    objects = models.Manager()
    
    def __unicode__(self):
        return u"作品:%d第%d页信息" % (self.auth_opus.id, self.page_index)
    
    class Meta:
        db_table = "auth_opus_page"
        verbose_name = u"作品单页信息表"
        verbose_name_plural = u"作品单页信息表"


class AuthOpusGrade(models.Model):
    """
        作品等级评分表
    """
    user = models.ForeignKey(AuthUser, verbose_name=u"评分人")
    library = models.ForeignKey(Library, blank=True, null=True, verbose_name=u"所属图书馆")
    auth_opus = models.ForeignKey(AuthOpus, verbose_name=u"作品")
    grade = models.SmallIntegerField(default=0, verbose_name=u"评的分数")
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    
    objects = models.Manager()
    
    def __unicode__(self):
        return u"作品等级评分"
    
    class Meta:
        db_table = "auth_opus_grade"
        verbose_name = u"作品等级评分"
        verbose_name_plural = u"作品等级评分列表"
        

class AuthOpusComment(models.Model):
    """
        作品评论表
    """
    user = models.ForeignKey(AuthUser, null=True, blank=True, verbose_name=u"评分人/匿名")
    library = models.ForeignKey(Library, blank=True, null=True, verbose_name=u"所属图书馆")
    auth_opus = models.ForeignKey(AuthOpus, verbose_name=u"作品")
    comment = models.CharField(max_length=500, verbose_name=u"评论内容")
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    
    objects = models.Manager()
    
    def __unicode__(self):
        return u"作品评论表"
    
    class Meta:
        db_table = "auth_opus_comment"
        verbose_name = u"作品评论表"
        verbose_name_plural = u"作品评论列表"
        
        
class AuthOpusPraise(models.Model):
    """
        作品点赞列表
    """
    user = models.ForeignKey(AuthUser, null=True, blank=True, verbose_name=u"评分人")
    library = models.ForeignKey(Library, blank=True, null=True, verbose_name=u"所属图书馆")
    auth_opus = models.ForeignKey(AuthOpus, verbose_name=u"作品")
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    
    objects = models.Manager()
    
    def __unicode__(self):
        return u"作品点赞列表"
    
    class Meta:
        db_table = "auth_opus_praise"
        verbose_name = u"作品点赞列表"
        verbose_name_plural = u"作品点赞列表"
                


class ZoneAsset(models.Model):
    """
        公共资源表
        editor: kamihati 2015/6/5
    """
    user = models.ForeignKey(AuthUser, verbose_name=u"上传人")
    library = models.ForeignKey(Library, blank=True, null=True, verbose_name=u"所属图书馆")
    
    res_title = models.CharField(max_length=255, null=False, blank=False, verbose_name=u"标题")
    #brief = models.CharField(max_length=1000, null=True, blank=True, verbose_name=u"摘要")
    # res_type 对应 resources.models 的 ResourceType表
    # editor: kamihati 2015/5/11
    # ((1,u"背景"),(2,u"装饰"),(3,u"画框"),(4,u"模板"),(5,u"声音"),(6,u"视频"),(7,u"图片"),(8,u"特效"),(10,u"话题模板"),(11,u"话题标签"),(12,u"话题表情"))
    res_type = models.SmallIntegerField(default=0, choices=ZONE_RES_TYPE_CHOICES, verbose_name=u"资源类型")
    opus_id = models.IntegerField(blank=True, null=True, verbose_name=u"模板来源作品")
    page_type = models.SmallIntegerField(default=0, choices=((0,u"不限"),(1,u"单页"),(2,u"双页")), verbose_name=u"单/双页")
    layout_type = models.SmallIntegerField(default=0, choices=((0,u"不限"),(1,u"横版"),(2,u"竖版")), verbose_name=u"版式")

    # res_style 对应 resources.models的ResourceStyle表
    # editor: kamihati 2015/5/11
    res_style = models.SmallIntegerField(default=0, choices=ZONE_RES_STYLE_CHOICES, verbose_name=u"资源风格")

    # 门类id,对应widget_opus_classify表
    type_id = models.SmallIntegerField(default=0, choices=OPUS_TYPE_CHOICES, verbose_name=u"[模板]作品类型")
    # 子类id。对应widget_opus_classify表.type_id为class_id父类
    class_id = models.SmallIntegerField(default=0, choices=OPUS_CLASS_CHOICES, verbose_name=u"[模板]作品子分类")
    create_type = models.SmallIntegerField(default=1, choices=((1,u"单页显示"),(2,u"双页显示")), verbose_name=u"[模板]创作显示方式")
    read_type = models.SmallIntegerField(default=1, choices=((1,u"单页显示"),(2,u"双页显示")), verbose_name=u"[模板]阅读显示方式")
    
    origin_path = models.CharField(max_length=255, null=True, blank=True, verbose_name=u"音频/视频原始文件路径")
    origin_del = models.BooleanField(default=0, verbose_name=u"标记源文件有没删除")
    video_width = models.SmallIntegerField(default=0, null=True, blank=True, verbose_name=u"视频原始宽度")
    video_height = models.SmallIntegerField(default=0, null=True, blank=True, verbose_name=u"视频原始高度")
    duration = models.FloatField(default=0.0, verbose_name=u"音/视频时长(秒)")
    
    res_path = models.CharField(max_length=255, null=True, blank=True, verbose_name=u"路径")
    mask_path = models.CharField(max_length=255, null=True, blank=True, verbose_name=u"遮罩路径") #只有画框有这个属性
    
    size_id = models.SmallIntegerField(default=0, verbose_name=u"size id")
    width = models.SmallIntegerField(default=0, verbose_name=u"图片资源的宽度")
    height = models.SmallIntegerField(default=0, verbose_name=u"图片资源的高度")
    
    row = models.SmallIntegerField(default=0, verbose_name=u"标签的行数")
    column = models.SmallIntegerField(default=0, verbose_name=u"标签的列数")
    template_id = models.IntegerField(default=0, verbose_name=u"标签模板的ID")
    
    img_large_path = models.CharField(max_length=255, null=True, blank=True, verbose_name=u"大图路径")
    img_medium_path = models.CharField(max_length=255, null=True, blank=True, verbose_name=u"中图路径")
    img_small_path = models.CharField(max_length=255, null=True, blank=True, verbose_name=u"小图/视频缩略图路径")
    
    ref_times = models.IntegerField(default=0, verbose_name=u"被引用次数")
    like_times = models.IntegerField(default=0, verbose_name=u"喜欢次数")
    page_count = models.SmallIntegerField(default=0, verbose_name=u"模板的总页数")
    is_recommend = models.SmallIntegerField(default=0, choices=((0, u'不推荐'), (1, u'推荐')), verbose_name=u"是否推荐")
    
    update_time = models.DateTimeField(default=datetime.now, verbose_name=u"更新时间")
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    codec_status = models.SmallIntegerField(default=0, choices=((0,u"正在转码"),(1,u"转码成功"),(-1,u"转码失败")), verbose_name=u"转码状态")
    # status = models.SmallIntegerField(default=1, choices=((0,u"待审核"),(1,u"可用"),(-1,u"删除")), verbose_name=u"可用状态")
    # 新版设计中状态只有可用和删除两种。coder:kamihati  2015/4/2  与牛淑倩确认
    status = models.SmallIntegerField(default=1, choices=((1, u"可用"), (-1, u"删除")), verbose_name=u"可用状态")
    # editor: kamihati 2015/6/18  一对一的标记。客户端使用这个标记来和表情地址对应
    mark_id = models.CharField(max_length=50, null=True, verbose_name=u'标记')

    objects = models.Manager()
    
    def __unicode__(self):
        return u"公共资源"
    
    class Meta:
        db_table = "zone_asset"
        verbose_name = u"公共资源"
        verbose_name_plural = u"公共资源列表"

class ZoneAssetRef(models.Model):
    """
        公共资源引用计数表，可以做推荐、删除个人资源时检查相关用
    """
    zone_asset = models.ForeignKey(ZoneAsset, verbose_name=u"公共资源ID")
    user = models.ForeignKey(AuthUser, verbose_name=u"作品作者")
    auth_opus = models.ForeignKey(AuthOpus, verbose_name=u"引用的作品")
    page_index = models.SmallIntegerField(default=0, verbose_name=u"作品页码")
    
    res_type = models.SmallIntegerField(default=0, choices=ZONE_RES_TYPE_CHOICES, verbose_name=u"资源类型")
    res_style = models.SmallIntegerField(default=0, choices=ZONE_RES_STYLE_CHOICES, verbose_name=u"资源风格")
    
    update_time = models.DateTimeField(default=datetime.now, verbose_name=u"更新时间")
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    
    objects = models.Manager()
    
    def __unicode__(self):
        return u"公共资源引用计数"
    
    class Meta:
        db_table = "zone_asset_ref"
        verbose_name = u"公共资源引用计数"
        verbose_name_plural = u"公共资源引用计数列表"


class ZoneAssetTemplate(models.Model):
    """
        公共资源的模板详细信息
    """
    zone_asset = models.ForeignKey(ZoneAsset, verbose_name=u"公共资源模板的ID")
    page_index = models.SmallIntegerField(default=0, verbose_name=u"模板页码")
    
    json = BlobField(blank=True, null=True, verbose_name=u'json文本')
    json_path = models.CharField(max_length=255, null=False, blank=False, verbose_name=u"json文件路径")
    img_path = models.CharField(max_length=255, null=False, blank=False, verbose_name=u"缩略图路径")
    img_small_path = models.CharField(max_length=255, null=False, blank=False, verbose_name=u"小图路径")
    
    ref_times = models.IntegerField(default=0, verbose_name=u"被引用次数")
    is_multimedia = models.IntegerField(default=0, verbose_name=u"是否多媒体页")
    
    update_time = models.DateTimeField(default=datetime.now, verbose_name=u"更新时间")
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    
    objects = models.Manager()
    
    def __unicode__(self):
        return u"模板:%d详细信息表" % self.zone_asset.id
    
    class Meta:
        db_table = "zone_asset_template"
        verbose_name = u"模板详细信息表"
        verbose_name_plural = u"模板详细信息表"


class ZoneAssetLike(models.Model):
    """
        公共资源喜欢表，用户喜欢的资源放前
        editor: kamihati 2015/6/9  公共资源
    """
    zone_asset_id = models.IntegerField(null=False, blank=False, verbose_name=u'喜欢的资源ID')
    res_type = models.SmallIntegerField(default=0, choices=ZONE_RES_TYPE_CHOICES, verbose_name=u"资源类型")
    user_id = models.IntegerField(null=False, blank=False, verbose_name=u'用户ID')
    is_like = models.SmallIntegerField(default=1, verbose_name=u"是否喜欢")

    update_time = models.DateTimeField(default=datetime.now, verbose_name=u"更新时间")
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")

    objects = models.Manager()
    
    def __unicode__(self):
        return u"%d喜欢公共资源:%d表" % (self.user_id, self.zone_asset_id)

    class Meta:
        db_table = "zone_asset_like"
        verbose_name = u"公共资源喜欢表"
        verbose_name_plural = u"公共资源喜欢表"


class DouAsset(models.Model):
    """
        3qdou所有资源列总表
        #Res_Article: 1
        #Res_Books: 2
        #Res_Game: 3
        #Res_Music: 4
        #Res_Picture: 5
        #Res_Video: 6
    """
    guid = models.CharField(max_length=50, unique=True, null=False, blank=False, verbose_name=u"文件的guid标识")
    type_id = models.SmallIntegerField(default=0, choices=DOU_ASSET_TYPE, verbose_name=u'3qdou资源类型')

    title = models.CharField(max_length=255, null=True, verbose_name=u"标题")
    sub_title = models.CharField(max_length=255, null=True, verbose_name=u"子标题")
    series_title = models.CharField(max_length=255, null=True, verbose_name=u"序列标题")
    label = models.CharField(max_length=50, null=True, verbose_name=u"标签")

    primary_responser = models.CharField(max_length=50, null=True, verbose_name=u"主要编辑")
    liability_method = models.CharField(max_length=50, null=True, verbose_name=u"责任方法")
    other_responser = models.CharField(max_length=50, null=True, verbose_name=u"其他编辑")
    other_method = models.CharField(max_length=50, null=True, verbose_name=u"其他方法")

    key_words = models.CharField(max_length=100, null=True, verbose_name=u"关键字")
    description = models.CharField(max_length=1000, null=True, verbose_name=u"简介")
    publisher = models.CharField(max_length=50, null=True, verbose_name=u"出版商")
    publish_date = models.DateTimeField(null=True, verbose_name=u"出版日期")

    page_count = models.IntegerField(default=0, verbose_name=u"总页数")
    
    width = models.SmallIntegerField(default=0, verbose_name=u"作品宽")
    height = models.SmallIntegerField(default=0, verbose_name=u"作品高")

    language = models.CharField(max_length=20, null=True, verbose_name=u"语言")
    area = models.CharField(max_length=20, null=True, verbose_name=u"区域")
    type_content = models.CharField(max_length=255, null=True, verbose_name=u"分类详情")
    fister_letter = models.CharField(max_length=10, null=True, verbose_name=u"首字字母")
    
    file_path = models.CharField(max_length=255, null=True, verbose_name=u"文件所在路径")
    thumb_path = models.CharField(max_length=255, null=True, verbose_name=u"缩略图路径")
    res_path = models.CharField(max_length=255, null=True, verbose_name=u"swf文件路径")
    cover = models.CharField(max_length=255, null=True, verbose_name=u"封面")
    thumbnail = models.CharField(max_length=255, null=True, verbose_name=u"封面缩略图")
    extension = models.CharField(max_length=50, null=True, verbose_name=u"扩展信息")
    
    is_top = models.SmallIntegerField(default=0, verbose_name=u"是否加精/推荐")
    total_grade = models.BigIntegerField(default=0, verbose_name=u"总分数")
    grade_times = models.IntegerField(default=0, verbose_name=u"总评分次数")
    grade = models.FloatField(default=0, verbose_name=u"平均分数")
    preview_times = models.IntegerField(default=0, verbose_name=u"预览次数")
    comment_times = models.IntegerField(default=0, verbose_name=u"评论次数")
    praise_times = models.IntegerField(default=0, verbose_name=u"点赞次数")

    update_time = models.DateTimeField(default=datetime.now, verbose_name=u"最后修改时间")
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    status = models.SmallIntegerField(default=1, choices=((-1,u"不可用"),(0,u"待定"),(1,u"可用")), verbose_name=u"可用状态")
    
    objects = models.Manager()
    
    def __unicode__(self):
        return u"资源:%d详细信息表" % self.id
    
    class Meta:
        db_table = "dou_asset"
        verbose_name = u"3qdou所有资源"
        verbose_name_plural = u"3qdou所有资源列表"




class DouBook(models.Model):
    """
        3qdou图书资源列表
    """
    guid = models.CharField(max_length=50, unique=True, null=False, blank=False, verbose_name=u"文件的guid标识")
    title = models.CharField(max_length=255, null=True, verbose_name=u"标题")
    sub_title = models.CharField(max_length=255, null=True, verbose_name=u"子标题")
    series_title = models.CharField(max_length=255, null=True, verbose_name=u"序列标题")
    label = models.CharField(max_length=50, null=True, verbose_name=u"标签")

    primary_responser = models.CharField(max_length=50, null=True, verbose_name=u"主要编辑")
    liability_method = models.CharField(max_length=50, null=True, verbose_name=u"责任方法")
    other_responser = models.CharField(max_length=50, null=True, verbose_name=u"其他编辑")
    other_method = models.CharField(max_length=50, null=True, verbose_name=u"其他方法")

    key_words = models.CharField(max_length=100, null=True, verbose_name=u"关键字")
    description = models.CharField(max_length=1000, null=True, verbose_name=u"简介")
    publisher = models.CharField(max_length=50, null=True, verbose_name=u"出版商")
    publish_date = models.DateTimeField(null=True, verbose_name=u"出版日期")

    page_count = models.IntegerField(default=0, verbose_name=u"总页数")
    
    width = models.SmallIntegerField(default=0, verbose_name=u"作品宽")
    height = models.SmallIntegerField(default=0, verbose_name=u"作品高")

    language = models.CharField(max_length=20, null=True, verbose_name=u"语言")
    area = models.CharField(max_length=20, null=True, verbose_name=u"区域")
    type_content = models.CharField(max_length=255, null=True, verbose_name=u"分类详情")
    fister_letter = models.CharField(max_length=10, null=True, verbose_name=u"首字字母")
    
    file_path = models.CharField(max_length=255, null=True, verbose_name=u"文件所在路径")
    thumb_path = models.CharField(max_length=255, null=True, verbose_name=u"缩略图路径")
    res_path = models.CharField(max_length=255, null=True, verbose_name=u"swf文件路径")
    cover = models.CharField(max_length=255, null=True, verbose_name=u"封面")
    thumbnail = models.CharField(max_length=255, null=True, verbose_name=u"封面缩略图")
    extension = models.CharField(max_length=50, null=True, verbose_name=u"扩展信息")
    
    is_top = models.SmallIntegerField(default=0, verbose_name=u"是否加精/推荐")
    total_grade = models.BigIntegerField(default=0, verbose_name=u"总分数")
    grade_times = models.IntegerField(default=0, verbose_name=u"总评分次数")
    grade = models.FloatField(default=0, verbose_name=u"平均分数")
    preview_times = models.IntegerField(default=0, verbose_name=u"预览次数")
    comment_times = models.IntegerField(default=0, verbose_name=u"评论次数")
    praise_times = models.IntegerField(default=0, verbose_name=u"点赞次数")

    update_time = models.DateTimeField(default=datetime.now, verbose_name=u"最后修改时间")
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    status = models.SmallIntegerField(default=1, choices=((-1,u"不可用"),(0,u"待定"),(1,u"可用")), verbose_name=u"可用状态")
    
    objects = models.Manager()
    
    def __unicode__(self):
        return u"资源:%d详细信息表" % self.id
    
    class Meta:
        db_table = "dou_book"
        verbose_name = u"3qdou图书资源"
        verbose_name_plural = u"3qdou图书资源列表"




class DouGame(models.Model):
    """
        3qdou游戏资源列表
    """
    guid = models.CharField(max_length=50, unique=True, null=False, blank=False, verbose_name=u"文件的guid标识")
    title = models.CharField(max_length=255, null=True, verbose_name=u"标题")
    sub_title = models.CharField(max_length=255, null=True, verbose_name=u"子标题")
    series_title = models.CharField(max_length=255, null=True, verbose_name=u"序列标题")
    label = models.CharField(max_length=50, null=True, verbose_name=u"标签")

    primary_responser = models.CharField(max_length=50, null=True, verbose_name=u"主要编辑")
    liability_method = models.CharField(max_length=50, null=True, verbose_name=u"责任方法")
    other_responser = models.CharField(max_length=50, null=True, verbose_name=u"其他编辑")
    other_method = models.CharField(max_length=50, null=True, verbose_name=u"其他方法")

    key_words = models.CharField(max_length=100, null=True, verbose_name=u"关键字")
    description = models.CharField(max_length=1000, null=True, verbose_name=u"简介")
    publisher = models.CharField(max_length=50, null=True, verbose_name=u"出版商")
    publish_date = models.DateTimeField(null=True, verbose_name=u"出版日期")

    page_count = models.IntegerField(default=0, verbose_name=u"总页数")
    
    width = models.SmallIntegerField(default=0, verbose_name=u"作品宽")
    height = models.SmallIntegerField(default=0, verbose_name=u"作品高")

    language = models.CharField(max_length=20, null=True, verbose_name=u"语言")
    area = models.CharField(max_length=20, null=True, verbose_name=u"区域")
    type_content = models.CharField(max_length=255, null=True, verbose_name=u"分类详情")
    fister_letter = models.CharField(max_length=10, null=True, verbose_name=u"首字字母")
    
    path = models.CharField(max_length=255, null=True, verbose_name=u"文件夹路径")
    res_path = models.CharField(max_length=255, null=True, verbose_name=u"swf文件路径")
    cover = models.CharField(max_length=255, null=True, verbose_name=u"封面")
    thumbnail = models.CharField(max_length=255, null=True, verbose_name=u"封面缩略图")
    extension = models.CharField(max_length=50, null=True, verbose_name=u"扩展信息")
    
    is_top = models.SmallIntegerField(default=0, verbose_name=u"是否加精/推荐")
    total_grade = models.BigIntegerField(default=0, verbose_name=u"总分数")
    grade_times = models.IntegerField(default=0, verbose_name=u"总评分次数")
    grade = models.FloatField(default=0, verbose_name=u"平均分数")
    preview_times = models.IntegerField(default=0, verbose_name=u"预览次数")
    comment_times = models.IntegerField(default=0, verbose_name=u"评论次数")
    praise_times = models.IntegerField(default=0, verbose_name=u"点赞次数")

    update_time = models.DateTimeField(default=datetime.now, verbose_name=u"最后修改时间")
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    status = models.SmallIntegerField(default=1, choices=((-1,u"不可用"),(0,u"待定"),(1,u"可用")), verbose_name=u"可用状态")
    
    objects = models.Manager()
    
    def __unicode__(self):
        return u"游戏:%d详细信息表" % self.id
    
    class Meta:
        db_table = "dou_game"
        verbose_name = u"3qdou游戏资源"
        verbose_name_plural = u"3qdou游戏资源列表"



class DouVideo(models.Model):
    """
        3qdou视频资源列表
    """
    guid = models.CharField(max_length=50, unique=True, null=False, blank=False, verbose_name=u"文件的guid标识")
    title = models.CharField(max_length=255, null=True, verbose_name=u"标题")
    sub_title = models.CharField(max_length=255, null=True, verbose_name=u"子标题")
    series_title = models.CharField(max_length=255, null=True, verbose_name=u"序列标题")
    label = models.CharField(max_length=50, null=True, verbose_name=u"标签")

    primary_responser = models.CharField(max_length=50, null=True, verbose_name=u"主要编辑")
    liability_method = models.CharField(max_length=50, null=True, verbose_name=u"责任方法")
    other_responser = models.CharField(max_length=50, null=True, verbose_name=u"其他编辑")
    other_method = models.CharField(max_length=50, null=True, verbose_name=u"其他方法")

    key_words = models.CharField(max_length=100, null=True, verbose_name=u"关键字")
    description = models.CharField(max_length=1000, null=True, verbose_name=u"简介")
    publisher = models.CharField(max_length=50, null=True, verbose_name=u"出版商")
    publish_date = models.DateTimeField(null=True, verbose_name=u"出版日期")

    page_count = models.IntegerField(default=0, verbose_name=u"总页数")
    
    width = models.SmallIntegerField(default=0, verbose_name=u"作品宽")
    height = models.SmallIntegerField(default=0, verbose_name=u"作品高")

    language = models.CharField(max_length=20, null=True, verbose_name=u"语言")
    area = models.CharField(max_length=20, null=True, verbose_name=u"区域")
    type_content = models.CharField(max_length=255, null=True, verbose_name=u"分类详情")
    fister_letter = models.CharField(max_length=10, null=True, verbose_name=u"首字字母")
    
    path = models.CharField(max_length=255, null=True, verbose_name=u"文件夹路径")
    res_path = models.CharField(max_length=255, null=True, verbose_name=u"swf文件路径")
    cover = models.CharField(max_length=255, null=True, verbose_name=u"封面")
    thumbnail = models.CharField(max_length=255, null=True, verbose_name=u"封面缩略图")
    extension = models.CharField(max_length=50, null=True, verbose_name=u"扩展信息")
    
    is_top = models.SmallIntegerField(default=0, verbose_name=u"是否加精/推荐")
    total_grade = models.BigIntegerField(default=0, verbose_name=u"总分数")
    grade_times = models.IntegerField(default=0, verbose_name=u"总评分次数")
    grade = models.FloatField(default=0, verbose_name=u"平均分数")
    preview_times = models.IntegerField(default=0, verbose_name=u"预览次数")
    comment_times = models.IntegerField(default=0, verbose_name=u"评论次数")
    praise_times = models.IntegerField(default=0, verbose_name=u"点赞次数")

    update_time = models.DateTimeField(default=datetime.now, verbose_name=u"最后修改时间")
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    status = models.SmallIntegerField(default=1, choices=((-1,u"不可用"),(0,u"待定"),(1,u"可用")), verbose_name=u"可用状态")
    
    objects = models.Manager()
    
    def __unicode__(self):
        return u"视频:%d详细信息表" % self.zone_asset.id
    
    class Meta:
        db_table = "dou_video"
        verbose_name = u"3qdou视频资源"
        verbose_name_plural = u"3qdou视频资源列表"


class AuthTopic(models.Model):
    """
        个人话题表
    """
    user_id = models.IntegerField(null=False, verbose_name=u"话题创建人ID")
    library_id = models.IntegerField(blank=True, null=True, verbose_name=u"所属图书馆ID")
    title = models.CharField(max_length=255, null=True, blank=True, verbose_name=u"标题")
    brief = models.CharField(max_length=1000, null=True, blank=True, verbose_name=u"摘要")
    tags = models.CharField(max_length=255, null=True, blank=True, verbose_name=u"标签")
    
    type_id = models.SmallIntegerField(default=0, choices=TOPIC_TYPE_CHOICES, verbose_name=u"话题类型的ID")
    template_id = models.SmallIntegerField(default=0, verbose_name=u"话题模板的ID")
    row_num = models.SmallIntegerField(default=0, verbose_name=u"话题标签的行数")
    col_num = models.SmallIntegerField(default=0, verbose_name=u"话题标签的列数")
    join_count = models.IntegerField(default=0, verbose_name=u"回复数量")

    
    is_top = models.SmallIntegerField(default=0, verbose_name=u"是否加精/推荐")
    width = models.SmallIntegerField(default=0, verbose_name=u"作品宽")
    height = models.SmallIntegerField(default=0, verbose_name=u"作品高")
    
    cover = models.CharField(max_length=255, null=False, blank=False, verbose_name=u"封面")
    thumbnail = models.CharField(max_length=255, null=False, blank=False, verbose_name=u"封面缩略图")
    background = models.CharField(max_length=255, null=False, blank=False, verbose_name=u"每页背景")
    
    expire_time = models.DateTimeField(verbose_name=u"截止时间")
    
    update_time = models.DateTimeField(default=datetime.now, verbose_name=u"最后修改时间")
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    status = models.SmallIntegerField(default=0, choices=((-1,u"创建失败"),(0,u"待审核"),(1,u"发表中")), verbose_name=u"可用状态")
    #新加字段
    praise = models.IntegerField(default=0, verbose_name=u"点赞个数")
    content = models.TextField(null=True, blank=True, verbose_name=u"话题内容")
    media_data = models.TextField(null=True,blank=True,verbose_name=u"多媒体信息")
    objects = models.Manager()
    
    def __unicode__(self):
        return u"个人话题"
    
    class Meta:
        db_table = "auth_topic"
        verbose_name = u"个人话题表"
        verbose_name_plural = u"个人话题列表"
        
        
class AuthTopicPage(models.Model):
    """
        个人话题每页表
    """
    user_id = models.IntegerField(null=False, verbose_name=u"说话人ID")
    library_id = models.IntegerField(blank=True, null=True, verbose_name=u"说话人所属图书馆")
    auth_topic_id = models.IntegerField(blank=False, null=False, verbose_name=u"所属话题ID")
    
    mark_id = models.IntegerField(null=False, verbose_name=u"标签ID")
    emotion_id = models.IntegerField(null=False, verbose_name=u"表情ID")
    
    content = models.CharField(max_length=255, null=True, blank=True, verbose_name=u"说话内容")
    url = models.CharField(max_length=255, null=False, blank=False, verbose_name=u"此条对应URL")
    
    page_index = models.SmallIntegerField(default=0, verbose_name=u"话题页码")
    page_order = models.SmallIntegerField(default=0, verbose_name=u"页顺序")
    
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    status = models.SmallIntegerField(default=1, choices=((-1,u"创建失败"),(0,u"待审核"),(1,u"发表中")), verbose_name=u"可用状态")
    
    objects = models.Manager()
    
    def __unicode__(self):
        return u"个人话题每页表"
    
    class Meta:
        db_table = "auth_topic_page"
        verbose_name = u"个人话题表"
        verbose_name_plural = u"个人话题列表"


        
        


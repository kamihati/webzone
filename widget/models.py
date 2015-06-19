# coding: utf-8
from datetime import datetime
from django.db import models

from account.models import AuthUser
from library.models import Library
from diy.models import AuthAsset

# Create your models here.

class WidgetOpusClassify(models.Model):
    """
        作品分类.个人创作分类
        editor: kamihati 2015/5/7  增加状态字段
        editor: kamihati 2015/6/9  增加is_sys字段用于区分是否系统分类(例如活动预告等）
    """
    classify_name = models.CharField(max_length=50, null=False, verbose_name=u"作品分类名称")
    parent_id = models.SmallIntegerField(default=0, verbose_name=u"父类ID")
    level = models.SmallIntegerField(default=1, verbose_name=u"等级")
    
    create_type = models.SmallIntegerField(default=1, choices=((1,u"单页显示"),(2,u"双页显示")), verbose_name=u"创作显示方式")
    read_type = models.SmallIntegerField(default=1, choices=((1,u"单页显示"),(2,u"双页显示")), verbose_name=u"阅读显示方式")
    status = models.SmallIntegerField(default=0, choices=((-1, u'删除'), (0, u'正常')), verbose_name=u'状态')
    is_sys = models.SmallIntegerField(default=0, choices=((0, u'普通分类'), (1, u'系统分类')), verbose_name=u'是否系统分类')

    
    objects = models.Manager()
    
    def __unicode__(self):
        return u"作品分类"
    
    class Meta:
        db_table = "widget_opus_classify"
        verbose_name = u"作品分类"
        verbose_name_plural = u"作品分类"
        
class WidgetOpusSize(models.Model):
    """
        作品画布大小表
    """
    classify_id = models.IntegerField(null=False, verbose_name=u"作品分类ID")
    size_id = models.SmallIntegerField(default=0, null=False, verbose_name=u"size id")
    
    create_type = models.SmallIntegerField(default=1, choices=((1,u"单页显示"),(2,u"双页显示")), verbose_name=u"创作显示方式")
    read_type = models.SmallIntegerField(default=1, choices=((1,u"单页显示"),(2,u"双页显示")), verbose_name=u"阅读显示方式")
    
    screen_width = models.SmallIntegerField(null=True, verbose_name=u"屏幕显示宽(px)")
    screen_height = models.SmallIntegerField(null=True, verbose_name=u"屏幕显示高(px)")
    print_width = models.FloatField(null=True, verbose_name=u"印刷宽(cm)")
    print_height = models.FloatField(null=True, verbose_name=u"印刷高(cm)")
    origin_width = models.SmallIntegerField(null=True, verbose_name=u"原图宽(px)")
    origin_height = models.SmallIntegerField(null=True, verbose_name=u"原图高(px)")
    
    objects = models.Manager()
    
    def __unicode__(self):
        return u"作品画布大小表"
    
    class Meta:
        db_table = "widget_opus_size"
        verbose_name = u"作品画布大小表"
        verbose_name_plural = u"作品画布大小表"
        
        
class WidgetPageSize(models.Model):
    """
        每页的尺寸
        editor: kamihati 2015/5/11 增加机构和用户两个字段
    """
    library_id = models.IntegerField(default=0, verbose_name=u'机构')
    user_id = models.IntegerField(default=0, verbose_name=u'添加用户')
    name = models.CharField(max_length=50, verbose_name=u"版面名称")
    
    create_type = models.SmallIntegerField(default=1, choices=((1,u"单页显示"),(2,u"双页显示"),(3,u"单双页示")), verbose_name=u"创作显示方式")
    read_type = models.SmallIntegerField(default=1, choices=((1,u"单页显示"),(2,u"双页显示"),(3,u"单双页")), verbose_name=u"阅读显示方式")
    
    screen_width = models.SmallIntegerField(null=True, verbose_name=u"屏幕显示宽(px)")
    screen_height = models.SmallIntegerField(null=True, verbose_name=u"屏幕显示高(px)")
    print_width = models.FloatField(null=True, verbose_name=u"印刷宽(cm)")
    print_height = models.FloatField(null=True, verbose_name=u"印刷高(cm)")
    origin_width = models.SmallIntegerField(null=True, verbose_name=u"原图宽(px)")
    origin_height = models.SmallIntegerField(null=True, verbose_name=u"原图高(px)")
    # 2为竖排。1为横排
    # editor: kamihati 2015/5/13
    temp_type = models.SmallIntegerField(default=1, verbose_name=u'模板类型')
    
    res_path = models.CharField(max_length=255, null=True, blank=True, verbose_name=u"原图路径")
    img_small_path = models.CharField(max_length=255, null=True, blank=True, verbose_name=u"小图路径")
    
    status = models.SmallIntegerField(default=1, choices=((0,u"待审核"), (1, u"可用"),(-1,u"已删除")), verbose_name=u"可用状态")
    add_time = models.DateTimeField(default=datetime.now(), verbose_name=u'添加时间')
    
    objects = models.Manager()
    
    def __unicode__(self):
        return u"半页画布大小"
    
    class Meta:
        db_table = "widget_page_size"
        verbose_name = u"半页画布大小表"
        verbose_name_plural = u"半页画布大小表"
                

class WidgetNotice(models.Model):
    """
        总管理员/图书馆管理员通知消息
    """
    user = models.ForeignKey(AuthUser, verbose_name=u"发消息人")
    library = models.ForeignKey(Library, null=True, blank=True, verbose_name=u"图书馆管理员")
    content = models.CharField(max_length=255, verbose_name=u"通知内容")
    read_times = models.IntegerField(default=0, verbose_name=u"阅读次数")
    
    expire_time = models.DateTimeField(default=datetime.now, verbose_name=u"过期时间")
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    status = models.SmallIntegerField(default=1, choices=((0,u"待审核"),(1,u"可用"),(-1,u"已删除")), verbose_name=u"可用状态")
    
    objects = models.Manager()
    
    def __unicode__(self):
        return u"管理员通知消息"
    
    class Meta:
        db_table = "widget_notice"
        verbose_name = u"管理员通知消息"
        verbose_name_plural = u"管理员通知消息"
        

class WidgetDistrict(models.Model):
    """
        故事大王大赛，每个省、市参选的作品数
    """
    id = models.IntegerField(null=False, primary_key=True, verbose_name=u"区域ID")
    parent_id = models.IntegerField(null=False, verbose_name=u"所属区域ID")
    name = models.CharField(max_length=30, verbose_name=u"区域名称")
    story_count = models.IntegerField(default=0, verbose_name=u"参赛作品个数")
    
    objects = models.Manager()
    
    def __unicode__(self):
        return u"区域参赛作品表"
    
    class Meta:
        db_table = "widget_district"
        verbose_name = u"区域参赛作品表"
        verbose_name_plural = u"区域参赛作品表"
        
        
class WidgetStoryUnit(models.Model):
    """
        故事大王大赛的报送单位（一般是图书馆、绘本馆）
    """
    library = models.ForeignKey(Library, null=True, blank=True, verbose_name=u"图书馆管理员")
    district_id = models.IntegerField(null=False, verbose_name=u"单位所属区域代码")
    name = models.CharField(max_length=255, verbose_name=u"单位名称")
    brief = models.CharField(max_length=500, verbose_name=u"单位简介")
    contact = models.CharField(max_length=20, verbose_name=u"联系人")
    telephone = models.CharField(max_length=20, verbose_name=u"联系电话")
    email = models.CharField(max_length=30, verbose_name=u"联系邮箱")
    story_count = models.IntegerField(default=0, verbose_name=u"参赛作品个数")
    
    update_time = models.DateTimeField(default=datetime.now, verbose_name=u"更新时间")
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    
    objects = models.Manager()
    
    def __unicode__(self):
        return u"报送单位信息"
    
    class Meta:
        db_table = "widget_story_unit"
        verbose_name = u"报送单位信息表"
        verbose_name_plural = u"报送单位信息表"
    
    
class WidgetStoryOpus(models.Model):
    """
        故事大王大赛参赛作品
    """
    library = models.ForeignKey(Library, null=True, blank=True, verbose_name=u"图书馆管理员")
    user = models.ForeignKey(AuthUser, null=False, verbose_name=u"自动新建账号")
    group_id = models.SmallIntegerField(default=0, choices=((1,u"学前组"),(2,u"小学组")), verbose_name=u"学前/小学组")
    auth_asset = models.ForeignKey(AuthAsset, null=False, verbose_name=u"个人资源ID")    
    district_id = models.IntegerField(null=False, verbose_name=u"作品所属区域代码")
    unit_id = models.IntegerField(null=False, verbose_name=u"所属报送单位代码")
    opus_id = models.IntegerField(null=True, verbose_name=u"对应作品ID")
    story_name = models.CharField(max_length=255, verbose_name=u"故事名称")
    story_brief = models.CharField(max_length=500, verbose_name=u"故事简介")
    actor_name = models.CharField(max_length=20, verbose_name=u"作者姓名")
    actor_brief = models.CharField(max_length=500, verbose_name=u"作者简介")
    sex = models.BooleanField(default=-1, choices=((0,u'女'),(1,u'男')), verbose_name=u"性别")
    age = models.SmallIntegerField(default=0, verbose_name=u'年龄')
    school_name = models.CharField(max_length=50, verbose_name=u"学校/幼儿园")
    telephone = models.CharField(max_length=20, verbose_name=u"联系电话")
    email = models.CharField(max_length=30, verbose_name=u"联系邮箱")
    
    score = models.IntegerField(default=0, verbose_name=u"裁判综合评分")
    vote = models.IntegerField(default=0, verbose_name=u"投票数")
    
    update_time = models.DateTimeField(default=datetime.now, verbose_name=u"更新时间")
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    
    objects = models.Manager()
    
    def __unicode__(self):
        return u"参赛作品"
    
    class Meta:
        db_table = "widget_story_opus"
        verbose_name = u"参赛作品表"
        verbose_name_plural = u"参赛作品表" 
        
        
class WidgetStoryVote(models.Model):
    """
        故事大王大赛参赛作品
    """
    library = models.ForeignKey(Library, null=True, blank=True, verbose_name=u"图书馆管理员")
    story_opus = models.ForeignKey(WidgetStoryOpus, null=False, verbose_name=u"投票的故事大王作品")
    user_id = models.IntegerField(null=True, verbose_name=u"投票人UID")
    #md5 = models.CharField(max_length=64, verbose_name=u"除了IP其他信息计算的MD5值")
    user_agent = models.CharField(max_length=255, verbose_name=u"投票人的user_agent")
    real_ip = models.CharField(max_length=255, verbose_name=u"ip")
    referer = models.CharField(max_length=255, verbose_name=u"REFERER")
    #accept = models.CharField(max_length=500, verbose_name=u"HTTP_ACCEPT")
    #accept_language = models.CharField(max_length=255, verbose_name=u"HTTP_ACCEPT_LANGUAGE")
    #accept_encoding = models.CharField(max_length=255, verbose_name=u"HTTP_ACCEPT_ENCODING")
    #http_cooike = models.CharField(max_length=255, verbose_name=u"HTTP_COOKIE")
    
    vote = models.IntegerField(default=0, verbose_name=u"投票数")
    
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    
    objects = models.Manager()
    
    def __unicode__(self):
        return u"故事大王比赛投票"
    
    class Meta:
        db_table = "widget_story_vote"
        verbose_name = u"故事大王比赛投票表"
        verbose_name_plural = u"故事大王比赛投票表"         

        
        
class WidgetGas(models.Model):
    """
    加油站
    新加入字段
    user library
    以备查询
    """
    user_id = models.IntegerField(default=0, verbose_name=u"发消息人")
    library_id = models.IntegerField(default=0, null=True, blank=True, verbose_name=u"图书馆")
    type_id = models.SmallIntegerField(default=0, choices=((0, u"默认"), (1,u"诗歌"), (2,u"笑话")), verbose_name=u'字条类别')
    content = models.CharField(max_length=500, verbose_name=u"内容")
    view_times = models.IntegerField(default=0, verbose_name=u"浏览次数数")
    update_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    status = models.SmallIntegerField(default=1, choices=((0,u"待审核"),(1,u"可用"),(-1,u"已删除")), verbose_name=u"可用状态")
    
    objects = models.Manager()
    
    def __unicode__(self):
        return u"加油站" % self.id
    
    class Meta:
        db_table = "widget_gas"
        verbose_name = u"加油站小字条"
        verbose_name_plural = u"加油站小字条"

class WidgetNull(models.Model):
    """
    write for null request, record the log
    """
    host = models.CharField(max_length=50, verbose_name=u"请求的HOST地址")
    user_agent = models.CharField(max_length=255, verbose_name=u"user_agent")
    real_ip = models.CharField(max_length=255, verbose_name=u"ip")
    referer = models.CharField(max_length=255, verbose_name=u"REFERER")

    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    
    objects = models.Manager()
    
    def __unicode__(self):
        return u"null请求"
    
    class Meta:
        db_table = "widget_null"
        verbose_name = u"null请求表"
        verbose_name_plural = u"null请求表"    

        
        
        
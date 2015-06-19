#coding: utf-8
from datetime import datetime
from django.db import models


class ActivityBackground(models.Model):
    '''
    活动背景信息表
    coder: kamihati 2015/4/8
    活动的背景图。背景图需要包含字体信息以及输入区域信息
    '''
    library_id = models.IntegerField(null=True, blank=True, verbose_name=u'图书馆id')
    user_id = models.IntegerField(verbose_name=u'添加人id')
    name = models.CharField(max_length=30, verbose_name=u'背景名称')
    origin_path = models.CharField(max_length=100, verbose_name=u'背景图原始文件路径')
    tag_font_style = models.CharField(max_length=30, verbose_name=u'标签字体名称')
    tag_font_color = models.CharField(max_length=20, verbose_name=u'标签文字颜色')
    tag_font_size = models.IntegerField(default=18, verbose_name=u'标签字体尺寸')
    content_font_style = models.CharField(max_length=30, verbose_name=u'正文字体名称')
    content_font_color = models.CharField(max_length=20, verbose_name=u'正文字体颜色')
    content_font_size = models.IntegerField(max_length=12, verbose_name=u'正文字体尺寸')
    # 格式为  w,h,x,y,x_w,y_h   w为图片宽度.h为图片高度。x为  起始x坐标。y为起始y坐标。x_w为从x起的像素数。y_h为y起始的像素数
    position = models.CharField(max_length=100, verbose_name=u'图片编辑区的范围')
    use_num = models.IntegerField(default=0, verbose_name=u'引用次数')
    create_time = models.DateTimeField(default=datetime.now(), verbose_name=u'创建时间')
    status = models.SmallIntegerField(default=0, choices=((0, u'正常'), (1, u'已删除')), verbose_name=u'状态')

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'activity_background'

class ActivityMember(models.Model):
    '''
    活动报名记录
    coder: kamihati 2015/4/8
    '''
    activity_id = models.IntegerField(verbose_name=u'参加的活动')
    user_id = models.IntegerField(verbose_name=u'参与人用户id')
    number = models.CharField(max_length=8, verbose_name=u'用户活动编号')
    unit_name = models.CharField(max_length=100, null=True, verbose_name=u'报送单位名称')
    join_time = models.DateTimeField(default=datetime.now(), verbose_name=u'报名时间')
    status = models.IntegerField(default=0, choices=((-1,u'已删除'), (0, u'已报名'), (1, u'已通过'), (2, u'已拒绝'), (3, u'已参加')))
    content = models.CharField(max_length=500, verbose_name=u'备注。填写删除理由等', null=True)
    realname = models.CharField(max_length=50, verbose_name=u'姓名', null=True)
    age = models.IntegerField(default=0, verbose_name=u'年龄')
    sex = models.IntegerField(default=0, verbose_name=u'性别', choices=((0, u'女'), (1, u'男')))
    school = models.CharField(null=True, max_length=100, verbose_name=u'学校')
    email = models.CharField(max_length=50, null=True, verbose_name='email')
    telephone = models.CharField(max_length=20, null=True, verbose_name=u'电话')
    address = models.CharField(max_length=200, null=True, verbose_name=u'家庭住址')
    description = models.CharField(max_length=1000, null=True, verbose_name=u'作者简介')

    def __unicode__(self):
        from account.models import AuthUser
        return AuthUser.objects.get(self.id).username

    class Meta:
        db_table = 'activity_member'
        verbose_name = u'活动报名记录'


class ActivityNews(models.Model):
    '''
    活动播报和活动结果表
    coder: kamihati 2015/4/9
    mark; 旧版本这两个内容存储在diy.models.AuthOpus表中。当作个人作品的两种类别来处理。新版本单独在这里处理并简化属性
    '''
    library_id = models.IntegerField(null=True, verbose_name=u'所属机构')
    activity_id = models.IntegerField(verbose_name=u'所属活动')
    user_id = models.IntegerField(default=0, verbose_name=u'创建人')
    news_type = models.SmallIntegerField(choices=((1, u'活动播报'), (2, u'活动结果')), verbose_name=u'类型')
    title = models.CharField(max_length=100, verbose_name=u'标题')
    background_id = models.IntegerField(verbose_name=u'使用的活动背景')
    cover = models.CharField(max_length=200, verbose_name=u'封面')
    content = models.CharField(max_length=5000, verbose_name=u'内容')
    status = models.SmallIntegerField(default=0, choices=((-1, u'删除'), (0, u'正常')), verbose_name=u'状态')
    create_time = models.DateTimeField(default=datetime.now(), verbose_name=u'创建时间')

    def __unicode__(self):
        return self.title

    class Meta:
        db_table = 'activity_news'


class ActivitySeries(models.Model):
    '''
    活动系列表
    editor: kamihati 2015/4/13
    '''
    library_id = models.IntegerField(null=True, verbose_name=u'所属机构')
    user_id = models.IntegerField(verbose_name=u'创建人id')
    title = models.CharField(max_length=40, verbose_name=u'系列名称')
    cover_path = models.CharField(max_length=100, verbose_name=u'封面图路径')
    create_time = models.DateTimeField(default=datetime.now(), verbose_name=u'创建时间')

    def __unicode__(self):
        return self.title

    class Meta:
        db_table = 'activity_series'


class ActivityList(models.Model):
    """
       活动列表
       ---------------------------------------------------------------
       editor: kamihati 2015/4/13
    """
    library_id = models.IntegerField(null=True, blank=True, verbose_name=u"图书馆ID")
    user_id = models.IntegerField(null=False, verbose_name=u"创建人ID")
    title = models.CharField(max_length=100, verbose_name=u"活动名称")
    sponsor_name = models.CharField(max_length=15, verbose_name=u"主办单位")
    # 所属系列活动id.默认为0.专题活动。否则为系列id
    series_id = models.IntegerField(default=0, verbose_name=u'所属系列活动')
    # 新增活动地点字段。0为网络活动1为现场活动
    place_type = models.CharField(max_length=10, default='net', choices=(('net', u'网络活动'), ('place', u'现场活动')), verbose_name=u'活动方式')
    #0表示全网(0.全国，只有自己一个ID时，1只是自己馆内，多个ID时，选择可参与的馆:
    scope_list = models.CharField(default="0", max_length=500, verbose_name=u"活动范围")
    # editor: kamihati 2015/4/30 原( 1,u"新闻播报"), (2,u"个人创作"), (3,u"图片"), (4,u"视频"), (5, u'特殊')
    # 现改为  ( 1,u"新闻播报"), (2,u"个人创作"), (3,u"图片"), (4,u"视频"), (5, u'特殊'), (6, u'音乐')
    #  新闻播报类型取消。但未免旧版本程序逻辑过多改动此类型id留置不用。新增6 音乐类型
    fruit_type = models.SmallIntegerField(default=0, choices=((1, u"新闻播报"), (2, u"个人创作"), (3,u"图片"),
                                                              (4, u"视频"), (5, u'特殊'), (6, u'音乐')),
                                          verbose_name=u"作品形式")
    opus_id = models.IntegerField(null=False, verbose_name=u"播报活动作品ID")

    # edtor: kamihati 2015/4/13 新增字段
    sign_up_start_time = models.DateTimeField(verbose_name=u'报名开始时间')
    sign_up_end_time = models.DateTimeField(verbose_name=u'报名截止时间')
    sign_up_member_count = models.IntegerField(default=0, verbose_name=u'当前已报名人数')
    join_member_count = models.IntegerField(default=0, verbose_name=u'参加人数')
    activity_start_time = models.DateTimeField(verbose_name=u'活动开始时间。现场活动', null=True)
    activity_end_time = models.DateTimeField(verbose_name=u'活动结束时间。现场活动', null=True)
    # 新增字段。最大报名人数.现场活动需要
    sign_up_count = models.IntegerField(default=0, verbose_name=u'最大报名人数')

    can_submit = models.SmallIntegerField(default=0, verbose_name=u"是否可以投搞")
    submit_start_time = models.DateTimeField(verbose_name=u"开始投稿时间。网络活动", null=True)
    submit_end_time = models.DateTimeField(verbose_name=u"结束投稿时间。网络活动", null=True)
    # 增加担任投稿作品数目限制
    # editor: kamihati 2015/4/30  支持用户投稿多个作品到一个活动
    submit_fruit_count = models.IntegerField(default=1, verbose_name=u'单人投稿限数')
    need_group = models.SmallIntegerField(default=0, choices=((0,u"否"),(1,u"是")), verbose_name=u"是否需要分组")
    need_unit = models.SmallIntegerField(default=0, choices=((0,u"否"),(1,u"是")), verbose_name=u"是否需要上报机构")
    need_district = models.SmallIntegerField(default=0, choices=((0,u"否"),(1,u"是")), verbose_name=u"是否需要所属区域")

    can_vote = models.SmallIntegerField(default=0, verbose_name=u"是否可以投票。网络活动")
    vote_start_time = models.DateTimeField(null=True, verbose_name=u"开始投票时间。网络活动")
    vote_end_time = models.DateTimeField(null=True, verbose_name=u"结束投票时间。网络活动")

    cover = models.CharField(max_length=255, null=True, verbose_name=u"海报")
    thumbnail = models.CharField(max_length=255, null=True, verbose_name=u"海报缩略图")

    annex = models.CharField(max_length=255, null=True, verbose_name=u'附件')

    is_top = models.SmallIntegerField(default=0, verbose_name=u"是否加精/推 荐")
    # 进行状态。新版设计中。此属性已无实际作用
    period = models.SmallIntegerField(default=0, choices=((0,u"未开始"), (1,u"进行中"), (2,u"已结束")), verbose_name=u"活动状态")

    update_time = models.DateTimeField(default=datetime.now, verbose_name=u"更新时间")
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    # editor: kamihati 2015/4/24  与牛淑倩确认。活动进行状态   为  。被删除。预告中。进行中。已结束
    status = models.SmallIntegerField(default=0, choices=((-2, u'编辑中'), (-1, u"已删除"), (0, u"预告中"), (1, u"进行中"), (2, u'已结束')), verbose_name=u"活动状态")
    # 临时添加字段。活动的海报图路径。把cover同步到此属性
    activity_img = models.CharField(max_length=100, verbose_name=u'特殊活动图片路径', null=True)
    # 临时添加字段。点击活动到达的地址  。把附件annex路径同步到此属性
    link_url = models.CharField(max_length=100, verbose_name=u'点击活动连接到的地址', null=True)
    # 新版增加字段。活动模板id
    background_id = models.IntegerField(verbose_name=u'使用的活动背景', default=0)
    # 新版增加字段。在活动背景上需要显示的标签内容
    tag = models.CharField(max_length=1000, default='', verbose_name=u'标签')
    description = models.CharField(max_length=2000, default='', verbose_name=u'活动简介')
    # 新增字段。评选方式1.投票。2线下评选。3专家评分
    vote_type = models.SmallIntegerField(default=1, choices=((1, u'投票'), (2, u'线下评选'), (3, u'专家评分')), verbose_name=u'评选方式')
    # 新增字段。投票频率1.
    vote_step = models.SmallIntegerField(default=1, choices=((1, u'每天每ip投票'), (2, u'每天每用户投票'), (3, u'每天每MAC投票')), verbose_name=u'投票频率')

    objects = models.Manager()

    def __unicode__(self):
        return u"活动列表"

    class Meta:
        db_table = "activity_list"
        verbose_name = u"活动列表"
        verbose_name_plural = u"活动列表"
        

class ActivityOption(models.Model):
    """
        网络活动投稿选项
    """
    library_id = models.IntegerField(null=True, blank=True, verbose_name=u"图书馆ID")
    activity_id = models.IntegerField(null=True, blank=True, verbose_name=u"活动ID")
    
    need_fruit_name = models.SmallIntegerField(default=1, choices=((0,u"否"),(1,u"是")), verbose_name=u"作品名称")
    need_fruit_brief = models.SmallIntegerField(default=0, choices=((0,u"否"),(1,u"是")), verbose_name=u"作品简介")
    
    need_author_name = models.SmallIntegerField(default=1, choices=((0,u"否"),(1,u"是")), verbose_name=u"作者名称")
    need_author_brief = models.SmallIntegerField(default=0, choices=((0,u"否"),(1,u"是")), verbose_name=u"作者简介")
    need_author_sex = models.SmallIntegerField(default=0, choices=((0,u"否"),(1,u"是")), verbose_name=u"选手性别")
    need_author_age = models.SmallIntegerField(default=0, choices=((0,u"否"),(1,u"是")), verbose_name=u"选手年龄")
    need_author_school = models.SmallIntegerField(default=0, choices=((0,u"否"),(1,u"是")), verbose_name=u"学校名称")
    need_author_telephone = models.SmallIntegerField(default=0, choices=((0,u"否"),(1,u"是")), verbose_name=u"电话")
    need_author_email = models.SmallIntegerField(default=0, choices=((0,u"否"),(1,u"是")), verbose_name=u"email")
    need_author_address = models.SmallIntegerField(default=0, choices=((0,u"否"),(1,u"是")), verbose_name=u'是否需要填写地址')
    need_author_business = models.SmallIntegerField(default=0, verbose_name=u'报送单位')

    update_time = models.DateTimeField(default=datetime.now, verbose_name=u"更新时间")
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")

    objects = models.Manager()
    
    def __unicode__(self):
        return u"活动的必填项"
    
    class Meta:
        db_table = "activity_option"
        verbose_name = u"活动的必填项表"
        verbose_name_plural = u"活动的必填项表"


class ActivityGroup(models.Model):
    """
        活动分组
    """
    library_id = models.IntegerField(null=True, blank=True, verbose_name=u"图书馆ID")
    activity_id = models.IntegerField(null=True, blank=True, verbose_name=u"活动ID")
    
    group_name = models.CharField(max_length=20, null=False, verbose_name=u"分组名称")
    
    update_time = models.DateTimeField(default=datetime.now, verbose_name=u"更新时间")
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    status = models.SmallIntegerField(default=0, choices=((-1, u'已删除'),(0, u'正常')), verbose_name=u'状态')
    
    objects = models.Manager()
    
    def __unicode__(self):
        return self.group_name
    
    class Meta:
        db_table = "activity_group"
        verbose_name = u"活动分组"
        verbose_name_plural = u"活动分组表"
        
        
class ActivityUnit(models.Model):
    """
       活动的报送单位（一般是图书馆、绘本馆）
       editor: kamihati 2015/5/18  由于新版设计活动作品的报送单位是直接填写名称的故此表暂无用
    """
    library_id = models.IntegerField(null=True, blank=True, verbose_name=u"图书馆ID")
    activity_id = models.IntegerField(null=True, blank=True, verbose_name=u"活动ID")
    
    district_id = models.IntegerField(null=False, verbose_name=u"单位所属区域代码")
    unit_name = models.CharField(max_length=255, verbose_name=u"单位名称")
    unit_brief = models.CharField(max_length=500, verbose_name=u"单位简介")
    unit_contact = models.CharField(max_length=20, verbose_name=u"联系人")
    unit_telephone = models.CharField(max_length=20, verbose_name=u"联系电话")
    unit_email = models.CharField(max_length=30, verbose_name=u"联系邮箱")
    fruit_count = models.IntegerField(default=0, verbose_name=u"参赛作品个数")
    
    update_time = models.DateTimeField(default=datetime.now, verbose_name=u"更新时间")
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")

    objects = models.Manager()

    def __unicode__(self):
        return self.unit_time

    class Meta:
        db_table = "activity_unit"
        verbose_name = u"活动上报单位信息表"
        verbose_name_plural = u"活动上报单位信息表"
    
    
class ActivityFruit(models.Model):
    """
        活动参赛作品
        editor: kamihati 2015/4/27  修改为新版本所用
    """
    library_id = models.IntegerField(null=True, blank=True, verbose_name=u"图书馆ID")
    activity_id = models.IntegerField(null=True, blank=True, verbose_name=u"活动ID")
    # editor: kamihati 2015/4/29  经与客户端沟通。fruit_type为5的时候当作省少儿的活动独立处理。此逻辑待优化
    fruit_type = models.SmallIntegerField(default=0, choices=((1,u"新闻播报"), (2, u"个人创作"), (3, u"图片"), (4, u"视频"), (5, u'特殊处理')), verbose_name=u"作品形式")
    # 对应AuthOpus的opus_type
    opus_type = models.SmallIntegerField(default=0, verbose_name=u"活动作品分类")
    
    user_id = models.IntegerField(null=False, verbose_name=u"资源拥有人账号ID")
    number = models.CharField(max_length=8, verbose_name=u"选编码(按活动递增)")
    group_id = models.SmallIntegerField(default=0, choices=((1,u"学前组"),(2, u"小学组")), verbose_name=u"学前/小学组")
    auth_asset_id = models.IntegerField(null=False, verbose_name=u"个人资源ID")
    district_id = models.IntegerField(null=False, verbose_name=u"作品所属区域代码")
    unit_name = models.CharField(null=True, max_length=100, verbose_name=u'报送单位名称')
    unit_id = models.IntegerField(null=False, verbose_name=u"所属报送单位代码")
    
    opus_id = models.IntegerField(null=False, verbose_name=u"原创作品ID")
    fruit_name = models.CharField(max_length=255, verbose_name=u"作品名称")
    fruit_brief = models.CharField(max_length=500, verbose_name=u"作品简介")
    author_name = models.CharField(max_length=20, verbose_name=u"作者姓名")
    author_brief = models.CharField(max_length=500, verbose_name=u"作者简介")
    author_sex = models.BooleanField(default=-1, choices=((0,u'女'),(1,u'男')), verbose_name=u"性别")
    author_age = models.SmallIntegerField(default=0, verbose_name=u'年龄')
    school_name = models.CharField(max_length=50, verbose_name=u"学校/幼儿园", null=True)
    author_telephone = models.CharField(max_length=20, verbose_name=u"联系电话", null=True)
    author_email = models.CharField(max_length=30, verbose_name=u"联系邮箱", null=True)
    author_address = models.CharField(max_length=100, verbose_name=u'联系地址', null=True)
    teacher = models.CharField(max_length=50, verbose_name=u'指导老师', null=True)

    score = models.IntegerField(default=0, verbose_name=u"裁判综合评分")
    score_brief = models.CharField(max_length=255, verbose_name=u'评分评语', null=True)
    vote = models.IntegerField(default=0, verbose_name=u"投票数")
    thumbnail = models.CharField(max_length=100, verbose_name=u'缩略图', null=True)
    
    is_top = models.SmallIntegerField(default=0, verbose_name=u"是否加精/推荐")
    total_grade = models.BigIntegerField(default=0, verbose_name=u"总分数")
    grade_times = models.IntegerField(default=0, verbose_name=u"总评分次数")
    grade = models.FloatField(default=0, verbose_name=u"平均分数")
    preview_times = models.IntegerField(default=0, verbose_name=u"预览次数")
    comment_times = models.IntegerField(default=0, verbose_name=u"评论次数")
    praise_times = models.IntegerField(default=0, verbose_name=u"点赞次数")
    
    width = models.SmallIntegerField(default=0, verbose_name=u"作品宽")
    height = models.SmallIntegerField(default=0, verbose_name=u"作品高")
    
    update_time = models.DateTimeField(default=datetime.now, verbose_name=u"更新时间")
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    # editor: kamihati 2015/6/16  (-1,u"驳回/草稿"), (0,u"待审核"), (1,u"审核中"), (2, u'已发表（审核通过）') 改为
    # (-1,u"驳回"), (0,u"草稿"), (1,u"待审核中"), (2, u'已发表（审核通过）')
    status = models.SmallIntegerField(default=0, choices=((-1, u"驳回"), (0, u"草稿"), (1, u"待审核"), (2, u'已发表（审核通过）')), verbose_name=u"发表")
    objects = models.Manager()

    def __unicode__(self):
        return u"参赛作品"
    
    class Meta:
        db_table = "activity_fruit"
        verbose_name = u"参赛作品表"
        verbose_name_plural = u"参赛作品表" 
        
        
class ActivityVote(models.Model):
    """
        活动投票
    """
    library_id = models.IntegerField(null=True, blank=True, verbose_name=u"图书馆ID")
    activity_id = models.IntegerField(null=True, blank=True, verbose_name=u"活动ID")
    fruit_id = models.IntegerField(null=False, verbose_name=u"活动作品ID")
    user_id = models.IntegerField(null=True, verbose_name=u"投票人UID")
    user_agent = models.CharField(max_length=255, verbose_name=u"投票人的user_agent")
    real_ip = models.CharField(max_length=255, verbose_name=u"ip")
    referer = models.CharField(max_length=255, verbose_name=u"REFERER")
    mac = models.CharField(max_length=25, verbose_name=u"MAC地址")
    
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    
    objects = models.Manager()
    
    def __unicode__(self):
        return u"活动投票"
    
    class Meta:
        db_table = "activity_vote"
        verbose_name = u"活动投票"
        verbose_name_plural = u"活动投票"         


class ActivityGrade(models.Model):
    """
        活动作品等级评分表
    """
    library_id = models.IntegerField(null=True, blank=True, verbose_name=u"图书馆ID")
    user_id = models.IntegerField(null=False, verbose_name=u"创建人ID")
    activity_fruit_id = models.IntegerField(null=True, blank=True, verbose_name=u"活动作品ID")
    grade = models.SmallIntegerField(default=0, verbose_name=u"评的分数")
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    
    objects = models.Manager()
    
    def __unicode__(self):
        return u"作品等级评分"
    
    class Meta:
        db_table = "activity_grade"
        verbose_name = u"活动作品等级评分"
        verbose_name_plural = u"活动作品等级评分列表"
        
class ActivityComment(models.Model):
    """
        活动作品评论表
    """
    library_id = models.IntegerField(null=True, blank=True, verbose_name=u"图书馆ID")
    user_id = models.IntegerField(null=False, verbose_name=u"创建人ID")
    activity_fruit_id = models.IntegerField(null=True, blank=True, verbose_name=u"活动作品ID")
    comment = models.CharField(max_length=500, verbose_name=u"评论内容")
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    
    objects = models.Manager()
    
    def __unicode__(self):
        return u"活动作品评论表"
    
    class Meta:
        db_table = "activity_comment"
        verbose_name = u"活动作品评论表"
        verbose_name_plural = u"活动作品评论列表"
                

class ActivityPraise(models.Model):
    """
        活动作品点赞列表
    """
    library_id = models.IntegerField(null=True, blank=True, verbose_name=u"图书馆ID")
    user_id = models.IntegerField(null=False, verbose_name=u"创建人ID")
    activity_fruit_id = models.IntegerField(null=True, blank=True, verbose_name=u"活动作品ID")
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    
    objects = models.Manager()
    
    def __unicode__(self):
        return u"活动作品点赞列表"
    
    class Meta:
        db_table = "activity_praise"
        verbose_name = u"活动作品点赞列表"
        verbose_name_plural = u"活动作品点赞列表"
        

    
        

        
        
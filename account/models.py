#coding: utf-8
'''
Created on 2014-3-24

@author: Administrator
'''
import warnings
import re
from datetime import datetime

from django.core.exceptions import ImproperlyConfigured

from django.core.mail import send_mail
from django.core import validators
from django.utils import timezone
from django.utils.http import urlquote
from django.utils.translation import ugettext_lazy as _

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

import django
if django.VERSION < (1, 7, 0):    # 兼容1.6和1.7
    from django.contrib.auth.models import SiteProfileNotAvailable
else:
    class SiteProfileNotAvailable(Exception):
        pass
from WebZone.conf import AUTH_TYPE_CHOICES
# 导入多媒体文件存储目录
from WebZone.settings import MEDIA_URL, MEDIA_ROOT

# 导入图片大中小尺寸名称变化方法
from utils import get_tile_image_name


class UserManager(BaseUserManager):

    def _create_user(self, username, password,
                     is_staff, is_superuser, **extra_fields):
        """
        Creates and saves a User with the given username, email and password.
        """
        now = timezone.now()
        if not username:
            raise ValueError('The given username must be set')
        #email = self.normalize_email(email)
        user = self.model(username=username, is_staff=is_staff, is_active=True,
                          is_superuser=is_superuser, last_login=now,
                          date_joined=now, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, password=None, **extra_fields):
        return self._create_user(username, password, False, False,
                                 **extra_fields)

    def create_superuser(self, username, password, **extra_fields):
        return self._create_user(username, password, True, True,
                                 **extra_fields)


class AuthUser(AbstractBaseUser, PermissionsMixin):
    """
    Users within the Django authentication system are represented by this
    model.

    Username, password and email are required. Other fields are optional.
    """
    username = models.CharField(_('username'), max_length=50, unique=True,
        help_text=_('Required. 30 characters or fewer. Letters, numbers and '
                    '@/./+/-/_ characters'),
        validators=[
            validators.RegexValidator(re.compile('^[\w.@+-]+$'), _('Enter a valid username.'), 'invalid')
        ])
    number = models.CharField(blank=True,null=True, max_length=8, verbose_name=u"账号编码(递增)")
    # ((0, u'普通会员'), (1, u'机构总管理员'), (2, u'机构二级管理员'), (5, u'游客会员'),(8, u'二级管理员'),  (9, u'超级管理员'), (11, u'故事大王会员'))
    auth_type = models.SmallIntegerField(_('auth type'), default=0, choices=AUTH_TYPE_CHOICES)
    library = models.ForeignKey('library.Library', blank=True, null=True, verbose_name=u"所属图书馆")
    realname = models.CharField(_('realname'), max_length=20, blank=True, null=True)
    nickname = models.CharField(_('nickname'), max_length=50, blank=True, null=True, unique=True)
    telephone = models.CharField(_('telephone number'), max_length=20, blank=True, null=True)
    qq = models.CharField(_('qq number'), max_length=20, blank=True, null=True)
    parent_qq = models.CharField(_('qq number'), max_length=20, blank=True, null=True)
    home_address = models.CharField(_('home address'), max_length=255, blank=True, null=True)
    hobby = models.CharField(_('personall hobby'), max_length=500, blank=True, null=True)
    email = models.EmailField(_('email address'), blank=True, null=True)
    sex = models.SmallIntegerField(_('sex'), default=-1, choices=((-1, u'未指定'),(0, u'女'),(1, u'男')))
    birthday = models.DateField(_('birthday'), null=True, blank=True)
    school = models.CharField(_('school name'), max_length=100, null=True, blank=True)
    sign = models.CharField(_('personal signature'), max_length=500, null=True, blank=True)
    question = models.CharField(_('security question'), max_length=100, null=True, blank=True)
    answer = models.CharField(_('security answer'), max_length=100, null=True, blank=True)
    avatar_id = models.SmallIntegerField(_('avatar id'), blank=True, null=True)
    avatar_img = models.CharField(_('avatar image url'), default="avatar.png", max_length=255, blank=True, null=True)
    is_staff = models.BooleanField(_('staff status'), default=False,
        help_text=_('Designates whether the user can log into this admin '
                    'site.'))
    is_active = models.BooleanField(_('active'), default=True,
        help_text=_('Designates whether this user should be treated as '
                    'active. Unselect this instead of deleting accounts.'))
    login_times = models.IntegerField(_('login times'), default=0)
    reg_ip = models.IPAddressField(_('user register ip address'), blank=True, null=True)
    last_ip = models.IPAddressField(_('user last login ip address'), blank=True, null=True)
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    status = models.IntegerField(default=0, choices=((-1, u'已删除'), (0, u'正常')))

    description = models.CharField(default='', verbose_name=u'简介', max_length=2000)
    age = models.IntegerField(default=0, verbose_name=u'年龄')

    objects = UserManager()

    USERNAME_FIELD = 'username'
    #REQUIRED_FIELDS = ['email']

    def __unicode__(self):
        return u"用户%s" % self.username

    class Meta:
        db_table = 'auth_user'
        verbose_name = _('user')
        verbose_name_plural = _('users')
        abstract = False

    def get_avatar_img(self, size='m', request=None):
        '''
        获取头像地址
        :return:
        '''
        avatar_path = MEDIA_URL + get_tile_image_name(self.avatar_img, size)

        if request is not None:
            host = request.get_host().lower()
            # 如果是本地环境则加上本地地址
            if host.find("10.0.0") > -1:
                import os
                if os.path.exists(os.path.join(MEDIA_ROOT, get_tile_image_name(self.avatar_img, size))):
                    avatar_path = host + avatar_path
                else:
                    avatar_path = 'http://yh.3qdou.com' + avatar_path
            #avatar_path = request.get_host().lower() + avatar_path

        return avatar_path

    def get_absolute_url(self):
        return "/users/%s/" % urlquote(self.username)

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.username, self.realname)
        return full_name.strip()

    def get_short_name(self):
        "Returns the short name for the user."
        return self.nickname

    def email_user(self, subject, message, from_email=None):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email])

    def get_profile(self):
        """
        Returns site-specific profile for this user. Raises
        SiteProfileNotAvailable if this site does not allow profiles.
        """
        warnings.warn("The use of AUTH_PROFILE_MODULE to define user profiles has been deprecated.",
            DeprecationWarning, stacklevel=2)
        if not hasattr(self, '_profile_cache'):
            from django.conf import settings
            if not getattr(settings, 'AUTH_PROFILE_MODULE', False):
                raise SiteProfileNotAvailable(
                    'You need to set AUTH_PROFILE_MODULE in your project '
                    'settings')
            try:
                app_label, model_name = settings.AUTH_PROFILE_MODULE.split('.')
            except ValueError:
                raise SiteProfileNotAvailable(
                    'app_label and model_name should be separated by a dot in '
                    'the AUTH_PROFILE_MODULE setting')
            try:
                model = models.get_model(app_label, model_name)
                if model is None:
                    raise SiteProfileNotAvailable(
                        'Unable to load the profile model, check '
                        'AUTH_PROFILE_MODULE in your project settings')
                self._profile_cache = model._default_manager.using(
                                   self._state.db).get(user__id__exact=self.id)
                self._profile_cache.user = self
            except (ImportError, ImproperlyConfigured):
                raise SiteProfileNotAvailable
        return self._profile_cache


# class AuthProfile(models.Model):
#     """
#         用户扩展信息
#     """
#     user = models.ForeignKey(AuthUser, unique=True, verbose_name=u'用户', primary_key=True)
#     notice_ids = models.CharField(max_length=500, verbose_name=u"已读通知的ＩＤ列表")
#     
#      
#     update_time = models.DateTimeField(default=datetime.now, verbose_name=u"更新时间")
#     create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
#      
#     objects = models.Manager()
#      
#     def __unicode__(self):
#         return u"用户扩展信息表"
#      
#     class Meta:
#         db_table = "auth_profile"
#         verbose_name = u"用户扩展信息表"
#         verbose_name_plural = u"用户扩展信息表"

class AuthNotice(models.Model):
    """
        用户已读通知消息ＩＤ列表
    """
    # editor: kamihati 2015/4/17 原设置 user为主键  。 现由于游客转普通用户的时候会因此报错而
    user = models.ForeignKey(AuthUser, unique=True, verbose_name=u'用户')
    notice_ids = models.CharField(max_length=500, verbose_name=u"已读通知的ＩＤ列表")
    
    update_time = models.DateTimeField(default=datetime.now, verbose_name=u"更新时间")
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    
    objects = models.Manager()
    
    def __unicode__(self):
        return u"用户已读通知消息"
    
    class Meta:
        db_table = "auth_notice"
        verbose_name = u"用户已读通知消息"
        verbose_name_plural = u"用户已读通知消息"


from WebZone.conf import AUTH_MSG_TYPE, AUTH_MSG_STATUS
class AuthMessage(models.Model):
    """
        用户个人信息，作品通过、未通过审核，被评论了，被点赞了
    """
    user = models.ForeignKey(AuthUser, blank=False, null=False, related_name="user", verbose_name=u'用户')
    from_user = models.ForeignKey(AuthUser, blank=True, null=True, related_name="from user", verbose_name=u'消息来源用户')
    opus = models.ForeignKey('diy.AuthOpus', blank=True, null=True, related_name="from opus", verbose_name=u'对应作品')
    msg_type = models.SmallIntegerField(default=0, choices=AUTH_MSG_TYPE, verbose_name=u'消息类型')
    content = models.CharField(max_length=500, verbose_name=u"消息/评论内容")
    
    status = models.SmallIntegerField(default=1, choices=AUTH_MSG_STATUS, verbose_name=u"消息状态")
    read_time = models.DateTimeField(blank=True, null=True, verbose_name=u"阅读时间")
    create_time = models.DateTimeField(default=datetime.now, verbose_name=u"创建时间")
    
    objects = models.Manager()
    
    def __unicode__(self):
        return u"用户个人信箱"
    
    class Meta:
        db_table = "auth_message"
        verbose_name = u"用户个人信箱"
        verbose_name_plural = u"用户个人信箱"


class AuthActionLog(models.Model):
    user = models.ForeignKey(AuthUser, unique=False, verbose_name=u'用户')
    library = models.ForeignKey('library.Library', blank=True, null=True, verbose_name=u"所属图书馆")
    username = models.CharField(max_length=50, null=True, blank=True, verbose_name=u'操作用户名')
    content = models.CharField(max_length=256, blank=True, null=True, verbose_name=u'内容')
    ip = models.IPAddressField(null=True, blank=True, verbose_name=u'操作IP')
    user_agent = models.CharField(max_length=255, verbose_name=u"投票人的user_agent")
    referer = models.CharField(max_length=255, verbose_name=u"REFERER")
    action_time = models.DateTimeField(default=datetime.now, verbose_name=u'时间')
    remark = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'说明')

    def __unicode__(self):
        return u"用户操作日志：%s" % self.user

    class Meta:
        db_table = 'auth_action_log'
        verbose_name = u'用户操作日志'
        verbose_name_plural = u'用户操作日志列表'


class UserPermission(models.Model):
    user_id = models.IntegerField(verbose_name=u'用户id')
    target_url = models.CharField(max_length=100, verbose_name=u'可操作的url地址')
    add_time = models.DateTimeField(default=datetime.now(), verbose_name=u'添加时间')

    objects = models.Manager()

    def __unicode__(self):
        return self.target_url

    class Meta:
        db_table = 'user_permission'
        verbose_name = u'用户权限记录'

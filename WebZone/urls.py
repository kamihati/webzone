# coding=utf8
from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

from WebZone.settings import MEDIA_ROOT, BASE_DIR

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'WebZone.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    # (r'^media/(?P<path>.*)$', 'WebZone.views.redirectm'),
    # (r'^/media/(?P<path>.*)$', 'WebZone.views.redirectm'),
    # (r'^/static/(?P<path>.*)$', 'WebZone.views.redirects'),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': MEDIA_ROOT}),
    (r'^/media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': MEDIA_ROOT}),
    # (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': STATIC_ROOT}),
    # (r'^/static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': STATIC_ROOT}),
    # mark: 暂未发现注释此配置节有何影响。待定
    # (r'^/static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': STATIC_ROOT}),
    url(r'^admin/', include(admin.site.urls)),
    # AMF Remoting Gateway
    (r'^gateway/', 'gateway.WebZoneGateway'),
    (r'^api/', include('api.urls')),
    (r'^manager/', include('manager.urls')),
    (r'^$', 'WebZone.views.index'),
    (r'^null$', 'WebZone.views.null'),
    (r'^null/$', 'WebZone.views.null'),
    (r'^3qdou_video/$', 'WebZone.views.qdou3_video'),
    (r'^3qdou_book/$', 'WebZone.views.qdou3_book'),
    (r'^3qdou_game/$', 'WebZone.views.qdou3_game'),
    (r'^online/', include('online_status.urls')),

    # 新版增加
    # 新版后台管理
    (r'^manager2/', include('manager2.urls')),
    # 新版话题模块
    (r'^topic/', include('topic.urls')),
    # 新版资源模块
    (r'^resource/', include('resources.urls')),
    # 新版活动模块
    (r'^activity/', include('activity.urls')),
    # 新版用户模块
    (r'^account/', include('account.urls')),
    # 新版机构模块
    (r'^library/', include('library.urls')),
    # 个人创作模块管理
    (r'^widget/', include('widget.urls')),
    # 导入diy模块
    (r'^diy/', include('diy.urls')),
    # 提供crossdomain.xml的文件内容
    (r'^(?P<path>.*)$', 'django.views.static.serve', {'document_root': BASE_DIR}),
)

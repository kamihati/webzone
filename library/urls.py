# coding=utf8


from django.conf.urls import patterns, include, url


urlpatterns = patterns(
    'library',
    # 获取指定机构下的活动列表
    (r'^get_ztree_library/$', 'views.get_ztree_library'),
    # 编辑机构信息
    (r'^edit/$', 'views.api_library_edit'),
    # 获取机构地区列表
    (r'^api_get_region/$', 'views.api_get_region'),
)
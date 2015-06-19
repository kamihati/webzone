#coding: utf-8
'''
Created on 2014-3-29

@author: Administrator
'''
from django.conf.urls import patterns, include, url
from django.views.decorators.cache import never_cache
from django.http import HttpResponse

@never_cache
def action(request, url):
    print url
    if not request.user or not request.user.is_staff or not url: return HttpResponse(u'没有权限访问请求的资源')
    from manager import misaction
    actionfunc = getattr(misaction, url)
    return actionfunc(request)


urlpatterns = patterns('manager',
                       url(r'^mis/(?P<url>\S*)/$', 'action'),
                       (r'^$', 'views.index'),
                       (r'^change_self_pass/$', 'views.change_self_pass'),
                       (r'^view_self_log/$', 'views.view_self_log'),
                       (r'^login/$', 'views.login'),
                       (r'^logout/$', 'views.logout'),
                       (r'^check_new_username/$', 'ajax_check.check_new_username'),
                       (r'^check_new_nickname/$', 'ajax_check.check_new_nickname'),
                       (r'^check_password/$', 'ajax_check.check_password'),
                       
                       (r'^check_curator_username/$', 'ajax_check.check_curator_username'),
                       (r'^check_auditor_username/$', 'ajax_check.check_auditor_username'),
                       (r'^check_domain/$', 'ajax_check.check_domain'),
                       (r'^check_host/$', 'ajax_check.check_host'),
                       (r'^check_lib_name/$', 'ajax_check.check_lib_name'),
                       (r'^library/$', 'views.library'),
                       (r'^lib_list/$', 'views.library_list'),
                       (r'^gas_list/$', 'views.gas_list'),
                       (r'^get_gas_list/$', 'views.get_gas_list'),
                       
                       (r'^get_opus_type_list/$', 'views.get_opus_type_list'),
                       (r'^opus_type_list/$', 'views.opus_type_list'),
                       (r'^opus_type/$', 'views.opus_type'),
                       (r'^opus_size_list/$', 'views.opus_size_list'),
                       (r'^get_opus_size/$', 'views.get_opus_size'),
                       (r'^opus_size/$', 'views.opus_size'),
                       (r'^page_size_list/$', 'views.page_size_list'),
                       (r'^page_size/$', 'views.page_size'),
                       (r'^delete_opus_size/$', 'views.delete_opus_size'),
                       (r'^delete_page_size/$', 'views.delete_page_size'),

                       (r'private_asset_detail/(\d+)','views.private_asset_detail'),
                       (r'^asset_list/$', 'views.asset_list'),
                       (r'^delete_asset/$', 'views.delete_asset'),
                       (r'^batch_upload_img/$', 'views.batch_upload_img'),
                       (r'^ajax_upload_img/$', 'views.ajax_upload_img'),
                       (r'^ajax_upload_json/$', 'views.ajax_upload_json'),
                       (r'^ajax_upload_audio/$', 'views.ajax_upload_audio'),
                       (r'^ajax_upload_video/$', 'views.ajax_upload_video'),

                       (r'^asset/$', 'views.asset'),
                       (r'^template_asset/$', 'views.template_asset'),
                       (r'^batch_asset/$', 'views.batch_asset'),
                       
                       (r'^change_user_active/$', 'views.change_user_active'),
                       (r'^reset_user_password/$', 'views.reset_user_password'),
                       
                       (r'^get_library_list/$', 'views.get_library_list'),
                       (r'^template_list/$', 'views.template_list'),
                       (r'^template/$', 'views.template'),
                       (r'^delete_template_page/$', 'views.delete_template_page'),
                       (r'^template_page/$', 'views.template_page'),
                       #(r'^login/$', 'views.login'),
                       (r'^user_list/$', 'views.user_list'),
                       (r'^auditor/$', 'views.auditor'),
                       (r'^auditor_list/$', 'views.auditor_list'),
                       (r'^notice/$', 'views.notice'),
                       (r'^notice_list/$', 'views.notice_list'),
                       (r'^opus_list/$', 'views.opus_list'),
                       (r'^opus/$', 'views.opus'),
                       (r'^top_opus/$', 'views.top_opus'),
                       (r'^audit_opus/$', 'views.audit_opus'),
                       (r'^get_opus_info/$', 'views.get_opus_info'),
                       (r'^get_opus_brief/$', 'views.get_opus_brief'),
                       (r'^opus_gallery/$', 'views.opus_gallery'),
                       (r'^opus_detail/$', 'views.opus_detail'),
                       
                       (r'^get_new_number/$', 'views_story.get_new_number'),
                       (r'^get_province_list/$', 'views_story.get_province_list'),
                       (r'^get_city_list/$', 'views_story.get_city_list'),
                       (r'^get_county_list/$', 'views_story.get_county_list'),
                       (r'^get_unit_list/$', 'views_story.get_unit_list'),
                       (r'^delete_unit/$', 'views_story.delete_unit'),
                       (r'^story_unit_list/$', 'views_story.story_unit_list'),
                       (r'^story_unit/$', 'views_story.story_unit'),
                       (r'^story_opus/$', 'views_story.story_opus'),
                       (r'^story_list/$', 'views_story.story_list'),
                       (r'^delete_story/$', 'views_story.delete_story'),
                      (r'^opus2template/$','views.opus2template'),
                      (r'^apply_for_template/$','views.apply_for_template'),
                       # 异步上传文件
                       # editor: kamihati 2015/5/7
                       (r'^ajax_upload_file/$', 'views.ajax_upload_file'),
)







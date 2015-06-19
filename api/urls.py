#coding: utf-8
'''
Created on 2014-3-26

@author: Administrator
'''

from django.conf.urls import patterns, include, url

urlpatterns = patterns('api',
                       #(r'^update_avatar/$', 'views.update_avatar'),
                       (r'^test/$', 'views.test'),
                       (r'^test_done/$', 'views.test_done'),
                       (r'^upload_personal_res/$', 'views.upload_personal_res'),
                       (r'^get_font_img/$', 'views_test.get_font_img'),
                       (r'^vote/$', 'views_test.vote'),
                       (r'^gas_station/$', 'views.gas_station'),
                       (r'^vote_test/$', 'views_test.vote_test'),
                       )
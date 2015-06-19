#coding: utf-8
'''
Created on 2014-3-24

@author: Administrator
'''
from django.contrib import admin
from django.core.exceptions import PermissionDenied

from account.models import AuthUser
# Register your models here.

class AuthUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'nickname', 'realname', 'email', 'telephone')
    search_fields = ['=username']
    list_filter = ('auth_type', 'is_active')
    raw_id_fields = ('library',)
    
    def save_model(self, request, obj, form, change):
        if request.user.is_staff:
            obj.save()
        else:
            raise PermissionDenied

admin.site.register(AuthUser, AuthUserAdmin)
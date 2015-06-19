#coding: utf-8
from django.contrib import admin
from django.core.exceptions import PermissionDenied

from library.models import Library
# Register your models here.

class LibraryAdmin(admin.ModelAdmin):
    list_display = ('user','domain', 'lib_name', 'lib_address', 'host', 'create_time')
    search_fields = ['=username']
    list_filter = ('domain', 'lib_name')
    #raw_id_fields = ('user',)
    
    def save_model(self, request, obj, form, change):
        if request.user.is_staff:
            obj.save()
        else:
            raise PermissionDenied

admin.site.register(Library, LibraryAdmin)
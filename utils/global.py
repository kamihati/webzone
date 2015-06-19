#coding: utf-8
'''
Created on 2014-7-1

@author: Administrator
'''
from library.models import Library
from manager import MANAGER_PERMS

def siteinfo(request):
    host = request.get_host()
    try:
        library = Library.objects.get(host=host)
        site_name = library.lib_name
    except: site_name = u"本地测试图书馆"
    
    full_path = request.get_full_path()
    #print full_path
    perm_code = ""
    group_name = ""
    #perm_code = "s_role_m"
    group_name = u"系统管理"
    is_find = False
    for perms in MANAGER_PERMS:
        if perms['url'] in full_path:
            perm_code = perms['code']
            group_name = perms['group']
            is_find = True
            #break
    if not is_find:
        pass
    return {'site_name':site_name, 'perm_code':perm_code, 'group_name':group_name}



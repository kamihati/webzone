#coding: utf-8
from django.db import connection, connections
from WebZone.settings import DB_READ_NAME
from django.http import HttpResponse
from django.views.decorators.cache import never_cache

MANAGER_GROUP = {1:u"系统管理",
                 2:u"会员管理",
                 3:u"学习平台管理",
                 4:u"创作平台管理",
                 5:u"活动管理",
                 }

'''
权限代码模式：所属组_对象_操作
'''
MANAGER_PERMS = ({'code':'s_role_m', 'url':'/manager/mis/s_role_m/', 'group':u"系统管理", 'sub_group':None, 'name':u'角色管理', 'show':1},
                 {'code':'s_role_m', 'url':'/manager/mis/get_role_list/', 'group':u"系统管理", 'sub_group':None, 'show':0}, #超级管理员接口
                 
                 {'code':'s_auth_m', 'url':'/manager/mis/can_role_list/', 'group':u"系统管理", 'sub_group':None, 'show':0}, #普通管理员添加管理下属管理员
                 {'code':'s_auth_m', 'url':'/manager/mis/s_auth_m/', 'group':u"系统管理", 'sub_group':None, 'name':u'权限管理', 'show':1},
                 {'code':'s_auth_m', 'url':'/manager/mis/s_auth_a/', 'group':u"系统管理", 'sub_group':None, 'show':0},  #添加、修改管理员信息
                 {'code':'s_auth_m', 'url':'/manager/mis/s_auth_pass/', 'group':u"系统管理", 'sub_group':None, 'show':0},  #添加、修改管理员信息
                 
                 {'code':'s_lib_m', 'url':'/manager/lib_list/', 'group':u"系统管理", 'sub_group':None, 'name':u'图书馆/机构管理', 'show':1},
                 {'code':'s_lib_m', 'url':'/manager/library/', 'group':u"系统管理", 'sub_group':None, 'show':0},
                 {'code':'s_gas_m', 'url':'/manager/gas_list/', 'group':u"系统管理", 'sub_group':None, 'name':u'加油站管理', 'show':1},
                 
                 {'code':'s_log_user', 'url':'/manager/mis/s_log_user/', 'group':u"系统管理", 'sub_group':u'日志统计', 'name':u'用户日志', 'show':1},
                 {'code':'s_log_manager', 'url':'/manager/mis/s_log_manager/', 'group':u"系统管理", 'sub_group':u'日志统计', 'name':u'管理员日志', 'show':1},
                 {'code':'s_msg_sys', 'url':'/manager/mis/s_msg_sys/', 'group':u"系统管理", 'sub_group':u'消息管理', 'name':u'系统消息', 'show':1},
                 {'code':'s_a_notice', 'url':'/manager/notice_list/', 'group':u"系统管理", 'sub_group':u'消息管理', 'name':u'活动公告', 'show':1},
                 {'code':'s_a_notice', 'url':'/manager/notice/', 'group':u"系统管理", 'sub_group':u'消息管理', 'show':0},
                 {'code':'s_opus_c', 'url':'/manager/mis/s_opus_c/', 'group':u"系统管理", 'sub_group':u'消息管理', 'name':u'作品评论', 'show':1},
                 {'code':'s_msg_friend', 'url':'/manager/mis/s_msg_friend/', 'group':u"系统管理", 'sub_group':u'消息管理', 'name':u'好友留言', 'show':1},
                 
                 {'code':'m_user_l', 'url':'/manager/user_list/', 'group':u"会员管理", 'sub_group':None, 'name':u'会员列表', 'show':1},
                 
                 {'code':'l_res_list', 'url':'/manager/mis/l_res_list/', 'group':u"学习平台管理", 'sub_group':None, 'name':u'资源分类列表', 'show':1},
                 {'code':'l_auth_list', 'url':'/manager/mis/l_auth_list/', 'group':u"学习平台管理", 'sub_group':None, 'name':u'得到图书馆资源权限', 'show':0},
                 {'code':'l_invite_code', 'url':'/manager/mis/l_invite_code/', 'group':u"学习平台管理", 'sub_group':None, 'name':u'邀请码管理', 'show':1},
                 {'code':'l_ip_c', 'url':'/manager/mis/l_ip_c/', 'group':u"学习平台管理", 'sub_group':None, 'name':u'ip地址控制', 'show':1},
                 
                 {'code':'c_opus_type', 'url':'/manager/opus_type/', 'group':u"创作平台管理", 'sub_group':None, 'name':u'作品分类管理', 'show':1},
                 {'code':'c_opus_size', 'url':'/manager/page_size/', 'group':u"创作平台管理", 'sub_group':None, 'name':u'作品尺寸管理', 'show':1},
                 {'code':'c_asset_b', 'url':'/manager/batch_asset/', 'group':u"创作平台管理", 'sub_group':None, 'name':u'批量上传素材管理', 'show':1},
                 {'code':'c_asset_list', 'url':'/manager/asset_list/', 'group':u"创作平台管理", 'sub_group':None, 'name':u'公共素材管理', 'show':1},
                 {'code':'c_asset_list', 'url':'/manager/asset/', 'group':u"创作平台管理", 'sub_group':None, 'show':0},
                 
                 {'code':'c_template_list', 'url':'/manager/template_list/', 'group':u"创作平台管理", 'sub_group':None, 'name':u'模板管理', 'show':1},
                 {'code':'c_template_list', 'url':'/manager/template/', 'group':u"创作平台管理", 'sub_group':None, 'name':u'模板', 'show':0},
                 {'code':'c_template_list', 'url':'/manager/template_page/', 'group':u"创作平台管理", 'sub_group':None, 'name':u'模板页', 'show':0},
                 {'code':'c_template_list', 'url':'/manager/template_asset/', 'group':u"创作平台管理", 'sub_group':None, 'name':u'模板详情', 'show':0},
                 {'code':'c_opus2template', 'url':'/manager/opus2template/', 'group':u"创作平台管理", 'sub_group':None, 'name':u'作品转为模板', 'show':1},
                 
                 {'code':'c_private_asset', 'url':'/manager/mis/c_private_asset/', 'group':u"创作平台管理", 'sub_group':None, 'name':u'私有素材管理', 'show':1},
                 
                 
                 {'code':'c_opus_1', 'url':'/manager/opus_list/', 'group':u"创作平台管理", 'sub_group':u'作品管理', 'name':u'待审核作品列表', 'show':1},
                 {'code':'c_opus_2', 'url':'/manager/opus_list/?status=2', 'group':u"创作平台管理", 'sub_group':u'作品管理', 'name':u'已出版作品列表', 'show':1},
                 #{'code':'c_opus_3', 'url':'/manager/mis/c_opus_3/', 'group':u"创作平台管理", 'sub_group':u'作品管理', 'name':u'私密作品列表', 'show':1},
                 {'code':'c_opus_0', 'url':'/manager/opus_list/?status=0', 'group':u"创作平台管理", 'sub_group':u'作品管理', 'name':u'作品草稿列表', 'show':1},
                 
                 {'code':'topic_mark', 'url':'/manager/mis/topic_mark/', 'group':u"话题", 'sub_group':None, 'name':u'标签', 'show':1},
                 {'code':'topic_mark', 'url':'/manager/mis/topic_mark_list/', 'group':u"话题", 'sub_group':None, 'name':u'标签列表', 'show':0},
                 {'code':'topic_emotion', 'url':'/manager/mis/topic_emotion/', 'group':u"话题", 'sub_group':None, 'name':u'表情', 'show':1},
                 {'code':'topic_emotion', 'url':'/manager/mis/get_emotion_type_list/', 'group':u"话题", 'sub_group':None, 'name':u'表情分类列表', 'show':0},
                 {'code':'topic_emotion', 'url':'/manager/mis/topic_emotion_list/', 'group':u"话题", 'sub_group':None, 'name':u'表情列表', 'show':0},
                 {'code':'topic_template', 'url':'/manager/mis/topic_template/', 'group':u"话题", 'sub_group':None, 'name':u'话题模板', 'show':1},
                 {'code':'topic_template', 'url':'/manager/mis/topic_template_list/', 'group':u"话题", 'sub_group':None, 'name':u'话题模板', 'show':0},
                 {'code':'topic_list', 'url':'/manager/mis/topic_list/', 'group':u"话题", 'sub_group':None, 'name':u'话题列表', 'show':1},
                 
                 {'code':'a_story_unit', 'url':'/manager/story_unit/', 'group':u"活动管理", 'sub_group':u'故事达人', 'name':u'报送单位管理', 'show':1},
                 {'code':'a_story_list', 'url':'/manager/story_list/', 'group':u"活动管理", 'sub_group':u'故事达人', 'name':u'选手作品管理', 'show':1},
                 {'code':'a_story_list', 'url':'/manager/story_opus/', 'group':u"活动管理", 'sub_group':u'故事达人', 'show':0},
                 )

def get_perms_json(request):
    '''
    generate json data for ztree control
    '''
    from itertools import groupby
    perms = [p for p in MANAGER_PERMS if p['show']==1]
    
    ztree_json = []
    #ztree_json.append({"id":0, "pId":-1, "name":u"所有权限", "open":True})
    group_id = 1
    for k, v in groupby(perms, lambda x: x['group']):
        ztree_json.append({"id":group_id, "pId":0, "name":k, "open":True})
        sub_group_id = 1
        for m, n in groupby(v, lambda x: x['sub_group']):
            new_subid = "%d%d" % (group_id, sub_group_id)
            if m <> None:
                ztree_json.append({"id":new_subid, "pId":group_id, "name":m, "open":False})
                sub_group_id += 1
            for i in n:
                if m == None:
                    ztree_json.append({"id":i['code'], "pId":group_id, "name":i['name'], "checked":False})
                else:
                    ztree_json.append({"id":i['code'], "pId":new_subid, "name":i['name'], "checked":False})
        group_id += 1
    import json
    return json.dumps(ztree_json)
    
def has_permissions(request, code):
    '''验证是否具有操作权限'''
    if not request.user or not request.user.is_staff:
        return False
    if not request.session.get('manager_login', False) or not request.user.is_active:
        return False
    if request.user.is_superuser: return True
    if code == "": return True
    if not request.session.get('mgr_perms', None): return False
    perms = request.session['mgr_perms']
    return code in perms

def get_permissions(request, delsession=False):
    if delsession or not request.user or not request.user.is_staff:
        try: del request.session['mgr_perms']
        except: pass
        return None
    perms = []
    if request.user.is_superuser:
        for p in MANAGER_PERMS:
            perms.append(p['code'])
    else:
        cursor = connections[DB_READ_NAME].cursor()
        cursor.execute('SELECT g.perms FROM manager_auth_group AS g INNER JOIN manager_user_group AS u ON u.group_id=g.id WHERE u.user_id=%s', [request.user.id])
        row = cursor.fetchone()
        perms = []
        while row:
            for p in row[0].split(','):
                perms.append(p)
            row = cursor.fetchone()
        cursor.close()
    request.session['mgr_perms'] = perms
    return perms


def update_group_perms(request, delsession=False):
    '''
    return all perms list order by group
    '''
    if delsession or not request.user or not request.user.is_staff:
        try: del request.session['gperms']
        except: pass
    else:
        gperms = []
        if not request.user or not request.user.is_staff:
            return gperms
        perms = get_permissions(request)
        if perms:
            from itertools import groupby
            perms = [p for p in MANAGER_PERMS if p['code'] in perms and p['show']==1]
            for k, v in groupby(perms, lambda x: x['group']):
                items = []
                for m, n in groupby(v, lambda x: x['sub_group']):
                    sub_items = []
                    for i in n:
                        sub_items.append({'name':i['name'], 'code':i['code'], 'url':i['url']})
                    items.append({'group':m, 'items':sub_items})
                gperms.append({'group':k, 'items':items})
        request.session['gperms'] = gperms

def update_top_perms(request, delsession=False):
    '''
    return manager top navigation menu,url...
    '''
    if delsession or not request.user or not request.user.is_staff:
        try: del request.session['tperms']
        except: pass
    else:
        tperms = []
        perms = get_permissions(request)
        if perms:
            from itertools import groupby
            perms = [p for p in MANAGER_PERMS if p['code'] in perms and p['show']==1]
            for k, v in groupby(perms, lambda x: x['group']):
                tperms.append({'group':k, 'url':v.next()['url']})
        request.session['tperms'] = tperms

def add_manager_action_log(request, content):
    '''
        记录管理员的操作记录
    '''
    from manager.models import ManagerActionLog
    from utils import get_ip
    ManagerActionLog(user=request.user, username=request.user.username, library=request.user.library, ip=get_ip(request), content=content).save()

    

@never_cache
def action(request, url):
    perm_code = get_perm_code(request)
    if not has_permissions(request, perm_code):
        from utils.decorator import CustomRedirect
        from django.utils.http import urlquote
        from WebZone.settings import REDIRECT_FIELD_NAME
        login_url = "/manager/login/"
        redirect_field_name = REDIRECT_FIELD_NAME
        path = urlquote(request.get_full_path())
        tup = login_url, redirect_field_name, path
        return CustomRedirect(request, '%s?%s=%s' % tup)
    from manager import misaction
    actionfunc = getattr(misaction, url)
    return actionfunc(request)


def get_perm_code(request):
    full_path = request.get_full_path()
    perm_code = ""
    for perms in MANAGER_PERMS:
        if perms['url'] in full_path:
            perm_code = perms['code']
    return perm_code







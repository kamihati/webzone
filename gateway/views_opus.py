#coding: utf-8
'''
Created on 2014-4-14

@author: Administrator
'''
import os
from math import ceil
import shutil
from datetime import datetime
from django.db import connection, connections
from WebZone.settings import DB_READ_NAME

from django.core.cache import cache

from PIL import Image
from StringIO import StringIO

from WebZone.conf import ALLOWED_IMG_EXTENSION, ALLOWED_IMG_UPLOAD_SIZE

from WebZone.settings import MEDIA_ROOT, MEDIA_URL

from utils import fmt_str as F
from utils import get_lib_path
from utils import get_user_path
from utils import get_new_filename, get_tile_image_name, get_img_ext
from utils import idlist2dict
from utils.decorator import login_required
from utils import get_small_size
from utils import get_lib_name
# 导入打印异常的方法
from utils.decorator import print_trace

from diy.models import AuthAsset, ZoneAsset, ZoneAssetTemplate
from diy.models import AuthAssetRef, ZoneAssetRef
from diy.models import AuthOpus, AuthOpusGrade, AuthOpusComment
from diy.models import AuthOpusPraise
from diy.models import AuthOpusPage
# 导入获取当前机构的方法
from library.handler import get_library_by_request
from gateway import SuccessResponse, FailResponse

from account.models import AuthMessage
from widget.models import WidgetOpusClassify

from account.models import AuthUser
from activity.models import ActivityList, ActivityFruit
# 导入获取相对路径实际url的方法
from utils.decorator import get_host_file_url

#新建、删除、更新作品页时，锁的最长时间
OPUS_LOCK_TIME  =60 * 2


def get_opus_cover_img(auth_opus_id):
    """
        得到作品的封面图片路径(第一页缩略图的路径)
        有可能没有第一页，需要注意考虑这种情况
    """
    try:
        auth_opus_page = AuthOpusPage.objects.get(auth_opus_id=auth_opus_id, page_index=1)
        return auth_opus_page.img_path, auth_opus_page.img_small_path
    except: return "", ""

def check_opus_type(type_id, class_id):
    """
        检查作品的类型，子分类是否正确
    """
    cache_type_key = "gateway.check_opus_type"
    cache_class_key = "gateway.check_opus_type.%s" % type_id
    type_id_list = cache.get(cache_type_key, None)
    class_id_list = cache.get(cache_class_key, None)
    if not type_id_list:
        type_id_list = []
        for e in WidgetOpusClassify.objects.filter(level=1):
            type_id_list.append(e.id)
    if not class_id_list:
        class_id_list = []
        for e in WidgetOpusClassify.objects.filter(parent_id=type_id):
            class_id_list.append(e.id)
            
    if type_id != 0 and type_id not in type_id_list:
        return u"作品类型:%d不正确" % type_id
    #if class_id not in (0, 100, 200, 300) and class_id not in class_id_list:
    #    return u"作品子类型:%d不正确" % class_id
    return "ok"


@print_trace
@login_required
def get_press_list(request, type_id=0, page_index=1, page_size=20, key=''):
    """
        得到首页推荐、热门、最新已发表的作品列表
        editor: kamihati 2015/4/27  更改key的搜索范围为作品。作者。机构名称。作品简介
    """
    where_clause = "a.opus_type=0 and a.status=2"   #个有作品
    if key != '' and key is not None:
        where_clause += ' AND (a.title LIKE \'%' + key + '%\' OR a.brief LIKE \'%' + key + '%\' OR b.nickname LIKE  \'%' + key + '%\' OR c.lib_name LIKE  \'%' + key + '%\')'
    # editor: kamihati 2015/6/2 原创乐园没有必要限制机构信息
    # library = get_library_by_request(request)
    # if library is not None:
    #    if library.is_global == 1:
    #        pass
    #    else:
    #        where_clause += " and a.library_id in (null,%d)" % library.id
    # else:
    #    where_clause += " and a.library_id is null"
    order_by = "a.update_time desc"
    if type_id > 0:
        where_clause += " and a.type_id=%d" % type_id
    elif type_id == 0:  #推荐作品列表
        where_clause += " and a.is_top=1"
    elif type_id == -1:  #热门作品列表
        order_by = "a.preview_times desc"
    elif type_id == -2:  #最新作品列表
        pass
    elif type_id == -3:  #不对type进行处理
        pass
    #print where_clause
    cursor = connections[DB_READ_NAME].cursor()
    sql = "select count(a.id) from auth_opus a "
    sql += " INNER JOIN auth_user b ON b.id=a.user_id LEFT JOIN library c ON c.id=a.library_id "
    sql += "where %s" % where_clause
    cursor.execute(sql)
    row = cursor.fetchone()
    count = 0
    if row: count = row[0]
    page_count = int(ceil(count/float(page_size)))
    
    sql = "select a.id,a.title,a.brief,a.tags,a.type_id,a.thumbnail,a.show_type,a.create_type,a.read_type,a.library_id,a.activity_id,a.opus_type,b.nickname,c.lib_name"
    sql += " from auth_opus a "
    sql += " INNER JOIN auth_user b ON b.id=a.user_id LEFT JOIN library c ON c.id=a.library_id"
    sql += " where %s order by %s LIMIT %s, %s" % (where_clause, order_by, (page_index-1)*page_size, page_size)
    cursor.execute(sql)
    rows = cursor.fetchall()
    opus_lists = []
    for row in rows:
        if not row: continue
        opus_dict = {}
        opus_dict["id"] = row[0]
        opus_dict["title"] = row[1] if row[1] else u"未命名作品"
        opus_dict["brief"] = row[2]
        opus_dict["tags"] = row[3]
        opus_dict["type_id"] = row[4]
        if row[5]:
            opus_dict["thumbnail"] = MEDIA_URL + row[5]
        else:
            thumbnail_path = get_opus_cover_img(opus_dict["id"])[1]    #第一页缩略图当封面
            if thumbnail_path:
                opus_dict["thumbnail"] = MEDIA_URL + thumbnail_path
            else:
                opus_dict["thumbnail"] = ""
        opus_dict["show_type"] = row[6]
        opus_dict["create_type"] = row[7]
        opus_dict["read_type"] = row[8]

        lib_id = int(row[9]) if row[9] else 0
        opus_dict["lib_name"] = get_lib_name(lib_id)
        
        opus_dict["activity_id"] = int(row[10])
        #((0,u"个人作品"),(1,u"活动播报"),(2,u"个人参赛作品"),(3,u"活动预告"),(4,u"活动结果")
        opus_dict["opus_type"] = int(row[11])
        opus_lists.append(opus_dict)
    return SuccessResponse({"data":opus_lists, "page_index": page_index, "page_count": page_count})


#@login_required
def get_opus_list(request, param):
    """
        editor: kamihati 2015/6/15  获取创作列表。 修改参数方式修改为数据字典。
    """
    type_id = param['type_id'] if param.has_key('type_id') else ''
    class_id = int(param['class_id']) if param.has_key('class_id') else 0
    page_index = int(param['page_index']) if param.has_key('page_index') else 0
    page_size = int(param['page_size']) if param.has_key('page_size') else 20

    from diy.auth_opus_handler import get_opus_pager
    data_list, data_count = get_opus_pager(
        page_index, page_size, type_id=type_id, class_id=class_id, user_id=request.user.id)

    for data in data_list:
        if not data['title']:
            data['title'] = u'未命名作品'
        if data['thumbnail']:
            data['thumbnail'] = MEDIA_URL + data['thumbnail']
        else:
            thumbnail_path = get_opus_cover_img(data["id"])[1]    #第一页缩略图当封面
            if thumbnail_path:
                #opus_dict["thumbnail"] = request.build_absolute_uri(MEDIA_URL + thumbnail_path)
                data["thumbnail"] = MEDIA_URL + thumbnail_path
            else:
                data["thumbnail"] = ""
        lib_id = int(data['library_id']) if data['library_id'] else 0
        data["lib_name"] = get_lib_name(lib_id)
    return SuccessResponse(
        {"data": data_list, "page_index": page_index, "page_size": page_size, 'data_count': data_count})


@login_required
def view_opus(request, opus_id):    #浏览作品，需要浏览次数加１
    try: auth_opus = AuthOpus.objects.get(id=opus_id)
    except(AuthOpus.DoesNotExist): return FailResponse(u"不存在的作品ID:%d" % opus_id)
    
    if (request.user.is_staff or request.user.is_superuser) and auth_opus.status not in (2, 11):
        #管理员审核作品时，不要浏览次数加1
        return SuccessResponse(opus_info(auth_opus))
    elif request.user.id == auth_opus.user_id and auth_opus.status not in (2, 11):
        #自己看自己未发表的作品，不要浏览次数加1
        return SuccessResponse(opus_info(auth_opus))
    
    if auth_opus.status not in (2, 11):
        return FailResponse(u"只有发表状态的作品，才能浏览")
    
    #auth_opus.preview_times += 1
    #auth_opus.save()
    sql = "update auth_opus set preview_times=preview_times+1 where id=%d" % auth_opus.id
    connection.cursor().execute(sql)

    return SuccessResponse(opus_info(auth_opus))


def get_opus_info(request, opus_id):
    '''
    获取指定的个人作品
    editor: kamihati 2015/6/18 改变activity_id的获取逻辑。从activity_fruit获取最近的一条
    :param request:
    :param opus_id:
    :return:
    '''

    try: auth_opus = AuthOpus.objects.get(id=opus_id)
    except(AuthOpus.DoesNotExist): return FailResponse(u"不存在的作品ID:%d" % opus_id)
    '''
    if request.user.auth_type in (1,2): #图书馆长，审核员
        if request.user.library_id <> auth_opus.library_id:
            return FailResponse(u"只能审核自己图书馆的作品")
    elif auth_opus.user_id <> request.user.id:
        pass
        #return FailResponse(u"不是自己的作品")
    '''
    result = opus_info(auth_opus)
    result['cover'] = get_host_file_url(request, result['cover'])
    result['thumbnail'] = get_host_file_url(request, result['thumbnail'])
    return SuccessResponse(result)


def opus_info(auth_opus):
    opus_info = dict()
    opus_info["id"] = auth_opus.id
    opus_info["user_id"] = auth_opus.user_id
    opus_info["title"] = auth_opus.title if auth_opus.title else u"未命名作品"
    opus_info["brief"] = F(auth_opus.brief)
    opus_info["tags"] = F(auth_opus.tags)
    from diy.auth_opus_handler import get_opus_activity_id
    opus_info["activity_id"] = get_opus_activity_id(auth_opus.id)
    opus_info["opus_type"] = auth_opus.opus_type
    
    opus_info["create_type"] = auth_opus.create_type
    opus_info["read_type"] = auth_opus.read_type
    
    opus_info["type_id"] = auth_opus.type_id
    opus_info["class_id"] = auth_opus.class_id
    opus_info["page_count"] = auth_opus.page_count
    opus_info["pages"] = opus_pages(auth_opus)
    
    opus_info["is_top"] = auth_opus.is_top
    opus_info["grade"] = auth_opus.grade   #评分
    
    opus_info["preview_times"] = auth_opus.preview_times
    opus_info["comment_times"] = auth_opus.comment_times
    opus_info["praise_times"] = auth_opus.praise_times
    opus_info["update_time"] = auth_opus.update_time.strftime("%Y-%m-%d %H:%M:%S")
    opus_info["create_time"] = auth_opus.create_time.strftime("%Y-%m-%d %H:%M:%S")
    opus_info["status"] = auth_opus.status
    
    opus_info["width"] = auth_opus.width
    opus_info["height"] = auth_opus.height
    
    if auth_opus.cover:
        #opus_info["cover"] = request.build_absolute_uri(MEDIA_URL + auth_opus.cover)
        #opus_info["thumbnail"] = request.build_absolute_uri(MEDIA_URL + auth_opus.thumbnail)
        opus_info["cover"] = MEDIA_URL + auth_opus.cover
        opus_info["thumbnail"] = MEDIA_URL + auth_opus.thumbnail
    else:
        if auth_opus.page_count == 0:
            opus_info["cover"] = ""
            opus_info["thumbnail"] = ""
        else:
            opus_info["cover"], opus_info["thumbnail"] = get_opus_cover_img(auth_opus.id)
            #opus_info["cover"] = request.build_absolute_uri(MEDIA_URL + cover)
            #opus_info["thumbnail"] = request.build_absolute_uri(MEDIA_URL + thumbnail)
            if opus_info["cover"]: opus_info["cover"] = MEDIA_URL + opus_info["cover"]
            if opus_info["thumbnail"]: opus_info["thumbnail"] = MEDIA_URL + opus_info["thumbnail"]
    return opus_info


def opus_pages(auth_opus):
    pages = []
    query_set = AuthOpusPage.objects.filter(auth_opus_id=auth_opus.id).order_by("page_index")
    if auth_opus.page_count <> len(query_set):
        print "opus_pages:error1"
    
    for opus_page in query_set:
        if not os.path.isfile(os.path.join(MEDIA_ROOT, opus_page.json_path)):
            print "opus_pages:error2"
        page_dict = {"page_index":opus_page.page_index}
        page_dict["media"] = opus_page.is_multimedia
        page_dict["orign"] = MEDIA_URL + opus_page.img_path
        page_dict["small"] = MEDIA_URL + opus_page.img_small_path
        page_dict["json"] = MEDIA_URL + opus_page.json_path
        pages.append(page_dict)
    
    return pages


# @login_required
# def get_opus_page_image(request, opus_id, page_index=1):
#     try: auth_opus = AuthOpus.objects.get(id=opus_id)
#     except(AuthOpus.DoesNotExist): return FailResponse(u"不存在的作品ID:%d" % opus_id)
#     
#     if auth_opus.user_id <> request.user.id:
#         return FailResponse(u"不是自己的作品")
#     
#     if page_index > auth_opus.page_count:
#         return FailResponse(u"作品总页数为:%d，没有第%d页" % (auth_opus.page_count, page_index))
#     
#     try: auth_opus_page = AuthOpusPage.objects.get(auth_opus_id=opus_id, page_index=page_index)
#     except(AuthOpusPage.DoesNotExist):
#         return FailResponse(u"当前页不存在")
#     
#     if not os.path.isfile(os.path.join(MEDIA_ROOT, auth_opus_page.img_path)):
#         return FailResponse(u"当前页的图片文件不存在")
#     
#     return SuccessResponse({#"id":auth_opus.id,
#                             "page_index": page_index,
#                             "orign":request.build_absolute_uri(MEDIA_URL + auth_opus_page.img_path),
#                             "small":request.build_absolute_uri(MEDIA_URL + auth_opus_page.img_small_path)})
#     
# 
# @login_required
# def get_opus_page_json(request, opus_id, page_index=1):
#     """
#     """
#     try: auth_opus = AuthOpus.objects.get(id=opus_id)
#     except(AuthOpus.DoesNotExist): return FailResponse(u"不存在的作品ID:%d" % opus_id)
#     
#     if auth_opus.user_id <> request.user.id:
#         return FailResponse(u"不是自己的作品")
#     
#     if page_index > auth_opus.page_count:
#         return FailResponse(u"作品总页数为:%d，没有第%d页" % (auth_opus.page_count, page_index))
#     
#     try: auth_opus_page = AuthOpusPage.objects.get(auth_opus_id=opus_id, page_index=page_index)
#     except(AuthOpusPage.DoesNotExist):
#         return FailResponse(u"当前页不存在")
#     
#     if not os.path.isfile(os.path.join(MEDIA_ROOT, auth_opus_page.json_path)):
#         return FailResponse(u"当前页的配置文件不存在")
#     
#     return SuccessResponse({#"id":auth_opus.id,
#                             "page_index": page_index,
#                             "json":request.build_absolute_uri(MEDIA_URL + auth_opus_page.json_path)})
#     
#     

#废弃    2014-04-21
# def flesh_multimedia_pages(multimedia_pages, page_index, is_multimedia=False):
#     """
#         取得新的多媒体页码
#     """
#     page_index = str(page_index)
#     page_list = []
#     if multimedia_pages:
#         page_list = multimedia_pages.split(',')
#     if is_multimedia and page_list.count(page_index) == 0:
#         page_list.append(page_index)
#     if not is_multimedia and page_list.count(page_index) > 0:
#         page_list.remove(page_index)
#     return ','.join([str(i) for i in page_list])


def update_auth_asset_ref(auth_opus, page_index, id_list):
    """
        更新个人资源的引用情况
    """
    id_dict = idlist2dict(id_list)
    asset_new_list = list(AuthAsset.objects.filter(id__in=id_dict.keys()))
    
    ref_done_list = AuthAssetRef.objects.filter(auth_opus=auth_opus, page_index=page_index)
    
    auth_ref_count = 0
    for ref_done in ref_done_list:
        if ref_done.auth_asset not in asset_new_list:
            ref_done.auth_asset.ref_times -= 1
            ref_done.auth_asset.save()
            
            ref_done.delete()
            auth_ref_count -= 1
        else:
            id_dict[ref_done.auth_asset.id] -= 1
            if id_dict[ref_done.auth_asset.id] <= 0:
                asset_new_list.remove(ref_done.auth_asset)
            if id_dict[ref_done.auth_asset.id] < 0:
                print "update_auth_asset_ref:error:id_dict[ref_done.auth_asset.id]:%d" % id_dict[ref_done.auth_asset.id]
    auth_ref_count += len(asset_new_list)
    
    for asset_ready in asset_new_list:
        while id_dict[asset_ready.id] > 0:
            auth_asset_ref = AuthAssetRef()
            auth_asset_ref.auth_asset = asset_ready
            auth_asset_ref.user = auth_opus.user
            auth_asset_ref.auth_opus = auth_opus
            auth_asset_ref.page_index = page_index
            
            auth_asset_ref.res_type = asset_ready.res_type
            auth_asset_ref.save()
            
            asset_ready.ref_times += 1
            asset_ready.save()
            id_dict[asset_ready.id] -= 1
    return auth_ref_count

def update_zone_asset_ref(auth_opus, page_index, id_list):
    """
        更新公共资源的引用情况
    """
    id_dict = idlist2dict(id_list)
    asset_new_list = list(ZoneAsset.objects.filter(id__in=id_dict.keys()))
    
    ref_done_list = ZoneAssetRef.objects.filter(auth_opus=auth_opus, page_index=page_index)
    
    zone_ref_count = 0
    for ref_done in ref_done_list:
        if ref_done.zone_asset not in asset_new_list:
            ref_done.zone_asset.ref_times -= 1
            ref_done.zone_asset.save()
            
            ref_done.delete()
            zone_ref_count -= 1
        else:
            id_dict[ref_done.zone_asset.id] -= 1
            if id_dict[ref_done.zone_asset.id] <= 0:
                asset_new_list.remove(ref_done.zone_asset)
            if id_dict[ref_done.zone_asset.id] < 0:
                print "update_zone_asset_ref:error:id_dict[ref_done.zone_asset.id]:%d" % id_dict[ref_done.zone_asset.id]
    zone_ref_count += len(asset_new_list)
    
    for zone_asset_ready in asset_new_list:
        while id_dict[zone_asset_ready.id] > 0:
            zone_asset_ref = ZoneAssetRef()
            zone_asset_ref.zone_asset = zone_asset_ready
            zone_asset_ref.user = auth_opus.user
            zone_asset_ref.auth_opus = auth_opus
            zone_asset_ref.page_index = page_index
            
            zone_asset_ref.res_type = zone_asset_ready.res_type
            zone_asset_ref.res_style = zone_asset_ready.res_style
            zone_asset_ref.save()
            
            zone_asset_ready.ref_times += 1
            zone_asset_ready.save()
            id_dict[zone_asset_ready.id] -= 1
    return zone_ref_count


@print_trace
@login_required
def new_opus_page(request, opus_id, page_index, template_id=0, template_page_index=0):
    """
        新建，或者插入作品的页
    """
    #print "new_opus_page", opus_id, page_index, template_id, template_page_index
    if page_index == 0:
        return FailResponse(u'新建页码不能为0.') 
    
    try: auth_opus = AuthOpus.objects.get(id=opus_id)
    except: return FailResponse(u'作品:%d不存在' % opus_id)
    if auth_opus.user_id <> request.user.id: return FailResponse(u'只能编辑自己的作品')
    if auth_opus.opus_type==0:
        if auth_opus.status not in (-2, -1, 0): return FailResponse(u'只有草稿状态的作品才能编辑')
    else: pass  
    
    if page_index <= auth_opus.page_count:
        sql = "update auth_opus_page set page_index=page_index+1 where auth_opus_id=%d and page_index>=%d" % (opus_id, page_index)
        #print sql
        connection.cursor().execute(sql)
    elif page_index == auth_opus.page_count + 1:
        pass
    else:
        return FailResponse(u'新建作品页:%d不正确' % page_index)

    if template_id:
        try: zone_asset = ZoneAsset.objects.get(id=template_id)
        except(ZoneAsset.DoesNotExist): return FailResponse(u'模板:%s不存在' % template_id)
        if zone_asset.library_id and zone_asset.library_id <> request.user.library_id:
            return FailResponse(u'没有权限作用模板:%d' % template_id)
        
        try: zone_asset_template = ZoneAssetTemplate.objects.get(zone_asset_id=zone_asset.id, page_index=template_page_index)
        except:
            return FailResponse(u'模板页:(%d,%d)不存在，请联系管理员' % (zone_asset.id, template_page_index))
    #opus_file = 'user/%s/%d/opus/%d/%d' % (request.user.date_joined.strftime("%Y"), request.user.id, auth_opus.id, page_index)
    opus_path = get_user_path(request.user, "opus", auth_opus.id)
    opus_file = "%s/%d" % (opus_path, page_index)
    
    auth_opus_page = AuthOpusPage()
    auth_opus_page.auth_opus_id = opus_id
    auth_opus_page.page_index = page_index

    print 'new_opus_page.template_id=%s, user_id=%s' % (template_id, request.user.id)
    print 'opus_path=', opus_path
    print 'opus_file=', opus_file
    if template_id:
        auth_opus_page.template_id = template_id
        auth_opus_page.template_page_index = template_page_index  #模板需要读的页码
        auth_opus_page.json = zone_asset_template.json

        template_file = "%s/%d/%d" % (get_lib_path(zone_asset.library, zone_asset.res_type), zone_asset.id, template_page_index)
        auth_opus_page.json_path = get_new_filename(MEDIA_ROOT, zone_asset_template.json_path.replace(template_file, opus_file))
        auth_opus_page.img_path = get_new_filename(MEDIA_ROOT, zone_asset_template.img_path.replace(template_file, opus_file))
        auth_opus_page.img_small_path = get_new_filename(MEDIA_ROOT, zone_asset_template.img_small_path.replace(template_file, opus_file))
        auth_opus_page.is_multimedia = zone_asset_template.is_multimedia
    else:

        auth_opus_page.json = open(os.path.join(MEDIA_ROOT, "blank.json")).read()
        auth_opus_page.json_path = get_new_filename(MEDIA_ROOT, "%s.json" % opus_file)
        auth_opus_page.img_path = get_new_filename(MEDIA_ROOT, "%s.jpg" % opus_file)
        auth_opus_page.img_small_path = get_tile_image_name(auth_opus_page.img_path, 's')
    auth_opus_page.save() 

    auth_opus.page_count += 1
    auth_opus.update_time = datetime.now()
    auth_opus.save()
    
    #文件全部复制过去
    if template_id:
        shutil.copyfile(os.path.join(MEDIA_ROOT, zone_asset_template.json_path), os.path.join(MEDIA_ROOT, auth_opus_page.json_path))
        shutil.copyfile(os.path.join(MEDIA_ROOT, zone_asset_template.img_path), os.path.join(MEDIA_ROOT, auth_opus_page.img_path))
        shutil.copyfile(os.path.join(MEDIA_ROOT, zone_asset_template.img_small_path), os.path.join(MEDIA_ROOT, auth_opus_page.img_small_path))
        zone_asset_template.ref_times += 1
        zone_asset_template.save()
    else:
        # 由于创建新页时在用户资源目录中可能不存在opus目录。故创建之
        json_path = os.path.join(MEDIA_ROOT, auth_opus_page.json_path)
        if not os.path.exists(os.path.dirname(json_path)):
            # 导入创建多级目录的方法
            from utils.decorator import make_dir
            make_dir(os.path.dirname(json_path))
        shutil.copyfile(os.path.join(MEDIA_ROOT, "blank.json"), os.path.join(MEDIA_ROOT, auth_opus_page.json_path))
        shutil.copyfile(os.path.join(MEDIA_ROOT, "blank.jpg"), os.path.join(MEDIA_ROOT, auth_opus_page.img_path))
        shutil.copyfile(os.path.join(MEDIA_ROOT, "blank_s.jpg"), os.path.join(MEDIA_ROOT, auth_opus_page.img_small_path))

    page_dict = {"page_index":page_index}
    page_dict["media"] = 0
    page_dict["orign"] = MEDIA_URL + auth_opus_page.img_path
    page_dict["small"] = MEDIA_URL + auth_opus_page.img_small_path
    page_dict["json"] = MEDIA_URL + auth_opus_page.json_path
        
    return SuccessResponse({"id":auth_opus.id,"page":page_dict, "page_index":page_index,
                            "json":MEDIA_URL + auth_opus_page.json_path,
                            "url":MEDIA_URL + auth_opus_page.img_path,
                            "thumbnail":MEDIA_URL + auth_opus_page.img_small_path})
    
@login_required
def update_opus_page(request, opus_page):
    """
        更新作品的页信息
        传入一个opus_page对象参数，对象的成员如下：
    opus_page.opus_id    作品ID，必传
    opus_page.page_index    更新，或者新建页的页码
    opus_page.json_data
    opus_page.image_data
    opus_page.is_multimedia=False    是否为多如期而媒体页
    opus_page.auth_asset_list=""    引用的个人资源的ID列表，如：1,3,20,12
    opus_page.zone_asset_list=""    引用的公共资源的ID列表，如：1,3,20,12
    """
    #print "update_opus_page", opus_page.page_index, opus_page.opus_id, opus_page.is_multimedia
    
    try:
        auth_opus = AuthOpus.objects.get(id=opus_page.opus_id)
        if auth_opus.user_id <> request.user.id: return FailResponse(u'只能编辑自己的作品')
    except(AuthOpus.DoesNotExist): return FailResponse(u'作品ID不正确')
    if auth_opus.opus_type==0:
        if auth_opus.status not in (-2, -1, 0): return FailResponse(u'只有草稿状态的作品才能编辑')
    else: pass 
    
    #2014-04-16    更新作品每页的表信息
    try:
        auth_opus_page = AuthOpusPage.objects.get(auth_opus_id=auth_opus.id, page_index=opus_page.page_index)
    except:
        return FailResponse(u'作品页不存在')
    
    image_data = opus_page.image_data.getvalue()
    if len(image_data) > ALLOWED_IMG_UPLOAD_SIZE:
        return FailResponse(u'文件超过最大充许大小')
    img = Image.open(StringIO(image_data))
    ext = get_img_ext(img)
    if ext == None:
        return FailResponse(u"只充许上传图片文件(%s)" % ';'.join(ALLOWED_IMG_EXTENSION))

    img.save(os.path.join(MEDIA_ROOT, auth_opus_page.img_path))
    
    #im_small = ImageOps.fit(img, (240,190), Image.ANTIALIAS)
    #im_small.save(os.path.join(MEDIA_ROOT, auth_opus_page.img_small_path))
    img.thumbnail(get_small_size(img.size[0], img.size[1]), Image.ANTIALIAS)
    img.save(os.path.join(MEDIA_ROOT, auth_opus_page.img_small_path))
    
    fp = open(os.path.join(MEDIA_ROOT, auth_opus_page.json_path), "wb")
    fp.write(opus_page.json_data.encode("utf-8"))
    fp.close()
    
    #2014-04-16    更新个人资源，公共资源的引用信息
    update_auth_asset_ref(auth_opus, opus_page.page_index, opus_page.auth_asset_list)
    update_zone_asset_ref(auth_opus, opus_page.page_index, opus_page.zone_asset_list)

    auth_opus_page.is_multimedia = opus_page.is_multimedia     
    auth_opus_page.auth_asset_list = opus_page.auth_asset_list
    auth_opus_page.zone_asset_list = opus_page.zone_asset_list
    auth_opus_page.json = opus_page.json_data.encode("utf-8")
    auth_opus_page.update_time = datetime.now()
    auth_opus_page.save()
    
    auth_opus.update_time = auth_opus_page.update_time
    if auth_opus.status == -2:  #新建作品开始保存
        auth_opus.status = 0    #草稿
    auth_opus.save()
    
    page_dict = {"page_index":opus_page.page_index}
    page_dict["media"] = auth_opus_page.is_multimedia
    page_dict["orign"] = MEDIA_URL + auth_opus_page.img_path
    page_dict["small"] = MEDIA_URL + auth_opus_page.img_small_path
    page_dict["json"] = MEDIA_URL + auth_opus_page.json_path
    
    return SuccessResponse({"id":auth_opus.id,"page":page_dict, "page_index":opus_page.page_index,
                            "json":MEDIA_URL + auth_opus_page.json_path,
                            "url":MEDIA_URL + auth_opus_page.img_path,
                            "thumbnail":MEDIA_URL + auth_opus_page.img_small_path})
    

@login_required
def update_opus_info(request, opus):
    """
        更新作品一些主详细信息
        editor: kamihati 2015/6/16 增加对后台创建活动预告等系统作品的支持
    """
    print 'amf.update_opus_info'
    print opus
    check_result = check_opus_type(opus.type_id, opus.class_id)
    if check_result != "ok":
        return FailResponse(check_result)
    
    try:
        auth_opus = AuthOpus.objects.get(id=opus.opus_id)
    except AuthOpus.DoesNotExist:
        return FailResponse(u'作品ID不正确')

    if auth_opus.user_id != request.user.id:
        return FailResponse(u'只能编辑自己的作品')

    if auth_opus.opus_type == 0:
        if auth_opus.status not in (-2, -1, 0): return FailResponse(u'只有草稿状态的作品才能编辑')

    auth_opus.title = opus.title if opus.title else u'系统创作'
    auth_opus.brief = opus.brief
    auth_opus.tags = opus.tags
    auth_opus.type_id = opus.type_id
    auth_opus.class_id = opus.class_id
    auth_opus.update_time = datetime.now()
    if auth_opus.status == -2:
        auth_opus.status = 0
    auth_opus.save()

    activity_id = opus.activity_id if opus.has_key('activity_id') else 0
    print 'activity_id=', activity_id
    if activity_id != 0:
        opus_type = opus.type_id
        # 导入系统分类列表
        from activity.fruit_handler import n_opus_type
        if n_opus_type.find(str(opus_type)) == -1:
            return SuccessResponse()
        auth_opus.type_id = opus_type
        auth_opus.activity_id = activity_id
        auth_opus.status = 2
        auth_opus.save()
        if ActivityFruit.objects.filter(activity_id=activity_id, opus_id=auth_opus.id, status=2).count() == 0:
            # editor: kamihati 后台进行系统类别的活动创作。需要保存到活动作品
            fruit = ActivityFruit.objects.create(fruit_name=auth_opus.title,
                                                 fruit_type=2,
                                                 fruit_brief=auth_opus.brief,
                                                 update_time=datetime.now(),
                                                 library_id=request.user.library.id,
                                                 activity_id=activity_id,
                                                 opus_id=auth_opus.id,
                                                 opus_type=auth_opus.type_id,
                                                 user_id=request.user.id,
                                                 author_name=request.user.nickname,
                                                 status=2)
    return SuccessResponse()


@login_required
def create_opus(request, param):
    print 'amf.create_opus.......'
    print param
    """
        新建作品，活动作品，活动播报作品，活动预告，比赛结果作品都是这一个函数
        editor: kamihati 2015/6/17  梳理逻辑。
    """
    title = param.title if param.has_key('title') else u'未命名作品'
    brief = param.brief if param.has_key('brief') else ''
    tags = param.tags if param.has_key('tags') else ''
    type_id = param.type_id if param.has_key('type_id') else 0
    class_id = param.class_id if param.has_key('class_id') else 0
    template_id = param.template_id if param.has_key('template_id') else 0
    create_type = param.create_type if param.has_key('create_type') else 1
    read_type = param.read_type if param.has_key('read_type') else 1
    width = param.width if param.has_key('width') else 0
    height = param.height if param.has_key('height') else 0
    activity_id = param.activity_id if param.has_key('activity_id') else 0
    fruit_id = param.fruit_id if param.has_key('fruit_id') else 0
    opus_type = param.opus_type if param.has_key('opus_type') else 0
    size_id = int(param['size_id']) if param.has_key('size_id') else 0

    if activity_id != 0:
        try:
            activity_list = ActivityList.objects.get(id=activity_id)
        except(ActivityList.DoesNotExist):
            return FailResponse(u'活动(%d)不存在' % activity_id)
        width = 886
        height = 744
    print '22222222222222222222222222'
    print 'opus_type=', opus_type
    if opus_type == 1:
        """
        if AuthOpus.objects.filter(activity_id=activity_id, opus_type=opus_type).count()>0:
            return FailResponse(u'活动(%s)已存在，请直接在个人中心编辑！' % activity_list.title)
        """
        pass
    elif opus_type == 2:    #个人参赛的电子创作作品
        if not fruit_id:
            return FailResponse(u'必须传入fruit_id')
        try: activity_fruit = ActivityFruit.objects.get(id=fruit_id)
        except(ActivityFruit.DoesNotExist): return FailResponse(u'对应的fruit_id不存在')
    elif opus_type == 3:
        """
        if AuthOpus.objects.filter(activity_id=activity_id, opus_type=opus_type).count()>0:
            return FailResponse(u'活动预告(%s)已存在，请直接在个人中心编辑！' % activity_list.title)
        if ActivityFruit.objects.filter(activity_id=activity_id, opus_type=opus_type).count()>0:
            return FailResponse(u'活动预告(%s)已存在，请直接在个人中心编辑！' % activity_list.title)
        """
        pass
    elif opus_type == 4:
        """
        if AuthOpus.objects.filter(activity_id=activity_id, opus_type=opus_type).count()>0:
            return FailResponse(u'活动结果(%s)已存在，请直接在个人中心编辑！' % activity_list.title)
        if ActivityFruit.objects.filter(activity_id=activity_id, opus_type=opus_type).count()>0:
            return FailResponse(u'活动结果(%s)已存在，请直接在个人中心编辑！' % activity_list.title)
        """
        pass

    check_result = check_opus_type(type_id, class_id)
    if check_result != "ok":
        return FailResponse(check_result)

    if create_type not in (1, 2) or read_type not in (1, 2):
        return FailResponse(u'创建/阅读模式只支持单/双页')
    
    if cache.get("opus:%s" % request.user.id, None):
        cache.delete("opus:%s" % request.user.id)
        # editor: kamihati 2015/6/9 由于目前并没有相应的异常处理来应对此种设置。故暂时不对缓存中已存在的为创建完毕的信息进行判断
        # return FailResponse(cache.get("opus:%s" % request.user.id))
    cache.set("opus:%s" % request.user.id, u"正在创建作品[%s]，请稍候[%s]" % (title, datetime.now().strftime("%Y-%m-%d %H:%M:%S")), 60)

    auth_opus = AuthOpus()
    auth_opus.user = request.user
    auth_opus.library_id = request.user.library_id
    auth_opus.title = title
    auth_opus.brief = brief
    auth_opus.tags = tags
    auth_opus.size_id = size_id
    auth_opus.activity_id = activity_id
    auth_opus.opus_type = opus_type
    auth_opus.create_type = create_type
    auth_opus.read_type = read_type
    auth_opus.type_id = type_id
    auth_opus.class_id = class_id
    if width:
        auth_opus.width = width
    if height:
        auth_opus.height = height
    auth_opus.page_count = 1
    if opus_type == 0:  #个人作品
        auth_opus.status = -2   #新建个人作品都用“待删除状态”，保存过后才是草稿状态
    else:
        auth_opus.status = 0    #活动作品，直接就是草稿状态
    auth_opus.save()

    if opus_type == 2:      #个人参赛的电子创作作品
        activity_fruit.opus_id = auth_opus.id
        activity_fruit.save()
    print 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
    #opus_dir = 'user/%s/%d/opus/%d' % (request.user.date_joined.strftime("%Y"), request.user.id, auth_opus.id)
    opus_path = get_user_path(request.user, "opus", auth_opus.id)
    print 'template_id=', template_id
    if template_id:
        print 'usee template..............'
        try:
            zone_asset = ZoneAsset.objects.get(id=template_id)
        except(ZoneAsset.DoesNotExist):
            return FailResponse(u'模板ID:%s不存在' % template_id)
        if zone_asset.library_id and zone_asset.library_id <> request.user.library_id:
            auth_opus.status = -3   #创建失败
            auth_opus.save()
            cache.delete("opus:%s" % request.user.id)
            return FailResponse(u'没有权限作用该模板')
        
        template_dir = "%s/%d" % (get_lib_path(zone_asset.library, zone_asset.res_type), zone_asset.id)
        
        for page_index in xrange(1, zone_asset.page_count + 1):
            try:
                zone_asset_template = ZoneAssetTemplate.objects.get(zone_asset_id=zone_asset.id, page_index=page_index)
            except:
                auth_opus.status = -3   #创建失败
                auth_opus.save()
                cache.delete("opus:%s" % request.user.id)
                return FailResponse(u'新建作品失败，请联系管理员:%d' % auth_opus.id)
            
            auth_opus_page = AuthOpusPage()
            auth_opus_page.auth_opus_id = auth_opus.id
            auth_opus_page.template_id = zone_asset.id
            auth_opus_page.page_index = page_index
            auth_opus_page.template_page_index = page_index
            
            auth_opus_page.json = zone_asset_template.json
            auth_opus_page.json_path = zone_asset_template.json_path.replace(template_dir, opus_path)
            auth_opus_page.img_path = zone_asset_template.img_path.replace(template_dir, opus_path)
            auth_opus_page.img_small_path = zone_asset_template.img_small_path.replace(template_dir, opus_path)
            auth_opus_page.is_multimedia = zone_asset_template.is_multimedia
            auth_opus_page.save() 
        
        auth_opus.template_id = zone_asset.id
        auth_opus.create_type = zone_asset.create_type
        auth_opus.read_type = zone_asset.read_type
        auth_opus.page_count = zone_asset.page_count
        if auth_opus.width == 0 or auth_opus.height == 0:
            auth_opus.width = zone_asset.width
            auth_opus.height = zone_asset.height
        auth_opus.save()
        
        #文件全部复制过去
        shutil.copytree(os.path.join(MEDIA_ROOT, template_dir), os.path.join(MEDIA_ROOT, opus_path))
        
        zone_asset.ref_times += 1
        zone_asset.save()
    else:
        print 'no template..........'
        if not os.path.exists(os.path.join(MEDIA_ROOT, opus_path)):
            os.makedirs(os.path.join(MEDIA_ROOT, opus_path))
        #print "blank opus:", os.path.join(MEDIA_ROOT, "blank.json")
        auth_opus_page = AuthOpusPage()
        auth_opus_page.auth_opus_id = auth_opus.id
        auth_opus_page.page_index = 1
        auth_opus_page.json = open(os.path.join(MEDIA_ROOT, "blank.json")).read()
        auth_opus_page.json_path = get_new_filename(MEDIA_ROOT, "%s/1.json" % opus_path)
        auth_opus_page.img_path = get_new_filename(MEDIA_ROOT, "%s/1.jpg" % opus_path)
        auth_opus_page.img_small_path = get_tile_image_name(auth_opus_page.img_path, 's')
        auth_opus_page.save()
        #print "blank opus:", auth_opus_page.json_path, auth_opus_page.img_path

        shutil.copyfile(os.path.join(MEDIA_ROOT, "blank.json"), os.path.join(MEDIA_ROOT, auth_opus_page.json_path))
        shutil.copyfile(os.path.join(MEDIA_ROOT, "blank.jpg"), os.path.join(MEDIA_ROOT, auth_opus_page.img_path))
        shutil.copyfile(os.path.join(MEDIA_ROOT, "blank.jpg"), os.path.join(MEDIA_ROOT, auth_opus_page.img_small_path))
        
        auth_user = AuthUser.objects.get(id=request.user.id)
        print 'create auth_opus_path over...........'
        #(0,u"普通作品"),(1,u"播报作品"),(2,u"个人参赛作品"),(3,u"活动预告"),(4,u"活动结果")
        if opus_type == 1:  #新闻播报
            """
            activity_list.opus_id = auth_opus.id
            activity_list.cover = auth_opus_page.img_path
            activity_list.thumbnail = auth_opus_page.img_small_path
            #activity_list.status = 1
            activity_list.save()
            """
            pass
        elif opus_type == 2:    #个人参赛作品 先创建，后写入信息
            activity_fruit.library_id = request.user.library_id
            activity_fruit.activity_id = activity_list.id
            #activity_fruit.opus_type = 0    #个人参赛作品，类型默认为0
            activity_fruit.user_id = request.user.id
            activity_fruit.opus_id = auth_opus.id
            #activity_fruit.fruit_name = auth_opus.title
            #activity_fruit.fruit_brief = auth_opus.brief
            #activity_fruit.author_name = auth_user.realname or auth_user.nickname
            #activity_fruit.author_brief = activity_fruit.author_name
            #activity_fruit.author_sex = auth_user.sex
            #activity_fruit.author_telephone = auth_user.telephone
            #activity_fruit.author_email = auth_user.email
            activity_fruit.save()
        elif opus_type == 3:    #活动预告
            pass
            """
            activity_list.opus_id = auth_opus.id    #修改时需要此参数
            activity_list.cover = auth_opus_page.img_path
            activity_list.thumbnail = auth_opus_page.img_small_path
            activity_list.save()
            
            activity_fruit = ActivityFruit()
            activity_fruit.library_id = activity_list.library_id
            activity_fruit.activity_id = activity_list.id
            activity_fruit.opus_type = 3
            activity_fruit.user_id = activity_list.user_id
            activity_fruit.opus_id = auth_opus.id
            activity_fruit.fruit_name = auth_opus.title
            activity_fruit.fruit_brief = auth_opus.brief
            activity_fruit.author_name = auth_user.realname or auth_user.nickname
            activity_fruit.author_brief = activity_fruit.author_name
            activity_fruit.author_sex = auth_user.sex
            activity_fruit.author_telephone = auth_user.telephone
            activity_fruit.author_email = auth_user.email
            activity_fruit.save()
            """
        elif opus_type == 4:    #比赛结果
            pass
            """
            activity_fruit = ActivityFruit()
            activity_fruit.library_id = activity_list.library_id
            activity_fruit.activity_id = activity_list.id
            activity_fruit.opus_type = 4
            activity_fruit.user_id = activity_list.user_id
            activity_fruit.opus_id = auth_opus.id
            activity_fruit.fruit_name = auth_opus.title
            activity_fruit.fruit_brief = auth_opus.brief
            activity_fruit.author_name = auth_user.realname or auth_user.nickname
            activity_fruit.author_brief = activity_fruit.author_name
            activity_fruit.author_sex = auth_user.sex
            activity_fruit.author_telephone = auth_user.telephone
            activity_fruit.author_email = auth_user.email
            activity_fruit.save()
            """
    print 'create_opus.oer........'
    cache.delete("opus:%s" % request.user.id)
    return SuccessResponse(opus_info(auth_opus))


@login_required
def copy_opus(request, opus):
    if request.session.has_key("opus:%s" % request.user.id):
        return FailResponse(request.session["opus:%s" % request.user.id])
    
    #opus: id, title, brief, tags, type_id, class_id
    #print opus.title, opus.brief, opus.tags, opus.type_id, type(opus.type_id), type(opus.class_id), opus.class_id
    opus.type_id = int(opus.type_id)
    opus.class_id = int(opus.class_id)
    check_result = check_opus_type(opus.type_id, opus.class_id)
    if check_result <> "ok": return FailResponse(check_result)
    
    try: source_opus = AuthOpus.objects.get(id=opus.id)
    except:  return FailResponse(u"源作品ID:%d不存在" % opus.id)
    if source_opus.user_id <> request.user.id:
        return FailResponse(u"不是自己的作品，不能复制")
    
    request.session["opus:%s" % request.user.id] = u"正在复制作品[%s]，请稍候[%s]" % (source_opus.title, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    auth_opus = AuthOpus()
    auth_opus.user = request.user
    auth_opus.library = request.user.library
    auth_opus.title = opus.title
    auth_opus.brief = opus.brief
    auth_opus.tags = opus.tags
    auth_opus.type_id = opus.type_id
    auth_opus.class_id = opus.class_id
    auth_opus.width = source_opus.width
    auth_opus.height = source_opus.height
    
    auth_opus.create_type = source_opus.create_type
    auth_opus.read_type = source_opus.read_type
    
    auth_opus.template_id = source_opus.template_id
    auth_opus.page_count = source_opus.page_count
    auth_opus.status = -2   #新建作品都用“待删除状态”，保存过后才是草稿状态
    auth_opus.save()
    
    #source_opus_dir = 'user/%s/%d/opus/%d' % (request.user.date_joined.strftime("%Y"), request.user.id, source_opus.id)
    #dest_opus_dir = 'user/%s/%d/opus/%d' % (request.user.date_joined.strftime("%Y"), request.user.id, auth_opus.id)
    source_opus_path = get_user_path(request.user, "opus", source_opus.id)
    dest_opus_path = get_user_path(request.user, "opus", auth_opus.id)
    
    for page_index in xrange(1, source_opus.page_count + 1):
        try: source_opus_page = AuthOpusPage.objects.get(auth_opus_id=source_opus.id, page_index=page_index)
        except:
            auth_opus.status = -3   #创建失败
            auth_opus.save()
            del request.session["opus:%s" % request.user.id]
            return FailResponse(u'新建作品失败，请联系管理员:%d' % auth_opus.id)
        
        auth_opus_page = AuthOpusPage()
        auth_opus_page.auth_opus_id = auth_opus.id
        auth_opus_page.template_id = source_opus_page.template_id
        auth_opus_page.page_index = page_index
        auth_opus_page.template_page_index = source_opus_page.template_page_index
        
        auth_opus_page.json = source_opus_page.json
        auth_opus_page.json_path = source_opus_page.json_path.replace(source_opus_path, dest_opus_path)
        auth_opus_page.img_path = source_opus_page.img_path.replace(source_opus_path, dest_opus_path)
        auth_opus_page.img_small_path = source_opus_page.img_small_path.replace(source_opus_path, dest_opus_path)
        auth_opus_page.is_multimedia = source_opus_page.is_multimedia
        auth_opus_page.save() 
        
    #文件全部复制过去
    shutil.copytree(os.path.join(MEDIA_ROOT, source_opus_path), os.path.join(MEDIA_ROOT, dest_opus_path))

    del request.session["opus:%s" % request.user.id]
    return SuccessResponse(opus_info(auth_opus))


@login_required
def apply_for_press(request, opus_id):
    """
        申请发表个人作品
        editor: kamihati 2015/6/17 调整逻辑。取消仅能在活动页面发布作品的限制
    """
    try: auth_opus = AuthOpus.objects.get(id=opus_id)
    except(AuthOpus.DoesNotExist): return FailResponse(u"不存在的作品ID:%d" % opus_id)
    if auth_opus.status == 2:
        # editor: kamihati 2015/6/17 当发布状态的作品调用直接返回成功。因为系统作品直接设置为发布状态。
        return SuccessResponse()
    
    if auth_opus.user.auth_type == 5:
        return FailResponse(u"游客用户不能发表作品")
    
    if auth_opus.user_id <> request.user.id:
        return FailResponse(u"不是自己的作品")
    
    if auth_opus.status not in (-1, 0):
        return FailResponse(u"只有草稿、审核未通过的作品才能申请发表")

    """
    if not auth_opus.brief or len(auth_opus.brief) == 0:
        return FailResponse(u"申请发表前，请先完善作品信息")
    """
    check_result = check_opus_type(auth_opus.type_id, auth_opus.class_id)
    if check_result <> "ok": return FailResponse(check_result)
    
    auth_opus.status = 1
    auth_opus.save()

    return SuccessResponse({"id": opus_id})


@login_required
def apply_for_template(request, opus_id):
    """
        已发表的作品，申请成为模板，只有管理员才有此权限
    """
    try: auth_opus = AuthOpus.objects.get(id=opus_id)
    except(AuthOpus.DoesNotExist): return FailResponse(u"不存在的作品ID:%d" % opus_id)
    
    if not auth_opus.user.is_staff:
        return FailResponse(u"只有管理员才能申请作品转为模板")
    
    if auth_opus.user_id <> request.user.id:
        return FailResponse(u"不是自己的作品")
    
    if auth_opus.status <> 2:
        return FailResponse(u"只有已发表作品，才能申请转为模板")
    
    if ZoneAsset.objects.filter(res_type=4, opus_id=auth_opus.id, status__gte=0).count() > 0:
        return FailResponse(u"已经转为模板过，如果需要重新转换，请先把旧的模板删除")
    
    if cache.get("opus:%s" % request.user.id, None):
        return FailResponse(cache.get("opus:%s" % request.user.id))
    cache.set("opus:%s" % request.user.id, u"正在把作品[%s]转为模板，请稍候[%s]" % (auth_opus.title, datetime.now().strftime("%Y-%m-%d %H:%M:%S")), 60)
    
    #先创建模板封面
    zone_asset = ZoneAsset()
    zone_asset.user_id = request.user.id
    zone_asset.res_title = auth_opus.title if auth_opus.title else ""
    zone_asset.res_type = 4 #模板
    zone_asset.opus_id = auth_opus.id
    
    zone_asset.type_id = auth_opus.type_id
    zone_asset.class_id = auth_opus.class_id
    zone_asset.create_type = auth_opus.create_type
    zone_asset.read_type = auth_opus.read_type
    
    #zone_asset.size_id = auth_opus.size_id
    zone_asset.width = auth_opus.width
    zone_asset.height = auth_opus.height
    zone_asset.page_count = auth_opus.page_count
    
    zone_asset.status = -1  #上传文件失败的，等待自动删除程序删除
    zone_asset.save()
    
    asset_path = "assets/4/%d" % zone_asset.id
    os.makedirs(os.path.join(MEDIA_ROOT, asset_path))   #创建目录
    
    page_list = AuthOpusPage.objects.filter(auth_opus_id=auth_opus.id).order_by('page_index')
    if page_list.count() <> auth_opus.page_count:
        return FailResponse(u"作品信息有错，请联系管理员改正")
    for opus_page in page_list:
        #print opus_page.page_index, opus_page.img_path
        ext = os.path.splitext(opus_page.img_path)[1]
        if opus_page.page_index == 1:
            zone_asset.res_path = "%s/origin%s" % (asset_path, ext)
            zone_asset.img_large_path = zone_asset.res_path.replace("origin", "l")
            zone_asset.img_medium_path = zone_asset.res_path.replace("origin", "m")
            zone_asset.img_small_path = zone_asset.res_path.replace("origin", "s")
            zone_asset.save()
            #copy文件到模板目录
            open(os.path.join(MEDIA_ROOT, zone_asset.res_path), "wb").write(open(os.path.join(MEDIA_ROOT, opus_page.img_path), "rb").read())
            
            img = Image.open(os.path.join(MEDIA_ROOT, zone_asset.res_path))
            if img.size[0] > 950 or img.size[1] > 950:
                img.thumbnail((950,950), Image.ANTIALIAS)
                img.save(os.path.join(MEDIA_ROOT, zone_asset.img_large_path))
            else:
                zone_asset.img_large_path = zone_asset.res_path
            if img.size[0] > 600 or img.size[1] > 600:
                img.thumbnail((600,600), Image.ANTIALIAS)
                img.save(os.path.join(MEDIA_ROOT, zone_asset.img_medium_path))
            else:
                zone_asset.img_medium_path = zone_asset.res_path
            img.thumbnail(get_small_size(img.size[0], img.size[1]), Image.ANTIALIAS)
            img.save(os.path.join(MEDIA_ROOT, zone_asset.img_small_path))

        json_data = template_json(opus_page.json)
        if json_data == None:
            return FailResponse(u"第%d页的json文件转换错误，请联系管理员" % opus_page.page_index)
                     
        templaete = ZoneAssetTemplate()   #新建模板页
        templaete.zone_asset_id = zone_asset.id
        templaete.page_index = opus_page.page_index
        templaete.json = json_data
        templaete.json_path = "%s/%d.json" % (asset_path, opus_page.page_index)
        templaete.img_path = "%s/%d%s" % (asset_path, opus_page.page_index, ext)
        templaete.img_small_path = "%s/%d_s%s" % (asset_path, opus_page.page_index, ext)
        templaete.save()
        #写入文件
        open(os.path.join(MEDIA_ROOT, templaete.img_path), "wb").write(open(os.path.join(MEDIA_ROOT, opus_page.img_path), "rb").read())
        open(os.path.join(MEDIA_ROOT, templaete.img_small_path), "wb").write(open(os.path.join(MEDIA_ROOT, opus_page.img_small_path), "rb").read())
        f = open(os.path.join(MEDIA_ROOT, templaete.json_path), "wb")
        f.write(json_data)
        f.close()
    zone_asset.status = 1  #转换成功，直接使用
    zone_asset.save()
    
    cache.delete("opus:%s" % request.user.id)
    return SuccessResponse(u"作品:%s申请转为模板成功，请等候审批" % auth_opus.title) 

def template_json(json_data):
    '''
        将作品的json值，转为模板可用的json值，失败返回为空
    '''
    try:
        import json
        json_data = json.loads(json_data)
        if json_data.has_key('childrens'):
            for item in json_data['childrens']:
                if item['localName'] == 'image':
                    item['photoid'] = -1
                    item['b'] = ''
                    item['m'] = ''
                    item['s'] = ''
                    try: item['o'] = ''
                    except: pass
                elif item['localName'] == 'music':
                    item['musicId'] = -1
                    item['musicUrl'] = ''
                elif item['localName'] == 'video':
                    item['videoId'] = -1
                    item['videoUrl'] = ''
        return json.dumps(json_data)
    except:
        import traceback
        traceback.print_exc()
        return None    
    

@login_required
def delete_opus(request, opus_id):
    """
        删除个人作品
        editor: kamihati
    """
    try: auth_opus = AuthOpus.objects.get(id=opus_id)
    except(AuthOpus.DoesNotExist): return FailResponse(u"不存在的作品ID:%d" % opus_id)
    
    if auth_opus.user_id <> request.user.id:
        return FailResponse(u"不是自己的作品")
    if auth_opus.status not in (-1, 0): return FailResponse(u'只有草稿状态的作品才能删除')

    if AuthOpusPage.objects.filter(auth_opus=auth_opus).count() > 0:
        #删除作品整个目录，所以，每一页的文件，不需要一个个的删除
        #opus_dir = 'user/%s/%d/opus/%d' % (request.user.date_joined.strftime("%Y"), request.user.id, auth_opus.id)
        opus_path = get_user_path(request.user, "opus", auth_opus.id)
        opus_absdir = os.path.join(MEDIA_ROOT, opus_path)
        try: shutil.rmtree(opus_absdir)
        except: pass
        
        delete_opus_ref(auth_opus)
    AuthOpusPage.objects.filter(auth_opus=auth_opus).delete()
    auth_opus.delete()
    # 删除活动作品。
    # editor: kamihati 2015/4/30  删除个人中心的作品时清除相应的活动作品记录
    ActivityFruit.objects.filter(opus_id=opus_id).delete()
    return SuccessResponse({"id":opus_id})                     


def delete_opus_ref(auth_opus):
    for opus_page in AuthOpusPage.objects.filter(auth_opus=auth_opus):
        delete_opus_page_ref(opus_page)


def delete_opus_page_ref(auth_opus_page):
    """
        删除作品的某一页前，先删除每一页作品引用资源的信息，以便准备统计很个资源的热度
    """
    auth_asset_ref_set = AuthAssetRef.objects.filter(auth_opus_id=auth_opus_page.auth_opus_id, page_index=auth_opus_page.page_index)
    for auth_asset_ref in auth_asset_ref_set:
        auth_asset_ref.auth_asset.ref_times -= 1
        auth_asset_ref.delete()
    
    zone_asset_ref_set = ZoneAssetRef.objects.filter(auth_opus_id=auth_opus_page.auth_opus_id, page_index=auth_opus_page.page_index)
    for zone_asset_ref in zone_asset_ref_set:
        zone_asset_ref.zone_asset.ref_times -= 1
        zone_asset_ref.delete()
        
                              
@login_required
def delete_opus_page_20140424(request, opus_id, page_index):
    """
        被删后，总页数减少一，后面页的页码，顺应的往前移一
    """
    #print "delete_opus_page", type(opus_id), opus_id, type(page_index), page_index
    try: auth_opus_page = AuthOpusPage.objects.get(auth_opus_id=opus_id, page_index=page_index)
    except(AuthOpusPage.DoesNotExist):
        import traceback
        traceback.print_exc()
        return FailResponse(u"作品页不存在")
            
    auth_opus = auth_opus_page.auth_opus
    page_index = auth_opus_page.page_index
    
    if auth_opus.user_id <> request.user.id:
        return FailResponse(u"不是自己的作品")
    
    if request.session.has_key("auth_opus:%s" % opus_id):
        return FailResponse(request.session["auth_opus:%s" % opus_id])
    request.session["auth_opus:%s" % opus_id] = u"正在删除当前作品的第%s页，请稍候" % page_index
    
    delete_opus_page_ref(auth_opus_page)
    if auth_opus_page.json_path and os.path.isfile(os.path.join(MEDIA_ROOT, auth_opus_page.json_path)):
        os.remove(os.path.join(MEDIA_ROOT, auth_opus_page.json_path))
    if auth_opus_page.img_path and os.path.isfile(os.path.join(MEDIA_ROOT, auth_opus_page.img_path)):
        os.remove(os.path.join(MEDIA_ROOT, auth_opus_page.img_path))
    if auth_opus_page.img_small_path and os.path.isfile(os.path.join(MEDIA_ROOT, auth_opus_page.img_small_path)):
        os.remove(os.path.join(MEDIA_ROOT, auth_opus_page.img_small_path))
    auth_opus_page.delete()
    
    cur_index = page_index + 1
    last_json_path = auth_opus_page.json_path
    last_img_path = auth_opus_page.img_path
    last_img_small_path = auth_opus_page.img_small_path
    while cur_index <= auth_opus.page_count:
        try: cur_opus_page = AuthOpusPage.objects.get(auth_opus_id=opus_id, page_index=cur_index)
        except(AuthOpusPage.DoesNotExist):
            print cur_index, '11111111111111111111111111111111'
            cur_index += 1
            continue
        
        #print os.path.join(MEDIA_ROOT, cur_opus_page.json_path)
        if os.path.isfile(os.path.join(MEDIA_ROOT, cur_opus_page.json_path)):
            os.rename(os.path.join(MEDIA_ROOT, cur_opus_page.json_path), os.path.join(MEDIA_ROOT, last_json_path))
            #print cur_opus_page.json_path, last_json_path
        #print os.path.join(MEDIA_ROOT, cur_opus_page.img_path)
        if os.path.isfile(os.path.join(MEDIA_ROOT, cur_opus_page.img_path)):
            os.rename(os.path.join(MEDIA_ROOT, cur_opus_page.img_path), os.path.join(MEDIA_ROOT, last_img_path))
            #print cur_opus_page.img_path, last_img_path
        #print os.path.join(MEDIA_ROOT, cur_opus_page.img_small_path)
        if os.path.isfile(os.path.join(MEDIA_ROOT, cur_opus_page.img_small_path)):
            os.rename(os.path.join(MEDIA_ROOT, cur_opus_page.img_small_path), os.path.join(MEDIA_ROOT, last_img_small_path))
            #print cur_opus_page.img_small_path, last_img_small_path
        
        cur_opus_page.page_index = cur_index - 1
        cur_opus_page.json_path, last_json_path = last_json_path, cur_opus_page.json_path
        cur_opus_page.img_path, last_img_path = last_img_path, cur_opus_page.img_path
        cur_opus_page.img_small_path, last_img_small_path = last_img_small_path, cur_opus_page.img_small_path
        cur_opus_page.update_time = datetime.now()
        cur_opus_page.save()
        cur_index += 1
    
    sql = "update auth_opus set page_count=page_count-1 where id=%s" % opus_id
    connection.cursor().execute(sql)
    
    del request.session["auth_opus:%s" % opus_id]
    return SuccessResponse({"opus_id":opus_id,"page_index":page_index})


@login_required
def delete_opus_page(request, opus_id, page_index):
    """
        被删后，总页数减少一
        新算法，只改索引值，不改文件名    2014-04-24
    """
    #print "delete_opus_page:new:", type(opus_id), opus_id, type(page_index), page_index
    try: auth_opus_page = AuthOpusPage.objects.get(auth_opus_id=opus_id, page_index=page_index)
    except(AuthOpusPage.DoesNotExist): return FailResponse(u"作品页不存在")
            
    auth_opus = auth_opus_page.auth_opus
    if auth_opus.opus_type==0:
        if auth_opus.status not in (-2, -1, 0): return FailResponse(u'只有草稿状态的作品才能编辑')
    else: pass 
    page_index = auth_opus_page.page_index
    
    if auth_opus.user_id <> request.user.id:
        return FailResponse(u"不是自己的作品")
    
    if request.session.has_key("auth_opus:%s" % opus_id):
        return FailResponse(request.session["auth_opus:%s" % opus_id])
    request.session["auth_opus:%s" % opus_id] = u"正在删除当前作品的第%s页，请稍候" % page_index
    
    delete_opus_page_ref(auth_opus_page)
    if auth_opus_page.json_path and os.path.isfile(os.path.join(MEDIA_ROOT, auth_opus_page.json_path)):
        os.remove(os.path.join(MEDIA_ROOT, auth_opus_page.json_path))
    if auth_opus_page.img_path and os.path.isfile(os.path.join(MEDIA_ROOT, auth_opus_page.img_path)):
        os.remove(os.path.join(MEDIA_ROOT, auth_opus_page.img_path))
    if auth_opus_page.img_small_path and os.path.isfile(os.path.join(MEDIA_ROOT, auth_opus_page.img_small_path)):
        os.remove(os.path.join(MEDIA_ROOT, auth_opus_page.img_small_path))
    auth_opus_page.delete()
    
    
    sql = "update auth_opus set page_count=page_count-1 where id=%s;" % opus_id
    sql += "update auth_opus_page set page_index=page_index-1 where auth_opus_id=%s and page_index>%s" % (opus_id, page_index)
    #print sql
    connection.cursor().execute(sql)
    
    del request.session["auth_opus:%s" % opus_id]
    return SuccessResponse({"opus_id":opus_id,"page_index":page_index})


@login_required
def change_opus_page(request, opus_id, page_index, new_page_index):
    try: auth_opus = AuthOpus.objects.get(id=opus_id)
    except(AuthOpus.DoesNotExist): return FailResponse(u"不存在的作品ID:%d" % opus_id)
    
    if auth_opus.user_id <> request.user.id:
        return FailResponse(u"不是自己的作品")
    if auth_opus.opus_type==0:
        if auth_opus.status not in (-2, -1, 0): return FailResponse(u'只有草稿状态的作品才能编辑')
    else: pass 
    
    if page_index == new_page_index:
        return FailResponse(u"交换前后页码不能相同")
    
    try: auth_opus_page = AuthOpusPage.objects.get(auth_opus_id=opus_id, page_index=page_index)
    except: return FailResponse(u"交换前页码不能正确")
    
    try: auth_opus_page2 = AuthOpusPage.objects.get(auth_opus_id=opus_id, page_index=new_page_index)
    except: return FailResponse(u"交换后页码不能正确")
    
    if request.session.has_key("auth_opus:%s" % opus_id):
        return FailResponse(request.session["auth_opus:%s" % opus_id])
    request.session["auth_opus:%s" % opus_id] = u"正在删除当前作品的第%s页，请稍候" % page_index
    
    auth_opus_page.page_index = new_page_index
    auth_opus_page.save()
    auth_opus_page2.page_index = page_index
    auth_opus_page2.save()
    
    del request.session["auth_opus:%s" % opus_id]
    return SuccessResponse(new_page_index)
    
    
@login_required
def grade_opus(request, opus_id, grade):
    if request.user.auth_type == 5: return FailResponse(u'游客不能评级!')
    
    try: auth_opus = AuthOpus.objects.get(id=opus_id)
    except(AuthOpus.DoesNotExist): return FailResponse(u"不存在的作品ID:%d" % opus_id)
    
    if auth_opus.status <> 2:
        return FailResponse(u'作品不是发表状态，不能评论')
    
    if grade not in range(1, 6):
        return FailResponse(u'分值只能为1-5之间的整数')
    
    if auth_opus.library_id and auth_opus.library_id <> request.user.library_id:
        return FailResponse(u'没有权限对此作品评级')
    
    if AuthOpusGrade.objects.filter(auth_opus_id=auth_opus.id).count() > 0:
        return FailResponse(u'已经对此作品作过评分')
    
    auth_opus_grade = AuthOpusGrade()
    auth_opus_grade.user = request.user
    auth_opus_grade.library_id = request.user.library_id
    auth_opus_grade.grade = grade
    auth_opus_grade.save()
    
    auth_opus.total_grade += grade
    auth_opus.grade_times += 1
    auth_opus.grade = "%.1f" % auth_opus.total_grade*1.0/auth_opus.grade_times 
    auth_opus.save()
    
    return SuccessResponse({"id":auth_opus.id})

@login_required
def grade_opus_mongo(request, opus_id, grade):
    if request.user.auth_type == 5: return FailResponse(u'游客不能评级!')
    
    try: auth_opus = AuthOpus.objects.get(id=opus_id)
    except(AuthOpus.DoesNotExist): return FailResponse(u"不存在的作品ID:%d" % opus_id)
    
    if auth_opus.status <> 2:
        return FailResponse(u'作品不是发表状态，不能评论')
    
    if grade not in range(1, 6):
        return FailResponse(u'分值只能为1-5之间的整数')
    
    if auth_opus.library_id and auth_opus.library_id <> request.user.library_id:
        return FailResponse(u'没有权限对此作品评级')
    
    from mongodb import AuthOpusGradeMongo
    if AuthOpusGradeMongo.objects(auth_opus_id=auth_opus.id).count() > 0:
        return FailResponse(u'已经对此作品作过评分')
    
    auth_opus_grade_mongo = AuthOpusGradeMongo(user_id=request.user.id, library_id=request.user.library_id,auth_opus_id=auth_opus.id)
    auth_opus_grade_mongo.grade = grade
    auth_opus_grade_mongo.save()
    
    auth_opus.total_grade += grade
    auth_opus.grade_times += 1
    auth_opus.grade = "%.1f" % auth_opus.total_grade*1.0/auth_opus.grade_times 
    auth_opus.save()
    
    return SuccessResponse({"id":auth_opus.id})
    
@login_required
def comment_opus(request, opus_id, comment):
    if len(comment) <= 5:
        return FailResponse(u'评论内容过短')
    
    if len(comment) == 0 or len(comment) > 500:
        return FailResponse(u'评论内容过长')
    
    if request.user.auth_type == 5: return FailResponse(u'游客不能评论!')
    
    try: auth_opus = AuthOpus.objects.get(id=opus_id)
    except(AuthOpus.DoesNotExist): return FailResponse(u"不存在的作品ID:%d" % opus_id)
    
    if auth_opus.status <> 2:
        return FailResponse(u'作品不是发表状态，不能评论')
        
    #if auth_opus.library_id and auth_opus.library_id <> request.user.library_id:
    #   return FailResponse(u'没有权限对此作品进行评论')
    
    auth_opus_comment = AuthOpusComment()
    auth_opus_comment.user = request.user
    auth_opus_comment.library_id = request.user.library_id
    auth_opus_comment.auth_opus_id = auth_opus.id
    auth_opus_comment.comment = comment
    auth_opus_comment.save()
    
    #发个人消息
    auth_message = AuthMessage()
    auth_message.user_id = auth_opus.user_id
    auth_message.from_user_id = request.user.id
    auth_message.opus_id = auth_opus.id
    auth_message.msg_type = 3   #作品评论
    auth_message.content = comment
    auth_message.save()
    
    auth_opus.comment_times += 1
    auth_opus.save()
    
    return SuccessResponse({"id":auth_opus.id})      
    
    
@login_required
def get_comment_list(request, opus_id, page_index=1, page_size=20):
    try: auth_opus = AuthOpus.objects.get(id=opus_id)
    except(AuthOpus.DoesNotExist): return FailResponse(u"不存在的作品ID:%d" % opus_id)
    
    if auth_opus.status <> 2:
        return FailResponse(u'作品不是发表状态，不能得到评论列表')
    
    where_clause = "auth_opus_id=%s" % opus_id
    cursor = connections[DB_READ_NAME].cursor()
    sql = "select count(*) from auth_opus_comment where %s" % where_clause
    cursor.execute(sql)
    row = cursor.fetchone()
    count = 0
    if row: count = row[0]
    page_count = int(ceil(count/float(page_size)))
    
    sql = "select c.id,user_id,nickname,`comment`,create_time from auth_opus_comment c LEFT JOIN auth_user u on u.id=c.user_id"
    sql += " where %s order by create_time desc limit %d, %d" % (where_clause, (page_index-1)*page_size, page_size)
    #print sql
    
    cursor.execute(sql)
    rows = cursor.fetchall()
    comm_list = []
    for row in rows:
        if not row: continue
        comm_list.append({"id":row[0],"user_id":row[1],"nickname":row[2],"comment":row[3],"create_time":row[4].strftime("%Y-%m-%d %H:%M:%S")})
        
    return SuccessResponse({"data":comm_list, "page_index":page_index, "page_count":page_count})
    

@login_required
def comment_opus_mongo(request, opus_id, comment):
    if len(comment) <= 5:
        return FailResponse(u'评论内容过短')
    
    if len(comment) == 0 or len(comment) > 500:
        return FailResponse(u'评论内容过长')
    
    if request.user.auth_type == 5: return FailResponse(u'游客不能评论!')
    
    try: auth_opus = AuthOpus.objects.get(id=opus_id)
    except(AuthOpus.DoesNotExist): return FailResponse(u"不存在的作品ID:%d" % opus_id)
    
    if auth_opus.status <> 2:
        return FailResponse(u'作品不是发表状态，不能评论')
        
    #if auth_opus.library_id and auth_opus.library_id <> request.user.library_id:
    #   return FailResponse(u'没有权限对此作品进行评论')
    
    from mongodb import AuthOpusCommentMongo
    
    auth_opus_comment_mongo = AuthOpusCommentMongo(user_id=request.user.id, library_id=request.user.library_id,auth_opus_id=auth_opus.id)
    auth_opus_comment_mongo.comment = comment
    auth_opus_comment_mongo.save()
    
    #发个人消息
    auth_message = AuthMessage()
    auth_message.user_id = auth_opus.user_id
    auth_message.from_user_id = request.user.id
    auth_message.opus_id = auth_opus.id
    auth_message.msg_type = 3   #作品评论
    auth_message.content = comment
    auth_message.save()
    
    auth_opus.comment_times += 1
    auth_opus.save()
    
    return SuccessResponse({"id":auth_opus.id})      
    
    
@login_required
def get_comment_list_mongo(request, opus_id, page_index=1, page_size=20):
    try: auth_opus = AuthOpus.objects.get(id=opus_id)
    except(AuthOpus.DoesNotExist): return FailResponse(u"不存在的作品ID:%d" % opus_id)
    
    if auth_opus.status <> 2:
        return FailResponse(u'作品不是发表状态，不能得到评论列表')
    
    from mongodb import AuthOpusCommentMongo
    count = AuthOpusCommentMongo.objects(auth_opus_id=opus_id).count()
    page_count = int(ceil(count/float(page_size)))
    
    
    comment_list_mongo = AuthOpusCommentMongo.objects(auth_opus_id=opus_id).order_by("-create_time").skip((page_index-1)*page_size).limit(page_size);
    
    comm_list = []
    uid_dict = {}
    for comment in comment_list_mongo:
        #avatar_img = MEDIA_URL + row[5] if row[5] else ""
        comm_list.append({"user_id":int(comment.user_id),"comment":comment.comment,"create_time":comment.create_time.strftime("%Y-%m-%d %H:%M:%S")})
        uid_dict[str(comment.user_id)] = None
    if len(uid_dict) > 0:
        sql = "select id, nickname, avatar_img from auth_user where id in (%s)" % ','.join(uid_dict.keys())
        cursor = connections[DB_READ_NAME].cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        for row in rows:
            uid = int(row[0])
            nickname = row[1]
            avatar_img = MEDIA_URL + row[2] if row[2] else ""
            for comm in comm_list:
                if comm["user_id"] == uid:
                    comm["nickname"] = nickname
                    comm["avatar_img"] = avatar_img
    return SuccessResponse({"data":comm_list, "page_index":page_index, "page_count":page_count})
    


@login_required
def praise_opus(request, opus_id):
    if request.user.auth_type == 5: return FailResponse(u'游客不能点赞!')
    
    try: auth_opus = AuthOpus.objects.get(id=opus_id)
    except(AuthOpus.DoesNotExist): return FailResponse(u"不存在的作品ID:%d" % opus_id)
    
    if auth_opus.status <> 2:
        return FailResponse(u'作品不是发表状态，不能评论')
    
    #sql = "select count(*) from auth_opus_praise where user_id=%d and auth_opus_id=%s" % (request.user.id, opus_id)
    #print sql
    if AuthOpusPraise.objects.filter(user_id=request.user.id, auth_opus_id=opus_id).count() > 0:
        return FailResponse(u'已经赞过，不要重复赞')
        
#     if auth_opus.library_id and auth_opus.library_id <> request.user.library_id:
#         return FailResponse(u'没有权限对此作品进行评论')
    
    auth_opus_praise = AuthOpusPraise()
    auth_opus_praise.user = request.user
    auth_opus_praise.library_id = request.user.library_id
    auth_opus_praise.auth_opus_id = auth_opus.id
    auth_opus_praise.save()
    
    #发个人消息
    auth_message = AuthMessage()
    auth_message.user_id = auth_opus.user_id
    auth_message.from_user_id = request.user.id
    auth_message.opus_id = auth_opus.id
    auth_message.msg_type = 4   #作品点赞
    auth_message.content = u"作品[%s]被用户(%s)赞了。" % (auth_opus.title, request.user.nickname)
    auth_message.save()
    
    auth_opus.praise_times += 1
    auth_opus.save()
    
    return SuccessResponse({"id":auth_opus.id, "praise_times":auth_opus.praise_times})     

    
@login_required
def praise_opus_mongo(request, opus_id):
    if request.user.auth_type == 5: return FailResponse(u'游客不能点赞!')
    
    try: auth_opus = AuthOpus.objects.get(id=opus_id)
    except(AuthOpus.DoesNotExist): return FailResponse(u"不存在的作品ID:%d" % opus_id)
    
    if auth_opus.status <> 2:
        return FailResponse(u'作品不是发表状态，不能评论')
    
    from mongodb import AuthOpusPraiseMongo
    if AuthOpusPraiseMongo.objects(user_id=request.user.id, auth_opus_id=opus_id).count() > 0:
        return FailResponse(u'已经赞过，不要重复赞')
        
#     if auth_opus.library_id and auth_opus.library_id <> request.user.library_id:
#         return FailResponse(u'没有权限对此作品进行评论')
    
    auth_opus_praise_mongo = AuthOpusPraiseMongo(user_id=request.user.id, library_id=request.user.library_id, auth_opus_id=auth_opus.id)
    auth_opus_praise_mongo.save()
    
    #发个人消息
    auth_message = AuthMessage()
    auth_message.user_id = auth_opus.user_id
    auth_message.from_user_id = request.user.id
    auth_message.opus_id = auth_opus.id
    auth_message.msg_type = 4   #作品点赞
    auth_message.content = u"作品[%s]被用户(%s)赞了。" % (auth_opus.title, request.user.nickname)
    auth_message.save()
    
    auth_opus.praise_times += 1
    auth_opus.save()
    
    return SuccessResponse({"id":auth_opus.id, "praise_times":auth_opus.praise_times})     


def cancel_opus_wait(request, param):
    '''
    editor: kamihati 2015/6/16 把原创作品从待审核撤回草稿状态。
    :param request:
    :param param:
    :return:
    '''
    opus_id = param.opus_id if param.has_key('opus_id') else 0
    opus = AuthOpus.objects.filter(pk=opus_id)
    if not opus:
        return FailResponse(u'作品不存在')
    opus = opus[0]
    if opus.user_id != request.user.id:
        return FailResponse(u'当前用户不是此作品的作者！')
    if opus.status != 1:
        return FailResponse(u'只能撤回待审核状态的作品！')
    opus.status = 0
    opus.save()
    return SuccessResponse(u'操作成功！')

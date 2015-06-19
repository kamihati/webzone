# coding=utf8
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
import os

# 导入MEDIA_配置
from WebZone.settings import MEDIA_URL, MEDIA_ROOT
# 导入获取机构资源路径的方法
from utils import get_lib_path
# 导入计算小缩略图尺寸的方法
from utils import  get_small_size
# 导入移动临时文件的方法
from utils.decorator import move_temp_file
from PIL import Image

# 导入异常输出方法
from utils.decorator import print_trace
# 导入资源分类和资源风格model
from resources.models import ResourceType, ResourceStyle
# 导入个人素菜分类model
from resources.models import ResourceTypePerson
# 导入个人素材model
from diy.models import AuthAsset
# 导入公共素材model
from diy.models import ZoneAsset
# 导入记录管理员操作记录的方法
from manager import add_manager_action_log
# 导入页面尺寸表
from widget.models import WidgetPageSize


@print_trace
def ajax_create_resource_type(request):
    '''
    增加资源类型的异步调用方法
    :param request:
        param.name : 资源类别名称
    :return:
    '''
    name = request.POST.get('name', '')
    if name == '':
        # 参数错误
        return HttpResponse("-1")
    if ResourceType.objects.filter(name=name):
        return HttpResponse('-2')
    # 名称不能大于6个字
    if len(name) > 6:
        return HttpResponse('-3')
    if ResourceType.objects.create(name=name, user_id=request.user.id):
        return HttpResponse("ok")
    return HttpResponse('fail')


def ajax_create_resource_type_person(request):
    '''
    增加个人素菜类型的异步调用方法
    :param request:
        param.name : 资源类别名称
    :return:
    '''
    name = request.POST.get('name', '')
    if name == '':
        # 参数错误
        return HttpResponse("-1")
    if ResourceTypePerson.objects.filter(name=name):
        return HttpResponse('-2')
    # 名称不能大于6个字
    if len(name) > 6:
        return HttpResponse('-3')
    if ResourceTypePerson.objects.create(name=name, user_id=request.user.id):
        return HttpResponse("ok")
    return HttpResponse('fail')


@print_trace
def ajax_alter_resource_type(request):
    '''
    修改资源类型的异步调用方法
    :param request:
        param.id: 资源类别id
        param.name : 资源类别名称
    :return:
    '''
    name = request.POST.get('name', '')
    id = int(request.POST.get('id', 0))
    if name == '' or id == 0:
        # 参数错误
        return HttpResponse("-1")
    if ResourceType.objects.filter(name=name).exclude(id=id):
        # 已存在相同类别名称
        return HttpResponse('-2')
    # 名称不能大于6个字
    if len(name) > 6:
        return HttpResponse('-3')
    if ResourceType.objects.filter(pk=id).update(name=name):
        return HttpResponse("ok")
    return HttpResponse('fail')


@print_trace
def ajax_alter_resource_type_person(request):
    '''
    修改资源类型的异步调用方法
    :param request:
        param.id: 资源类别id
        param.name : 资源类别名称
    :return:
    '''
    name = request.POST.get('name', '')
    id = int(request.POST.get('id', 0))
    if name == '' or id == 0:
        # 参数错误
        return HttpResponse("-1")
    if ResourceTypePerson.objects.filter(name=name).exclude(id=id):
        # 已存在相同类别名称
        return HttpResponse('-2')
    # 名称不能大于6个字
    if len(name) > 6:
        return HttpResponse('-3')
    if ResourceTypePerson.objects.filter(pk=id).update(name=name):
        return HttpResponse("ok")
    return HttpResponse('fail')


@print_trace
def ajax_create_resource_style(request):
    '''
    增加资源风格的异步调用方法
    :param request:
        param.name : 资源风格名称
    :return:
    '''
    name = request.POST.get('name', '')
    if name == '':
        # 参数错误
        return HttpResponse("-1")
    # 名称不能大于6个字
    if len(name) > 6:
        return HttpResponse('-3')
    if ResourceStyle.objects.filter(name=name):
        return HttpResponse('-2')
    if ResourceStyle.objects.create(name=name,user_id=request.user.id):
        return HttpResponse("ok")
    return HttpResponse('fail')


@print_trace
def ajax_alter_resource_style(request):
    '''
    修改资源风格的异步调用方法
    :param request:
        param.id: 资源风格id
        param.name : 资源风格名称
    :return:
    '''
    name = request.POST.get('name', '')
    id = int(request.POST.get('id', 0))
    if name == '' or id == 0:
        # 参数错误
        return HttpResponse("-1")
    # 名称不能大于6个字
    if len(name) > 6:
        return HttpResponse('-3')
    if ResourceStyle.objects.filter(name=name).exclude(id=id):
        # 已存在相同风格名称
        return HttpResponse('-2')
    if ResourceStyle.objects.filter(pk=id).update(name=name):
        return HttpResponse("ok")
    return HttpResponse('fail')


@print_trace
def ajax_drop_type(request):
    '''
    删除资源类型
    :param request:
    :return:
    '''
    id = request.POST.get('id', 0)
    if ResourceType.objects.filter(pk=id).update(status=1):
        return HttpResponse('ok')
    return HttpResponse('fail')


def ajax_drop_person_type(request):
    '''
    删除个人资源类型
    :param request:
    :return:
    '''
    id = request.POST.get('id', 0)
    if ResourceTypePerson.objects.filter(pk=id).update(status=1):
        return HttpResponse('ok')
    return HttpResponse('fail')


@print_trace
def ajax_drop_style(request):
    '''
    删除资源风格
    :param request:
    :return:
    '''
    id = request.POST.get('id', 0)
    if ResourceStyle.objects.filter(pk=id).update(status=1):
        return HttpResponse('ok')
    return HttpResponse('fail')


def ajax_del_person_res(request):
    '''
    删除个人资源
    :param request:
        request.POST.get('id')  资源id
    :return:
           'ok': 成功。 'fail': 失败
    '''
    id = request.POST.get('id', 0)
    if AuthAsset.objects.filter(pk=id).update(status=-1):
        return HttpResponse('ok')
    return HttpResponse('fail')


def ajax_del_common_res(request):
    '''
    删除公共资源
    :param request:
          request.POST.get('id')  素材id
    :return:
          'ok'成功，   'fail':失败
    '''
    id = request.POST.get("id", 0)
    if ZoneAsset.objects.filter(pk=id).update(status=-1):
        return HttpResponse("ok")
    return HttpResponse('fail')


def view_resource_origin(request):
    """
    查看指定id的素材
    :param request:
    :return:
    """
    # 素材id
    id = request.GET.get('id', 0)
    # 是否个人素材.0为否。１为是
    is_person = int(request.GET.get('is_person', 0))
    origin_path = ''
    if is_person == 0:
        asset = ZoneAsset.objects.get(pk=id)
        origin_path = asset.origin_path if asset.origin_path else asset.img_large_path
    elif is_person == 1:
        asset = AuthAsset.objects.get(id=id)
        origin_path = asset.origin_path if asset.origin_path else asset.img_large_path
    return HttpResponseRedirect(MEDIA_URL + origin_path)


def update_asset_status(request):
    '''
    修改公共素材状态ZoneAsset
    editor: kamihati 2015/5/11
    :param request:
           request.POST.get("id")  素材id
           request.POST.get("status")   -1 为禁用  1为正常
    :return:
    '''
    id = request.POST.get('id', 0)
    status = request.POST.get('status', 1)
    if ZoneAsset.objects.filter(pk=id).update(is_recommend=status):
        return HttpResponse("ok")
    return HttpResponse("fail")


@print_trace
def api_edit_resource(request):
    '''
    编辑公共素材
    editor: kamihati 2015/5/11
    :param request:
    :return:
    '''
    id = request.POST.get('id', '')
    title = request.POST.get('title', '')
    temp_path = request.POST.get('temp', '')
    # 类型
    res_type = int(request.POST.get('res_type', ''))
    # 风格
    res_style = int(request.POST.get('res_style', ''))

    # 创建类型。单页。双页
    create_type = request.POST.get('create_type', 1)
    temp2_path = request.POST.get('temp2', '')
    zone_asset = ZoneAsset()
    if id != '':
        zone_asset = ZoneAsset.objects.get(pk=id)

    zone_asset.res_type = res_type
    zone_asset.res_style = res_style
    zone_asset.res_title = title
    zone_asset.user = request.user
    zone_asset.library = request.user.library
    zone_asset.page_type = 0
    zone_asset.layout_type_id = 0
    zone_asset.save()

    if res_type == 1:
        # 背景素材需要宽高和创建类型
        # 尺寸id
        size_id = int(request.POST.get('size', 0))
        if size_id == 0:
            return HttpResponse('-1')
        zone_asset.size_id = size_id
        zone_asset.create_type = create_type
        zone_asset.save()
    elif res_type in (3, 8):
        # 边框。 特效  需要上传第二资源
        if temp2_path == '' and id == '':
            return HttpResponse('-2')
        asset_res_path = "%s/%d" % (get_lib_path(request.user.library, res_type), zone_asset.id)
        if not os.path.exists(os.path.join(MEDIA_ROOT, asset_res_path)):
            os.makedirs(os.path.join(MEDIA_ROOT, asset_res_path))
        hid_mask_path = temp2_path
        ext = os.path.splitext(hid_mask_path)[1]
        if hid_mask_path.find("temp") != -1:
            # 画框
            if res_type == 3:
                if not zone_asset.mask_path:
                    zone_asset.mask_path = "%s/%d/mask%s" % (
                        get_lib_path(request.user.library, res_type), zone_asset.id, os.path.splitext(hid_mask_path)[1])
                open(os.path.join(MEDIA_ROOT, zone_asset.mask_path), "wb").write(open(os.path.join(MEDIA_ROOT, hid_mask_path), "rb").read())
            elif res_type == 8:
                # 特效类型存储源文件。
                zone_asset.origin_path = "%s/%s.swf" % (asset_res_path, zone_asset.id)
                open(os.path.join(MEDIA_ROOT, zone_asset.origin_path), "wb").write(open(os.path.join(MEDIA_ROOT, hid_mask_path), "rb").read())
            os.remove(os.path.join(MEDIA_ROOT, hid_mask_path))
            zone_asset.save()

    # 生成资源路径
    asset_res_path = "assets/%s/%s/%s" % (res_type, res_style, zone_asset.id)
    hid_res_path = temp_path
    ext = os.path.splitext(hid_res_path)[1] #扩展名 .swf等
    if hid_res_path.find("temp") != -1:
        zone_asset.res_path = "%s/origin%s" % (asset_res_path, ext)
        if res_type in (1, 2, 3, 4, 7, 8):
            if ext.lower() not in (".swf"):
                zone_asset.img_large_path = zone_asset.res_path.replace("origin", "l")
                zone_asset.img_medium_path = zone_asset.res_path.replace("origin", "m")
                zone_asset.img_small_path = zone_asset.res_path.replace("origin", "s")
            elif ext.lower() in (".swf"):
                zone_asset.img_large_path = zone_asset.res_path
                zone_asset.img_medium_path = zone_asset.res_path
                zone_asset.img_small_path = zone_asset.res_path
        elif res_type == 5: #声音
            zone_asset.res_path = "%s/%s.mp3" % (asset_res_path, zone_asset.id)
        elif res_type == 6: #视频
            zone_asset.res_path = "%s/%s.flv" % (asset_res_path, zone_asset.id)
            zone_asset.img_large_path = "%s/l.jpg" % asset_res_path  #存视频截图的原图
            zone_asset.img_small_path = "%s/s.jpg" % asset_res_path
        elif res_type == 8: #特效
            pass
            # open(os.path.join(MEDIA_ROOT, zone_asset.res_path), "wb").write(open(os.path.join(MEDIA_ROOT, hid_res_path), "rb").read())
        # 移动临时文件到指定目录
        zone_asset.res_path = move_temp_file(temp_path, "%s/origin" % asset_res_path)
        #try: os.remove(os.path.join(MEDIA_ROOT, hid_res_path))
        #except: pass

        # 处理图片素材的缩略图
        if res_type in (1, 8) or ext.lower() not in (".swf"):
            img = Image.open(os.path.join(MEDIA_ROOT, zone_asset.res_path))
            zone_asset.width = img.size[0]
            zone_asset.height = img.size[1]

            if img.size[0] > 950 or img.size[1] > 950:
                img.thumbnail((950,950), Image.ANTIALIAS)
                img.save(os.path.join(MEDIA_ROOT, zone_asset.img_large_path))
            else:
                zone_asset.img_large_path = zone_asset.res_path

            if img.size[0] > 600 or img.size[1] > 600:
                img.thumbnail((600, 600), Image.ANTIALIAS)
                img.save(os.path.join(MEDIA_ROOT, zone_asset.img_medium_path))
            else:
                zone_asset.img_medium_path = zone_asset.res_path

            img.thumbnail(get_small_size(img.size[0], img.size[1]), Image.ANTIALIAS)
            img.save(os.path.join(MEDIA_ROOT, zone_asset.img_small_path))
        zone_asset.status = 1
        zone_asset.save()
    #记录日志
    add_manager_action_log(request, u'%s编辑了公共素材[%s(%s)]' % (request.user, zone_asset.res_title, ResourceType.objects.get(pk=res_type).name))
    return HttpResponse("ok")


@print_trace
def api_size_edit(request):
    '''
    编辑作品尺寸
    editor: kamihati 2015/5/13
    :param request:
    :return:
    '''
    hid_id = request.POST.get('id', '')
    create_type = int(request.POST.get('create_type', 1))
    read_type = int(request.POST.get('read_type', 1))
    name = request.POST.get('title', '')
    screen_width = int(request.POST.get('screen_width', 0))
    screen_height = int(request.POST.get('screen_height', 0))
    print_width = float(request.POST.get('print_width', 0))
    print_height = float(request.POST.get('print_height', 0))
    origin_width = int(request.POST.get('origin_width', ''))
    origin_height = int(request.POST.get('origin_height', ''))
    temp_type = int(request.POST.get('temp_type', 1))
    res_path = request.POST.get("res_path")
    widget_pages_size = WidgetPageSize()
    if hid_id != "":
        widget_pages_size = WidgetPageSize.objects.get(pk=hid_id)

    widget_pages_size.name = name
    widget_pages_size.create_type = create_type
    widget_pages_size.read_type = read_type
    widget_pages_size.screen_width = screen_width
    widget_pages_size.screen_height = screen_height
    widget_pages_size.print_width = print_width
    widget_pages_size.print_height = print_height
    widget_pages_size.origin_width = origin_width
    widget_pages_size.origin_height = origin_height
    widget_pages_size.temp_type = temp_type
    widget_pages_size.save()
    if res_path.find("temp") >= 0:  #有新上传文件
        ext = os.path.splitext(res_path)[1]
        if ext not in ('.jpg','.jpeg','.png','.gif','.bmp'):
            return HttpResponse(u"上传图片格式不正确:%s" % ext)
        res_type = 21   # 作品尺寸图片
        asset_res_path = "%s/%s" % (get_lib_path(request.user.library, res_type), widget_pages_size.id)
        if not os.path.exists(os.path.join(MEDIA_ROOT, asset_res_path)):
            os.makedirs(os.path.join(MEDIA_ROOT, asset_res_path))
        widget_pages_size.res_path = "%s/origin%s" % (asset_res_path, ext)
        widget_pages_size.img_small_path = widget_pages_size.res_path.replace("origin", "s")
        move_temp_file(res_path, asset_res_path + "/origin")
        # open(os.path.join(MEDIA_ROOT, widget_pages_size.res_path), "wb").write(open(os.path.join(MEDIA_ROOT, widget_pages_size.res_path), "rb").read())
        # try: os.remove(os.path.join(MEDIA_ROOT, res_path))
        # except: pass
        from PIL import Image
        img = Image.open(os.path.join(MEDIA_ROOT, widget_pages_size.res_path))
        #print get_small_size(img.size[0], img.size[1])
        img.thumbnail(get_small_size(img.size[0], img.size[1]), Image.ANTIALIAS)
        img.save(os.path.join(MEDIA_ROOT, widget_pages_size.img_small_path))
        widget_pages_size.save()
    #记录日志
    #add_manager_action_log(request, u'%s新建/更新了作品页尺寸：[%s(%sx%s)]' % (request.user, widget_pages_size.name, widget_pages_size.print_width, widget_pages_size.print_height))
    return HttpResponse("ok")


def api_get_widget_page_size(request):
    '''
    获取指定的页面尺寸信息
    editor: kamihati 2015/5/13
    :param request:
    :return:
    '''
    size = WidgetPageSize.objects.get(pk=request.GET.get('id'))
    result = dict(id=size.id,
                  name=size.name,
                  create_type=size.create_type,
                  read_type=size.read_type,
                  screen_height=size.screen_height,
                  screen_width=size.screen_width,
                  print_height=size.print_height,
                  print_width=size.print_width,
                  origin_height=size.origin_height,
                  origin_width=size.origin_width,
                  res_path=size.res_path,
                  temp_type=size.temp_type)
    import json
    return HttpResponse(json.dumps(result))

# coding=utf8
import os
from django.shortcuts import render
from django.http import HttpResponse

from WebZone.settings import MEDIA_URL
from WebZone.settings import MEDIA_ROOT

from utils.db_handler import  get_json_str
# 导入管理员权限验证
from utils.decorator import manager_required, print_trace
# 导入向客户端输出json字符串流的方法
from utils import json_response
# 导入根据相对路径获取完整url的方法
from utils.decorator import get_host_file_url

# 导入话题model
from topic.models import Topic
# 导入话题评论model
from topic.models import TopicRemark
# 导入话题资源，评论资源model
from topic.models import TopicResource, RemarkResource

# 导入更新话题状态方法
from topic.handler import update_topic_status
# 导入更新话题置顶状态方法
from topic.handler import update_topic_top
# 导入搜索话题方法
from topic.handler import search_topic_dict
# 导入搜索话题评论方法
from topic.handler import search_comment_dict
# 导入搜索话题表情方法
from topic.handler import search_emotion_list
# 导入评论删除
from topic.handler import delete_remark
# 导入话题表情类型
from topic.models import PhizType
# 导入公共素菜表用作表情处理   res_type=12  为表情
from diy.models import ZoneAsset
# 获取当前用户的素材路径, 增加管理员操作记录
from manager.views import get_asset_path, add_manager_action_log
# 导入获取话题和话题评论资源明细的方法
from topic.resource_handler import get_topic_resource_dict, get_remark_resource_dict


def search_topic_list_json(request):
    '''
    把查询到的话题数据转为json返回给页面post请求
    请求方法：GET
    参数： page_index:   页码。从0开始计数
           page_count:    步长。
           search_text:   搜索关键字
           sheng: 省
           shi: 市名
           xian: 县区名称
           library: 机构id
    coder by: kamihati   2015/3/16
    coder: kamihati 2015/3/23  返回结果里面增加data_count字段供客户端计算页数
    '''

    sheng = request.GET.get('sheng', '')
    shi = request.GET.get('shi', '')
    xian = request.GET.get('xian', '')
    library_id = request.GET.get("library", '')

    if library_id != '':
        library_id = int(library_id)

    search_text = request.GET.get('search_text', '')
    page_index = request.GET.get("page_index", 1)
    page_size = request.GET.get("page_size", 15)
    data, data_count = search_topic_dict(
        search_text,
        int(page_index) - 1,
        int(page_size),
        privince=sheng,
        city=shi,
        region=xian,
        library_id=library_id
    )

    return HttpResponse(
        get_json_str({'data': data,
                      'page_index': page_index, 'page_size': page_size,  'data_count': data_count,
                      'search_text': search_text, 'sheng': sheng, 'shi': shi, 'xian': xian, 'library_id': library_id}))


def ajax_update_topic_status(request):
    '''
    更新话题状态
    参数描述：
          id:话题id
          status: 话题状态 （0: 正常， 1: 被删除）
    coder: kamihati 2015/3/13
    coder: kamihati 2015/3/20  新版话题只有两种状态。正常和被删除
    '''
    if update_topic_status(request.POST.get("id"), request.POST.get("status")):
        return HttpResponse('ok')
    return HttpResponse('fail')


def ajax_update_topic_top(request):
    '''
    更新话题置顶状态
    参数描述：
          id:话题id
          status: 话题状态 （0: 正常， 1: 被删除）
    coder: kamihati 2015/3/13
    coder: kamihati 2015/3/20  新版话题只有两种状态。正常和被删除
    '''
    if update_topic_top(request.POST.get("id"), request.POST.get("status")):
        return HttpResponse('ok')
    return HttpResponse('fail')


def get_comment_by_id(request):
    '''
    获取指定评论的数据
    -------------------
    参数描述:
        id: 评论id
    coder: kamihati 2015/3/20
    mark: 未完成
    '''
    id = int(request.GET.get('id', 0))
    data_obj = dict()
    return HttpResponse(get_json_str(data_obj))


def remove_topic_remark(request):
    '''
    删除话题评论
    :param request:
         id: 评论id
    :return:
        删除成功返回ok .失败返回fail
    '''
    if delete_remark(request.POST.get("id", 0)):
        return HttpResponse("ok")
    return HttpResponse("fail")


@print_trace
def edit_phiz_type(request):
    '''
    修改话题表情类型
    coder: kamihati 2015/3/19
    '''
    id = int(request.POST.get("id", 0))
    name = request.POST.get("name", '')
    if PhizType.objects.filter(name=name).exclude(id=id):
        # 由于名称有重复修改失败
        return HttpResponse(0)
    if PhizType.objects.filter(id=id).update(name=name):
        return  HttpResponse('ok')
    return HttpResponse('fail')


def add_phiz_type(request):
    '''
    创建话题表情类型
    coder: kamihati 2015/3/19
    '''
    name = request.POST.get("name", 'name')
    if PhizType.objects.filter(name=name):
        # 由于名称有重复修改失败
        return HttpResponse(0)
    PhizType.objects.create(name=name, user_id=request.user.id, status=0)
    return HttpResponse("ok")


def remove_phiz_type(request):
    '''
    删除话题表情类型
    coder: kamihati 2015/3/19
    '''
    id = request.POST.get("id", 0)
    if PhizType.objects.filter(id=id).update(status=1):
        return HttpResponse("ok")
    # 删除成功
    return HttpResponse("fail")


@print_trace
def add_phiz(request):
    '''
    增加表情  写入ZoneAsset表 res_type=12
    coder: kamihati 2015/4/6
    :param request:
    :return:
    '''
    phiz_type = int(request.POST.get("phiz_type", 0))
    phiz_name = request.POST.get('phiz_name', '')
    phiz_path = request.POST.get("phiz_path", '')
    mark = request.POST.get('mark', '')
    width = request.POST.get('width', 0)
    height = request.POST.get('height', 0)
    phiz = ZoneAsset()
    phiz.user_id = request.user.id
    phiz.library = request.user.library
    phiz.res_type = 12
    # 图片处理完毕前设为删除状态。
    phiz.status = -1
    phiz.res_title = phiz_name
    phiz.type_id = phiz_type
    if ZoneAsset.objects.filter(mark_id=mark, status=1).count() != 0:
        return HttpResponse("-2")
    phiz.mark_id = mark
    phiz.width = width
    phiz.height = height
    phiz.save()
    return  HttpResponse(handle_phiz_file(request, phiz, phiz_path))


@print_trace
def edit_phiz(request):
    '''
    编辑话题表情。写入ZoneAsset表  res_type=12
    coder: kamihati 2015/4/6
    :param request:
    :return:
    '''
    id = int(request.POST.get("id", 0))
    phiz_type = int(request.POST.get("phiz_type", 0))
    phiz_name = request.POST.get('phiz_name', '')
    phiz_path = request.POST.get("phiz_path", '')
    mark = request.POST.get('mark', '')
    width = request.POST.get('width', 0)
    height = request.POST.get('height', 0)
    phiz = ZoneAsset.objects.get(id=id)
    phiz.type_id = phiz_type
    phiz.res_title = phiz_name
    phiz.width = width
    phiz.height = height
    if ZoneAsset.objects.filter(mark_id=mark, status=1).exclude(pk=id).count() !=0:
        return HttpResponse('-2')
    phiz.mark_id = mark
    phiz.save()

    result = 1
    if phiz_path != "":
        result = handle_phiz_file(request, phiz, phiz_path)
    return HttpResponse(result)


def handle_phiz_file(request, phiz, phiz_path):
    '''
    处理表情上传的逻辑
    :param request:
    :param phiz:
    :param phiz_path:
    :return:
    '''
    asset_res_path = "%s/%d" % (get_asset_path(request, 12), phiz.id)
    if not os.path.exists(os.path.join(MEDIA_ROOT, asset_res_path)):
        os.makedirs(os.path.join(MEDIA_ROOT, asset_res_path))

    if phiz_path.find("temp") >= 0:  #有新上传文件
        ext = os.path.splitext(phiz_path)[1] #扩展名
        if ext not in ('.jpg','.jpeg','.png','.gif','.bmp'):
            # 格式不正确
            return -1

        phiz.res_path = "%s/origin%s" % (asset_res_path, ext)
        phiz.img_small_path = phiz.res_path.replace("origin", "s")
        open(os.path.join(MEDIA_ROOT, phiz.res_path), "wb").write(open(os.path.join(MEDIA_ROOT, phiz_path), "rb").read())
        try:
            os.remove(os.path.join(MEDIA_ROOT, phiz_path))
        except:
            pass

        from PIL import Image
        img = Image.open(os.path.join(MEDIA_ROOT, phiz.res_path))

        if phiz.type_id == 1:
            # 默认
            img.thumbnail((36, 34), Image.ANTIALIAS)
        elif phiz.type_id == 2:
            # 蘑菇头
            img.thumbnail((45, 45), Image.ANTIALIAS)
        else:
            # 其他暂时使用蘑菇头的尺寸
            img.thumbnail((45, 45), Image.ANTIALIAS)

        img.save(os.path.join(MEDIA_ROOT, phiz.img_small_path))
        phiz.status = 1
        phiz.save()

        #记录日志
        add_manager_action_log(request, u'%s新建/更新了话题表情：[%s]' % (request.user, phiz.res_title))
        return 1


def remove_phiz(request):
    '''
    删除话题表情
    :param request:
    :return:
    '''
    id = request.POST.get("id", 0)
    if ZoneAsset.objects.filter(id=id).update(status=-1):
        return HttpResponse("ok")
    return HttpResponse("fail")


@print_trace
def remark_resource_detail(request):
    '''
    获取评论资源明细
    :param request:  .id  评论资源id
    :return:
    '''
    id = request.GET.get('id', 0)
    res_list = get_remark_resource_dict(id)
    for res in res_list:
        if not res:
            res_list.remove(res)
            continue
        res['thumbnail'] = MEDIA_URL + res['thumbnail'] if res['thumbnail'] else ''
        res['origin_path'] = MEDIA_URL + res['origin_path'] if res['origin_path'] else ''
    return json_response(res_list)


@print_trace
def topic_resource_detail(request):
    '''
    获取话题资源明细
    :param request:
    :return:
    '''
    id = request.GET.get('id', 0)
    res_list = get_topic_resource_dict(id)
    for res in res_list:
        if not res:
            res_list.remove(res)
            continue

        res['thumbnail'] = get_host_file_url(request, res['thumbnail']) if res['thumbnail'] else ''
        res['origin_path'] = get_host_file_url(request, res['origin_path']) if res['origin_path'] else ''
    return json_response(res_list)


def remove_topic_resource(request):
    '''
    移除话题引用的资源
    :param request: .id 话题资源id
    :return:
    '''
    TopicResource.objects.filter(pk=request.POST.get('id', 0)).delete()
    return HttpResponse('ok')

def remove_remark_resource(request):
    '''
    移除评论引用的资源
    :param request:.id 评论资源id
    :return:
    '''
    RemarkResource.objects.filter(pk=request.POST.get('id', 0)).delete()
    return HttpResponse('ok')


@print_trace
def edit_topic(request):
    '''
    编辑话题信息
    :param request: id, title, content
    :return:
    '''
    id = request.POST.get("id", 0)
    title = request.POST.get('title', "")
    content = request.POST.get("content", "")

    if Topic.objects.filter(pk=id).update(title=title, content=content):
        return  HttpResponse('ok')
    return HttpResponse('fail')


def edit_remark(request):
    '''
    编辑评论
    :param request: id, content
    :return:
    '''
    id = request.POST.get('id', 0)
    content = request.POST.get('content', '')

    if TopicRemark.objects.filter(pk=id).update(content=content):
        return  HttpResponse('ok')
    return  HttpResponse('fail')

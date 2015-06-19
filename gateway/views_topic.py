#coding:utf-8
'''
Created on 2014年11月17日

@author: Administrator
'''
import os
from math import ceil
from django.db import connections
from WebZone.settings import DB_READ_NAME

from WebZone.settings import MEDIA_URL, MEDIA_ROOT
from WebZone.conf import TOPIC_TYPE_CHOICES

from utils.decorator import login_required
from gateway import SuccessResponse, FailResponse
from diy.models import  AuthTopicPage, AuthTopic
from diy.models import AuthAsset, AuthOpus
from account.models import AuthUser

from utils import get_user_path

from WebZone.conf import ALLOWED_IMG_UPLOAD_SIZE, ALLOWED_IMG_EXTENSION
from StringIO import StringIO
from PIL import Image
from utils import get_img_ext
# 导入话题与话题评论model
from topic.models import Topic, TopicRemark
# 导入话题点赞和评论点赞方法
from topic.handler import add_topic_praise, add_remark_praise
# 导入话题资源model
from topic.models import TopicResource, RemarkResource
# 导入添加话题评论，搜索话题评论列表的方法
from topic.handler import  add_topic_remark,search_comment_dict
# 导入添加话题。编辑话题方法
from topic.handler import add_topic
# 导入搜索话题列表的方法
from topic.handler import search_topic_dict
# 导入获取话题资源明细和话题评论资源明细的方法
from topic.resource_handler import get_topic_resource_dict, get_remark_resource_dict
# 导入根据相对路径获取完整url的方法
from utils.decorator import get_host_file_url

def thumbnail_save(request, thumbnail, auth_topic):
    topic_path = "%s/%d" % (get_user_path(request.user, 'topic'), auth_topic.id)
    if not os.path.lexists(os.path.join(MEDIA_ROOT, topic_path)):
        os.makedirs(os.path.join(MEDIA_ROOT, topic_path))  #不存在，则创建文件夹
        
    if thumbnail:
        cover_image_data = thumbnail.getvalue()
        if len(cover_image_data) > ALLOWED_IMG_UPLOAD_SIZE:
            return FailResponse(u'文件超过最大充许大小')
        cover_img = Image.open(StringIO(cover_image_data))
        cover_ext = get_img_ext(cover_img)
        thumbnail_img = "%s/thumbnail_img%s" % (topic_path, cover_ext)
        if os.path.isfile(MEDIA_ROOT+thumbnail):
            i = 0 
            while True:
                thumbnail_img = "%s/thumbnail_img_%d_%s" % (topic_path, i, cover_ext)
                if os.path.isfile(MEDIA_ROOT+thumbnail_img):
                    break 
                  
        print "cover image:", os.path.join(MEDIA_ROOT, thumbnail_img) 
        cover_img.save(os.path.join(MEDIA_ROOT, thumbnail_img))
        return thumbnail_img


@login_required
def get_topic_classify(request, param):
    """
        得到话题分类
    """
    return SuccessResponse(TOPIC_TYPE_CHOICES)


from utils.decorator import print_trace  

@print_trace
@login_required
def update_topic(request, param):
    """
        新建话题
        参数描述：
          param: 参数字典：
          param.title: 话题标题
          param.content: 话题内容
          param.data: 话题附件 格式为 [{'id',1,'type_id':1,'thumbnail':img_obj},{},{}]
                                  'id': 附件资源id
                                  'type_id': 附件类型
                                  'thumbnail': 附件文件对象
    """
    if not param.has_key('title') or not param.has_key('content'):
        return FailResponse(u'参数错误')
    title = param['title']
    if len(title) > 24:
        return FailResponse(u"话题标题超过24个字")
    if title.strip() == "":
        return FailResponse(u"话题标题不能为空")

    content = param["content"]

    # 由于话题内有表情存在。前端的字数计算方式与后台不一样。故取消这个验证。
    # if len(content)>240:
    #     return FailResponse(u"话题内容超过240个字")
    if content.strip() == "":
        return FailResponse(u"话题内容不能为空")

    media_data = param['data'] if param.get('data', None) is not None else []

    if Topic.objects.filter(title=title):
        return FailResponse(u"此话题已存在！")
    add_topic(request.user, title, content, media_data)
    return SuccessResponse(u"话题成功创建")

@login_required
def get_emotion_type_list(request, param):
    """
        表情分类列表
    """
    #ZONE_EMOTION_CHOICES = ((1,u"默认"), (2,u"蘑菇头"))
    from WebZone.conf import ZONE_EMOTION_CHOICES
    return SuccessResponse(ZONE_EMOTION_CHOICES)

@login_required
def fetch_topic_template(request, param):
    """
        得到话题的模板列表
    """
    from manager.misaction import get_topic_list
    top_list = get_topic_list()
    return SuccessResponse(top_list)

@login_required
def fetch_topic_mark(request, param):
    """
        得到话题的标签列表
    """
    if param.has_key("template_id"): template_id = int(param.template_id)
    else: template_id = 0
    if param.has_key("page_index"): page_index = int(param.page_index)
    else: page_index = 1
    if param.has_key("page_size"): page_size = int(param.page_size)
    else: page_size = 20
    
    where_clause = "res_type=11 and status=1"
    if template_id:
        where_clause += " and template_id=%d" % template_id

    cursor = connections[DB_READ_NAME].cursor()
    sql = "select count(*) from zone_asset where %s" % where_clause
    cursor.execute(sql)
    row = cursor.fetchone()
    count = int(row[0]) if row and row[0] else 0
    page_count = int(ceil(count/float(page_size)))
    
    sql = "select id,res_title,res_path,img_small_path,`row`,`column`,template_id,update_time from zone_asset where %s" % where_clause
    sql += " order by update_time desc LIMIT %s,%s" % ((page_index-1)*page_size, page_size)
    #print sql
    cursor.execute(sql)
    rows = cursor.fetchall()
    back_list = []
    from manager.misaction import get_topic_template_name
    for row in rows:
        id = int(row[0])
        title = row[1]
        url =  MEDIA_URL + row[2]
        small =  MEDIA_URL + row[3]
        row_num = int(row[4])
        col_num = int(row[5])
        template_id = int(row[6])
        template_name = get_topic_template_name(template_id)
        update_time = row[7].strftime("%Y-%m-%d %H:%M:%S")
        back_list.append({"id":id, "title":title, "url":url, "small":small, "row_num":row_num, "col_num":col_num, "template_name":template_name, "template_id":template_id,"update_time":update_time})

    
    DOM = {"data":back_list, "page_index": page_index, "page_count": page_count}    
    print DOM
    return SuccessResponse({"data":back_list, "page_index": page_index, "page_count": page_count})
    

@login_required
def fetch_topic_emotion(request, param):
    """
        得到话题的表情列表
    """
    if param.has_key("type_id"): type_id = int(param.type_id)
    else: type_id = 0
    if param.has_key("page_index"): page_index = int(param.page_index)
    else: page_index = 1
    if param.has_key("page_size"): page_size = int(param.page_size)
    else: page_size = 20
    
    
    where_clause = "res_type=12 and status=1"
    if type_id:
        where_clause += " and type_id=%d" % type_id
    
    cursor = connections[DB_READ_NAME].cursor()
    sql = "select count(*) from zone_asset where %s" % where_clause
    cursor.execute(sql)
    row = cursor.fetchone()
    count = int(row[0]) if row and row[0] else 0
    page_count = int(ceil(count/float(page_size)))
    
    sql = "select id,res_title,res_path,img_small_path,type_id,update_time from zone_asset where %s" % where_clause
    sql += " order by update_time desc LIMIT %s,%s" % ((page_index-1)*page_size, page_size)
    #print sql
    cursor.execute(sql)
    rows = cursor.fetchall()
    back_list = []
    from manager.misaction import get_emotion_type_name
    media_path = request.get_host().lower()
    for row in rows:
        id = int(row[0])
        title = row[1]
        url = MEDIA_URL + row[2]
        small = MEDIA_URL + row[3]
        type_id = int(row[4])
        type_name = get_emotion_type_name(type_id)
        update_time = row[5].strftime("%Y-%m-%d %H:%M:%S")
        back_list.append({"id":id, "title":title, "url":url, "small":small, "type_name":type_name, "type_id":type_id,"update_time":update_time})
    return SuccessResponse({"data":back_list, "page_index": page_index, "page_count": page_count})



@login_required
def fetch_topic_emotion_mark(request, param=dict()):
    """
        获取话题的表情数据标记供客户端调用表情用
        editor: kamihati 2015/6/18  客户端反馈说此接口和上面那个接口并不是同一个功能。故。。分开。。。。
    """
    if param.has_key("type_id"): type_id = int(param.type_id)
    else: type_id = 0
    if param.has_key("page_index"): page_index = int(param.page_index)
    else: page_index = 1
    if param.has_key("page_size"): page_size = int(param.page_size)
    else: page_size = 999

    where_clause = "res_type=12 and status=1"
    if type_id:
        where_clause += " and type_id=%d" % type_id

    cursor = connections[DB_READ_NAME].cursor()
    sql = "select count(*) from zone_asset where %s" % where_clause
    cursor.execute(sql)
    row = cursor.fetchone()
    count = int(row[0]) if row and row[0] else 0
    page_count = int(ceil(count/float(page_size)))

    sql = "select id,res_title,res_path,img_small_path,type_id,update_time,mark_id,width,height from zone_asset where %s" % where_clause
    sql += " order by update_time desc LIMIT %s,%s" % ((page_index-1)*page_size, page_size)
    #print sql
    cursor.execute(sql)
    rows = cursor.fetchall()
    back_list = []
    from manager.misaction import get_emotion_type_name
    media_path = request.get_host().lower()
    for row in rows:
        id = row[6]
        url = MEDIA_URL + row[2]
        # small = MEDIA_URL + row[3]
        width = int(row[7]) if row[7] else 0
        height = int(row[8]) if row[8] else 0
        back_list.append({"url":url, 'id': id, 'width': width, 'height': height})
    return SuccessResponse(back_list)



@login_required
def topic_praise(request, param):
    '''
    给话题或评论点赞。同一用户同一天只能给同一话题或同意评论点一次赞
    :param request:
    :param param:
          user_id: 用户id
          topic_id: 话题id .不为空则给评论点赞。否则给话题点赞
          remark_id: 评论id

    :return:
    '''
    topic_id = param.topic_id if param.has_key('topic_id') else 0
    remark_id = param.remark_id if param.has_key('remark_id') else 0

    result = 1
    if topic_id:
        result = add_topic_praise(topic_id, request.user.id)
    elif remark_id:
        result = add_remark_praise(remark_id, request.user.id)
    else:
        return  FailResponse(u'参数错误')


    if result == 1:
        return SuccessResponse(u'投票成功')
    elif result == -1:
        return FailResponse(u'今天已经投过票了')
    elif result == 0:
        return FailResponse(u'投票记录写入失败')


@login_required
def fetch_topic_list(request, param):
    """
        搜索话题返回话题列表。供amf调用
        coder: kamihati  2015/3/25    修改查询逻辑
    """
    page_index = int(param.page_index) if param.has_key("page_index") else 1
    page_size = int(param.page_size) if param.has_key('page_size') else 20
    key = param.key if param.has_key('key') else ''
    topic_list, data_count = search_topic_dict(key, page_index - 1, page_size)
    results = []
    for data in topic_list:
        user = AuthUser.objects.get(pk=data['user_id'])
        data['avartar_img'] = user.get_avatar_img('m', request)
        resource_list = []
        for res in TopicResource.objects.filter(topic_id=data['id']):
            res_dict = dict()
            res_dict["res_id"] = res.res_id
            res_dict["type_id"] = res.type_id
            # 附件为个人作品
            if res.type_id == 4:
                res_obj = AuthOpus.objects.filter(id=res.res_id)
            else:
                res_obj = AuthAsset.objects.filter(id=res.res_id)
            if res_obj is None or res_obj.count() == 0:
                continue
            res_obj = res_obj[0]
            res_dict["thumbnail"] = get_host_file_url(request, res.thumbnail) if res.thumbnail else ''

            origin_path = ''
            if res.type_id == 1:
                # 图片
                origin_path = res_obj.img_large_path
            elif res.type_id in (2, 3):
                # 音乐或视频
                origin_path = res_obj.origin_path
            res_dict['origin_path'] = get_host_file_url(request, origin_path)
            resource_list.append(res_dict)

        data['resource_list'] = resource_list
        
        results.append(data)
    page_count = int(data_count / page_size)
    if data_count % page_size > 0:
        page_count += 1
    return SuccessResponse({"page_size":page_size, "page_index":page_index, "data":results, "page_count":page_count})


@login_required
def fetch_topic_info(request, param):
    """
        得到话题详细信息
    """
    if param.has_key("topic_id"): topic_id = int(param.topic_id)
    else: return FailResponse(u"必须指定话题ID")
    
    try: auth_topic = AuthTopic.objects.get(id=topic_id)
    except(AuthTopic.DoesNotExist): return FailResponse(u"指定的话题ID:%d不存在" % topic_id)
    
    topic_dict = {"id":auth_topic.id, "title":auth_topic.title, "template_id":auth_topic.template_id}
    topic_dict["row_num"] = auth_topic.row_num
    topic_dict["col_num"] = auth_topic.col_num
    topic_dict["width"] = auth_topic.width
    topic_dict["height"] = auth_topic.height
    topic_dict["cover"] = MEDIA_URL + auth_topic.cover if auth_topic.cover else ""
    topic_dict["thumbnail"] = MEDIA_URL + auth_topic.thumbnail if auth_topic.thumbnail else ""
    topic_dict["background"] = MEDIA_URL + auth_topic.background if auth_topic.background else ""
    topic_dict["expire_time"] = auth_topic.expire_time.strftime("%Y-%m-%d")
    topic_dict["status"] = auth_topic.status
    topic_dict["join_count"] = auth_topic.join_count
    page_size = auth_topic.row_num * auth_topic.col_num
    topic_dict["page_count"] = auth_topic.join_count / page_size
    if auth_topic.join_count % page_size: topic_dict["page_count"] += 1
    print topic_dict
    return SuccessResponse(topic_dict)
    


@login_required
def fetch_topic_page(request, param):
    """
        得到现有话题列表
    """
    if param.has_key("topic_id"): topic_id = int(param.topic_id)
    else: return FailResponse(u"必须指定话题ID")
    if param.has_key("page_index"): page_index = int(param.page_index)
    else: page_index = 1
    if param.has_key("back_count"): back_count = int(param.back_count)
    else: back_count = 5
    
    try: auth_topic = AuthTopic.objects.get(id=topic_id)
    except(AuthTopic.DoesNotExist): return FailResponse(u"指定的话题ID:%d不存在" % topic_id)
    
    page_size = auth_topic.row_num * auth_topic.col_num
    page_count = auth_topic.join_count / page_size
    if auth_topic.join_count % page_size: page_count += 1
    
    #if page_index<1 or page_index>page_count:
    #    return FailResponse(u"当前话题总页数为：%d，你请求的页为:%d，页码不存在" % (page_count, page_index))
    
    back_dict = {}
    for i in xrange(page_index, page_index + back_count):
        back_dict[i] = []
    
    where_clause = "auth_topic_id=%d and status=1" % auth_topic.id

    cursor = connections[DB_READ_NAME].cursor()
    sql = "select id, url from auth_topic_page where %s order by id" % where_clause
    sql += " limit %s, %s" % ((page_index-1)*page_size, back_count*page_size)
    #print sql
    cursor.execute(sql)
    rows = cursor.fetchall()
    
    count_index = 0
    for row in rows:
        id = int(row[0])
        url = MEDIA_URL + row[1]
        cur_page_index = page_index + count_index/page_size
        count_index += 1
        page_order = count_index%page_size
        if page_order == 0: page_order = page_size
        back_dict[cur_page_index].append({"id":id, "page_order":page_order, "url":url})
        
    #for auth_topic_page in AuthTopicPage.objects.filter(page_index__gte=page_index, page_index__lt=page_index+back_count, status=1).order_by("page_index","page_order"):
    #    back_dict[auth_topic_page.page_index].append({"id":auth_topic_page.id, "page_order":auth_topic_page.page_order, "url":auth_topic_page.url})
    #print back_dict
    dict_list = {"data":back_dict, "page_index": page_index, "back_count": back_count, "page_count": page_count}
    print dict_list 
    return SuccessResponse({"data":back_dict, "page_index": page_index, "back_count": back_count, "page_count": page_count})

@login_required
def join_topic(request, param):
    """
        参与话题
    """
    if param.has_key("topic_id"): topic_id = int(param.topic_id)
    else: return FailResponse(u"必须指定话题ID")
    if param.has_key("mark_id"): mark_id = int(param.mark_id)
    else: return FailResponse(u"必须指定话题模板")
    if param.has_key("emotion_id"): emotion_id = int(param.emotion_id)
    else: return FailResponse(u"必须指定话题的分类")
    if param.has_key("content") or not param.content: content = param.content
    else: return FailResponse(u"必须输入你的话题")
    if param.has_key("img_data") or not param.img_data: img_data = param.img_data
    else: return FailResponse(u"必须传输话题图片")

    try: auth_topic = AuthTopic.objects.get(id=topic_id)
    except(AuthTopic.DoesNotExist): return FailResponse(u"指定的话题ID:%d不存在" % topic_id)

    img_data = img_data.getvalue()
    if len(img_data) > ALLOWED_IMG_UPLOAD_SIZE:
        return FailResponse(u'文件超过最大充许大小')
    img = Image.open(StringIO(img_data))
    img_ext = get_img_ext(img)
    if img_ext == None:
        return FailResponse(u"只充许上传图片文件(%s)" % ';'.join(ALLOWED_IMG_EXTENSION))

    auth_topic_page = AuthTopicPage()
    auth_topic_page.user_id = request.user.id
    auth_topic_page.library_id = request.user.library_id
    auth_topic_page.auth_topic_id = auth_topic.id
    auth_topic_page.mark_id = mark_id
    auth_topic_page.emotion_id = emotion_id
    auth_topic_page.content = content
    auth_topic_page.url = ""
    auth_topic_page.status = -1
    auth_topic_page.save()

    topic_user = AuthUser.objects.get(id=auth_topic.user_id)
    auth_topic_page.url = "%s/%d/%d%s" % (get_user_path(topic_user, 'topic'), auth_topic.id, auth_topic_page.id, img_ext)
    img.save(os.path.join(MEDIA_ROOT, auth_topic_page.url))

    auth_topic_page.status = 1
    auth_topic_page.save()
    auth_topic.join_count += 1
    auth_topic.save()

    #更新话题的页码，顺序
    #auth_topic_count = AuthTopicPage.objects.filter(auth_topic_id=auth_topic.id,status=1,id__gte=auth_topic_page.id).count()
    page_size = auth_topic.row_num * auth_topic.col_num
    auth_topic_page.page_index = auth_topic.join_count / page_size
    if auth_topic.join_count % page_size: auth_topic_page.page_index += 1
    auth_topic_page.page_order = auth_topic.join_count % page_size
    if auth_topic_page.page_order == 0:
        auth_topic_page.page_order = page_size
    auth_topic_page.save()

    back_dict = {"id":auth_topic_page.id, "auth_topic_id":auth_topic.id, "page_index":auth_topic_page.page_index, "page_order":auth_topic_page.page_order}
    back_dict["url"] = MEDIA_URL + auth_topic_page.url
    back_dict["page_count"] = auth_topic_page.page_index

    return SuccessResponse(back_dict)


@login_required
def create_remark(request, param):
    '''
    创建话题评论的方法。amf用。
    参数描述：
          param: 参数字典：
          param.topic_id: 话题id
          param.content: 评论内容
          param.data: 评论附件 格式为 [{'id',1,'type_id':1,'thumbnail':img_obj},{},{}]
                                  'id': 附件资源id
                                  'type_id': 附件类型
                                  'thumbnail': 附件文件对象
    :return:
    '''
    user = request.user
    if not param.has_key("topic_id") or not param.has_key('content'):
        return FailResponse(u'参数错误')
    content = param.content
    # 由于话题内有表情存在。前端的字数计算方式与后台不一样。故取消这个验证。
    # if len(content) > 240:
    #     return  FailResponse(u'评论内容不能超过240个字。')
    if content.strip() == "":
        return FailResponse(u'评论内容不能为空')
    media_data = param.data if param.has_key('data') else []
    result = add_topic_remark(request.user, param.topic_id, content, media_data)
    if result == -1:
        # 时效判断。测试时移除
        return FailResponse(u'距离上次发表评论之后的30秒内不能再次对同一话题进行评论。')
    return SuccessResponse({"remark_count": TopicRemark.objects.filter(topic_id=param.topic_id).count()})


@login_required
def get_remark_list(request, param):
    '''
    返回相关的评论列表
    2015.3.24
    coder: kamihati 2015/3/25  修改页码
    '''

    topic_id = param.topic_id if param.get("topic_id",None) else 0
    if not Topic.objects.filter(pk=topic_id, status=0):
        return  FailResponse(u'指定的话题已被删除或不存在。')
    page_size = int(param.page_size) if param.get("page_size",None) else 8
    page_index = int(param.page_index) if param.get('page_index',None) else 1
    topic = Topic.objects.get(id=topic_id)
    remark_list, page_count, data_count = search_comment_dict(topic_id, page_index-1, page_size)
    result = []

    for obj in remark_list:
        data = dict()
        data["id"] = obj['id']
        data['topic_id'] = topic_id
        data['title'] = topic.title
        data['praise_count'] = obj['praise_count']
        data['content'] =  obj['content']
        data["username"] = obj["username"]
        data['nickname'] = obj['nickname']
        user = AuthUser.objects.get(pk=obj['user_id'])
        data['avartar_img'] = user.get_avatar_img('m', request)
        data['create_time'] = obj['create_time']
        data['resource_list'] = []
        for res in RemarkResource.objects.filter(remark_id=obj['id']):
            res_dict = dict()
            res_dict["res_id"] = res.res_id
            res_dict["type_id"] = res.type_id
            # 附件为个人作品
            if res.type_id == 4:
                res_obj = AuthOpus.objects.filter(id=res.res_id)
            else:
                res_obj = AuthAsset.objects.filter(id=res.res_id)
            if res_obj is None or res_obj.count() == 0:
                continue
            res_obj = res_obj[0]
            res_dict["thumbnail"] = get_host_file_url(request, res.thumbnail) if res.thumbnail else ''

            origin_path = ''
            if res.type_id == 1:
                # 图片
                origin_path = res_obj.img_large_path
            elif res.type_id in (2, 3):
                # 音乐或视频
                origin_path = res_obj.origin_path
            res_dict['origin_path'] = get_host_file_url(request, origin_path)
            data['resource_list'].append(res_dict)
        result.append(data)
    topic.view_count += 1
    topic.save()
    return SuccessResponse({"data":result,"page_index":page_index,"page_size":page_size,"page_count":page_count,
                            'view_count': topic.view_count, 'praise_count': topic.praise_count, 'remark_count': topic.remark_count})


def fetch_topic_one(request, param):
    '''
    获取指定话题的数据
    :param request:
    :param param:
           param.id:  话题id
    :return:
    coder: kamihati 2015/3/24   获取指定话题数据
    '''
    if not param.has_key('id'):
        return  FailResponse(u'参数错误')
    topic = Topic.objects.get(id=param.id)
    if topic.status == 1:
        return  FailResponse(u'此话题已被删除')
    topic_dict = dict()
    user = AuthUser.objects.get(id=topic.user_id)

    topic_dict["id"] = topic.id
    topic_dict['user_id'] = user.id
    topic_dict['nickname'] = user.nickname
    topic_dict["title"] = topic.title
    topic_dict["content"] = topic.content
    topic_dict["avartar_img"] = user.get_avatar_img('m', request)
    topic_dict["view_count"] = topic.view_count
    topic_dict['remark_count'] = topic.remark_count
    topic_dict['praise_count'] = topic.praise_count
    topic_dict['create_time'] = str(topic.create_time)
    topic_dict['resource_list'] = []
    for res in TopicResource.objects.filter(topic_id=topic.id):
        res_dict = dict()
        res_dict["res_id"] = res.res_id
        res_dict["type_id"] = res.type_id
        res_obj = None
        # 附件为个人作品
        if res.type_id == 4:
            res_obj = AuthOpus.objects.filter(id=res.res_id)
        else:
            res_obj = AuthAsset.objects.filter(id=res.res_id)
        if res_obj is None or res_obj.count() == 0:
            continue
        res_obj = res_obj[0]
        res_dict["thumbnail"] = get_host_file_url(request, res.thumbnail) if res.thumbnail else ''

        origin_path = ''
        if res.type_id == 1:
            # 图片
            origin_path = res_obj.img_large_path
        elif res.type_id in (2, 3):
            # 音乐或视频
            origin_path = res_obj.origin_path
        elif res.type_id == 4:
            # 个人创作只需提供id既可
            pass
        res_dict['origin_path'] = get_host_file_url(request, origin_path)
        topic_dict.append(res_dict)
    return SuccessResponse(topic_dict)



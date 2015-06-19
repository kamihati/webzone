# coding=utf8

# 导入个人资源表
from diy.models import AuthAsset
# 导入话题资源。话题评论资源的model
from topic.models import TopicResource, RemarkResource

# 导入根据相对路径获取完整url的方法
from utils.decorator import get_host_file_url

def get_topic_resource_dict(id):
    '''
    获取话题资源字典
    :param id:   话题资源id
    :return:
    '''
    result = []
    for obj in TopicResource.objects.filter(topic_id=id):
        result.append(get_resource_dict(TopicResource.objects.get(id=obj.id)))
    return result


def get_remark_resource_dict(id):
    '''
    获取话题评论资源字典
    :param id:  话题评论资源id
    :return:
    '''
    result = []
    for obj in RemarkResource.objects.filter(remark_id=id):
        result.append(get_resource_dict(RemarkResource.objects.get(id=obj.id)))
    return result


def get_resource_dict(res):
    '''
    获取资源对象的数据解析成dict
    :param res_obj: 资源对象
    :return:
        dict(res_id,    #资源id, 对应auth_asset表id
             type_id,   # 资源类型.对应auth_asset.res_type
             thumbnail,  #缩略图路径
             origin_path  #原始文件路径
             }

    '''
    res_dict = dict()
    res_dict['id'] = res.id
    res_dict["res_id"] = res.res_id
    res_dict["type_id"] = res.type_id
    if not AuthAsset.objects.filter(pk=res.res_id):
        return dict()

    res_obj = AuthAsset.objects.get(id=res.res_id)
    res_dict["thumbnail"] = res.thumbnail if res.thumbnail else ''

    origin_path = ''
    if res_obj.origin_path:
        origin_path = res_obj.origin_path
    elif res_obj.img_large_path:
        origin_path = res_obj.img_large_path
    res_dict['origin_path'] = origin_path
    return res_dict
# coding=utf8
import datetime
import os
import StringIO
import math
from PIL import Image

from django.db.models import Q

#　导入多媒体文件url, 路径
from WebZone.settings import MEDIA_URL
# 导入异常输出函数
from utils.decorator import print_trace
# 导入用户上传缩略图的存储方法
from utils.decorator import thumbnail_save

# 导入用户model
from account.models import AuthUser
# 导入资源类型model。导入资源风格model
from resources.models import ResourceType, ResourceStyle
# 导入个人资源类型model
from resources.models import ResourceTypePerson

# 导入objects转dict的方法
from utils.db_handler import rows_to_dict_list
# 导入sql语句分页方法。sql语句获取数据总数方法
from utils.db_handler import get_pager, get_data_count
# 导入sql语句获取数据总数方法
from utils.db_handler import get_data_count
# 导入获取用户文件存储路径的路径
from utils import get_user_path
# 导入个人资源models
from diy.models import  AuthAsset


def get_resource_type_list(rs_type=0):
    '''
    获取素材类型。
    :param rs_type:
        1为公共素材类型
        2为个人素材类型
    :return:
    '''
    if rs_type == 0:
        return ResourceType.objects.filter(status=0), ResourceTypePerson.objects.filter(status=0)
    elif rs_type == 1:
        return ResourceType.objects.filter(status=0)
    elif rs_type == 2:
        return ResourceTypePerson.objects.filter(status=0)

def get_resource_style_list():
    '''
    获取素材风格列表
    :return:
    '''
    return ResourceStyle.objects.filter(status=0)


def get_person_resource_pager(page_index, page_size, **args):
    '''
    获取个人资源列表
    page_index: 页码。从0开始
    page_size: 每页数据数。0则取所有
    args 可选参数
         args.key: 查询关键字
         args.library_id: 所属机构
         args.type_id:  所属类型
    :return:
         data_list   查询结果AuthAssetlist
         data_count:  查询结果数据总数
         page_count: 查询结果分页总页数
    '''

    type_id = args['type_id'] if args.has_key('type_id') else ''
    key = args['key'] if args.has_key('key') else ''
    library_id = args['library_id'] if args.has_key('library_id') else ''
    # 取可用状态的资源
    where_str = 'a.status=1'
    if type_id != '':
        where_str += ' AND a.res_type=%s' % type_id
    if key != '':
        where_str += ' AND a.res_title LIKE \'%' + key + '%\''
    if library_id != '':
        where_str += ' AND a.library_id=%s' % library_id

    join_str =  'INNER JOIN auth_user u ON u.id=a.user_id INNER JOIN library l ON l.id=a.library_id INNER JOIN resource_type_person t ON t.id=a.res_type=t.id'
    data_count = get_data_count('a.id', 'auth_asset a', join_str, where_str)
    page_count = int(math.ceil(data_count / page_size))
    return rows_to_dict_list(
        get_pager('a.id,a.res_title,l.lib_name,u.username,t.`name` as type_name,a.create_time',
                  'auth_asset a',
                  join_str,
                  where_str,
                  'ORDER BY a.id DESC',
                  page_index,
                  page_size),
        ['id', 'title', 'lib_name', 'username', 'type_name', 'create_time']
    ), data_count, page_count


def get_common_resource_pager(page_index, page_size, **args):
    '''
    获取公共资源列表
    editor: kamihati 2015/6/11
    page_index: 页码。从0开始
    page_size: 每页数据数。0则取所有
    args 可选参数
         args.key: 查询关键字
         args.library_id: 所属机构
         args.type_id:  所属类型
    :return:
         data_list   查询结果ZoneAssetlist
         data_count:  查询结果数据总数
         page_count: 查询结果分页总页数
    '''

    type_id = args['type_id'] if args.has_key('type_id') else ''
    key = args['key'] if args.has_key('key') else ''
    library_id = args['library_id'] if args.has_key('library_id') else ''
    style_id = args['style_id'] if args.has_key('style_id') else ''

    # 取可用状态的资源
    where_str = 'a.status=1'

    if key != '':
        where_str += ' AND a.res_title LIKE \'%' + key + '%\''
    if library_id != '':
        where_str += ' AND a.library_id=%s' % library_id

    if type_id != '':
        where_str += ' AND a.res_type=%s' % type_id

    if style_id != '':
        where_str += ' AND a.res_style=%s' % style_id

    join_str =  'INNER JOIN auth_user u ON u.id=a.user_id INNER JOIN library l ON l.id=a.library_id INNER JOIN resource_type t ON t.id=a.res_type INNER JOIN resource_style s ON s.id=a.res_style'
    data_count = get_data_count('a.id', 'zone_asset a', join_str, where_str)
    page_count = int(math.ceil(data_count / page_size))
    return rows_to_dict_list(
        get_pager('a.id,a.res_title,l.lib_name,u.username,t.`name` as type_name,a.create_time,a.is_recommend,a.ref_times,s.`name` as style_name,a.res_path,a.res_type,a.res_style,a.origin_path,a.size_id,a.create_type,a.mask_path',
                  'zone_asset a',
                  join_str,
                  where_str,
                  'ORDER BY a.id DESC',
                  page_index,
                  page_size),
        ['id', 'title', 'lib_name', 'username', 'type_name', 'create_time', 'is_recommend', 'ref_times', 'style_name', 'res_path', 'res_type', 'res_style', 'origin_path', 'size_id', 'create_type', 'mask_path']
    ), data_count, page_count

# coding=utf8

import datetime
# 导入机构model
from library.models import Library
from utils.db_handler import get_pager
from utils.db_handler import get_data_count
from utils.db_handler import rows_to_dict_list
# 导入保存models数据
from utils.db_handler import save_model_data
# 导入机构地区表。如地市信息不存在则创建新的地市
from library.models import LibraryRegion

# 导入文件转移方法
from utils.decorator import move_temp_file


def get_region(parent_id):
    '''
    获取地区列表
    editor: kamihati 2015/5/8
    :param parent_id: 父级id
    :return:
    '''
    return LibraryRegion.objects.filter(parent_id=parent_id)

def get_library_list(status=None):
    '''
    获取机构列表。
    :param status:状态。默认为None。读取所有机构
    :return:
    '''
    return Library.objects.all() if status is None else Library.objects.filter(status=status)


def get_library_list_by_user(user, **kwargs):
    '''
    根据用户获取机构列表
    # 暂时读取所有未禁用的。做用户权限时需要判断
    :param user:
    :return:
    '''
    librarys = None
    if user.auth_type in (8, 9):
        librarys = Library.objects.exclude(status=-1)
    else:
        librarys = Library.objects.filter(pk=user.library.id)
    if kwargs.has_key('status'):
        librarys = librarys.filter(status__in=kwargs['status'])
    return librarys


def get_ztree_library(library_id, **kwargs):
    '''
         获取机构地区列表并组织返回ztree可用的数据
         editor: kamihati  2015/4/17
         editor: kamihati 2015/5/11 增加预设选定机构的参数  checked_library =[]
         :library_id: 机构id
         :return:
    '''
    now_library = Library.objects.get(pk=library_id)
    library_list = Library.objects.filter(level__gte=now_library.level).exclude(pk=library_id)
    result = []
    open = True if 'open' not in kwargs else kwargs['open']
    result.append(dict(id=0,
                       name=u'国家图书馆',
                       pId=0,
                       open=open))
    checked_library = [] if not kwargs.has_key('checked_library') else kwargs['checked_library']
    region_dict = {}
    for obj in library_list:
        if obj.province not in region_dict:
            region_dict[obj.province] = dict()

        if obj.city not in region_dict[obj.province]:
            region_dict[obj.province][obj.city] = dict()

        if obj.region not in region_dict[obj.province][obj.city]:
            region_dict[obj.province][obj.city][obj.region] = dict()

        if obj.id not in region_dict[obj.province][obj.city][obj.region]:
            region_dict[obj.province][obj.city][obj.region][obj.id] = dict(id=obj.id, name=obj.lib_name)

    result = []
    i = j = x = 1

    for key, val in region_dict.iteritems():
        result.append(dict(id='province_%s' % i, name=key, pId=0, open=True))
        if val:
            for key_city, val_city in val.iteritems():
                result.append(dict(id='city_%s' % j, name=key_city, pId='province_%s' % i, open=True))
                if val_city:
                    for key_region, val_region in val_city.iteritems():
                        result.append(dict(id='region_%s' % x, name=key_region, pId='city_%s' % j, open=True))
                        if val_region:
                            for key_lib, val_lib in val_region.iteritems():
                                if val_lib:
                                    is_checked = True if str(val_lib['id']) in checked_library else False
                                    result.append(dict(id='lib_%s' % val_lib['id'], name=val_lib['name'], pId='region_%s' % x, checked=is_checked))
                        x += 1
                j += 1
        i += 1
    return result


def get_library_by_request(request):
    '''
    根据当前请求判断所访问的机构地址(目前使用url)
    editor: kamihati 2015/4/28   改变目前项目中获取机构多使用用户机构的逻辑
    :param request:
    :return:
    '''
    library = Library.objects.filter(host=request.get_host().lower())
    if not library:
        return None
    return library[0]


def get_library_pager(page_index, page_size, **kwargs):
    '''
    获取机构的分页数据
    :param page_index: 页码。从0开始
    :param page_size:
    :param kwargs:
    :return:
    '''
    where = "a.status<>-1"
    if 'quick_expire' in kwargs:
        where += ' AND a.expire_time>\'%s\' AND a.expire_time<\'%s\'' % (datetime.datetime.now(), (datetime.datetime.now() + datetime.timedelta(30 * 3)))
    join_str = "INNER JOIN auth_user b ON b.id=a.user_id"

    data_count = get_data_count('a.id', 'library a', join_str, where)
    return rows_to_dict_list(
        get_pager('a.id,a.lib_name,a.create_time,a.expire_time,b.realname,b.telephone',
                  'library a',
                  join_str,
                  where,
                  'ORDER BY a.id DESC',
                  page_index,
                  page_size),
        ['id', 'lib_name', 'create_time', 'expire_time', 'realname', 'telephone']
    ), data_count


def get_library_manager(page_index, page_size, **kwargs):
    '''
    获取机构的管理员列表(auth_type=1)
    editor: kamihati 2015/6/3 增加对机构状态的查询
    :param page_index:
    :param page_size:
    :param kwargs:
    :return:
    '''
    cols = 'b.id,a.lib_name,b.username,b.realname,a.create_time,a.expire_time,a.status,a.id as library_id,b.login_times,b.last_login,b.nickname'
    where = 'a.status<>-1 AND b.status<>-1'
    if 'auth_type' in kwargs:
        where += '  AND b.auth_type=%s' % kwargs['auth_type']
    if 'library_id' in kwargs and kwargs['library_id'] != '':
        where += ' AND a.id=%s' % kwargs['library_id']
    if 'key' in kwargs and kwargs['key'] != '':
        where += ' AND (b.username LIKE \'%'+ kwargs['key'] + '%\' OR b.realname LIKE \'%' + kwargs['key'] + '%\' OR b.nickname LIKE \'%' + kwargs['key'] + '%\')'
    if 'library_status' in kwargs and kwargs['library_status'] != '':
        where += ' AND a.status=%s' % kwargs['library_status']
    join_str = 'INNER JOIN auth_user b ON b.library_id=a.id'
    data_count = get_data_count('a.id', 'library a', join_str, where)
    return rows_to_dict_list(
        get_pager(cols,
                  'library a',
                  join_str,
                  where,
                  'ORDER BY b.id DESC',
                  page_index,
                  page_size),
        ['id', 'lib_name', 'username', 'realname', 'create_time', 'expire_time', 'status', 'library_id', 'login_times', 'last_login', 'nickname']
    ), data_count


def edit_library(param, user):
    '''
    编辑机构信息
    editor: kamihati 2015/5/6  编辑机构信息
    :param param: 编辑参数
    :param user: 操作人
    :return:
    '''
    # 读取logo临时文件地址
    temp_logo = param.pop('logo_temp_path') if 'logo_temp_path' in param else ''
    # 读取swf临时文件地址
    temp_swf = param.pop('swf_temp_path') if 'swf_temp_path' in param else ''
    # 读取客户端临时文件地址
    temp_annex = param.pop('annex_temp_path') if 'annex_temp_path' in param else ""
    # 新版本设定所有机构均可查看其他机构信息。故此设定均为1
    # editor: kamihati 2015/5/7
    param['is_global'] = 1
    # 如果到期时间为空则设为半年
    if 'expire_time' not in param or param['expire_time'] == '':
        param['expire_time'] = datetime.datetime.now() + datetime.timedelta(180)
    # 保存机构数据
    library = save_model_data(Library, param)

    # 把机构的客户端文件移动到相应目录
    # editor: kamihati 2015/5/6
    if temp_annex != "":
        library.annex = move_temp_file(temp_annex, '/lib/%s/yunhui' % library.id)
        library.save()

    # 把机构的客户端文件移动到相应目录
    # editor: kamihati 2015/5/6
    if temp_logo != "":
        library.logo_path = move_temp_file(temp_logo, '/lib/%s/lib_title' % library.id)
        library.save()

    # 把机构的客户端文件移动到相应目录
    # editor: kamihati 2015/5/6
    if temp_swf != "":
        library.swf_path = move_temp_file(temp_swf, '/lib/%s/loaderAsset' % library.id)
        library.save()

    # 保存机构地区信息
    province = param['province']
    city = param['city']
    region = param['region']

    if province != "":
        province = LibraryRegion.objects.filter(parent_id=0, name=province)
        if province.count() == 0:
            province = LibraryRegion.objects.create(parent_id=0, name=province, level=1)
        else:
            province = province[0]

        if city != "":
            city = LibraryRegion.objects.filter(level=2, name=city)
            if city.count() == 0:
                city = LibraryRegion.objects.create(parent_id=province.id, name=city, level=2)
            else:
                city = city[0]

            if region != "":
                region = LibraryRegion.objects.filter(level=3, name=region)
                if region.count() == 0:
                    region = LibraryRegion.objects.create(parent_id=city.id, name=region, level=3)
    # 添加操作记录
    # ****
    return library

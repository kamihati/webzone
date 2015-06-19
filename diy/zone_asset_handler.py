# coding=utf8

from utils import get_user_path
from WebZone.settings import MEDIA_ROOT

# 导入分页方法
from utils.db_handler import get_pager
# 导入数据转dict的方法
from utils.db_handler import rows_to_dict_list
# 导入获取数据条数的放啊分
from utils.db_handler import get_data_count
# 导入model数据保存方法
from utils.db_handler import save_model_data

from diy.models import ZoneAsset


def get_zone_asset_list(res_type, res_style, **kwargs):
    '''
    获取制定类型的素材列表
    :param res_type: 素菜类型id,为0则不限
    :param res_style: 素材风格id.为0则不限
    :param kwargs:
    :return:
    '''
    asset_list = ZoneAsset.objects.exclude(status=-1)
    if res_type != 0:
        asset_list = asset_list.filter(res_type=res_type)
    if res_style != 0:
        asset_list = asset_list.filter(res_style=res_style)
    return asset_list


def get_zone_asset_pager(page_index, page_size, **kwargs):
    '''
    获取指定条件的素材列表
    editor: kamihati 2015/6/9  供客户端调用
    editor: kamihati 2015/6/10  整理优先显示收藏素材的分页逻辑
             逻辑如下。：
                   获取收藏列表
                   计算收藏列表总数是否刚好填充够所在的每一页
                         如果可以。则说明获取非收藏数据的分页数据时只需要对页码进行计算
                         如果不行。则根据收藏数据最后一页的数目计算与页码的差值。
                                  后续每一页非收藏分页数据计算步长时要加入这个差值。
                   is_like=1
                        判断当页是否需要显示收藏数据
                        如果收藏数据可以显示满一页  。则返回这部分数据和数据总数
                        如果不能。则格式化这部分数据为需要返回的list  。根据差值计算当页需要显示的非收藏数据。然后用收
                                   藏数据与这部分数据进行组合
                        如果当页不需要现实收藏数据。则根据收藏数据所占的页数和差值计算当页需要显示的非收藏数据
                   is_like=0
                        直接计算素材分页。根据收藏列表更新每个页面的数据的收藏状态
    editor: kamihati 2015/6/15  优化搜索逻辑。利用mysql的排序特性解决个人收藏作品的优先排序
    :param res_type: 资源分类id
    :param res_style: 资源风格id
    :param kwargs:
    :return:
    '''
    res_type = int(kwargs['res_type']) if kwargs.has_key('res_type') else 0
    res_style = int(kwargs['res_style']) if kwargs.has_key('res_style') else 0
    is_like = int(kwargs['is_like']) if kwargs.has_key('is_like') else 0
    # 所属api的request对象
    req = kwargs['req'] if kwargs.has_key('req') else None
    # 定义用于检索分页数据的条件
    where = "status<>-1"
    if res_type != 0:
        where += ' AND res_type=%s' % res_type
    if res_style != 0:
        where += ' AND res_style=%s' % res_style
    # 计算所查询的数据总数
    data_count = get_data_count('id', 'zone_asset', "", where)
    # 定义喜欢的资源列表供可能的过滤
    like_list = get_asset_like_list(req.user.id, res_type=res_type, res_style=res_style)
    # 获取喜欢的素材id列表供数据筛选
    id_list = [obj.zone_asset_id for obj in like_list]
    order_str = 'ORDER BY is_recommend DESC,id DESC'
    if is_like == 1 and id_list != []:
        order_str = 'ORDER BY if(id IN (%s),0,1),is_recommend DESC,id DESC' % ','.join([str(id) for id in id_list])
    data_list = rows_to_dict_list(
        get_pager('id,res_title,res_path,origin_path,img_large_path,is_recommend,0',
                  'zone_asset',
                  "",
                  where,
                  order_str,
                  page_index, page_size),
        ['id', 'name', 'img', 'preview', 'img_l', 'is_recommend', 'is_like'])
    for obj in data_list:
        # 标识每条数据是否是被点过喜欢过的
        if is_like == 0:
            if obj['id'] in id_list:
                obj['is_like'] = 1
        obj['img'] = '/media/' + obj['img'] if obj['img'] else ''
        obj['preview'] = '/media/' + obj['preview']
        obj['img_l'] = '/media/' + obj['img_l'] if obj['img_l'] else ''
    return data_list, data_count, len(id_list)


def get_asset_like_list(user_id, **kwargs):
    '''
    获取用户喜欢的资源列表\
    editor: kamihati 2015/6/9
    :param request:
    :return:
    '''
    res_type = int(kwargs['res_type']) if kwargs.has_key('res_type') else 0
    from diy.models import ZoneAssetLike
    data = ZoneAssetLike.objects.filter(user_id=user_id).order_by("-recommend", "-id")
    if res_type != 0:
        data = data.filter(res_type=res_type)
    return data.order_by("-id")


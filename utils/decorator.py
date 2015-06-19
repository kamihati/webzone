#coding: utf-8
'''
Created on 2014-3-28

@author: Administrator
'''
import os
import time, datetime
import StringIO
import os,shutil
from PIL import Image
from functools import wraps
from django.utils.decorators import available_attrs
from django.http import HttpResponseRedirect, HttpResponse
from gateway import FailResponse
from django.utils.http import urlquote

# 导入图片最大上传尺寸的配置
from WebZone.conf import ALLOWED_IMG_UPLOAD_SIZE
from WebZone.settings import LOGIN_URL
from WebZone.settings import REDIRECT_FIELD_NAME
# 获取setting文件中配置的测试服务器url和在线服务器url
from WebZone.settings import TEST_HOST, ONLINE_HOST

#　导入多媒体文件url, 路径
from WebZone.settings import MEDIA_URL, MEDIA_ROOT
# 导入图片文件扩展名处理方法
from utils import get_img_ext
# 导入获取用户文件存储路径的路径
from utils import get_user_path
# 导入增加管理员操作日志方法
from manager import add_manager_action_log
# 导入图片裁剪方法
from utils import get_small_size



class CustomRedirect(HttpResponseRedirect):
    def __init__(self, request, redirect_to):
        HttpResponseRedirect.__init__(self, redirect_to)
        try: forwarded_host = 'http://' + request.META['HTTP_X_FORWARDED_HOST']
        except: forwarded_host = 'http://%s' % (request.get_host().replace('*', 'www'))
        self['Location'] = forwarded_host + self['Location']
        

def print_exec_time(view_func):
    """
    Decorator that is user logon, if not return the necessary message
    if logon, do nothing.
    """
    @wraps(view_func, assigned=available_attrs(view_func))
    def _wrapped_view_func(request, *args, **kwargs):
        t1 = time.time()
        back_view = view_func(request, *args, **kwargs)
        print request.get_full_path(), time.time() - t1
        return back_view
    return _wrapped_view_func

        
def print_trace(view_func):
    """
    Decorator that is user logon, if not return the necessary message
    if logon, do nothing.
    """
    @wraps(view_func, assigned=available_attrs(view_func))
    def _wrapped_view_func(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except:
            import traceback
            traceback.print_exc()
    return _wrapped_view_func


def login_required(view_func):
    """
    Decorator that is user logon, if not return the necessary message
    if logon, do nothing.
    """
    @wraps(view_func, assigned=available_attrs(view_func))
    def _wrapped_view_func(request, *args, **kwargs):
        if hasattr(request, "session") and request.session.get('is_logon', False) and request.user.is_active:
            return view_func(request, *args, **kwargs)
        else:
            return FailResponse(u'请先登录')
    return _wrapped_view_func


def login_web_required(view_func):
    """
    Decorator that is user logon, if not return the necessary message
    if logon, do nothing.
    """
    @wraps(view_func, assigned=available_attrs(view_func))
    def _wrapped_view_func(request, *args, **kwargs):
        if hasattr(request, "session") and request.session.get('is_logon', False) and request.user.is_active:
            return view_func(request, *args, **kwargs)
        else:
            return HttpResponse(FailResponse(u'请先登录'))
    return _wrapped_view_func


def user_passes_test(test_func, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Decorator for views that checks that the user passes the given test,
    redirecting to the log-in page if necessary. The test should be a callable
    that takes the user object and returns True if the user passes.
    """
    if not login_url:
        login_url = LOGIN_URL
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if test_func(request):
                return view_func(request, *args, **kwargs)
            path = urlquote(request.get_full_path())
            tup = login_url, redirect_field_name, path
            return CustomRedirect(request, '%s?%s=%s' % tup)
        return wraps(view_func, assigned=available_attrs(view_func))(_wrapped_view)
    return decorator


#if not has_permissions(request, 's_auth_m'): return HttpResponse(u'没有权限')
def login_manager_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Decorator for views that checks that the user is logged in web, redirecting
    to the log-in page if necessary.
    """
    #print function, type(function), function.func_name
    actual_decorator = user_passes_test(
        lambda req: hasattr(req, "session") and req.session.get('manager_login', False) and req.user.is_active and (req.user.is_staff or req.user.auth_type in (1, 2)),
        login_url="/manager/login/",
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def login_admin_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Decorator that is admin user logon, if not redirect to the admin login page
    """
    actual_decorator = user_passes_test(
        lambda req: hasattr(req, "session") and req.session.get('manager_login', False) and req.user.is_active and req.user.is_staff,
        login_url="/manager/login/",
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def manager_required(view_func=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Decorator for views that checks that the user is logged in web, redirecting
    to the log-in page if necessary.
    """
    @wraps(view_func, assigned=available_attrs(view_func))
    def _wrapped_view_func(request, *args, **kwargs):
        from manager import get_perm_code, has_permissions
        # print "manager_required", request.session.get('mgr_perms', None), perm_code, has_permissions(request, perm_code), request.get_full_path()
        # 如果是管理员用户类型。则准许登录后台
        # editor: kamihati 2015/5/18
        if not request.user or str(request.user) == 'AnonymousUser':
            return CustomRedirect(
                request,
                '%s?%s=%s' % ("/manager2/login/", REDIRECT_FIELD_NAME, urlquote(request.get_full_path())))
        if request.user.auth_type in (1, 2, 8, 9):
            return view_func(request, *args, **kwargs)

        if not has_permissions(request, get_perm_code(request)):
            return CustomRedirect(
                request,
                '%s?%s=%s' % ("/manager2/login/", REDIRECT_FIELD_NAME, urlquote(request.get_full_path())))
        else:
            return view_func(request, *args, **kwargs)
    return _wrapped_view_func


def validate_permission(view_func):
    '''
    判断当前页面的用户权限是否允许访问操作
    editor: kamihati 2015/5/4
    :param view_func:
    :param redirect_field_name:
    :return:
    '''
    @wraps(view_func, assigned=available_attrs(view_func))
    def _wrapped_view_func(request, *args, **kwargs):
        # 导入获取用户权限列表的方法
        from account.handler import get_person_permission
        # request.path  request.path_info 区别未明
        # editor: kamihati 2015/5/4
        # 如果用户权限正确或当前用户为超级管理员则允许访问。否则跳转到登陆界面
        if request.path_info.lower().replace("/manager2", "") in get_person_permission(request.user.id) \
                or request.user.auth_type == 9:
            return view_func(request, *args, **kwargs)
        return CustomRedirect(
            request,
            '%s?%s=%s' % ("/manager/login/", "next", urlquote(request.get_full_path())))
    return _wrapped_view_func


def get_host_file_url(request, file_path, folder_root='', root_url=''):
    '''
    返回media文件夹下的文件完整url
    :param file_path:
            request：客户端请求
             file_path：文件相对路径 。一般为数据库初始值
            folder_root: 根目录文件夹。一般为MEDIA_ROOT或 STATIC_ROOT
            root_url: 根目录文件夹配置地址。一般为MEDIA_URL或STATIC_URL
    :return:
    coder: kamihati 2015/3/31   本地测试很多资源文件不在测试服务器。故判断如果不在测试服务器则使用公网服务器地址
    '''
    result = ''
    folder = MEDIA_ROOT if folder_root == '' else folder_root
    folder_url = MEDIA_URL if root_url == '' else root_url
    # 本地测试服务器由于没有服务器的资源所以需要这个配置。线上服务器不需要
    if request.get_host().lower().find(ONLINE_HOST.lower()) == -1:
        if os.path.exists(os.path.join(folder, file_path)):
            result =  TEST_HOST + folder_url + file_path
        else:
            result =  ONLINE_HOST + folder_url + file_path
    return folder_url + file_path


def format_datetime_to_str(datetime_obj, format_str=""):
    '''
    把datetime对象转换为指定格式的string 。
    editor: kamihati 2015/6/8
    :param datetime_obj:
                  要转换的datetime对象
    :param format_str:
              为空则转换为<input type='datetime_local"> 所需的格式
    :return:
    '''
    if datetime_obj is None:
        return ""
    if format_str == "":
        format_str = '%Y-%m-%dT%H:%M'
    if datetime_obj.year < 1900:
        return ''
    return datetime_obj.strftime(format_str)


def format_str_to_datetime(datetime_str, main_split_char=" ", day_split_char='-', time_split_char=':'):
    '''
    把日期字符串转换为datetime对象.
    editor: kamihati 2015/6/8
    :param datetime_str:时间字符串
    :param main_split_char: 日期部分与时间部分的间隔字符
    :param day_split_char: 日期部分的间隔字符
    :param time_split_char: 时间部分的间隔字符
    :return:
    '''
    date_s = datetime_str.split(main_split_char)[0].split(day_split_char)
    time_s = datetime_str.split(main_split_char)[1].split(time_split_char)
    return datetime.datetime(
        int(date_s[0]), int(date_s[1]), int(date_s[2]), int(time_s[0]), int(time_s[1]), int(time_s[2]))


def thumbnail_save(user, thumbnail, obj_type, obj_id):
    """
        保存图片的缩略图
        参数描述：
          user: 用户实体
          thumbnail: 图片文件实体
          obj_type: 图片属于哪类实体 。string.  待选项为  ('topic', 'topic_remark')
          obj_id:  图片所属实体的id
    coder: kamihati 2015/3/24   从gateway/views_topic.py转移到这里改为通用方法
    coder: kamihati 2015/6/3 此方法暂无用处。确认无用后要删除。
    """
    t_path = "%s/%d" % (get_user_path(user, obj_type), obj_id)
    if not os.path.lexists(os.path.join(MEDIA_ROOT, t_path)):
        os.makedirs(os.path.join(MEDIA_ROOT, t_path))  #不存在，则创建文件夹

    if thumbnail:
        cover_image_data = thumbnail.getvalue()
        if len(cover_image_data) > ALLOWED_IMG_UPLOAD_SIZE:
            return FailResponse(u'文件超过最大充许大小')
        cover_img = Image.open(StringIO.StringIO(cover_image_data))
        cover_ext = get_img_ext(cover_img)

        thumbnail_img = "%s/thumbnail_img%s" % (t_path, cover_ext)
        if os.path.isfile(MEDIA_ROOT + thumbnail_img):
            i = 0
            while True:
                thumbnail_img = "%s/thumbnail_img_%d_%s" % (t_path, i, cover_ext)
                if os.path.isfile(MEDIA_ROOT+thumbnail_img):
                    break
        cover_img.save(os.path.join(MEDIA_ROOT, thumbnail_img))
        return thumbnail_img


def list_media_dir(folder_name):
    '''
    获取meida目录下指定目录的文件以及文件夹列表
    editor: kamihati 2015/4/15  增加此方法初步目的是把游客的资源路径转换为指定用户的
    :param folder_name:
    :return:
    '''
    root_path = os.path.join(MEDIA_ROOT, folder_name)
    fielnum = 0
    list = os.listdir(root_path)#列出目录下的所有文件和目录
    for line in list:
        filepath = os.path.join(root_path, line)
        if os.path.isdir(filepath):#如果filepath是目录，则再列出该目录下的所有文件
            for li in os.listdir(filepath):
                fielnum = fielnum +1
        elif os.path:#如果filepath是文件，直接列出文件名
            pass


def move_temp_file(temp_path, new_filename):
    '''
    把上传的临时文件移动到指定的路径
    :param temp_path:
              临时文件相对路径   例如：  /temp/xxx.jpg
    :param new_filename:
               指定文件相对路径 。  例如 /activity/1/annex     扩展名继承临时文件的扩展名
    :return:
    '''
    # 获取临时文件的扩展名
    try:
        ext = os.path.splitext(temp_path)[1]
        target_path = MEDIA_ROOT + "/" + new_filename + ext
        temp_path = MEDIA_ROOT + "/" + temp_path
        if not os.path.exists(os.path.dirname(target_path)):
            make_dir(os.path.dirname(target_path))
        # 移动文件到指定目录
        shutil.move(os.path.join(MEDIA_ROOT, temp_path), target_path)

    except:
        pass
    return new_filename + ext


def make_dir(dir_path):
    '''
    创建文件夹
    editor: kamihati 2015/4/29  创建文件夹
    :param dirname:文件夹名称
    :return:
    '''
    os.makedirs(dir_path)


def move_file(old_path, new_path):
    '''
    移动文件
    :param old_path: 旧文件路径
    :param new_path: 新文件路径
    :return:
    '''
    shutil.move(old_path, new_path)


def image_thumbail(image_path, image_large_path, image_medium_path, image_small_path):
    '''
    生成指定路径图片三种规格的缩略图
    editor: kamihati 2015/5/11 .  根据旧版本设计剥离
    :param image_path:    图片原始路径
    :param image_large_path:    较大的缩略图路径
    :param image_medium_path:  中等的缩略图路径
    :param image_small_path:  较小的缩略图路径
    :return:  返回处理完毕后的文件路径（因为缩略图路径可能改变为原始路径）
    '''
    img = Image.open(os.path.join(MEDIA_ROOT, image_path))
    # zone_asset.width = img.size[0]
    # zone_asset.height = img.size[1]

    if img.size[0] > 950 or img.size[1] > 950:
        img.thumbnail((950,950), Image.ANTIALIAS)
        img.save(os.path.join(MEDIA_ROOT, image_large_path))
    else:
        image_large_path = image_path

    if img.size[0] > 600 or img.size[1] > 600:
        img.thumbnail((600,600), Image.ANTIALIAS)
        img.save(os.path.join(MEDIA_ROOT, image_medium_path))
    else:
        image_medium_path = image_path

    img.thumbnail(get_small_size(img.size[0], img.size[1]), Image.ANTIALIAS)
    img.save(os.path.join(MEDIA_ROOT, image_small_path))
    return image_large_path, image_medium_path, image_small_path


@print_trace
def download_file(file_path, file_down_name, **kwargs):
    '''
    下载指定文件
    editor: kamihati 2015/5/20
    :param file_path:
    :return:
    '''
    from django.http import StreamingHttpResponse
    def file_iterator(file_name, chunk_size=512):
        with open(file_name) as f:
            while True:
                c = f.read(chunk_size)
                if c:
                    yield c
                else:
                    break
    file_path = MEDIA_ROOT + file_path
    response = StreamingHttpResponse(file_iterator(file_path))
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="{0}"'.format(file_down_name)
    return response


@print_trace
def write_excel(data_list, xls_download_name, **kwargs):
    '''
    制作excel文件
    editor: kamihati 2015/5/20
    :param data:
    :param file_path:
    :return:
    '''
    import xlwt
    wbk = xlwt.Workbook(encoding='utf-8', style_compression=0)
    # 第二参数用于确认同一个cell单元是否可以重设值。
    sheet = wbk.add_sheet('sheet 1', cell_overwrite_ok=True)
    col_count = 0
    # 如有标题。写标题
    if kwargs.has_key('title'):
        col_count = len(kwargs['title'])
        for i in range(col_count):
            sheet.write(0, i, kwargs['title'][i])
    row_count = len(data_list)
    for i in range(row_count):
        row = i + 1
        col_count = len(data_list[i]) if col_count == 0 else col_count
        data = data_list[i].values()
        for j in range(col_count):
            val = str(data[j]) if data[j] else ''
            val = val.encode('utf8')
            sheet.write(row, j, val)
    response = HttpResponse()#content_type='application/vnd.ms-excel')
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = u'attachment; filename=%s' % xls_download_name
    wbk.save(response)
    return response

    # sheet.write(0, 0,'this should overwrite')   ##重新设置，需要cell_overwrite_ok=True
    # style = xlwt.XFStyle()
    # font = xlwt.Font()
    # font.name = 'Times New Roman'
    # font.bold = True
    # style.font = font
    # sheet.write(0, 1, 'some bold Times text', style)
    # 该文件必须存在
    # wbk.save(file_path)



def make_valify_image():
    '''
    生成验证码所需的图片并发挥图片对象与验证码
    editor: kamihati 2015/5/22
    :return:
    '''
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    import random

    # 随机字母:
    def rndChar():
        return chr(random.randint(65, 90))

    # 随机颜色1:
    def rndColor():
        return (random.randint(64, 255), random.randint(64, 255), random.randint(64, 255))

    # 随机颜色2:
    def rndColor2():
        return (random.randint(32, 127), random.randint(32, 127), random.randint(32, 127))

    # 图片尺寸
    width = 75
    height = 32
    image = Image.new('RGB', (width, height), (255, 255, 255))
    # 创建Font对象:
    font = ImageFont.truetype(MEDIA_ROOT + '/Arial.ttf', 20)
    # 创建Draw对象:
    draw = ImageDraw.Draw(image)
    # 填充每个像素:
    for x in range(width):
        for y in range(height):
            draw.point((x, y), fill=rndColor())
    chars = ''
    # 输出文字:
    for t in range(4):
        char = rndChar()
        # x, y
        draw.text((15 * t + 5, 5), char, font=font, fill=rndColor2())
        chars += char
    # 模糊:
    # image = image.filter(ImageFilter.BLUR)
    return image, chars

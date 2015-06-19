# coding=utf-8
'''
Created on 2014-3-28

@author: Administrator
'''
import traceback
from django.utils import timezone
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from datetime import datetime
from django.http import HttpResponse

from utils import get_ip, get_tile_image_name
from utils import get_age
from utils import get_library
from utils.reg_check import *
from utils import fmt_str as F
from utils.decorator import login_required

from account.models import AuthNotice
from diy.models import AuthAlbum

from gateway import SuccessResponse, FailResponse
from WebZone.settings import MEDIA_URL

def reg_checkusername(request, username):
    username = username.lower().strip()
    if is_username_valid(username):
        if is_username_exist(username):
            return FailResponse(u'用户名已存在，请重新选择')
        return SuccessResponse(u'用户名可用')
    return FailResponse(u'用户名为3-20个字符，可以包含英文，数字，.@+-_符号')


def reg_checknickname(request, nickname):
    nickname = nickname.lower().strip()
    if is_nickname_valid(nickname):
        if is_nickname_exist(nickname):
            return FailResponse(u'笔名已存在，请重新选择')
        return SuccessResponse(u'笔名可用')
    return FailResponse(u'笔名为2-20个字符，可以包含中文，英文，数字，.@+-_符号')


def add_user_action_log(request, content):
    '''
        记录用户的操作记录
    '''
    from account.models import AuthActionLog
    ua = request.META.get('HTTP_USER_AGENT', '')
    ref = request.META.get('REFERER', '')
    AuthActionLog(user=request.user, username=request.user.username, library=request.user.library, content=content, ip=get_ip(request), user_agent=ua, referer=ref).save()


def register(request, account):
    '''
    editor: kamihati 2015/6/15  客户端注册用户
    :param request:
    :param account:
    :return:
    '''
    username = account.username.lower().strip()
    if not is_username_valid(username) or is_username_exist(username):
        return FailResponse(u'不合规的用户名')
    password = account.password
    if not is_password_valid(password):
        return FailResponse(u'密码为6-20个字符，不能包含空格')
    nickname = account.nickname.lower().strip()
    if not is_nickname_valid(nickname) or is_nickname_exist(nickname):
        return FailResponse(u'不合规的笔名')
    
    if account.has_key("sex"): sex = int(account.sex)
    else: sex = -1
    if sex not in (-1, 0, 1):
        return FailResponse(u'不合规的性别')
    
    host = request.get_host()
    from library.models import Library
    try: library = Library.objects.get(host=host)
    except: library = None
    
    if not library: library = get_library(account.library_id)[2]
    
    ip_address = get_ip(request)
    
    auth_user = AuthUser()
    auth_user.username = username
    auth_user.set_password(password)
    auth_user.nickname = nickname
    auth_user.sex = sex
    if account.has_key("email"):
        auth_user.email = account.email.lower().strip()
    if account.has_key("question") and account.has_key("answer"):
        auth_user.question = account.question.strip()
        auth_user.answer = account.answer.strip()
    auth_user.library = library
    
    auth_user.reg_ip = ip_address
    auth_user.last_ip = ip_address
    auth_user.last_login = timezone.now()
    auth_user.save()
    
    auth_notice = AuthNotice()
    auth_notice.user = auth_user
    auth_notice.save()
    
    auth_album = AuthAlbum()
    auth_album.user_id = auth_user.id
    auth_album.type_id = 0  #系统自动生成
    auth_album.album_title = u"默认相册"
    auth_album.status = 1   #可用状态
    auth_album.save()
    
    login_user = authenticate(username=username, password=password)
    auth_login(request, login_user)
    request.session["is_logon"] = True
    login_user.login_times += 1
    login_user.save()
    
    #return SuccessResponse(u"注册成功，感谢你观注少儿成长空间")
    return SuccessResponse(user_data(request.user))


def backend_login(request, param):
    '''
    editor: kamihati 2015/6/16 传入user_id获取用户登陆状态的逻辑
    :param request:
    :param param:
              .user_id
    :return:
    '''
    user_id = param.user_id if param.has_key('user_id') else 0
    user = AuthUser.objects.get(pk=user_id)
    return SuccessResponse(user_data(user))


def guest_login(request, user_id=0):
    '''
    editor: kamihati 2015/6/17  修改逻辑使支持使用user_id登录
    :param request:
    :param user_id:
    :return:
    '''
    from library.models import Library
    host = request.get_host()
    try:
        print 'guest_login...'
        library = Library.objects.get(host=host)
        print 'library_id=', library.id
    except:
        # 本地
        if host.find("8000") > -1:
            library = Library.objects.get(pk=3)
        else:
            return FailResponse(u"不存在的机构请求")
    if user_id != 0:
        # 当用户使用user_id登录
        user = AuthUser.objects.filter(pk=user_id)
        if not user:
            return FailResponse(u'用户不存在')
        user = user[0]
        try:
            auth_login(request, user)
        except Exception, e:
            print 'guest_login %s error:' % user_id
            print e
        request.session["is_logon"] = True
        return SuccessResponse(user_data(user))
    # 当sesstion中没有用户登录或者当前登录用户不为游客的时候创建新的游客账户供游客登录
    if 'is_logon' not in request.session or request.user.auth_type != 5:
        import string
        from random import choice
        chars = string.digits
        username = "guest%s" %  ''.join([choice(chars) for _ in range(6)])
        while is_username_exist(username):
            username = "guest%s" %  ''.join([choice(chars) for _ in range(6)])
        chars = string.digits + string.letters
        password = ''.join([choice(chars) for _ in range(8)])

        auth_user = AuthUser()

        auth_user.auth_type = 5     #游客会员
        auth_user.username = username
        auth_user.set_password(password)
        auth_user.nickname = username
        auth_user.sex = choice([0, 1])
        auth_user.library = library

        auth_user.reg_ip = get_ip(request)
        auth_user.last_ip = auth_user.reg_ip
        auth_user.last_login = timezone.now()
        auth_user.save()

        auth_notice = AuthNotice()
        auth_notice.user = auth_user
        auth_notice.save()

        auth_album = AuthAlbum()
        auth_album.user_id = auth_user.id
        auth_album.type_id = 0  #系统自动生成
        auth_album.album_title = u"默认相册"
        auth_album.status = 1   #可用状态
        auth_album.save()

        login_user = authenticate(username=username, password=password)
        auth_login(request, login_user)
        request.session["is_logon"] = True
        login_user.login_times += 1
        login_user.save()
    return SuccessResponse(user_data(request.user))


@login_required
def guest_register(request, param):
    """
        游客转正式用户
    """
    if request.user.auth_type <> 5:
        return FailResponse(u'用户不是游客，不需要转为正式用户')

    if param.has_key("username"): username = param.username.lower().strip()
    else: return FailResponse(u'必须传入用户名')
    if param.has_key("nickname"): nickname = param.nickname.lower().strip()
    else: return FailResponse(u'必须传入笔名')
    if param.has_key("password"): password = param.password
    else: return FailResponse(u'必须传入账号密码')
    if param.has_key("question"): question = param.question
    else: return FailResponse(u'必须传入密保问题')
    if param.has_key("answer"): answer = param.answer
    else: return FailResponse(u'必须传入密保答案')
    
    if not is_username_valid(username) or is_username_exist(username):
        return FailResponse(u'不合规的用户名')
    if not is_password_valid(password):
        return FailResponse(u'密码为6-20个字符，不能包含空格')
    if not is_nickname_valid(nickname) or is_nickname_exist(nickname):
        return FailResponse(u'不合规的笔名')
    
    if len(question) not in xrange(6, 21):
        return FailResponse(u'安全问题长度为6-20')
    if len(answer) not in xrange(2, 21):
        return FailResponse(u'安全问题长度为2-20')
    
    request.user.auth_type = 0  #正式用户的类型
    request.user.username = username
    request.user.set_password(password)
    request.user.nickname = nickname
    request.user.question = question
    request.user.answer = answer
    request.user.save()

    return SuccessResponse(user_data(request.user))

@login_required
def get_account(request, uid=None):
    if uid:
        try: auth_user = AuthUser.objects.get(id=uid)
        except: return FailResponse(u"用户ＩＤ:%s不存在" % uid)
    else: auth_user = request.user
    return SuccessResponse(user_data(auth_user))

def user_data(user):
    avatar_img = user.avatar_img if user.avatar_img else "avatar.png"
    avatar_large, avatar_medium, avatar_small = get_tile_image_name(avatar_img, 'l'), get_tile_image_name(avatar_img, 'm'), get_tile_image_name(avatar_img, 's')
    lib_id, lib_name = get_library(user.library_id)[:2]
    user_json = {"id":user.id, "username":user.username, "nickname":user.nickname, "realname":F(user.realname),
                 "sex":user.sex, "age":get_age(user.birthday), "birthday":user.birthday.strftime("%Y-%m-%d") if user.birthday else "",
                 "library_id":lib_id, "library_name":lib_name, "auth_type":user.auth_type, 
                 "telephone":F(user.telephone), "email":F(user.email), "qq":F(user.qq), "parent_qq":F(user.parent_qq),
                 "home_address":F(user.home_address), "school":F(user.school), "sign":F(user.sign), "hobby":F(user.hobby),
                 #"avatar_id":user.avatar_id if user.avatar_id else "",
                 #"large":request.build_absolute_uri(MEDIA_URL + avatar_large),"medium":request.build_absolute_uri(MEDIA_URL + avatar_medium),"small":request.build_absolute_uri(MEDIA_URL + avatar_small)}
                 "large":MEDIA_URL + avatar_large,"medium":MEDIA_URL + avatar_medium,"small":MEDIA_URL + avatar_small}
    #print user_data
    user_json["is_staff"] = user.is_staff
    return user_json

@login_required
def update_account(request, account):
    """
        更新个人信息，需要传入个人ID
    """
    if account.id <> request.user.id:
        return FailResponse(u"只能更新自己的个人信息")
    
    request.user.hobby = account.hobby
    request.user.sign = account.sign    #个人签名
    try:
        birthday = datetime.strptime(account.birthday, "%Y-%m-%d")
        request.user.birthday = birthday.date()
    except:
        traceback.print_exc()
        pass
    
    request.user.realname = account.realname
    request.user.qq = account.qq
    request.user.sex = account.sex
    request.user.email = account.email
    request.user.telephone = account.telephone
    request.user.parent_qq = account.parent_qq
    request.user.home_address = account.home_address
    request.user.school = account.school
    request.user.save()
    
    return SuccessResponse(user_data(request.user))    


from utils.decorator import print_trace
@print_trace
def login(request, username, password):
    '''
    :param request:
    :param username:
    :param password:
    :return:
    '''
    if request.method <> "POST":
        return FailResponse(u'非法请求')

    # 如果有登录状态的游客。则在登陆成功后把此游客的资源全数转移到用户名下
    guest_id = 0
    if 'is_logon' in request.session:
        if request.user.auth_type == 5:
            guest_id = request.user.id
    login_user = authenticate(username=username.lower().strip(), password=password)
    if not login_user:
        return FailResponse(u'用户名或者密码错误，请检查后重新输入')

    if login_user.library:
        if  login_user.library.expire_time <= datetime.now():
            return  FailResponse(u'您的机构已到期，请联系管理人员')

#     host = request.get_host()
#     try:
#         from library.models import Library
#         library = Library.objects.get(host=host)
#         if login_user.library_id <> library.id:
#             return FailResponse(u'不是本图书馆〖%s〗账户，请下载账户所在图书馆客户端登录' % library.lib_name)
#     except: pass

    request.session['last_ip'] = login_user.last_ip
    request.session['last_login'] = str(login_user.last_login)

    login_user.last_ip = get_ip(request)
    login_user.login_times += 1
    login_user.save()
    auth_login(request, login_user)
    request.session['is_logon'] = True
    add_user_action_log(request, u"登录云汇平台")

    user_id = request.user.id
    # 当游客id不为0 。则说明此次登陆是在游客登录之后登录。把游客资源转移到此用户名下

    if guest_id != 0:
        try:
            AuthNotice.objects.filter(user__id=guest_id).update(user=request.user)
            AuthAlbum.objects.filter(user__id=guest_id).update(user=request.user)
            # 导入diy目录的用户资源相关表转移数据
            from diy.models import AuthOpus, AuthOpusPage, AuthAsset, AuthAssetRef, AuthAssetShare, AuthOpusGrade, AuthOpusComment, AuthOpusPraise, ZoneAsset, ZoneAssetRef
            AuthOpus.objects.filter(user__id=guest_id).update(user=request.user, library=request.user.library)
            AuthAsset.objects.filter(user__id=guest_id).update(library=request.user.library, user=request.user)
            AuthAssetRef.objects.filter(user__id=guest_id).update(user=request.user)
            AuthAssetShare.objects.filter(user__id=guest_id).update(user=request.user)
            AuthOpusGrade.objects.filter(user__id=guest_id).update(user=request.user, library=request.user.library)
            AuthOpusComment.objects.filter(user__id=guest_id).update(user=request.user, library=request.user.library)
            AuthOpusPraise.objects.filter(user__id=guest_id).update(user=request.user, library=request.user.library)

            ZoneAsset.objects.filter(user__id=guest_id).update(user=request.user, library=request.user.library)
            ZoneAssetRef.objects.filter(user__id=guest_id).update(user=request.user)
            # 导入话题表用来转移数据
            from topic.models import Topic, TopicRemark
            Topic.objects.filter(user_id=guest_id).update(user_id=user_id)
            TopicRemark.objects.filter(user_id=guest_id).update(user_id=user_id)
        except Exception as err_0:
            print 'guest %s to user %s  error is: %s', (guest_id, user_id, err_0)

    return SuccessResponse(user_data(request.user))

def logout(request):
    try: del request.session['is_logon']
    except: pass
    
    auth_logout(request)
    return SuccessResponse(u"退出成功")


@login_required
def change_pass(request, oldpass, newpass):
    if request.user.check_password(oldpass):
        if not is_password_valid(newpass):
            return FailResponse(u'新密码不合规，密码为6-20个字符，不能包含空格')
        request.user.set_password(newpass)
        request.user.save()
        return SuccessResponse(u"密码修改成功")
    return FailResponse(u'旧密码错误')


@login_required
def question(request, oldpass, question, answer):
    if request.user.check_password(oldpass):
        if len(question) not in xrange(6, 21):
            return FailResponse(u'安全问题长度为6-20')
        if len(answer) not in xrange(2, 21):
            return FailResponse(u'安全问题长度为2-20')
        request.user.question = question
        request.user.answer = answer
        request.user.save()
        return SuccessResponse(u"密保问题设置成功")
    return FailResponse(u'用户密码错误')


def reset_password(request, account):
    '''
        根据安全问题重置密码，需要选择的问题，和回答的答案都一致
    '''
    username = account.username.lower().strip()
    try: auth_user = AuthUser.objects.get(username=username)
    except: return FailResponse(u'不存在的用户名:%s' % username)
    
    print auth_user.question, account.question
    print auth_user.question == account.question
    if auth_user.question == "[object Object]": #修正以前的一个错误，没有保存到密保问题，只要答案正确，就重新保存下    2014-08-19
        if auth_user.answer <> account.answer:
            return FailResponse(u'请回输入正确的密保答案')
        auth_user.question = account.question   #修改密保问题
    else:
        if auth_user.question <> account.question:
            return FailResponse(u'安全问题不正确')
        if auth_user.answer <> account.answer:
            return FailResponse(u'请回输入正确的密保答案')
    password = account.password
    if not is_password_valid(password):
        return FailResponse(u'密码为6-20个字符，不能包含空格')
    
    auth_user.set_password(password)
    auth_user.save()
    return SuccessResponse(u"密码重置成功，新密码为:%s" % password)








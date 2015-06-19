# coding=utf8
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse

from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate

# 管理员鉴权
from utils.decorator import manager_required

from django.utils import timezone

@manager_required
def index(request):
    '''
    后台首页统计数据
    editor: kamihati 2015/5/27
    :param request:
    :return:
    '''
    result = dict()
    from diy.models import AuthOpus
    # 待审核个人创作
    wait_opus_count = AuthOpus.objects.filter(status=1).count()
    result['wait_opus_count'] = wait_opus_count

    # 建议留言
    from message.models import UserMessage
    wait_message_count = UserMessage.objects.filter(status=0).count()
    result['wait_message_count'] = wait_message_count

    # 到期机构
    from library.models import Library
    old_library_count = Library.objects.filter(expire_time__lt=timezone.now()).count()
    result['old_library_count'] = old_library_count

    # 进行中活动
    from activity.models import ActivityList
    activity_count = ActivityList.objects.filter(status=1).count
    result['activity_count'] = activity_count

    # 新增学习资源
    from diy.models import ZoneAsset
    # 一天内添加的可用状态为可用的公共资源
    asset_count = ZoneAsset.objects.filter(status=1, create_time__gt=timezone.now() + timezone.timedelta(-1)).count()
    result['asset_count'] = asset_count

    # 待审核活动作品
    from activity.models import ActivityFruit
    wait_activity_fruit_count = ActivityFruit.objects.filter(status=0).count()
    result['wait_activity_fruit_count'] = wait_activity_fruit_count

    # 管理员操作记录
    from manager.models import ManagerActionLog
    manager_option_count = ManagerActionLog.objects.filter(status=0).count()
    result['manager_option_count'] = manager_option_count

    # 试用 机构
    test_library_count = Library.objects.filter(status=0).count()
    result['test_library_count'] = test_library_count
    return render(request, "manager2/default.html", result)


def login(request, redirect_field_name="/manager2/login/"):
    redirect_to = request.REQUEST.get(redirect_field_name, '/manager2/')

    if request.method == "GET":
        if request.session.get('manager_login', False) and request.user.is_active and request.user.auth_type in (1, 2):
            return HttpResponseRedirect(redirect_to)
        import datetime
        return render(request, "manager2/login.html", {"now": str(datetime.datetime.now())})
    elif request.method == "POST":
        try:
            if request.session.get('valify', '') != request.POST.get('validate').lower():
                return render(request, "manager2/login.html", {"error":u"验证码错误"})
            username = request.REQUEST["username"].strip().lower()
            password = request.REQUEST["password"].strip()
            print username, password
        except:
            return render(request, "manager2/login.html", {"error":u"参数错误"})

        try:
            login_user = authenticate(username=username, password=password)
            print '%s lgoin .success' % username
        except Exception,e :
            print e
            return render(request, "manager2/login.html", {"error":u"用户名或密码错误，请检查后重新输入"})

        if login_user is None:
            return render(request, "manager2/login.html", {"error":u"用户名或密码错误，请检查后重新输入"})

        if not login_user.is_active:
            return render(request, "manager2/login.html", {"error":u"你的账号(%s)已被封，解封请联系管理员" % username})
        '''
        if login_user.library:
            if login_user.library.host <> request.get_host().lower():
                return HttpResponse(u"<h1>非法的登录请求!</h1><br>请通过自己所属的登录网页:<a href='http://%s/manager/login/'>http://%s/manager/login/</a>进行登录!" % (login_user.library.host, login_user.library.host))
        else:
            if request.get_host().lower() not in  ("yh.3qdou.com", "10.0.0.177:8000","127.0.0.1:8000","localhost:8000"):
                return HttpResponse(u"<h1>非法的登录请求!</h1><br>请通过自己所属的登录网页:<a href='http://yh.3qdou.com/manager/login/'>http://yh.3qdou.com/manager/login/</a>进行登录!")

        request.session['last_ip'] = login_user.last_ip
        request.session['last_login'] = login_user.last_login.strftime("%Y-%m-%d %H:%M:%S") if login_user.last_login else ""
        if  login_user.library and login_user.library.expire_time:
            if login_user.library.expire_time <= datetime.now():
                return render(request, "manager/login.html", {"error":u"您的机构已到期，请联系管理人员"})
        '''
        #退出当前账号
        auth_logout(request)
        auth_login(request, login_user)
        # print "last_ip", login_user.last_ip, login_user.last_login

        request.session['last_ip'] = login_user.last_ip
        request.session['last_login'] = login_user.last_login.strftime("%Y-%m-%d %H:%M:%S") if login_user.last_login else ""

        auth_type_dict = dict()
        auth_type_dict[0] = u'普通会员'
        auth_type_dict[1] = u'图书馆长'
        auth_type_dict[2] = u'图书馆审核员'
        auth_type_dict[5] = u'游客会员'
        auth_type_dict[8] = u'二级管理员'
        auth_type_dict[9] = u'超级管理员'
        auth_type_dict[11] = u'故事大王会员'
        request.session['level'] = auth_type_dict[login_user.auth_type]
        # 原版本设计。此处非必要且在非缓存存储session的情况下会引起异常故注释 editor: kamihati 2015/4/16
        # request.session['library'] = request.user.library
        from utils import get_ip
        login_user.last_ip = get_ip(request)
        login_user.login_times += 1
        import datetime
        login_user.last_login = datetime.datetime.now()
        login_user.save()

        request.session['manager_login'] = True
        from manager import update_group_perms, update_top_perms
        update_group_perms(request)
        update_top_perms(request)
        #记录日志
        log_content = u'%s登陆管理信息系统' % login_user
        from manager2 import add_manager_action_log
        add_manager_action_log(request, log_content)
        # 导入获取用户权限列表的方法
        from account.handler import get_user_permission
        request.session['permission'] = get_user_permission(request.user.id)
        print '%s permission is.......' % username
        print request.session['permission']
        return HttpResponseRedirect(redirect_to)


def api_valify_image(request):
    '''
    获取验证码图片
    editor: kamihati 2015/5/22
    :param request:
    :return:
    '''
    from utils.decorator import make_valify_image
    img, txt = make_valify_image()
    import cStringIO
    buf = cStringIO.StringIO()
    request.session['valify'] = txt.lower()
    img.save(buf, 'png')
    return HttpResponse(buf.getvalue(), 'image/png')


def logout(request, redirect_field_name="/manager2/login/"):
    redirect_to = request.REQUEST.get(redirect_field_name, '/manager2/login/')
    auth_logout(request)
    from manager import update_group_perms, update_top_perms
    update_group_perms(request, True)
    update_top_perms(request, True)
    request.session['manager_login'] = False
    return HttpResponseRedirect(redirect_to)
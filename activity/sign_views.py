# coding=utf8

from django.http import HttpResponse


def api_del_activity_sign_member(request):
    '''
    删除报名
    editor: kamihait 2015/5/19
    :param request:
    :return:
    '''
    # 导入删除报名记录的方法
    from activity.sign_handler import del_activity_sign_member
    if del_activity_sign_member(request.POST.get('id')):
        return HttpResponse('ok')
    return HttpResponse('fail')



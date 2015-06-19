# coding=utf-8
'''
Created on 2014-3-25

@author: Administrator
'''
import os, datetime
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from library.models import Library
from WebZone.settings import MEDIA_URL, MEDIA_ROOT
from widget.models import WidgetNull
from django.core.cache import cache
from utils import get_ip

ResMusicPath = "/ResourceList/music/"
ResBookPath = "/ResourceList/Book/"
ResGamePath = "/ResourceList/game/"
ResVideoPath = "/ResourceList/video/"

from WebZone.conf import DOU_RES_HOST
from WebZone.conf import DOU_VIDEO_STREAM_HOST


def index(request):
    #import time
    #redirect_url = "/media/swf/WebOpus.swf?t=%s" % int(time.time()*1000)
    #return HttpResponseRedirect(redirect_url)
    host = request.get_host().lower()
    print 'index.begin.............'
    print 'host=', host, datetime.datetime.now()
    swf_path = ""
    try:
        lib = Library.objects.get(host=host)
        print 'lib=', lib.id
        lib_url = MEDIA_URL + lib.swf_path if lib.swf_path else ""
        print "lib_url", lib_url
        swf_path = MEDIA_URL + "lib/%s/" % lib.id
        print 'swf_path=', swf_path
        is_wtf = 0
        # 1， 9 为河南省少儿的两个机构
        if lib.id in (1, 9):
            is_wtf = 1
        print 'is_hnsst=', is_wtf
        activity_id = request.GET.get('activity_id', 0)
        opus_type = request.GET.get('opus_type', 0)
        user_id = request.user.id
        return render(request, "index.html",
                      {"lib_id": lib.id, "lib_url": lib_url, "site_name": lib.lib_name, 'host': host.lower(),
                       'asset_url': swf_path, 'is_wtf': is_wtf, 'backend': 1, 'user_id': user_id,
                       'activity_id':activity_id, 'opus_type':opus_type})
    except Library.DoesNotExist:
        return HttpResponse('机构不存在')
    
def null(request):
    #cache_key = ""
    widget_null = WidgetNull()
    widget_null.host = request.get_host()
    widget_null.real_ip = get_ip(request)
    widget_null.user_agent = request.META.get('HTTP_USER_AGENT', '')
    widget_null.referer = request.META.get('REFERER', '')
    widget_null.save()
    return HttpResponse(u"空请求")


def qdou3_video(request):
    title = request.REQUEST.get("title", "")
    if not title: return HttpResponse(u"资源文件不存在，请联系管理员")
    from django.db import connections
    cursor = connections["p2ps"].cursor()
    sql = "select path from p2p_video where title='%s'" % title
    cursor.execute(sql)
    row = cursor.fetchone()
    video_path = ""
    if row and row[0]: video_path = row[0]
    cursor.close()
    if not video_path: return HttpResponse(u"资源文件不存在，请联系管理员")
    #return HttpResponseRedirect(DOU_RES_HOST + video_path + '/vod_player.swf')

    from utils import get_ip
    ip_address = get_ip(request)
    stream_host = "800li.3qdou.com"
    if is_lan(ip_address):
        stream_host = "192.168.0.252"
    return render(request, "3qdou_video.html", {"stream_host":stream_host, "video_path":video_path})


def is_lan(ip_address):
    try:
        if ip_address.find('192.168') == 0:
            return True
        first_digit = int(ip_address.split('.')[0])
    except:
        import traceback
        traceback.print_exc()
        return False


def qdou3_book(request):
    guid = request.REQUEST.get("guid", "")
    if not guid: return HttpResponse(u"资源文件不存在，请联系管理员")
    from django.db import connections
    cursor = connections["KidsLibrarySystem"].cursor()
    sql = "select Res_Path from Res_BooksItem where Res_MetaId='%s'" % guid
    print sql
    cursor.execute(sql)
    row = cursor.fetchone()
    book_path = ""
    if row and row[0]: book_path = ResBookPath + row[0]
    cursor.close()
    if not book_path: return HttpResponse(u"资源文件不存在，请联系管理员")
    #return HttpResponseRedirect(DOU_RES_HOST + book_path)
    return render(request, "3qdou_book.html", {"book_path":book_path})



def qdou3_game(request):
    guid = request.REQUEST.get("guid", "")
    if not guid: return HttpResponse(u"资源文件不存在，请联系管理员")
    from django.db import connections
    cursor = connections["KidsLibrarySystem"].cursor()
    sql = "select Res_Path from Res_GameItem where Res_MetaId='%s'" % guid
    print sql
    cursor.execute(sql)
    row = cursor.fetchone()
    game_path = ""
    if row and row[0]: game_path = ResGamePath + row[0]
    cursor.close()
    if not game_path: return HttpResponse(u"资源文件不存在，请联系管理员")
    #return HttpResponseRedirect(DOU_RES_HOST + game_path)
    return render(request, "3qdou_game.html", {"game_path":game_path})


from django.http import HttpResponseRedirect
# django.views.decorators.csrf.csrf_token,
from django.views.static import serve as server
from WebZone.settings import MEDIA_ROOT
dom = "http://yh.3qdou.com/" 
def redirectm(request,path):
    print "media"
    "test media"
    res = dom+"media/"+path
    print res
    try:
        result = server(path,MEDIA_ROOT)
        if result:
            return result
        else:
            return HttpResponseRedirect(res)
    except:

        return HttpResponseRedirect(res)

def redirects(request,path):
    "test static"
    print "static"
    res = dom+"static/"+path
    try:
        result = server(path, MEDIA_ROOT)
        if result :
            return result
        else:
            return HttpResponseRedirect(res)
    except:

        return HttpResponseRedirect(res)


def media_serve(request, server):
    '''
    对资源文件访问进行控制
    :param server:
    :return:
    '''
    pass

#coding: utf-8
'''
Created on 2014-4-28

@author: Administrator
'''
import os

from random import choice
from WebZone.settings import FONT_ROOT
from WebZone.conf import fonts
from django.http import HttpResponse
from StringIO import StringIO

from api import txt2img

def vote(request):
    print dir(request)
    print dir(request.session)
    
    return HttpResponse("")

from utils.decorator import print_exec_time
@print_exec_time
def get_font_img(request):
    font_id = choice(range(1, len(fonts)+1))
    font_size = 24
    width = 180
    height = 480
    font_color = (choice(range(0, 256)), choice(range(0, 256)), choice(range(0, 256)))
    font_file = os.path.join(FONT_ROOT, fonts[font_id]["font"])
    font_file = font_file.encode('utf-8')
    print font_file, type(font_file)
    if not os.path.isfile(font_file):
        return HttpResponse(u'字体文件不存在')
    
    content = u'长歌行  汉乐府\r青青园中葵，\r朝露待日晞。\r阳春布德泽，\r万物生光辉。\r常恐秋节至，\r焜黄华叶衰。\r百川东到海，\r何时复西归?\r少壮不努力，\r老大徒伤悲。'
    img = txt2img(font_file, content, font_size, font_color, width, height, "right")
    #img.save("c:\\font1.png")
    buf = StringIO()
    img.save(buf, 'png')
    del img
    return HttpResponse(buf.getvalue(), mimetype="image/png")


from utils.decorator import print_exec_time
@print_exec_time
def vote_test(request):
    fruit_id = request.REQUEST.get("id", 0)
    mac = request.REQUEST.get('mac', '')
    from activity.models import ActivityFruit, ActivityVote, ActivityList
    from datetime import datetime, timedelta, date
    from django.db import connection
    from utils import get_ip
    try: activity_fruit = ActivityFruit.objects.get(id=fruit_id)
    except(ActivityFruit.DoesNotExist): return HttpResponse(u"不存在的活动作品ID")
    
    if activity_fruit.status <> 2:
        return HttpResponse(u'活作品不是发表状态，不能投票')
    
    activity_list = ActivityList.objects.get(id=activity_fruit.activity_id)
    
    if datetime.now() < activity_list.vote_start_time:
        return HttpResponse(u"《%s》投票开始时间为%s，请到时再参与投票！" % (activity_list.title, (activity_list.vote_start_time).strftime("%Y-%m-%d")))
    
    if datetime.now() >= activity_list.vote_end_time:
        return HttpResponse(u"《%s》投票截止时间为%s，感谢你的参与。" % (activity_list.title, (activity_list.vote_end_time + timedelta(days=-1)).strftime("%Y-%m-%d")))
    
    real_ip = get_ip(request)
    if real_ip <> real_ip:
        return HttpResponse(u"非法请求2")
    
    referer = request.META.get('REFERER', '')
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    user_limit_count = ActivityVote.objects.filter(create_time__gte=date.today(), user_id=1).count()
    if user_limit_count >= 1000000000:
        return HttpResponse(u"当前登录账号今日投票数超限.")
    
    ip_limit_count = ActivityVote.objects.filter(create_time__gte=date.today(), real_ip=real_ip).count()
    if ip_limit_count >= 50000000000:
        return  HttpResponse(u"你的IP(%s)今日投票数超限." % real_ip)
    
    
    cursor = connection.cursor()
    sql = "update activity_fruit set vote=vote+1 where id=%s and vote=%d" % (fruit_id, activity_fruit.vote)
    #print sql
    if cursor.execute(sql) == 0:
        return HttpResponse(u"投票失败，请重试")
    
    activity_vote = ActivityVote()
    activity_vote.library_id = 1
    activity_vote.activity_id = activity_fruit.activity_id
    activity_vote.fruit_id = fruit_id
    activity_vote.user_id = 1
    
    activity_vote.real_ip = real_ip
    activity_vote.user_agent = user_agent
    activity_vote.referer =  referer
    activity_vote.mac =  mac
    activity_vote.save()
    
    return HttpResponse('ok:(fruit_id:%s,vote:%s)' % (fruit_id, activity_fruit.vote))


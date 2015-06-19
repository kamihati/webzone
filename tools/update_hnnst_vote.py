#coding: utf-8
'''
Created on 2014-8-13

@author: Administrator
'''
import sys
sys.path.append('/www/wwwroot/')

from random import choice
import os
#使用django的数据库
os.environ['DJANGO_SETTINGS_MODULE'] = 'WebZone.settings'
from django.db import connection

if __name__ == "__main__":
    #王嘉怡    426 任可  423    一个第一页，一个第二页
    #王岩钢   424  康楷元  425    第二页，或者第三页
    cursor = connection.cursor()
    sql = "select vote from widget_story_opus ORDER BY vote DESC LIMIT 36"
    cursor.execute(sql)
    rows = cursor.fetchall()
    
    vote_list = []
    for row in rows:
        vote_list.append(int(row[0]))
    print "vote_list", len(vote_list), vote_list[23]
    
    vote1 = choice(range(vote_list[8], vote_list[5]))
    sql = "update widget_story_opus set vote=%d where id=426" % vote1
    print sql
    cursor.execute(sql)
    
    vote2 = choice(range(vote_list[23], vote_list[11]))
    sql = "update widget_story_opus set vote=%d where id=423" % vote2
    print sql
    cursor.execute(sql)
    
    vote3 = choice(range(vote_list[26], vote_list[11]))
    sql = "update widget_story_opus set vote=%d where id=424" % vote3
    print sql
    cursor.execute(sql)
    
    vote4 = choice(range(vote_list[len(vote_list)-1], vote_list[23]))
    sql = "update widget_story_opus set vote=%d where id=425" % vote4
    print sql
    cursor.execute(sql)
    
    cursor.close()


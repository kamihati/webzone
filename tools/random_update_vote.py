#coding: utf-8
'''
Created on 2014年8月14日

@author: Administrator
'''
import sys
sys.path.append('/www/wwwroot/')
from datetime import datetime

from random import choice
import os
#使用django的数据库
os.environ['DJANGO_SETTINGS_MODULE'] = 'WebZone.settings'
from django.db import connection
from twisted.internet import reactor


class RandomVote():
    def __init__(self):
        self.dt_end = datetime.strptime("2014-08-21", "%Y-%m-%d")
        self.run()
    
    def run(self):
        cursor = connection.cursor()
        sql = "select id,vote from widget_story_opus ORDER BY vote DESC"
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        for row in rows:
            id = row[0]
            vote = int(row[1])
            reward_vote = self.get_choice_vote(vote)
            if reward_vote > 0:
                sql = "update widget_story_opus set vote=vote+%d where id=%d" % (reward_vote, id)
                print sql
                cursor.execute(sql)
        time_out = choice(range(8*60,11*60))
        if datetime.now()<self.dt_end:
            reactor.callLater(time_out, self.run)
        
    def get_choice_vote(self, cur_vote):
        if cur_vote < 50:
            return choice(range(1,5))
        elif cur_vote < 100:
            return choice(range(1,6))
        elif cur_vote < 500:
            return choice(range(2,6))
        elif cur_vote < 1000:
            return choice(range(2,5))
        elif cur_vote < 5000:
            return choice(range(1,4))
        elif cur_vote < 10000:
            return choice(range(0,3))
        else:
            return choice(range(0,2))

if __name__ == "__main__":
    RandomVote()
    reactor.run()
    
    
    
    
    
    
    
    
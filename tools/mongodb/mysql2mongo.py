#coding: utf-8
'''
Created on 2015年3月2日

@author: Administrator
'''

import sys
reload(sys)
sys.setdefaultencoding('utf-8') 
sys.path.insert(0, '..')
sys.path.insert(0, '../..')
import re

import os
import shutil
#使用django的数据库
os.environ['DJANGO_SETTINGS_MODULE'] = 'WebZone.settings'

from activity.models import ActivityVote, ActivityComment, ActivityPraise
from diy.models import AuthOpusComment, AuthOpusPraise

import pymongo

class Mysql2Mongo():
    def __init__(self):
        conn = pymongo.Connection("127.0.0.1", 27017)
        conn.webzone.authenticate("webzone", "mongodb@svvt#7H")
        self.db = conn.webzone
        print self.db.activity_praise.count()
        #self.activity_praise()
        #self.activity_comment()
        #self.activity_vote()
        self.auth_opus_comment()
        self.auth_opus_praise()
    
    
    def activity_praise(self):
        for activity_praise in ActivityPraise.objects.all():
            #print activity_praise.id, activity_praise.library_id, activity_praise.user_id
            #print activity_praise.activity_fruit_id, activity_praise.create_time
            d = {"id":activity_praise.id, "library_id":activity_praise.library_id, "user_id":activity_praise.user_id}
            d["activity_fruit_id"] = activity_praise.activity_fruit_id
            d["create_time"] = activity_praise.create_time
            self.db.activity_praise.save(d)
        self.db.activity_praise.find_one()
        
    def activity_comment(self):
        for activity_comment in ActivityComment.objects.all():
            d = {"id":activity_comment.id, "library_id":activity_comment.library_id, "user_id":activity_comment.user_id}
            d["activity_fruit_id"] = activity_comment.activity_fruit_id
            d["comment"] = activity_comment.comment
            d["create_time"] = activity_comment.create_time
            self.db.activity_comment.save(d)
        print self.db.activity_comment.find_one()
        
    def activity_vote(self):
        for activity_vote in ActivityVote.objects.all():
            d = {"id":activity_vote.id, "library_id":activity_vote.library_id, "user_id":activity_vote.user_id}
            d["fruit_id"] = activity_vote.fruit_id
            d["user_agent"] = activity_vote.user_agent
            d["real_ip"] = activity_vote.real_ip
            d["referer"] = activity_vote.referer
            d["create_time"] = activity_vote.create_time
            self.db.activity_vote.save(d)
        print self.db.activity_vote.find_one()
    
    
    
    def auth_opus_praise(self):
        for auth_opus_praise in AuthOpusPraise.objects.all():
            d = {"id":auth_opus_praise.id, "library_id":auth_opus_praise.library_id, "user_id":auth_opus_praise.user_id}
            d["auth_opus_id"] = auth_opus_praise.auth_opus_id
            d["create_time"] = auth_opus_praise.create_time
            self.db.auth_opus_praise.save(d)
        self.db.auth_opus_praise.find_one()
        
    def auth_opus_comment(self):
        for auth_opus_comment in AuthOpusComment.objects.all():
            d = {"id":auth_opus_comment.id, "library_id":auth_opus_comment.library_id, "user_id":auth_opus_comment.user_id}
            d["auth_opus_id"] = auth_opus_comment.auth_opus_id
            d["comment"] = auth_opus_comment.comment
            d["create_time"] = auth_opus_comment.create_time
            self.db.auth_opus_comment.save(d)
        print self.db.auth_opus_comment.find_one()
    
if __name__ == "__main__":
    Mysql2Mongo()







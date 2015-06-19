#coding: utf-8
'''
Created on 2015年3月4日

@author: Administrator
'''
from datetime import datetime
import mongoengine
from mongoengine import connect
from mongoengine import Document
from mongoengine.fields import StringField, DateTimeField, ListField, IntField
#connect('webzone','webzone','webzone')
#mongoengine.register_connection('default', name="webzone", username="webzone", password="webzone")
mongoengine.register_connection('default', name="webzone", username="webzone", password="mongodb@svvt#7H")

class Test(Document):
    title = StringField(required=True, max_length=200)
    posted = DateTimeField(default=datetime.now)
    tags = ListField(StringField(max_length=50))
    


# def get_next_id(tablename='topic'):
#     #db.ids.findAndModify({update:{$inc: {id:1}},query:{tablename:'topic'},new:true});
#     data = {'findAndModify':'ids','update':{'$inc':{'id':1}},'query':{'tablename':tablename},'new':True}
#     idrecord = $this->db()->command( $data );
#     $newid = $idrecord['value'];
#     
#     return $newid['id'];
    
class ActivityVoteMongo(Document):
    library_id = IntField(required=True)
    activity_id = IntField(required=True)
    fruit_id = IntField(required=True)
    user_id = IntField(required=False)
    user_agent = StringField(max_length=255)
    real_ip = StringField(max_length=255)
    referer = StringField(max_length=255)
    mac = StringField(max_length=25)
    
    create_time = DateTimeField(default=datetime.now)
    
    
    meta = {"collection":"activity_vote",
            }


class ActivityGradeMongo(Document):
    library_id = IntField(required=True)
    user_id = IntField(required=True)
    fruit_id = IntField(required=True)
    grade = IntField(default=0)
    create_time = DateTimeField(default=datetime.now)
    
    meta = {"collection":"activity_grade",
            }

        
class ActivityCommentMongo(Document):
    library_id = IntField(required=True)
    user_id = IntField(required=True)
    fruit_id = IntField(required=True)
    comment = StringField(max_length=500, required=True)
    create_time = DateTimeField(default=datetime.now)
    
    meta = {"collection":"activity_comment",
            }



class ActivityPraiseMongo(Document):
    library_id = IntField(required=True)
    user_id = IntField(required=True)
    fruit_id = IntField(required=True)
    
    create_time = DateTimeField(default=datetime.now)
    
    meta = {"collection":"activity_praise",
            }

        


class AuthOpusGradeMongo(Document):
    library_id = IntField(required=True)
    user_id = IntField(required=True)
    auth_opus_id = IntField(required=True)
    grade = IntField(default=0)
    create_time = DateTimeField(default=datetime.now)
    
    meta = {"collection":"auth_opus_grade",
            }

        
class AuthOpusCommentMongo(Document):
    library_id = IntField(required=True)
    user_id = IntField(required=True)
    auth_opus_id = IntField(required=True)
    comment = StringField(max_length=500, required=True)
    create_time = DateTimeField(default=datetime.now)
    
    meta = {"collection":"auth_opus_comment",
            }



class AuthOpusPraiseMongo(Document):
    library_id = IntField(required=True)
    user_id = IntField(required=True)
    auth_opus_id = IntField(required=True)
    
    create_time = DateTimeField(default=datetime.now)
    
    meta = {"collection":"auth_opus_praise",
            }







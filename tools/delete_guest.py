#coding: utf-8
'''
Created on 2014年11月05日

@author: Administrator
'''
import os
from datetime import datetime, timedelta
import sys
sys.path.insert(0, '..')
sys.path.append('/www/webzone/')

#使用django的数据库
os.environ['DJANGO_SETTINGS_MODULE'] = 'WebZone.settings'

from account.models import AuthUser
from diy.models import AuthAlbum
from diy.models import AuthAsset
from diy.models import AuthAssetRef
from diy.models import AuthAssetShare

from diy.models import AuthOpus
from diy.models import AuthOpusPage
from diy.models import AuthOpusPraise
#from diy.models import AuthOpusGrade
from diy.models import AuthOpusComment

from account.models import AuthMessage
from account.models import AuthNotice
from account.models import AuthActionLog

from django.db import connection
import shutil

class DeleteGuest():
	def __init__(self):
		self.init()


	def init(self):
		cursor = connection.cursor()
		date_end = datetime.now() + timedelta(days=-1)
		sql = "select id, library_id,date_joined from auth_user where auth_type=5 and last_login<'%s'" % date_end.strftime('%Y-%m-%d %H:%M:%S')
		print sql
		cursor.execute(sql)
		rows = cursor.fetchall()
		ready_count = len(rows)
		finish_count = 0
		print "ready_count:%d" % ready_count
		for row in rows:
			uid = int(row[0])
			library_id = int(row[1]) if row[1] else None
			date_joined = row[2]
			if not library_id: continue

			user_path = '/www/wwwroot/media/user/%d/%s/%d' % (library_id, date_joined.strftime("%Y"), uid)
			#print user_path
			if os.path.isdir(user_path):
				shutil.rmtree(user_path)
				print user_path, 'deleted'

			AuthAssetShare.objects.filter(user_id=uid).delete()
			AuthAssetRef.objects.filter(user_id=uid).delete()
			AuthAlbum.objects.filter(user_id=uid).delete()
			AuthAsset.objects.filter(user_id=uid).delete()

			AuthMessage.objects.filter(user_id=uid).delete()
			AuthMessage.objects.filter(from_user_id=uid).delete()

			AuthNotice.objects.filter(user_id=uid).delete()
			AuthActionLog.objects.filter(user_id=uid).delete()

			AuthOpusComment.objects.filter(user_id=uid).delete()
			#AuthOpusGrade.objects.filter(user_id=uid).delete()
			AuthOpusPraise.objects.filter(user_id=uid).delete()

			opus_list = AuthOpus.objects.filter(user_id=uid)
			if opus_list:
				for opus in opus_list:
					AuthOpusPage.objects.filter(auth_opus_id=opus.id).delete()
					print 'opus:%d deleted' % opus.id
					opus.delete()

			AuthUser.objects.filter(id=uid).delete()

			print "auth_user:%d is deleted" % uid
			finish_count += 1
		print "ready_count:%d, finish_count:%d" % (ready_count, finish_count)

if __name__ == "__main__":
	DeleteGuest()

#coding: utf-8
'''
Created on 2014-6-10

@author: Administrator
'''
#from converter import Converter
#from math import ceil, floor
import traceback
from random import choice
import sys
from datetime import datetime
sys.path.insert(0, '..')
sys.path.append('/www/wwwroot/')

import os
import re
#使用django的数据库
os.environ['DJANGO_SETTINGS_MODULE'] = 'WebZone.settings'
from WebZone.settings import MEDIA_ROOT
from diy.models import DouBook, DouVideo, DouGame, DouAsset

from django.db import connection, connections
import shutil
from utils import get_small_size
#from WebZone.conf import THUMBNAIL_SIZE
from PIL import Image

import shutil



def sync_res_books():
	db_cursor = connections["KidsLibrarySystem"].cursor()
	sql = "select Res_Guid,Res_Title,Res_Subtitle,Res_SeriesTitle,Res_Label,Res_PrimaryResponser,Res_LiabilityMethod,Res_OtherResponser,Res_OtherMethod,Res_KeyWords,Res_Abstract,Res_Publisher,Res_PublishDate,Res_PageNum,Res_Language,Res_Area,Res_Type,Res_FirstLetter,Res_FacePath,Res_Extension from Res_Books"
	db_cursor.execute(sql)
	rows = db_cursor.fetchall()
	print len(rows)
	for row in rows:
		Res_Guid = row[0]
		Res_Title = row[1]
		Res_Subtitle = row[2]
		Res_SeriesTitle = row[3]
		Res_Label = row[4]
		Res_PrimaryResponser = row[5]
		Res_LiabilityMethod = row[6]
		Res_OtherResponser = row[7]
		Res_OtherMethod = row[8]
		Res_KeyWords = row[9]
		Res_Abstract = row[10]
		Res_Publisher = row[11]
		Res_PublishDate = row[12]
		Res_PageNum = row[13]
		Res_Language = row[14]
		Res_Area = row[15]
		Res_Type = row[16]
		Res_FirstLetter = row[17]
		Res_FacePath = row[18]
		Res_Extension = row[19]

		dou_book = DouBook()
		dou_book.guid = Res_Guid
		dou_book.title = Res_Title
		dou_book.sub_title = Res_Subtitle
		dou_book.series_title = Res_SeriesTitle
		dou_book.label = Res_Label
		dou_book.primary_responser = Res_PrimaryResponser
		dou_book.liability_method = Res_LiabilityMethod
		dou_book.other_responser = Res_OtherResponser
		dou_book.other_method = Res_OtherMethod
		dou_book.key_words = Res_KeyWords
		dou_book.description = Res_Abstract
		dou_book.publisher = Res_Publisher
		dou_book.publish_date = Res_PublishDate
		dou_book.page_count = Res_PageNum
		dou_book.language = Res_Language
		dou_book.area = Res_Area
		dou_book.type_content = Res_Type
		dou_book.fister_letter = Res_FirstLetter
		dou_book.thumbnail = Res_FacePath
		dou_book.extension = Res_Extension
		dou_book.save()
		#break
		print "1"
	db_cursor.close()

def sync_res_books_item():
	db_cursor = connections["KidsLibrarySystem"].cursor()
	sql = "select Res_MetaId,Res_Path,Res_Date from Res_BooksItem"
	db_cursor.execute(sql)
	rows = db_cursor.fetchall()
	print len(rows)
	for row in rows:
		Res_MetaId = row[0]
		Res_Path = row[1]
		Res_Date = row[2]

		try: dou_book = DouBook.objects.get(guid=Res_MetaId)
		except(DouBook.DoesNotExist ): print Res_MetaId, 'not found'
		dou_book.res_path = Res_Path
		dou_book.create_time = Res_Date
		dou_book.save()
		print 'ok'

def update_books_desc():
	db_cursor = connections["KidsLibrarySystem"].cursor()
	sql = "select Res_Guid,Res_Abstract from Res_Books"
	db_cursor.execute(sql)
	rows = db_cursor.fetchall()
	print len(rows)
	index = 1
	for row in rows:
		Res_MetaId = row[0]
		Res_Abstract = row[1]

		try: dou_book = DouBook.objects.get(guid=Res_MetaId)
		except(DouBook.DoesNotExist ): print Res_MetaId, 'not found'
		dou_book.description = Res_Abstract
		dou_book.save()
		index += 1
		print 'ok', index


def sync_res_video():
	db_cursor = connections["KidsLibrarySystem"].cursor()
	sql = "select Res_Guid,Res_Title,Res_Subtitle,Res_SeriesName,Res_Lable,0,0,0,0,Res_KeyWords,Res_Description,0,0,0,Res_Language,Res_Area,Res_Type,Res_FirstLetter,Res_FacePath,Res_Extension from Res_Videos"
	db_cursor.execute(sql)
	rows = db_cursor.fetchall()
	print len(rows)
	index = 1
	for row in rows:
		Res_Guid = row[0]
		Res_Title = row[1]
		Res_Subtitle = row[2]
		Res_SeriesTitle = row[3]
		Res_Label = row[4]
		#Res_PrimaryResponser = row[5]
		#Res_LiabilityMethod = row[6]
		#Res_OtherResponser = row[7]
		#Res_OtherMethod = row[8]
		Res_KeyWords = row[9]
		Res_Abstract = row[10]
		#Res_Publisher = row[11]
		#Res_PublishDate = row[12]
		#Res_PageNum = row[13]
		Res_Language = row[14]
		Res_Area = row[15]
		Res_Type = row[16]
		Res_FirstLetter = row[17]
		Res_FacePath = row[18]
		Res_Extension = row[19]

		dou_video = DouVideo()
		dou_video.guid = Res_Guid
		dou_video.title = Res_Title
		dou_video.sub_title = Res_Subtitle
		dou_video.series_title = Res_SeriesTitle
		dou_video.label = Res_Label
		#dou_video.primary_responser = Res_PrimaryResponser
		#dou_video.liability_method = Res_LiabilityMethod
		#dou_video.other_responser = Res_OtherResponser
		#dou_video.other_method = Res_OtherMethod
		dou_video.key_words = Res_KeyWords
		dou_video.description = Res_Abstract
		#dou_video.publisher = Res_Publisher
		#dou_video.publish_date = Res_PublishDate
		#dou_video.page_count = Res_PageNum
		dou_video.language = Res_Language
		dou_video.area = Res_Area
		dou_video.type_content = Res_Type
		dou_video.fister_letter = Res_FirstLetter
		dou_video.thumbnail = Res_FacePath
		dou_video.extension = Res_Extension
		dou_video.save()
		#break
		index += 1
		print index, "ok"
	db_cursor.close()

def sync_res_video_item():
	db_cursor = connections["KidsLibrarySystem"].cursor()
	sql = "select Res_MetaId,Res_Path,Res_Date from Res_VideosItem"
	db_cursor.execute(sql)
	rows = db_cursor.fetchall()
	index = 1
	for row in rows:
		Res_MetaId = row[0]
		Res_Path = row[1]
		Res_Date = row[2]

		try: dou_video = DouVideo.objects.get(guid=Res_MetaId)
		except(DouVideo.DoesNotExist ): print Res_MetaId, 'not found'
		dou_video.res_path = Res_Path
		dou_video.create_time = Res_Date
		dou_video.save()
		index += 1
		print index, len(rows)

def update_video_rest():
	db_cursor = connections["KidsLibrarySystem"].cursor()
	sql = "select Res_Guid,Res_PrimaryResponser,Res_IsRecommend,Res_WatchingNum,Res_CommentNum,Res_Score from Res_Videos"
	db_cursor.execute(sql)
	rows = db_cursor.fetchall()
	print len(rows)
	index = 1
	for row in rows:
		Res_Guid = row[0]
		Res_PrimaryResponser = row[1]
		Res_IsRecommend = row[2]
		Res_WatchingNum = row[3]
		Res_CommentNum = row[4]
		Res_Score = row[5]

		try: dou_video = DouVideo.objects.get(guid=Res_Guid)
		except(DouVideo.DoesNotExist ): print Res_Guid, 'not found'
		if Res_PrimaryResponser and len(Res_PrimaryResponser)>0:
			dou_video.primary_responser = Res_PrimaryResponser
		if Res_IsRecommend:
			dou_video.is_top = 1
		if Res_WatchingNum:
			dou_video.preview_times = Res_WatchingNum
		if Res_CommentNum:
			dou_video.comment_times = Res_CommentNum
		if Res_Score:
			dou_video.grade = Res_Score
		dou_video.save()
		index += 1
		print index, len(rows)

def update_video_path():
	db_cursor = connection.cursor()
	sql = "select id,res_path from dou_video where status=-1"
	db_cursor.execute(sql)
	rows = db_cursor.fetchall()
	prefix_path = u'/www/wwwroot/media/4t/3qdou/lost/'
	#prefix_path = '/www/wwwroot/media/4t/3qdou/v_3qdou/'
	desc_path = u'/www/wwwroot/media/4t/3qdou/video/'
	index = 1
	ok_count = 0
	fail_count = 0
	#ok_file = open("")
	for row in rows:
		id = row[0]
		res_path = row[1]

		video_path = prefix_path + res_path
		print video_path
		if os.path.isfile(video_path):
			try: dou_video = DouVideo.objects.get(id=id)
			except(DouVideo.DoesNotExist ): print id, 'not found'
			desc_video_path = desc_path + res_path
			#copy and delete original file
			shutil.move(video_path, desc_video_path)
			dou_video.status = 1
			dou_video.save()
			print dou_video.id
			ok_count += 1
		else:
			#print index, len(rows), res_path
			fail_count += 1
		index += 1
		#print index, len(rows)
	print ok_count, fail_count, len(rows)


def sync_res_game():
	db_cursor = connections["KidsLibrarySystem"].cursor()
	sql = "select Res_Guid,Res_Title,Res_Subtitle,Res_SeriesName,Res_Lable,0,0,0,0,Res_KeyWords,Res_Description,0,0,0,Res_Language,Res_Area,Res_Type,Res_FirstLetter,Res_FacePath,Res_Extension,Res_IsRecommend,Res_PlayingNum,Res_CommentNum,Res_Score from Res_Game"
	db_cursor.execute(sql)
	rows = db_cursor.fetchall()
	index = 1
	for row in rows:
		Res_Guid = row[0]
		Res_Title = row[1]
		Res_Subtitle = row[2]
		Res_SeriesTitle = row[3]
		Res_Label = row[4]
		Res_PrimaryResponser = row[5]
		#Res_LiabilityMethod = row[6]
		#Res_OtherResponser = row[7]
		#Res_OtherMethod = row[8]
		Res_KeyWords = row[9]
		Res_Abstract = row[10]
		#Res_Publisher = row[11]
		#Res_PublishDate = row[12]
		#Res_PageNum = row[13]
		Res_Language = row[14]
		Res_Area = row[15]
		Res_Type = row[16]
		Res_FirstLetter = row[17]
		Res_FacePath = row[18]
		Res_Extension = row[19]
		Res_IsRecommend = row[20]
		Res_PlayingNum = row[21]
		Res_CommentNum = row[22]
		Res_Score = row[23]

		dou_game = DouGame()
		dou_game.guid = Res_Guid
		dou_game.title = Res_Title
		dou_game.sub_title = Res_Subtitle
		dou_game.series_title = Res_SeriesTitle
		dou_game.label = Res_Label
		dou_game.primary_responser = Res_PrimaryResponser
		#dou_video.liability_method = Res_LiabilityMethod
		#dou_video.other_responser = Res_OtherResponser
		#dou_video.other_method = Res_OtherMethod
		dou_game.key_words = Res_KeyWords
		dou_game.description = Res_Abstract
		#dou_video.publisher = Res_Publisher
		#dou_video.publish_date = Res_PublishDate
		#dou_video.page_count = Res_PageNum
		dou_game.language = Res_Language
		dou_game.area = Res_Area
		dou_game.type_content = Res_Type
		dou_game.fister_letter = Res_FirstLetter
		dou_game.thumbnail = Res_FacePath
		dou_game.extension = Res_Extension

		if Res_IsRecommend:
			dou_game.is_top = 1
		if Res_PlayingNum:
			dou_game.preview_times = Res_PlayingNum
		if Res_CommentNum:
			dou_game.comment_times = Res_CommentNum
		if Res_Score:
			dou_game.grade = Res_Score

		dou_game.save()
		print index, len(rows)
		index += 1
	db_cursor.close()

def sync_res_game_item():
	db_cursor = connections["KidsLibrarySystem"].cursor()
	sql = "select Res_MetaId,Res_Path,Res_Date from Res_GameItem"
	db_cursor.execute(sql)
	rows = db_cursor.fetchall()
	index = 1
	for row in rows:
		Res_MetaId = row[0]
		Res_Path = row[1]
		Res_Date = row[2]

		try: dou_game = DouGame.objects.get(guid=Res_MetaId)
		except(DouGame.DoesNotExist ): print Res_MetaId, 'not found'
		dou_game.res_path = Res_Path
		dou_game.create_time = Res_Date
		dou_game.save()
		index += 1
		print index, len(rows)


def update_game_path():
	db_cursor = connection.cursor()
	sql = "select id,guid,title,res_path from dou_game where status=-1"
	db_cursor.execute(sql)
	rows = db_cursor.fetchall()
	#prefix_path = '/www/wwwroot/media/4t/3qdou/tszy_hnsst/game/'
	prefix_path = '/www/wwwroot/media/4t/3qdou/g_3qdou/'
	desc_path = '/www/wwwroot/media/4t/3qdou/game/'
	index = 1
	ok_count = 0
	fail_count = 0
	for row in rows:
		id = row[0]
		guid = row[1]
		title = row[2]
		res_path = row[3]

		game_path = prefix_path + res_path
		if os.path.isfile(game_path):
			try: dou_game = DouGame.objects.get(id=id)
			except(DouGame.DoesNotExist ): print Res_Guid, 'not found'
			desc_game_path = desc_path + res_path
			#copy and delete original file
			shutil.move(game_path, desc_game_path)
			dou_game.status = 1
			dou_game.save()
			ok_count += 1
		else:
			#print index, len(rows), res_path
			fail_count += 1
		index += 1
		print index, len(rows)
	print ok_count, fail_count, len(rows)


def insert_into_asset(type_id=6):
	index = 1
	if type_id == 6:
		for dou_video in DouVideo.objects.all():
			dou_asset = DouAsset()
			dou_asset.type_id = 6 	#video

			dou_asset.guid = dou_video.guid
			dou_asset.title = dou_video.title
			dou_asset.sub_title = dou_video.sub_title
			dou_asset.series_title = dou_video.series_title
			dou_asset.label = dou_video.label
			dou_asset.primary_responser = dou_video.primary_responser
			#dou_video.liability_method = Res_LiabilityMethod
			#dou_video.other_responser = Res_OtherResponser
			#dou_video.other_method = Res_OtherMethod
			dou_asset.key_words = dou_video.key_words
			dou_asset.description = dou_video.description
			#dou_video.publisher = Res_Publisher
			#dou_video.publish_date = Res_PublishDate
			#dou_video.page_count = Res_PageNum
			dou_asset.language = dou_video.language
			dou_asset.area = dou_video.area
			dou_asset.type_content = dou_video.type_content
			dou_asset.fister_letter = dou_video.fister_letter
			dou_asset.thumbnail = dou_video.thumbnail
			dou_asset.extension = dou_video.extension
			dou_asset.res_path = dou_video.res_path

			dou_asset.is_top = dou_video.is_top
			dou_asset.preview_times = dou_video.preview_times
			dou_asset.comment_times = dou_video.comment_times
			dou_asset.grade = dou_video.grade

			dou_asset.status = dou_video.status
			dou_asset.save()
			index += 1
			print index, "ok"
	elif type_id == 3:
		for dou_game in DouGame.objects.all():
			dou_asset = DouAsset()
			dou_asset.type_id = 3 	#game

			dou_asset.guid = dou_game.guid
			dou_asset.title = dou_game.title
			dou_asset.sub_title = dou_game.sub_title
			dou_asset.series_title = dou_game.series_title
			dou_asset.label = dou_game.label
			dou_asset.primary_responser = dou_game.primary_responser
			#dou_video.liability_method = Res_LiabilityMethod
			#dou_video.other_responser = Res_OtherResponser
			#dou_video.other_method = Res_OtherMethod
			dou_asset.key_words = dou_game.key_words
			dou_asset.description = dou_game.description
			#dou_video.publisher = Res_Publisher
			#dou_video.publish_date = Res_PublishDate
			#dou_video.page_count = Res_PageNum
			dou_asset.language = dou_game.language
			dou_asset.area = dou_game.area
			dou_asset.type_content = dou_game.type_content
			dou_asset.fister_letter = dou_game.fister_letter
			dou_asset.thumbnail = dou_game.thumbnail
			dou_asset.extension = dou_game.extension
			dou_asset.res_path = dou_game.res_path

			dou_asset.is_top = dou_game.is_top
			dou_asset.preview_times = dou_game.preview_times
			dou_asset.comment_times = dou_game.comment_times
			dou_asset.grade = dou_game.grade

			dou_asset.status = dou_game.status
			dou_asset.save()
			index += 1
			print index, "ok"


def update_book_path():
	db_cursor = connection.cursor()
	sql = "select id,guid,title,res_path,extension from dou_book where status=-1"
	db_cursor.execute(sql)
	rows = db_cursor.fetchall()
	prefix_path = '/www/wwwroot/media/4t/3qdou/book/'
	index = 1
	ok_count = 0
	fail_count = 0
	for row in rows:
		id = row[0]
		guid = row[1]
		title = row[2]
		res_path = row[3]
		extension = row[4]

		try: dou_book = DouBook.objects.get(id=id)
		except(DouBook.DoesNotExist ): print guid, 'not found'
		if extension == "main.swf":
			file_path = os.path.join(prefix_path + title.lower(),'files')
			if not os.path.isdir(file_path):
				dou_book.status = -1
				dou_book.save()
				fail_count += 1
			else:
				dou_book.status = 1
				dou_book.file_path = title.lower() + "/files"
				dou_book.thumb_path = title.lower() + "/files"
				dou_book.save()
				ok_count += 1
		elif extension == "book.swf":
			file_path = os.path.join(prefix_path + title.lower(),'files/page')
			if not os.path.isdir(file_path):
				print file_path
				dou_book.status = -1
				dou_book.save()
				fail_count += 1
			else:
				dou_book.status = 1
				dou_book.file_path = title.lower() + "/files/page"
				dou_book.thumb_path = title.lower() + "/files/thumb"
				dou_book.save()
				ok_count += 1
		elif extension == "swf":
			book_file = prefix_path + res_path
			if not os.path.isfile(book_file):
				dou_book.status = -1
				dou_book.save()
				fail_count += 1
			else:
				dou_book.status = 1
				dou_book.page_count = 1
				dou_book.file_path = res_path
				dou_book.save()
				ok_count += 1
		else:
			print id, guid, title, extension

		index += 1
		print index, len(rows)
	print ok_count, fail_count, len(rows)

def update_book_width1():
	from BeautifulSoup import BeautifulSoup

	db_cursor = connection.cursor()
	sql = "select id,guid,title,res_path,extension from dou_book where extension='main.swf'"
	db_cursor.execute(sql)
	rows = db_cursor.fetchall()
	prefix_path = '/www/wwwroot/media/4t/3qdou/book/'
	index = 1
	ok_count = 0
	fail_count = 0
	for row in rows:
		id = row[0]
		guid = row[1]
		title = row[2]
		res_path = row[3]
		extension = row[4]

		setting_file = os.path.join(prefix_path, title.lower()) + "/setting.xml"
		f = open(setting_file, 'r')
		text = f.read()
		text = text.replace('\x00','').replace('\t','')[2:]
		f.close()

		try:
			soup = BeautifulSoup(text)
			page_count = int(soup.find('pagecount').text)
			width = int(soup.find('pagewidth').text)
			height = int(soup.find('pageheight').text)
			try: dou_book = DouBook.objects.get(id=id)
			except(DouBook.DoesNotExist ): print guid, 'not found'
			if dou_book.page_count <> page_count:
				print dou_book.id, dou_book.page_count, page_count
				dou_book.page_count = page_count
				fail_count += 1
			else:
				ok_count += 1
			dou_book.width = width
			dou_book.height = height
			dou_book.save()
		except:
			print id, text
			#print ok_count, fail_count, len(rows)
			break
	print ok_count, fail_count, len(rows)

def update_book_width2():
	from PIL import Image

	db_cursor = connection.cursor()
	sql = "select id,title,file_path,thumb_path from dou_book where extension='book.swf'"
	db_cursor.execute(sql)
	rows = db_cursor.fetchall()
	prefix_path = '/www/wwwroot/media/4t/3qdou/book/'
	index = 1
	ok_count = 0
	fail_count = 0
	for row in rows:
		id = row[0]
		title = row[1]
		file_path = row[2]
		thumb_path = row[3]

		img_path = os.path.join(prefix_path, title.lower()) + "/files/mobile/1.jpg"
		if not os.path.isfile(img_path):
			print "no image file", id, title, img_path
			break
		img = Image.open(img_path)
		width = img.size[0]
		height = img.size[1]

		file_path = os.path.join(prefix_path, file_path)
		if not os.path.isdir(file_path):
			print "no file path", file_path
			break
		page_count = get_file_count(file_path, '.swf')
		if not page_count:
			print "can not get file count", id, title, page_count
			break
		try: dou_book = DouBook.objects.get(id=id)
		except(DouBook.DoesNotExist ): print guid, 'not found'
		if dou_book.page_count <> page_count:
			print dou_book.id, dou_book.page_count, page_count
			dou_book.page_count = page_count
			fail_count += 1
		else:
			ok_count += 1
		dou_book.width = width
		dou_book.height = height
		dou_book.save()

	print ok_count, fail_count, len(rows)

def get_file_count(file_path, extension=''):
	count = 0
	for item in os.listdir(file_path):
		if not os.path.isfile(os.path.join(file_path,item)):
			print file_path, item
			continue
		filename, ext = os.path.splitext(item)
		if re.search(r'[A-Z]', ext):
			print "get upper case letter", file_path
			return None
		if extension:
			if ext == extension:
				count += 1
			else:
				print "extension not match", ext, extension
		else:
			count += 1
	return count

def res_exist():
	for dou_asset in DouAsset.objects.filter(status=1, type_id__in=(2)):
		#if dou_asset.res_path and re.search(r'[A-Z]', dou_asset.res_path):
		file_path = ""
		if dou_asset.type_id == 2:	#books
			file_path = '/www/wwwroot/media/4t/3qdou/book/' + dou_asset.res_path
		elif dou_asset.type_id == 3:	#game
			file_path = '/www/wwwroot/media/4t/3qdou/game/' + dou_asset.res_path
		elif dou_asset.type_id == 6:	#video
			file_path = '/www/wwwroot/media/4t/3qdou/video/' + dou_asset.res_path
		if not os.path.isfile(file_path):
			print dou_asset.id, dou_asset.res_path


def update_book_page():
	db_cursor = connection.cursor()
	sql = "select id,guid,page_count,width,height,file_path,thumb_path from dou_book"
	db_cursor.execute(sql)
	rows = db_cursor.fetchall()
	index = 1
	for row in rows:
		id = row[0]
		guid = row[1]
		page_count = row[2]
		width = row[3]
		height = row[4]
		file_path = row[5]
		thumb_path = row[6]

		try: dou_asset = DouAsset.objects.get(guid=guid)
		except(DouAsset.DoesNotExist ):
			print guid, 'not found'
			break
		dou_asset.page_count = page_count
		dou_asset.width = width
		dou_asset.height = height
		dou_asset.file_path = file_path
		dou_asset.thumb_path = thumb_path
		dou_asset.save()
		print index, len(rows)
		index += 1

if __name__ == "__main__":
	#lower_path('/www/wwwroot/media/4t/3qdou/g_3qdou/')
	#lower_path('/www/wwwroot/media/4t/3qdou/v_3qdou/')
	#update_game_path()
	#insert_into_asset(3)
	#update_video_path()
	update_video_path()





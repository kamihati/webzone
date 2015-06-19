#coding: utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf-8') 
#print sys.getdefaultencoding()
import re
import os
import shutil


def do_lower_path(file_path, is_recursion=False, effect_folder=True, only_extension=True):
	"""
	is_recursion:	为True时遍历所有目录
	effect_folder:	为True时文件也需要修改
	only_extension:	为True时只把扩展名改为小写
	"""
	for item in os.listdir(file_path):
		#有大字字母，是文件
		if os.path.isfile(os.path.join(file_path,item)) and re.search(r'[A-Z]', item):
			if only_extension:
				filename, ext = os.path.splitext(item)
				if re.search(r'[A-Z]', ext):
					new_file = filename + ext.lower()
					print "file", filename, ext
					shutil.move(os.path.join(file_path,item), os.path.join(file_path, new_file))
			else:
				#shutil.move(os.path.join(file_path,item), os.path.join(file_path, item.lower()))
				print item
		elif os.path.isdir(os.path.join(file_path,item)):
			if effect_folder and re.search(r'[A-Z]', item):
				print "folder", item
				shutil.move(os.path.join(file_path,item), os.path.join(file_path, item.lower()))
				item = item.lower()
			if is_recursion:
				do_lower_path(os.path.join(file_path,item), is_recursion, effect_folder, only_extension)



if __name__ == "__main__":
	#do_lower_path(u"G:\\3Q豆资源（已制作）", is_recursion=True)
	do_lower_path("/www/wwwroot/media/4t/3qdou/book/", is_recursion=True)
	#do_lower_path(u"C:\SS111aa", is_recursion=True)
#coding:utf-8
'''
Created on 2014-5-7

@author: Administrator
'''
import sys;
sys.path.insert(0, '..')
import os


path = "/www/wwwroot/font/"
filelist = [item for item in os.listdir(path) if os.path.isfile(os.path.join(path,item))]
print filelist
for hfile in filelist:
    print hfile
    os.rename(os.path.join(path, hfile), os.path.join(path, ''.join([os.path.splitext(hfile)[0], os.path.splitext(hfile)[1].lower()])))
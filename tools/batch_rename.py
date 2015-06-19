#coding: utf-8
'''
Created on 2014-4-10

@author: Administrator
'''

#批量修改扩展名
#http://blog.csdn.net/johnny1209/article/details/7596021
# Filename: rename.py
import os
def BatRename(path):
    filelist = [item for item in os.listdir(path) if os.path.isfile(os.path.join(path,item)) \
                and os.path.splitext(item)[1] == '.png']
    print filelist
    for hfile in filelist:
        print hfile
        os.rename(os.path.join(path, hfile), os.path.join(path, ''.join([os.path.splitext(hfile)[0], '.jpg'])))
     
if __name__ == '__main__':
    filedir = "D:\\work\\WebZone\\media\\user\\2014\\2\\opus"
    opus_list = [os.path.join(filedir,item) for item in os.listdir(filedir) if os.path.isdir(os.path.join(filedir,item))]
    print opus_list
    for path in opus_list:
        BatRename(path)
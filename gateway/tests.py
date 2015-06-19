#coding: utf-8
'''
Created on 2014-3-24

@author: Administrator
'''
#from django.test import TestCase

# Create your tests here.


import logging
    
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s'
)

from pyamf.remoting.client import RemotingService

url = 'http://10.0.0.177:8000/gateway/'
#url = 'http://www.383k.com/gateway/'
gw = RemotingService(url, logger=logging)

myservice = gw.getService('DiyService')
#myservice = gw.getService('AccountService')
print myservice.get_font_list()
# print myservice.guest_login()
# print myservice.get_account()


#AccountService = gw.getService('AccountService')
#print AccountService.register("account.username")




#coding:utf-8
"""
WSGI config for WebZone project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

import os
import sys

#sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from site import addsitedir

#os.environ['PYTHON_EGG_CACHE'] = '/tmp/.python-eggs'
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

#sys.path.append('/www/wwwroot')
addsitedir('/usr/local/lib/python2.7/site-packages')


from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

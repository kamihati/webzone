#!/usr/bin/env python
import os
import sys

reload(sys)
if os.name=='posix':
    sys.setdefaultencoding('utf-8')
else:
    sys.setdefaultencoding('gbk')
    

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "WebZone.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)

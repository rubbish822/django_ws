#!usr/bin/env python 
# -*- coding:utf-8 _*-
"""
@author:-
@file: asgi.py 
@version:
@time: 2019/06/26 

"""
"""
ASGI entrypoint. Configures Django and then runs the application
defined in the ASGI_APPLICATION setting.
"""

import os
import django
from channels.routing import get_default_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_ws.pro")
django.setup()
application = get_default_application()

from chat.models import RoomUserIp, RoomUser


# 重启服务器时, 更新所有客户端为离线状态
# RoomUserIp.objects.all().update(is_online=False)
# RoomUser.objects.all().update(is_delete=False)


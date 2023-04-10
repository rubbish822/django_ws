#!usr/bin/env python 
# -*- coding:utf-8 _*-
"""
@author:-
@file: router.py 
@version:
@time: 2019/06/25 

"""
from django.urls import re_path

from . import consumer


websocket_urlpatterns = [
    # re_path(r'^ws/chat/$', consumer.ChatConsumer),
    re_path(r'^ws/chat/(?P<room_name>[^/]+)/$', consumer.ChatConsumer.as_asgi()),
    re_path(r'^ws/room/(?P<room_name>[^/]+)/$', consumer.RoomConsumer.as_asgi()),
]

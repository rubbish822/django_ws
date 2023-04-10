#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:-
@file: signals.py 
@version:
@time: 2019/07/01 

"""
import typing
import datetime
import logging

from django.dispatch import Signal
from django.dispatch.dispatcher import receiver
from django.db.models.signals import post_save, post_delete

from .models import BlackIp, MessageIp, UserIp, RoomIp


logger = logging.getLogger(__name__)


@receiver(post_save, sender=BlackIp)
def receive_insert_black_user(
    sender: typing.Any, instance: typing.Any, **kwargs
) -> typing.Any:
    """
    notify black user message
    :param sender:
    :param instance:
    :param kwargs:
    :return:
    """
    if kwargs.get('created', False):
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        user_ip = UserIp.objects.filter(ip=instance.ip)
        if user_ip.exists():
            user_id = user_ip.first().id
        else:
            user_id = UserIp.objects.create(ip=instance.ip).id
        MessageIp.objects.create(
            room_id=None,
            user_id=user_id,
            content=f'{now} 系统通知 : {instance.ip} 违规已经被禁用!',
            is_notify=True,
            send_time=now,
        )


@receiver(post_delete, sender=RoomIp)
def receive_room_post_delete(
    sender: typing.Any, instance: typing.Any, **kwargs
) -> typing.Any:
    """
    删除房间时 清空该房间内的聊天记录
    :param sender:
    :param instance:
    :param kwargs:
    :return:
    """
    MessageIp.objects.filter(room_id=instance.id).delete()

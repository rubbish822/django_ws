#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:-
@file: consumer.py 
@version:
@time: 2019/06/25 

"""
import logging
import json
import datetime

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.http.response import HttpResponseForbidden, HttpResponseNotFound

from . import models
from .utils import redis_client


logger = logging.getLogger(__name__)


# todo 1. 广播消息 2. 单人私聊
class ChatConsumer(AsyncWebsocketConsumer):
    room_group_name = None
    room_owner_id = None
    login_user_id = None
    # group_send 时会出现问题(message_user_id不正确), 不能使用
    # message_user_id = None

    def is_room_owner(self, message_user_id):
        # 当前登录用户是否是房主
        return message_user_id == self.room_owner_id

    def get_user(self):
        self.login_user_id = self.scope['user'].id
        return self.scope['user']

    @database_sync_to_async
    def group_add_user(self, room):
        # 用户加入房间
        user = self.get_user()
        # is_owner 是否是房主
        is_owner = user.id == room.get('id')
        room_user = models.RoomUser.objects.filter(user=user, room_id=room.get('id'))
        if room_user.exists():
            # 重新加入房间
            room_user.update(is_delete=False)
        else:
            # 第一次加入房间
            models.RoomUser.objects.create(
                user=user, room_id=room.pop('id'), is_delete=False, is_owner=is_owner
            )

    @database_sync_to_async
    def group_remove_user(self):
        # 将用户移除房间
        user = self.get_user()
        models.RoomUser.objects.filter(
            user=user, room__label=self.scope.get('url_route')['kwargs']['room_name']
        ).update(is_delete=True)

    @database_sync_to_async
    def get_room(self):
        # 查询房间是否存在
        room = models.Room.objects.filter(
            label=self.scope.get('url_route')['kwargs']['room_name']
        )
        if room.exists():
            room = room.values().first()
            self.room_owner_id = room['user_id']
            return room

    @database_sync_to_async
    def online_user_count(self):
        # 统计在线用户
        room_user_count = models.RoomUser.objects.filter(
            is_delete=False,
            room__label=self.scope.get('url_route')['kwargs']['room_name'],
        ).count()
        return room_user_count

    def get_now_time(self):
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    async def user_connect_or_disconnect_notify(self, notify='connect'):
        # 用户进入/离开 广播通知
        connect_user = self.get_user()
        online_user_count = await self.online_user_count()
        content = (
            f'用户{connect_user.username}进入了房间({online_user_count}人在线)'
            if notify == 'connect'
            else f'用户{connect_user.username}离开了房间({online_user_count}人在线)'
        )
        rs = dict(
            user=dict(id=connect_user.id, username=connect_user.username),
            message=dict(id=1, content=content, room_id=self.room_group_name),
            notify=True,
        )
        await self.channel_layer.group_send(
            self.room_group_name, {'type': 'chat_message', 'message': rs}
        )

    async def connect(self):
        room = await self.get_room()

        # Join room group
        if room:
            self.room_group_name = room.get('label')
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.group_add_user(room)
            await self.user_connect_or_disconnect_notify()
            await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        # 从房间移除用户
        await self.group_remove_user()
        await self.user_connect_or_disconnect_notify(notify='disconnect')

    @database_sync_to_async
    def send_message(self, content=''):
        room = models.Room.objects.filter(
            label=self.scope.get('url_route')['kwargs']['room_name']
        ).first()
        message = models.Message.objects.create(
            room=room, content=content, user=self.get_user()
        )
        return message

    # Receive message from WebSocket
    async def receive(self, text_data=None):
        # 收到消息后, 再把消息转发到对应的房间(广播消息)
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        message = await self.send_message(message)

        rs = dict(
            user=dict(id=message.user.id, username=message.user.username),
            message=dict(
                id=message.id, content=message.content, room_id=message.room_id
            ),
            notify=False,
        )
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name, {'type': 'chat_message', 'message': rs}
        )

    # Receive message from room group
    async def chat_message(self, event):
        # 会for循环将消息依次发送给房间内的所有用户
        now = self.get_now_time()
        if not event['message']['notify']:
            owner_str = (
                '(房主)' if event['message']['user']['id'] == self.room_owner_id else ''
            )
            if event['message']['user']['id'] == self.login_user_id:
                message = (
                    f'{now}  我{owner_str}：' + event['message']['message']['content']
                )
            else:
                message = (
                    f'{now}  {event["message"]["user"]["username"]}{owner_str}：'
                    + event['message']['message']['content']
                )
        else:
            message = f'{now}  系统通知：' + event['message']['message']['content']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({'message': message}))

    async def notify_message(self, event):
        # 系统广播通知
        now = self.get_now_time()
        message = f"{now} : {event['message']['message']}"
        # Send message to WebSocket
        await self.send(text_data=json.dumps({'message': message}))


# todo 1.当前在线用户列表 2. 用户消息记录
class RoomConsumer(AsyncWebsocketConsumer):
    room_owner_id = 1
    room_group_name = None
    room_id = None

    @database_sync_to_async
    def get_room(self):
        # 查询房间是否存在
        room = models.RoomIp.objects.filter(
            label=self.scope.get('url_route')['kwargs']['room_name'], is_delete=False
        )
        if room.exists():
            room = room.values().first()
        else:
            room = models.RoomIp.objects.filter(is_delete=False).values().first()
        self.room_id = room.get('id')
        self.room_group_name = room.get('label')
        return room

    @database_sync_to_async
    def check_user_if_black(self):
        """
        检查用户ip是否在黑名单中以及过期时间
        :return:
        """
        ip = self.scope['client'][0]
        black_ip = models.BlackIp.objects.filter(is_delete=False, ip=ip).order_by(
            '-create_time'
        )
        if not black_ip.exists():
            return False
        black_ip = black_ip.first()
        if black_ip.end_time:
            # 如果有设置禁用的具体时间段
            return black_ip.end_time > datetime.datetime.now()
        return True

    @database_sync_to_async
    def send_message(self, content=''):
        room = models.RoomIp.objects.filter(
            label=self.scope.get('url_route')['kwargs']['room_name']
        ).first()
        user_id = models.UserIp.objects.filter(ip=self.get_user_ip()).first().id
        message_ips = models.MessageIp.objects.filter(room=room, user_id=user_id)
        if message_ips.exists():
            message_ips.update(content=content, send_time=datetime.datetime.now())
        else:
            models.MessageIp.objects.create(
                room=room,
                content=content,
                user_id=models.UserIp.objects.filter(ip=self.get_user_ip()).first().id,
            )

    @database_sync_to_async
    def add_user(self):
        # 用户进入房间记录
        # ip = self.get_user_ip(request)
        ip = self.scope['client'][0]
        user_ips = models.UserIp.objects.filter(ip=ip)
        if user_ips.exists():
            user_ip = user_ips.first()
        else:
            user_ip = models.UserIp.objects.create(ip=ip)
        return user_ip

    async def user_connect_or_disconnect_notify(self, notify_type='connect'):
        # 用户进入/离开房间通知
        logger.info('client: ', str(self.scope['client']))
        user_ip = self.scope['client'][0]
        now = self.get_now_time()
        # 更新在线用户人数
        # room_user_number = await self.room_user_number(number_type=notify_type)
        room_user_number, is_notify = await self.room_user_record(
            notify_type=notify_type
        )
        if is_notify and room_user_number > 0:
            notify_content = '进入' if notify_type == 'connect' else '离开'
            message = (
                f'{now} 系统通知 : {user_ip}{notify_content}了房间({room_user_number}人在线)'
            )
            message_data = dict(
                user_ip=user_ip, time=now, content=message, online=room_user_number
            )
            rs = dict(message=message_data, notify=True)
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name, {'type': 'notify_message', 'message': rs}
            )

    def get_user_ip(self):
        # 获取用户ip
        return self.scope['client'][0]

    @database_sync_to_async
    def room_user_record(self, notify_type='connect'):
        # 添加/更新用户进入房间记录, 更新用户在线状态, 返回在线人数
        user_ip = self.get_user_ip()
        room_user_ips = models.RoomUserIp.objects.filter(
            ip=user_ip, room_ip_id=self.room_id, client_port=self.scope['client'][-1]
        )
        is_online = True if notify_type == 'connect' else False
        if room_user_ips.exists():
            # 进入过房间的用户则更新在线状态
            if is_online:
                room_user_ips.update(
                    is_online=is_online, last_connect_time=datetime.datetime.now()
                )
            else:
                # 离线时更新离线时间
                room_user_ips.update(
                    disconnect_type=1,
                    is_online=is_online,
                    disconnect_time=datetime.datetime.now(),
                )
        else:
            # 没有进入过的用户记录
            models.RoomUserIp.objects.create(
                ip=user_ip,
                room_ip_id=self.room_id,
                is_online=is_online,
                client_port=self.scope['client'][-1],
            )
        ip_online_users = models.RoomUserIp.objects.filter(
            is_online=True, ip=user_ip
        ).count()
        if ip_online_users == 1:
            # 只同一个ip只有一个web-socket连接在线或者没有时, 则广播通知
            if is_online:
                # 离线时剩一个连接时, 则不通知, 建立连接时只有一个连接时才广播通知
                is_current_ip_online = True
            else:
                is_current_ip_online = False
        elif ip_online_users == 0:
            is_current_ip_online = True
        else:
            # 同一个ip有多个web-socket在线, 则不广播通知
            is_current_ip_online = False
        # 同一个ip可能会有多个 web-socket连接, 因此需要根据ip地址去重
        online_user_count = (
            models.RoomUserIp.objects.filter(is_online=True).distinct('ip').count()
        )
        return online_user_count, is_current_ip_online

    async def room_user_number(self, number_type='connect'):
        # 更新在线用户人数
        cache_key = f'room:{self.room_id}'
        redis = await redis_client()
        room_user_number = await redis.get(cache_key) or 0
        room_user_number = (
            int(room_user_number.decode())
            if isinstance(room_user_number, bytes)
            else int(room_user_number)
        )
        if number_type == 'connect':
            room_user_number += 1
        else:
            if room_user_number > 0:
                room_user_number -= 1
            else:
                room_user_number = 0
        await redis.set(cache_key, room_user_number)
        return room_user_number

    def get_now_time(self):
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    async def connect(self):
        room = await self.get_room()
        user_if_black = await self.check_user_if_black()
        if user_if_black:
            # return HttpResponseForbidden(content='ip被锁定!')
            self.close()
            # 必须返回, 否则会继续往下执行
            return
        # Join room group
        if room:
            self.room_group_name = room.get('label')
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.add_user()
            # 广播用户进入通知
            await self.user_connect_or_disconnect_notify()
            await self.accept()
        # return HttpResponseNotFound('房间不存在或者已经关闭!')
        else:
            self.close()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        # 从房间移除用户, 广播通知
        await self.user_connect_or_disconnect_notify(notify_type='disconnect')

    # Receive message from WebSocket
    async def receive(self, text_data=None):
        # 收到消息后, 再把消息转发到对应的房间(广播消息)
        # fixme ps: 注意, 再调用chat_message方法之前(此处)获取的self里面的东西才是当前连接的客户端的信息, 例如ip地址等信息,
        # 进入chat_message后, self则是group里面的客户端(for循环中的当前的一个客户端)的信息
        if await self.check_user_if_black():
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )
            self.close()
            return
            # return HttpResponseForbidden('ip被锁定!')
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        now = self.get_now_time()
        user_ip = self.scope['client'][0]
        message_data = dict(user_ip=user_ip, time=now, content=message)
        rs = dict(message=message_data, notify=False)
        await self.send_message(content=message)
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name, {'type': 'chat_message', 'message': rs}
        )

    async def notify_message(self, event):
        # 系统广播通知
        # Send message to WebSocket
        await self.send(text_data=json.dumps({'message': event['message']}))

    async def chat_message(self, event):
        # 消息发送
        # Send message to WebSocket
        await self.send(text_data=json.dumps({'message': event['message']}))

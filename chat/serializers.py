#!usr/bin/env python 
# -*- coding:utf-8 _*-
"""
@author:-
@file: serializer.py 
@version:
@time: 2019/06/27 

"""
from rest_framework import serializers

from . import models


class MessageSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Message
        fields = '__all__'
        read_only_fields = ('user', 'room', )


class RoomSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Room
        fields = '__all__'
        read_only_fields = ('user', )


class RoomUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.RoomUser
        fields = '__all__'


class MessageIpSerializer(serializers.ModelSerializer):
    ip = serializers.SerializerMethodField()

    def get_ip(self, obj):
        user_ip = models.UserIp.objects.filter(
            id=obj.user_id
        )
        if user_ip.exists():
            return user_ip.first().ip
        return ''

    class Meta:
        model = models.MessageIp
        exclude = ('user_id', )


class RoomIpSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.RoomIp
        fields = '__all__'


class BlackIpSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.BlackIp
        fields = '__all__'


class RoomUserIpSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.RoomUserIp
        fields = '__all__'

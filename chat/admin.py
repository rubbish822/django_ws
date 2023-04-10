# coding: utf-8
from django.contrib import admin

from . import models


class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'label', 'user')
    list_per_page = 20
    list_filter = ('name', )


class RoomUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'room', 'is_delete', 'is_owner')
    list_per_page = 20
    list_filter = ('user', 'room', 'is_delete', 'is_owner')


class MessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'content', 'send_time')
    list_per_page = 20


class RoomUserIpAdmin(admin.ModelAdmin):
    list_display = (
        'ip', 'room_ip_id', 'client_port', 'is_online',
        'connect_time', 'disconnect_time', 'last_connect_time'
    )
    list_filter = ('is_online', 'room_ip_id')
    list_per_page = 20
    search_fields = ('ip', )


class UserIpAdmin(admin.ModelAdmin):
    list_display = ('ip', 'username')
    list_per_page = 20
    search_fields = ('ip', 'username')


class RoomIpAdmin(admin.ModelAdmin):
    list_display = ('name', 'label', 'content')
    list_per_page = 20
    list_filter = ('name',)
    search_fields = ('name', 'label')


class MessageIpAdmin(admin.ModelAdmin):
    list_display = ('room_id', 'get_ip', 'content', 'send_time')
    list_per_page = 20
    search_fields = ('content', 'room_id', 'user_id')
    list_filter = ('room_id', )

    def get_ip(self, obj):
        user_ip = UserIp.objects.filter(
            id=obj.user_id
        )
        if user_ip.exists():
            return user_ip.first().ip
        return ''
    get_ip.short_description = 'ip'


class BlackIpAdmin(admin.ModelAdmin):
    list_display = ('ip', 'start_time', 'end_time')
    list_per_page = 20
    search_fields = ('ip', )


admin.site.register(models.User)
admin.site.register(models.Room, RoomAdmin)
admin.site.register(models.RoomUser, RoomUserAdmin)
admin.site.register(models.Message, MessageAdmin)
admin.site.register(models.UserIp, UserIpAdmin)
admin.site.register(models.RoomIp, RoomIpAdmin)
admin.site.register(models.RoomUserIp, RoomUserIpAdmin)
admin.site.register(models.MessageIp, MessageIpAdmin)
admin.site.register(models.BlackIp, BlackIpAdmin)

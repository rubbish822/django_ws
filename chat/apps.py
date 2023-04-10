from django.apps import AppConfig


class ChatConfig(AppConfig):
    name = 'chat'

    def ready(self):
        # import datetime
        # from chat.models import RoomUser, RoomUserIp
        # import chat.signals
        # # 重启服务器时, 更新所有客户端为离线状态
        # RoomUserIp.objects.all().update(
        #     is_online=False, disconnect_time=datetime.datetime.now(),
        #     disconnect_type=2
        # )
        # RoomUser.objects.all().update(is_delete=False)
        pass
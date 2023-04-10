# coding: utf-8
import uuid

from django.core import validators
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.contrib.auth.models import (
    AbstractUser,
    AbstractBaseUser,
    Permission,
    PermissionsMixin,
    BaseUserManager,
)
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail


class AbstractModel(models.Model):
    create_time = models.DateTimeField(
        auto_now_add=True,
        blank=True,
    )
    update_time = models.DateTimeField(auto_now=True, blank=True)
    is_delete = models.BooleanField(default=False, blank=True)

    class Meta:
        abstract = True


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, username, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        telephone = extra_fields.get('telephone', '')
        if not telephone:
            raise ValueError('The given telephone must be set')
        # email = self.normalize_email(email)
        username = self.model.normalize_username(username)
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, password, **extra_fields)

    def create_superuser(self, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        username = extra_fields.pop('username', '')
        password = extra_fields.pop('password', '')
        return self._create_user(username, password, **extra_fields)


@deconstructible
class CustomUnicodeUsernameValidator(validators.RegexValidator):
    regex = r'^[\w.@+-\\*]+$'
    message = _(
        'Enter a valid username. This value may contain only letters, '
        'numbers, and @/./+/-/_ characters.'
    )
    flags = 0


class User(AbstractBaseUser, PermissionsMixin):
    """
    An abstract base class implementing a fully featured User model with
    admin-compliant permissions.

    Username and password are required. Other fields are optional.
    """

    username_validator = CustomUnicodeUsernameValidator()

    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_(
            'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'
        ),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    email = models.EmailField(_('email address'), blank=True)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = UserManager()

    telephone = models.CharField(
        max_length=11, blank=True, unique=True, verbose_name='手机号'
    )
    vip_recommend_id = models.SmallIntegerField(
        default=0,
        blank=True,
        verbose_name='vip等级',
        help_text='-1: 会员过期,0: 非会员,大于0: 具体的会员等级',
    )
    user_type = models.PositiveSmallIntegerField(
        default=1, blank=True, choices=((1, 'Normal'), (2, 'Sale')), verbose_name='用户类型'
    )
    gender = models.PositiveSmallIntegerField(
        default=1, blank=True, choices=((1, '男'), (2, '女')), verbose_name='性别'
    )
    login_time = models.DateTimeField(blank=True, null=True, verbose_name='登录时间')
    public_message_id = models.PositiveSmallIntegerField(
        default=0, blank=True, verbose_name='公共消息阅读id'
    )
    city_id = models.PositiveSmallIntegerField(
        default=0, blank=True, verbose_name='所在城市id'
    )
    head_pic = models.CharField(
        max_length=64, blank=True, default='', verbose_name='头像'
    )
    vip_start_time = models.DateTimeField(blank=True, null=True)
    vip_end_time = models.DateTimeField(blank=True, null=True)

    EMAIL_FIELD = 'telephone'
    USERNAME_FIELD = 'telephone'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        indexes = [models.Index(fields=['telephone'])]

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = self.username
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.username

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)

    @property
    def is_vip(self):
        # 是否是会员
        return self.vip_recommend_id > 0

    @property
    def vip_expired(self):
        # 会员是否过期
        return self.vip_recommend_id == -1

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = '****'.join([self.telephone[:3], self.telephone[-4:]])
        return super(User, self).save(*args, **kwargs)


class Room(AbstractModel):
    name = models.CharField(max_length=64, blank=True, verbose_name='name')
    label = models.CharField(max_length=32, blank=True, verbose_name='label uuid')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='user', related_name='rooms'
    )
    content = models.CharField(max_length=128, blank=True, verbose_name='content')

    class Meta:
        verbose_name = 'Room'
        verbose_name_plural = verbose_name
        indexes = [models.Index(fields=['label']), models.Index(fields=['create_time'])]

    def __str__(self):
        return '--'.join([self.name, str(self.user_id)])

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if not self.label:
            self.label = uuid.uuid4().hex
        return super(Room, self).save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )


class RoomUser(AbstractModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_rooms')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='room_users')
    is_owner = models.BooleanField(default=False, blank=True, verbose_name='Is Owner')

    class Meta:
        verbose_name = 'RoomUser'
        verbose_name_plural = verbose_name
        indexes = [models.Index(fields=['is_owner'])]
        unique_together = ('user', 'room')

    def __str__(self):
        return str(self.id)


class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='user',
        related_name='user_messages',
    )
    content = models.TextField(blank=True, verbose_name='content')
    send_time = models.DateTimeField(
        auto_now_add=True, blank=True, verbose_name='send time'
    )

    class Meta:
        verbose_name = 'Message'
        verbose_name_plural = verbose_name
        indexes = [models.Index(fields=['send_time'])]

    def __str__(self):
        return self.content[:10]


class UserIp(AbstractModel):
    ip = models.GenericIPAddressField(unique=True)
    username = models.CharField(max_length=32, blank=True, verbose_name='username')

    class Meta:
        verbose_name = 'UserIp'
        verbose_name_plural = verbose_name
        indexes = [models.Index(fields=['ip']), models.Index(fields=['username'])]

    def __str__(self):
        return self.username

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if not self.username:
            self.username = uuid.uuid4().hex
        return super(UserIp, self).save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )


class RoomIp(AbstractModel):
    name = models.CharField(max_length=64, blank=True, verbose_name='name')
    label = models.CharField(max_length=32, blank=True, verbose_name='label uuid')
    content = models.CharField(max_length=128, blank=True, verbose_name='content')

    class Meta:
        verbose_name = 'RoomIp'
        verbose_name_plural = verbose_name
        indexes = [models.Index(fields=['label']), models.Index(fields=['create_time'])]

    def __str__(self):
        return self.name

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if not self.label:
            self.label = uuid.uuid4().hex
        return super(RoomIp, self).save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )


class RoomUserIp(models.Model):
    ip = models.GenericIPAddressField()
    room_ip_id = models.IntegerField(default=0, blank=True, verbose_name='roomIp_id')
    is_online = models.BooleanField(default=False, blank=True, verbose_name='is_online')
    connect_time = models.DateTimeField(
        auto_now_add=True, blank=True, verbose_name='connect_time'
    )
    disconnect_time = models.DateTimeField(
        blank=True, null=True, verbose_name='disconnect_time'
    )
    last_connect_time = models.DateTimeField(
        auto_now_add=True, verbose_name='last_connect_time'
    )
    client_port = models.CharField(max_length=16, blank=True, verbose_name='port')
    disconnect_type = models.PositiveSmallIntegerField(
        default=0,
        blank=True,
        choices=((0, ''), (1, '用户断开'), (2, '系统重启'), (3, '连接超时'), (4, '违规被踢')),
    )
    # 每一次websocket连接, port都不一样, 因此同一个ip可能会有多个websocket连接

    class Meta:
        verbose_name = 'RoomUserIp'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['ip']),
            models.Index(fields=['room_ip_id']),
            models.Index(fields=['is_online']),
            models.Index(fields=['connect_time']),
            models.Index(fields=['client_port']),
            models.Index(fields=['disconnect_type']),
        ]
        unique_together = ('ip', 'client_port')

    def __str__(self):
        return str(self.ip)


class MessageIp(models.Model):
    room = models.ForeignKey(
        RoomIp, on_delete=models.CASCADE, related_name='messages', blank=True, null=True
    )
    user_id = models.IntegerField(default=0, blank=True, verbose_name='UserId')
    content = models.TextField(blank=True, verbose_name='content')
    send_time = models.DateTimeField(
        auto_now_add=True, blank=True, verbose_name='send time'
    )
    is_show = models.BooleanField(default=True, blank=True, verbose_name='is_show')
    is_notify = models.BooleanField(default=False, blank=True, verbose_name='is_notify')

    class Meta:
        verbose_name = 'MessageIp'
        verbose_name_plural = verbose_name
        indexes = [models.Index(fields=['send_time']), models.Index(fields=['user_id'])]

    def __str__(self):
        return self.content[:10]


class BlackIp(AbstractModel):
    ip = models.GenericIPAddressField(
        unique=True,
    )
    start_time = models.DateTimeField(
        blank=True,
        null=True,
    )
    end_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = 'BlackIp'
        verbose_name_plural = verbose_name
        indexes = [models.Index(fields=['ip'])]

    def __str__(self):
        return str(self.ip)

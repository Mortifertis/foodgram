from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.core.validators import (EmailValidator, MaxLengthValidator,
                                    RegexValidator)
from django.db import models

username_validator = RegexValidator(
    regex=r'^[\w.@+-]+\Z',
    message='Введите корректное имя пользователя. Допустимы только буквы, '
            'цифры и знаки @/./+/-/_.',
)

MAX_LEN_UNAME = 150
MAX_LEN_NAME = 150
MAX_LEN_EMAIL = 254


class User(AbstractUser):
    """
    Кастомный пользователь:
    - email обязателен и уникален (логинимся по email),
    - avatar — опциональный ImageField, не обязателен для create,
    - никаких лишних обязательных полей, чтобы POST /api/users/ не падал 400.
    """
    username = models.CharField(
        'username',
        max_length=MAX_LEN_UNAME,
        unique=True,
        validators=[username_validator, MaxLengthValidator(MAX_LEN_UNAME)],
        help_text=(
            'Обязательное поле. Не более 150 символов. '
            'Только буквы, цифры и @/./+/-/_'
        ),
    )
    first_name = models.CharField('first name', max_length=MAX_LEN_NAME)
    last_name = models.CharField('last name', max_length=MAX_LEN_NAME)
    email = models.EmailField(
        'email address',
        max_length=MAX_LEN_EMAIL,
        unique=True,
        validators=[EmailValidator(), MaxLengthValidator(MAX_LEN_EMAIL)],
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ('id',)
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self) -> str:
        return f'{self.username} <{self.email}>'


class Subscription(models.Model):
    """Подписка пользователя на автора рецептов."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='Автор',
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created',)
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_user_author_subscription',
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='prevent_self_subscription',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.user} -> {self.author}'

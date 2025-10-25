from django.contrib.auth.models import AbstractUser
from django.core.validators import EmailValidator, MaxLengthValidator
from django.db import models

from .constants import (AVATAR_UPLOAD_TO, MAX_LEN_EMAIL, MAX_LEN_NAME,
                        MAX_LEN_UNAME)
from .validators import USERNAME_VALIDATOR


class User(AbstractUser):
    """
    Кастомный пользователь:
    - email обязателен и уникален (логинимся по email),
    - avatar — опциональный ImageField,
    - без лишних обязательных полей.
    """
    username = models.CharField(
        'Имя пользователя',
        max_length=MAX_LEN_UNAME,
        unique=True,
        validators=[USERNAME_VALIDATOR, MaxLengthValidator(MAX_LEN_UNAME)],
        help_text=(
            'Обязательное поле. Не более 150 символов. '
            'Только буквы, цифры и @/./+/-/_'
        ),
    )
    first_name = models.CharField('Имя', max_length=MAX_LEN_NAME)
    last_name = models.CharField('Фамилия', max_length=MAX_LEN_NAME)
    email = models.EmailField(
        'Адрес электронной почты',
        max_length=MAX_LEN_EMAIL,
        unique=True,
        validators=[EmailValidator(), MaxLengthValidator(MAX_LEN_EMAIL)],
    )
    avatar = models.ImageField(
        'Аватар',
        upload_to=AVATAR_UPLOAD_TO,
        blank=True,
        null=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ('id',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

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

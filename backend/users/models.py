from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Пользовательский менеджер, использующий почту как логин."""

    use_in_migrations = True

    def _create_user(self, email: str, password: str, **extra_fields):
        if not email:
            raise ValueError('Необходимо указать адрес электронной почты')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(
        self,
        email: str,
        password: str | None = None,
        **extra_fields,
    ):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        if password is None:
            raise ValueError('Необходимо указать пароль')
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(
                'У суперпользователя должно быть is_staff=True.'
            )
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(
                'У суперпользователя должно быть is_superuser=True.'
            )

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Пользовательская модель, авторизующаяся по электронной почте."""

    email = models.EmailField(_('электронная почта'), unique=True)
    username = models.CharField(
        _('имя пользователя'),
        max_length=150,
        unique=True,
    )
    first_name = models.CharField(_('имя'), max_length=150)
    last_name = models.CharField(_('фамилия'), max_length=150)
    avatar = models.ImageField(
        _('аватар'),
        upload_to='users/avatars/',
        blank=True,
        null=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    objects = UserManager()

    class Meta:
        ordering = ['id']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self) -> str:
        return self.email


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
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['-created']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_user_author_subscription',
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='prevent_self_subscription',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.user} -> {self.author}'

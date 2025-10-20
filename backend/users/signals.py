"""Сигналы приложения пользователей."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User
from .services import set_default_avatar


@receiver(post_save, sender=User)
def ensure_default_avatar(sender, instance: User, created: bool, **kwargs) -> None:
    """Назначает аватар по умолчанию новому пользователю."""

    if created:
        set_default_avatar(instance)

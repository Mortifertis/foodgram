"""Служебные функции для работы с аватарами пользователей."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from django.core.files import File

if TYPE_CHECKING:  # pragma: no cover
    from .models import User


_ASSETS_DIR = Path(__file__).resolve().parent / 'assets'
_DEFAULT_AVATAR_FILE = _ASSETS_DIR / 'default_avatar.jpg'
_DEFAULT_AVATAR_PREFIX = 'default_avatar_'


def _get_default_avatar_path() -> Path:
    """Возвращает путь к исходному файлу аватара по умолчанию."""

    if not _DEFAULT_AVATAR_FILE.exists():
        raise FileNotFoundError(
            'Файл аватара по умолчанию не найден: '
            f"{_DEFAULT_AVATAR_FILE}"
        )
    return _DEFAULT_AVATAR_FILE


def set_default_avatar(user: 'User', *, force: bool = False) -> bool:
    """Устанавливает пользователю аватар по умолчанию.

    Параметр ``force`` указывает, что текущий аватар необходимо заменить,
    даже если он уже установлен.
    Возвращает ``True``, если изображение было изменено.
    """

    if user.avatar and not force:
        return False

    avatar_path = _get_default_avatar_path()

    if user.avatar:
        user.avatar.delete(save=False)

    file_suffix = avatar_path.suffix
    file_name = f'{_DEFAULT_AVATAR_PREFIX}{user.pk}{file_suffix}'

    with avatar_path.open('rb') as avatar_file:
        user.avatar.save(file_name, File(avatar_file), save=True)
    return True


def delete_avatar_file(user: 'User') -> None:
    """Удаляет файл текущего аватара пользователя без сброса поля."""

    if user.avatar:
        user.avatar.delete(save=False)

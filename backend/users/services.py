def delete_avatar_file(user) -> None:
    """
    Безопасно удаляет файл текущего аватара, не обнуляя поле модели.
    """
    avatar_field = getattr(user, 'avatar', None)
    try:
        if avatar_field and avatar_field.name:
            storage = avatar_field.storage
            name = avatar_field.name
            avatar_field.delete(save=False)
            if storage.exists(name):
                storage.delete(name)
    except Exception:
        pass


def set_default_avatar(user, force: bool = False) -> None:
    """
    Сбрасывает поле avatar к пустому значению.
    """
    avatar_field = getattr(user, 'avatar', None)
    if avatar_field is None:
        return
    user.avatar = None
    user.save(update_fields=['avatar'])

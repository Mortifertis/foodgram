from django.core.validators import RegexValidator

USERNAME_VALIDATOR = RegexValidator(
    regex=r'^[\w.@+-]+\Z',
    message=(
        'Введите корректное имя пользователя. Допустимы только буквы, '
        'цифры и знаки @/./+/-/_.'
    ),
)

__all__ = ['USERNAME_VALIDATOR']

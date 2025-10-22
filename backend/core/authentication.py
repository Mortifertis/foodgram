from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed


class SafeTokenAuthentication(TokenAuthentication):
    """
    Как обычно аутентифицируем по токену, но если токен неправильный
    или пустой — возвращаем None (гость), а не 401. Это даёт корректные
    ответы на публичных эндпоинтах даже при наличии неверного заголовка.
    """
    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except AuthenticationFailed:
            return None

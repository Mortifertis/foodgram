DEFAULT_PAGE_SIZE = 6
AVATAR_MAX_SIZE_MB = 5
AVATAR_MAX_SIZE_BYTES = AVATAR_MAX_SIZE_MB * 1024 * 1024
AVATAR_TOO_LARGE_MESSAGE = (
    'Размер файла не должен превышать '
    f'{AVATAR_MAX_SIZE_MB} МБ'
)
AVATAR_ALLOWED_FORMATS = {'JPEG', 'JPG', 'PNG'}
AVATAR_INVALID_IMAGE_MESSAGE = 'Не удалось прочитать изображение'
AVATAR_INVALID_FORMAT_MESSAGE = (
    'Допустимы только изображения формата JPG или PNG'
)

SHOPPING_LIST_FILENAME = 'shopping-list.txt'
SHORT_LINK_RESPONSE_KEY = 'short-link'
PARAM_RECIPES_LIMIT = 'recipes_limit'
MIME_TEXT = 'text/plain; charset=utf-8'
HDR_CONTENT_DISPOSITION = 'Content-Disposition'

ERR_SELF_SUBSCRIBE = 'Нельзя подписаться на самого себя'
ERR_SUB_EXISTS = 'Подписка уже существует'
ERR_SUB_NOT_FOUND = 'Подписка не найдена'
ERR_FAV_EXISTS = 'Рецепт уже в избранном'
ERR_FAV_NOT_FOUND = 'Рецепт не найден в избранном'
ERR_CART_EXISTS = 'Рецепт уже в списке покупок'
ERR_CART_NOT_FOUND = 'Рецепт не найден в списке покупок'
ERR_EMPTY_CART = 'Список покупок пуст'
ERR_LIMIT_POS_INT = (
    'Параметр recipes_limit должен быть положительным целым числом'
)

__all__ = [
    'DEFAULT_PAGE_SIZE',
    'AVATAR_MAX_SIZE_MB',
    'AVATAR_MAX_SIZE_BYTES',
    'AVATAR_TOO_LARGE_MESSAGE',
    'AVATAR_ALLOWED_FORMATS',
    'AVATAR_INVALID_IMAGE_MESSAGE',
    'AVATAR_INVALID_FORMAT_MESSAGE',
    'SHOPPING_LIST_FILENAME',
    'SHORT_LINK_RESPONSE_KEY',
    'PARAM_RECIPES_LIMIT',
    'MIME_TEXT',
    'HDR_CONTENT_DISPOSITION',
    'ERR_SELF_SUBSCRIBE',
    'ERR_SUB_EXISTS',
    'ERR_SUB_NOT_FOUND',
    'ERR_FAV_EXISTS',
    'ERR_FAV_NOT_FOUND',
    'ERR_CART_EXISTS',
    'ERR_CART_NOT_FOUND',
    'ERR_EMPTY_CART',
    'ERR_LIMIT_POS_INT',
]

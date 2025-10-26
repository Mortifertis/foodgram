from django.utils.crypto import get_random_string

from .constants import (RECIPE_SHORT_LINK_ALLOWED_CHARS,
                        RECIPE_SHORT_LINK_LENGTH)


def generate_unique_short_link(
    model, length: int = RECIPE_SHORT_LINK_LENGTH
) -> str:
    while True:
        candidate = get_random_string(
            length=length,
            allowed_chars=RECIPE_SHORT_LINK_ALLOWED_CHARS,
        )
        if not model.objects.filter(short_link=candidate).exists():
            return candidate

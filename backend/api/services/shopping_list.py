from typing import Any, Iterable

from django.db.models import Sum
from recipes.models import RecipeIngredient, ShoppingCart


class ShoppingListRenderer:
    """
    Формирует сводный список ингредиентов для всех рецептов,
    добавленных пользователем в корзину.
    """

    def __init__(self, user):
        self.user = user

    @staticmethod
    def _format_row(row: dict[str, Any]) -> str:
        return (
            f"{row['ingredient__name']} "
            f"({row['ingredient__measurement_unit']}) — {row['total']}"
        )

    def render(self) -> str:
        recipe_ids = (
            ShoppingCart.objects.filter(user=self.user)
            .values_list('recipe_id', flat=True)
        )
        if not recipe_ids:
            return ''

        rows: Iterable[dict[str, Any]] = (
            RecipeIngredient.objects.filter(recipe_id__in=recipe_ids)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total=Sum('amount'))
            .order_by('ingredient__name')
        )

        lines: list[str] = [self._format_row(row) for row in rows]
        return '\n'.join(lines)

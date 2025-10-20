"""Служебные инструменты для сбора и отображения списков покупок."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from django.contrib.auth import get_user_model
from django.db.models import QuerySet, Sum

from recipes.models import RecipeIngredient

User = get_user_model()


@dataclass(frozen=True)
class ShoppingListItem:
    """Сводные данные по отдельному ингредиенту."""

    name: str
    measurement_unit: str
    total: int


class ShoppingListRenderer:
    """Формирует текстовый список покупок для конкретного пользователя."""

    title: str = 'Список покупок'

    def __init__(self, user: User):
        self.user = user

    def get_totals(self) -> QuerySet:
        """Возвращает агрегированные количества ингредиентов в корзине."""

        return (
            RecipeIngredient.objects.filter(
                recipe__in_carts__user=self.user
            )
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total=Sum('amount'))
            .order_by('ingredient__name', 'ingredient__measurement_unit')
        )

    def build_items(self) -> List[ShoppingListItem]:
        """Преобразует агрегированные данные в объекты для отображения."""

        return [
            ShoppingListItem(
                name=item['ingredient__name'],
                measurement_unit=item['ingredient__measurement_unit'],
                total=item['total'],
            )
            for item in self.get_totals()
        ]

    def render(self, items: Iterable[ShoppingListItem] | None = None) -> str:
        """Создает текстовое представление списка покупок в кодировке UTF-8."""

        if items is None:
            items = self.build_items()
        items = list(items)
        if not items:
            return ''

        lines = [self.title]
        for item in items:
            lines.append(
                f'{item.name} ({item.measurement_unit}) — {item.total}'
            )
        return '\n'.join(lines)

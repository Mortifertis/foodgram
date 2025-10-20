"""Фильтры для выборок рецептов и ингредиентов."""

import django_filters
from django.db.models import QuerySet
from recipes.models import Ingredient, Recipe


class RecipeFilter(django_filters.FilterSet):
    """Позволяет фильтровать рецепты по тегам и пользовательским флагам."""

    tags = django_filters.CharFilter(method='filter_tags')
    author = django_filters.NumberFilter(field_name='author__id')
    is_favorited = django_filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = django_filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def filter_tags(
        self, queryset: QuerySet, name: str, value: str
    ) -> QuerySet:
        """Возвращает рецепты с тегами из параметров запроса."""

        request = getattr(self, 'request', None)
        if request is None:
            return queryset
        tags = request.query_params.getlist('tags')
        if not tags:
            return queryset
        return queryset.filter(tags__slug__in=tags).distinct()

    def filter_is_favorited(
        self, queryset: QuerySet, name: str, value: bool | None
    ) -> QuerySet:
        """Фильтрует рецепты, добавленные в избранное текущим пользователем."""

        return self._filter_by_user_relation(queryset, value, 'favorited_by')

    def filter_is_in_shopping_cart(
        self, queryset: QuerySet, name: str, value: bool | None
    ) -> QuerySet:
        """Фильтрует рецепты по наличию в списке покупок пользователя."""

        return self._filter_by_user_relation(queryset, value, 'in_carts')

    def _filter_by_user_relation(
        self, queryset: QuerySet, value: bool | None, relation: str
    ) -> QuerySet:
        """Применяет фильтрацию по связи Many-to-Many с пользователем."""

        if value is None:
            return queryset
        user = getattr(self.request, 'user', None)
        if user is None or not user.is_authenticated:
            return queryset.none() if value else queryset
        relation_filter = {f'{relation}__user': user}
        if value:
            return queryset.filter(**relation_filter)
        return queryset.exclude(**relation_filter)


class IngredientFilter(django_filters.FilterSet):
    """Позволяет находить ингредиенты по префиксу названия."""

    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith',
    )

    class Meta:
        model = Ingredient
        fields = ('name',)

from __future__ import annotations

import django_filters as filters
from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart

User = get_user_model()


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr="istartswith")

    class Meta:
        model = Ingredient
        fields = ("name",)


class RecipeFilter(filters.FilterSet):
    author = filters.NumberFilter(field_name="author__id", lookup_expr="exact")
    tags = filters.AllValuesMultipleFilter(field_name="tags__slug")
    is_favorited = filters.NumberFilter(method="filter_is_favorited")
    is_in_shopping_cart = filters.NumberFilter(method="filter_is_in_cart")

    class Meta:
        model = Recipe
        fields = ("author", "tags", "is_favorited", "is_in_shopping_cart")

    def _to_int_or_none(self, value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def filter_is_favorited(self, queryset, name, value):
        user = getattr(self.request, "user", None)
        if not user or not user.is_authenticated:
            return queryset
        val = self._to_int_or_none(value)
        if val is None:
            return queryset

        fav_exists = Favorite.objects.filter(user=user, recipe=OuterRef("pk"))
        queryset = queryset.annotate(_fav=Exists(fav_exists))
        if val == 1:
            return queryset.filter(_fav=True)
        if val == 0:
            return queryset.filter(_fav=False)
        return queryset

    def filter_is_in_cart(self, queryset, name, value):
        user = getattr(self.request, "user", None)
        if not user or not user.is_authenticated:
            return queryset
        val = self._to_int_or_none(value)
        if val is None:
            return queryset

        cart_exists = ShoppingCart.objects.filter(
            user=user, recipe=OuterRef("pk")
        )
        queryset = queryset.annotate(_cart=Exists(cart_exists))
        if val == 1:
            return queryset.filter(_cart=True)
        if val == 0:
            return queryset.filter(_cart=False)
        return queryset

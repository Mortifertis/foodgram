import django_filters as filters
from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart

User = get_user_model()


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith',
    )

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    author = filters.NumberFilter(
        field_name='author__id',
        lookup_expr='exact',
    )
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = filters.NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.NumberFilter(method='filter_is_in_cart')

    class Meta:
        model = Recipe
        fields = (
            'author',
            'tags',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def _to_int_or_none(self, value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _filter_by_flag(self, queryset, value, model, annotate_name):
        """Общая логика для флагов"""
        user = getattr(self.request, 'user', None)
        if not user or not user.is_authenticated:
            return queryset

        val = self._to_int_or_none(value)
        if val not in (0, 1):
            return queryset

        exists_qs = model.objects.filter(user=user, recipe=OuterRef('pk'))
        qs = queryset.annotate(**{annotate_name: Exists(exists_qs)})
        return qs.filter(**{annotate_name: bool(val)})

    def filter_is_favorited(self, queryset, name, value):
        return self._filter_by_flag(queryset, value, Favorite, '_fav')

    def filter_is_in_cart(self, queryset, name, value):
        return self._filter_by_flag(queryset, value, ShoppingCart, '_cart')

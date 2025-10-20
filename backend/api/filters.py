import django_filters
from recipes.models import Ingredient, Recipe


class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.CharFilter(method='filter_tags')
    author = django_filters.NumberFilter(field_name='author__id')
    is_favorited = django_filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = django_filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def filter_tags(self, queryset, name, value):
        request = getattr(self, 'request', None)
        if request is None:
            return queryset
        tags = request.query_params.getlist('tags')
        if not tags:
            return queryset
        return queryset.filter(tags__slug__in=tags).distinct()

    def filter_is_favorited(self, queryset, name, value):
        user = getattr(self.request, 'user', None)
        if value:
            if user and user.is_authenticated:
                return queryset.filter(favorited_by__user=user)
            return queryset.none()
        if value is False and user and user.is_authenticated:
            return queryset.exclude(favorited_by__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = getattr(self.request, 'user', None)
        if value:
            if user and user.is_authenticated:
                return queryset.filter(in_carts__user=user)
            return queryset.none()
        if value is False and user and user.is_authenticated:
            return queryset.exclude(in_carts__user=user)
        return queryset


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith',
    )

    class Meta:
        model = Ingredient
        fields = ('name',)

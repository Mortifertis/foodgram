from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)


class RecipeIngredientInlineFormSet(BaseInlineFormSet):
    """Форма, контролирующая заполнение ингредиентов рецепта."""

    def clean(self):
        super().clean()
        unique_ingredients = set()
        ingredients_count = 0

        for form in self.forms:
            if not hasattr(form, 'cleaned_data'):
                continue

            cleaned_data = form.cleaned_data

            if not cleaned_data or cleaned_data.get('DELETE'):
                continue

            ingredient = cleaned_data.get('ingredient')
            amount = cleaned_data.get('amount')

            if ingredient is None or amount in (None, ''):
                raise ValidationError(
                    'Укажите ингредиент и его количество.'
                )

            if ingredient in unique_ingredients:
                raise ValidationError('Ингредиенты не должны повторяться.')

            unique_ingredients.add(ingredient)
            ingredients_count += 1

        if ingredients_count == 0:
            raise ValidationError(
                'Необходимо указать хотя бы один ингредиент.'
            )


class IngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1
    validate_min = True
    formset = RecipeIngredientInlineFormSet


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')
    search_fields = ('name', 'slug')
    list_filter = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'favorites_count', 'short_link')
    search_fields = ('name', 'author__email', 'author__username')
    list_filter = ('author', 'tags')
    inlines = (IngredientInline,)
    readonly_fields = ('favorites_count',)

    @admin.display(description='Количество в избранном')
    def favorites_count(self, obj):
        return Favorite.objects.filter(recipe=obj).count()


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', 'added')
    search_fields = ('user__email', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', 'added')
    search_fields = ('user__email', 'recipe__name')


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')
    list_filter = ('ingredient',)

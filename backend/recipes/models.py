from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from .constants import (INGREDIENT_MEASUREMENT_MAX_LENGTH,
                        INGREDIENT_NAME_MAX_LENGTH, RECIPE_COOKING_TIME_MIN,
                        RECIPE_COOKING_TIME_MIN_MESSAGE,
                        RECIPE_IMAGE_UPLOAD_DIR,
                        RECIPE_INGREDIENT_AMOUNT_MESSAGE,
                        RECIPE_INGREDIENT_AMOUNT_MIN, RECIPE_NAME_MAX_LENGTH,
                        RECIPE_SHORT_LINK_MAX_LENGTH, TAG_COLOR_MAX_LENGTH,
                        TAG_NAME_MAX_LENGTH, TAG_SLUG_MAX_LENGTH)
from .utils import generate_unique_short_link


class Tag(models.Model):
    """Тег для группировки рецептов."""

    name = models.CharField(
        'Название', max_length=TAG_NAME_MAX_LENGTH, unique=True
    )
    color = models.CharField(
        'Цветовой HEX-код', max_length=TAG_COLOR_MAX_LENGTH, unique=True
    )
    slug = models.SlugField(
        'Слаг', max_length=TAG_SLUG_MAX_LENGTH, unique=True
    )

    class Meta:
        ordering = ['id']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self) -> str:
        return self.name


class Ingredient(models.Model):
    """Ингредиент с указанием единицы измерения."""

    name = models.CharField('Название', max_length=INGREDIENT_NAME_MAX_LENGTH)
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=INGREDIENT_MEASUREMENT_MAX_LENGTH,
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient_name_unit',
            )
        ]

    def __str__(self) -> str:
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    """Рецепт, опубликованный пользователем."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    name = models.CharField('Название', max_length=RECIPE_NAME_MAX_LENGTH)
    image = models.ImageField('Изображение', upload_to=RECIPE_IMAGE_UPLOAD_DIR)
    text = models.TextField('Описание')
    cooking_time = models.PositiveIntegerField(
        'Время приготовления (мин)',
        validators=[
            MinValueValidator(
                RECIPE_COOKING_TIME_MIN,
                message=RECIPE_COOKING_TIME_MIN_MESSAGE,
            )
        ],
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиенты',
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    short_link = models.SlugField(
        'Короткая ссылка',
        max_length=RECIPE_SHORT_LINK_MAX_LENGTH,
        unique=True,
        blank=True,
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'name'],
                name='unique_recipe_author_name',
            )
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields')
        if not self.short_link:
            self.short_link = generate_unique_short_link(
                self.__class__
            )
            if update_fields is not None:
                kwargs['update_fields'] = list(
                    set(update_fields) | {'short_link'}
                )
        super().save(*args, **kwargs)


class RecipeIngredient(models.Model):
    """Количество конкретного ингредиента в рецепте."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_recipes',
        verbose_name='Ингредиент',
    )
    amount = models.PositiveIntegerField(
        'Количество',
        validators=[
            MinValueValidator(
                RECIPE_INGREDIENT_AMOUNT_MIN,
                message=RECIPE_INGREDIENT_AMOUNT_MESSAGE,
            )
        ],
    )

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'
        ordering = ['recipe__name']
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient',
            )
        ]

    def __str__(self) -> str:
        return f'{self.ingredient.name} — {self.amount}'


class BaseRecipeRelation(models.Model):
    user_related_name = None
    recipe_related_name = None

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    added = models.DateTimeField('Дата добавления', auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ['-added']

    def __str__(self) -> str:
        return f'{self.user} -> {self.recipe}'

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if getattr(cls._meta, 'abstract', False):
            return
        user_field = cls._meta.get_field('user')
        recipe_field = cls._meta.get_field('recipe')
        if cls.user_related_name is not None:
            user_field.remote_field.related_name = cls.user_related_name
        if cls.recipe_related_name is not None:
            recipe_field.remote_field.related_name = cls.recipe_related_name


class Favorite(BaseRecipeRelation):
    """Избранный рецепт пользователя."""

    user_related_name = 'favorites'
    recipe_related_name = 'favorited_by'

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite_recipe',
            )
        ]


class ShoppingCart(BaseRecipeRelation):
    """Позиции списка покупок пользователя."""
    user_related_name = 'shopping_cart'
    recipe_related_name = 'in_carts'

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_cart_recipe',
            )
        ]

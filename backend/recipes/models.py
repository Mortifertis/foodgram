from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.crypto import get_random_string


class Tag(models.Model):
    """Тег для группировки рецептов."""

    name = models.CharField('Название', max_length=200, unique=True)
    color = models.CharField('Цветовой HEX-код', max_length=7, unique=True)
    slug = models.SlugField('Слаг', max_length=200, unique=True)

    class Meta:
        ordering = ['id']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self) -> str:
        return self.name


class Ingredient(models.Model):
    """Ингредиент с указанием единицы измерения."""

    name = models.CharField('Название', max_length=200)
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=200,
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
    name = models.CharField('Название', max_length=200)
    image = models.ImageField('Изображение', upload_to='recipes/')
    text = models.TextField('Описание')
    cooking_time = models.PositiveIntegerField(
        'Время приготовления (мин)',
        validators=[
            MinValueValidator(
                1,
                message='Минимальное время приготовления — 1 минута',
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
        max_length=32,
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
            self.short_link = self._generate_short_link()
            if update_fields is not None:
                kwargs['update_fields'] = list(
                    set(update_fields) | {'short_link'}
                )
        super().save(*args, **kwargs)

    def _generate_short_link(self, length: int = 6) -> str:
        """Генерирует короткий идентификатор для рецепта."""
        allowed_chars = (
            'abcdefghijklmnopqrstuvwxyz'
            'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            '0123456789'
        )
        while True:
            candidate = get_random_string(
                length=length,
                allowed_chars=allowed_chars,
            )
            if not Recipe.objects.filter(short_link=candidate).exists():
                return candidate


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
                1,
                message='Количество должно быть не меньше 1',
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


class Favorite(models.Model):
    """Избранный рецепт пользователя."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='Рецепт',
    )
    added = models.DateTimeField('Дата добавления', auto_now_add=True)

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        ordering = ['-added']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite_recipe',
            )
        ]

    def __str__(self) -> str:
        return f'{self.user} -> {self.recipe}'


class ShoppingCart(models.Model):
    """Позиции списка покупок пользователя."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_carts',
        verbose_name='Рецепт',
    )
    added = models.DateTimeField('Дата добавления', auto_now_add=True)

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        ordering = ['-added']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_cart_recipe',
            )
        ]

    def __str__(self) -> str:
        return f'{self.user} -> {self.recipe}'

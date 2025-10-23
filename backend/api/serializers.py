from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from PIL import Image, UnidentifiedImageError
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from rest_framework import serializers
from users.models import Subscription

User = get_user_model()


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(read_only=True)

    class Meta(DjoserUserSerializer.Meta):
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
        )

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        user = request.user if request else None
        if user and user.is_authenticated:
            return Subscription.objects.filter(user=user, author=obj).exists()
        return False


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Создание пользователя без проверки "сложности" пароля.
    """
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "password",
        )
        read_only_fields = ("id",)

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def to_representation(self, instance):
        data = {
            "id": instance.id,
            "username": instance.username,
            "first_name": instance.first_name,
            "last_name": instance.last_name,
            "email": instance.email,
        }
        return data


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    """
    В запросе запись ингредиента выглядит как:
    {"id": <ingredient_id>, "amount": <int>}
    """
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source="ingredient",
    )
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount")


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    """
    В ответе ингредиенты раскрываются:
    {"id", "name", "measurement_unit", "amount"}
    """
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeShortSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")

    def get_image(self, obj):
        image_field = getattr(obj, 'image', None)
        if not image_field:
            return None

        try:
            url = image_field.url
        except ValueError:
            return None

        request = self.context.get("request")
        if request is not None:
            return request.build_absolute_uri(url)
        return url


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        source="recipe_ingredients",
        many=True,
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        user = request.user if request else None
        if user and user.is_authenticated:
            return Favorite.objects.filter(user=user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request")
        user = request.user if request else None
        if user and user.is_authenticated:
            return ShoppingCart.objects.filter(user=user, recipe=obj).exists()
        return False


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientWriteSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "ingredients",
            "tags",
            "image",
            "name",
            "text",
            "cooking_time",
        )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if self.instance is not None:
            initial_data = getattr(self, 'initial_data', {})
            missing = {}
            for field_name in ('ingredients', 'tags'):
                if field_name not in initial_data:
                    field = self.fields[field_name]
                    missing[field_name] = [
                        field.error_messages.get('required', 'Обязательное поле.')
                    ]
            if missing:
                raise serializers.ValidationError(missing)
        return attrs

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError('Изображение не может быть пустым')
        try:
            value.seek(0)
            with Image.open(value) as image:
                image_format = (image.format or '').upper()
        except (UnidentifiedImageError, OSError):
            raise serializers.ValidationError('Не удалось прочитать изображение') from None
        finally:
            try:
                value.seek(0)
            except Exception:
                pass

        if image_format not in {'JPEG', 'JPG', 'PNG'}:
            raise serializers.ValidationError(
                'Допустимы только изображения формата JPG или PNG'
            )
        return value

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                "Необходимо указать хотя бы один ингредиент"
            )
        seen = set()
        for ingredient in ingredients:
            ingredient_id = ingredient["ingredient"].id
            if ingredient_id in seen:
                raise serializers.ValidationError(
                    "Ингредиенты не должны повторяться"
                )
            seen.add(ingredient_id)
            if ingredient["amount"] < 1:
                raise serializers.ValidationError(
                    "Количество ингредиента должно быть положительным"
                )
        return ingredients

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError(
                "Необходимо указать хотя бы один тег"
            )
        if len(tags) != len({tag.id for tag in tags}):
            raise serializers.ValidationError("Теги не должны повторяться")
        return tags

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self._set_ingredients(recipe, ingredients_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop("ingredients", None)
        tags = validated_data.pop("tags", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tags is not None:
            instance.tags.set(tags)
        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            self._set_ingredients(instance, ingredients_data)
        return instance

    def to_representation(self, instance):
        context = self.context
        return RecipeReadSerializer(instance, context=context).data

    def _set_ingredients(self, recipe, ingredients_data):
        RecipeIngredient.objects.bulk_create(
            [
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=item["ingredient"],
                    amount=item["amount"],
                )
                for item in ingredients_data
            ]
        )


class SubscriptionSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField(source="author.email")
    id = serializers.ReadOnlyField(source="author.id")
    username = serializers.ReadOnlyField(source="author.username")
    first_name = serializers.ReadOnlyField(source="author.first_name")
    last_name = serializers.ReadOnlyField(source="author.last_name")
    avatar = serializers.SerializerMethodField()

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "avatar",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )

    def get_is_subscribed(self, obj):
        return True

    def get_recipes(self, obj):
        recipes_qs = obj.author.recipes.order_by('-pub_date')
        recipes_limit = self.context.get('recipes_limit')
        if recipes_limit is None:
            request = self.context.get('request')
            if request is not None:
                raw_limit = request.query_params.get('recipes_limit')
                if raw_limit is not None and raw_limit.isdigit():
                    recipes_limit = int(raw_limit)
        if recipes_limit is not None:
            recipes_qs = recipes_qs[: int(recipes_limit)]
        serializer = RecipeShortSerializer(
            recipes_qs,
            many=True,
            context=self.context,
        )
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.author.recipes.count()

    def get_avatar(self, obj):
        avatar_field = getattr(obj.author, 'avatar', None)
        if not avatar_field:
            return None

        try:
            url = avatar_field.url
        except ValueError:
            return None

        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(url)
        return url


class AvatarSerializer(serializers.Serializer):
    avatar = Base64ImageField()

    def validate_avatar(self, value):
        """Проверяет формат и (разумный) размер изображения аватара."""
        max_size = 5 * 1024 * 1024  # 5 MB
        size = getattr(value, 'size', None)
        if size is not None and size > max_size:
            raise serializers.ValidationError(
                "Размер файла не должен превышать 5 МБ"
            )
        try:
            value.seek(0)
            with Image.open(value) as image:
                image_format = (image.format or '').upper()
        except (UnidentifiedImageError, OSError):
            raise serializers.ValidationError(
                "Не удалось прочитать изображение"
            ) from None
        finally:
            try:
                value.seek(0)
            except Exception:
                pass

        if image_format not in {"JPEG", "JPG", "PNG"}:
            raise serializers.ValidationError(
                "Допустимы только изображения формата JPG или PNG"
            )
        return value

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef, Prefetch
from django.http import HttpResponse
from django.urls import reverse
from djoser.views import UserViewSet as DjoserUserViewSet
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from users.models import Subscription
from users.services import delete_avatar_file, set_default_avatar

from .filters import IngredientFilter
from .pagination import LimitPageNumberPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (AvatarSerializer, IngredientSerializer,
                          RecipeReadSerializer, RecipeShortSerializer,
                          RecipeWriteSerializer, SubscriptionSerializer,
                          TagSerializer, UserCreateSerializer)
from .services import ShoppingListRenderer

User = get_user_model()

SHOPPING_LIST_FILENAME = "shopping-list.txt"
SHORT_LINK_RESPONSE_KEY = "short-link"


class CustomUserViewSet(DjoserUserViewSet):
    """
    Расширяет Djoser:
    - публичный create (201 и 5 полей);
    - подписки (list/subscribe/unsubscribe);
    - аватар (PUT base64 / DELETE 204).
    """

    permission_classes = [AllowAny]

    def get_permissions(self):
        """
        Доступ:
        - list/retrieve/create — публичные;
        - остальное — только аутентифицированным.
        """
        public = {"list", "retrieve", "create"}
        private = {
            "me",
            "set_password",
            "subscriptions",
            "subscribe",
            "set_avatar",
            "delete_avatar",
        }
        if self.action in public:
            return [AllowAny()]
        if self.action in private:
            return [IsAuthenticated()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        """
        Создаёт пользователя через UserCreateSerializer.
        Возвращает 201 и поля:
        id, username, first_name, last_name, email.
        """
        serializer = UserCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=["put"],
        url_path="me/avatar",
        permission_classes=[IsAuthenticated],
    )
    def set_avatar(self, request):
        """Ставит новый аватар (base64)."""
        serializer = AvatarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        avatar_file = serializer.validated_data["avatar"]

        delete_avatar_file(request.user)
        file_name = (
            getattr(avatar_file, "name", None) or f"avatar_{request.user.pk}"
        )
        request.user.avatar.save(file_name, avatar_file, save=True)
        avatar_url = request.build_absolute_uri(request.user.avatar.url)
        return Response({"avatar": avatar_url})

    @set_avatar.mapping.delete
    def delete_avatar(self, request):
        """Удаляет аватар."""
        set_default_avatar(request.user, force=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        """
        Список авторов, на которых подписан текущий пользователь.
        Поддерживает ?recipes_limit=.
        """
        recipes_limit = request.query_params.get('recipes_limit')
        parsed_limit = None
        if recipes_limit is not None:
            error_message = (
                'Параметр recipes_limit должен быть положительным целым числом'
            )
            if not recipes_limit.isdigit():
                return Response(
                    {'errors': error_message},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            parsed_limit = int(recipes_limit)
            if parsed_limit < 1:
                return Response(
                    {'errors': error_message},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        queryset = (
            Subscription.objects.filter(user=request.user)
            .select_related("author")
            .prefetch_related(
                Prefetch(
                    "author__recipes",
                    queryset=Recipe.objects.order_by("-id"),
                )
            )
        )
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            page if page is not None else queryset,
            many=True,
            context={
                'request': request,
                'recipes_limit': parsed_limit,
            },
        )
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        """Создаёт подписку на автора."""
        author = self.get_object()
        if author == request.user:
            return Response(
                {"errors": "Нельзя подписаться на самого себя"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        subscription, created = Subscription.objects.get_or_create(
            user=request.user,
            author=author,
        )
        if not created:
            return Response(
                {"errors": "Подписка уже существует"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = SubscriptionSerializer(
            subscription,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        """Удаляет подписку на автора."""
        author = self.get_object()
        deleted, _ = Subscription.objects.filter(
            user=request.user,
            author=author,
        ).delete()
        if deleted == 0:
            return Response(
                {"errors": "Подписка не найдена"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.GenericViewSet):
    queryset = Tag.objects.all().order_by("id")
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        obj = self.get_object()
        serializer = self.get_serializer(obj)
        return Response(serializer.data)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Справочник ингредиентов; фильтр name=istartswith."""

    queryset = Ingredient.objects.all().order_by("id")
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """CRUD по рецептам и связанные действия."""

    queryset = (
        Recipe.objects.all()
        .select_related("author")
        .prefetch_related("tags", "recipe_ingredients__ingredient")
    )
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = LimitPageNumberPagination

    def get_queryset(self):
        queryset = (
            Recipe.objects.select_related("author")
            .prefetch_related("tags", "recipe_ingredients__ingredient")
            .order_by("-pub_date", "-id")
        )
        request = getattr(self, "request", None)
        if request is None:
            return queryset

        params = request.query_params
        author = params.get("author")
        if author:
            try:
                queryset = queryset.filter(author_id=int(author))
            except (TypeError, ValueError):
                return queryset.none()

        tag_slugs = [slug for slug in params.getlist("tags") if slug]
        if tag_slugs:
            queryset = queryset.filter(tags__slug__in=tag_slugs).distinct()

        user = request.user
        fav_param = params.get("is_favorited")
        cart_param = params.get("is_in_shopping_cart")

        if fav_param in {"0", "1"}:
            if not user.is_authenticated:
                if fav_param == "1":
                    queryset = queryset.none()
            else:
                fav_exists = Favorite.objects.filter(
                    user=user,
                    recipe=OuterRef("pk"),
                )
                queryset = queryset.annotate(_fav=Exists(fav_exists))
                queryset = queryset.filter(_fav=(fav_param == "1"))

        if cart_param in {"0", "1"}:
            if not user.is_authenticated:
                if cart_param == "1":
                    queryset = queryset.none()
            else:
                cart_exists = ShoppingCart.objects.filter(
                    user=user,
                    recipe=OuterRef("pk"),
                )
                queryset = queryset.annotate(_cart=Exists(cart_exists))
                queryset = queryset.filter(_cart=(cart_param == "1"))

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action in {"list", "retrieve"}:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_permissions(self):
        if self.action in {"list", "retrieve", "get_link"}:
            return [AllowAny()]
        return super().get_permissions()

    @action(
        detail=True,
        methods=["get"],
        url_path="get-link",
        permission_classes=[AllowAny],
    )
    def get_link(self, request, pk=None):
        """Возвращает короткую ссылку на рецепт (абсолютный URL)."""
        recipe = self.get_object()
        if not getattr(recipe, "short_link", None):
            recipe.save(update_fields=["short_link"])
        short_path = reverse(
            "recipes:short-link",
            kwargs={"short_link": recipe.short_link},
        )
        short_url = request.build_absolute_uri(short_path)
        return Response({SHORT_LINK_RESPONSE_KEY: short_url})

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        """Добавляет рецепт в избранное."""
        recipe = self.get_object()
        _, created = Favorite.objects.get_or_create(
            user=request.user,
            recipe=recipe,
        )
        if not created:
            return Response(
                {"errors": "Рецепт уже в избранном"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = RecipeShortSerializer(
            recipe,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        """Удаляет рецепт из избранного."""
        recipe = self.get_object()
        deleted, _ = Favorite.objects.filter(
            user=request.user,
            recipe=recipe,
        ).delete()
        if deleted == 0:
            return Response(
                {"errors": "Рецепт не найден в избранном"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        """Добавляет рецепт в список покупок."""
        recipe = self.get_object()
        _, created = ShoppingCart.objects.get_or_create(
            user=request.user,
            recipe=recipe,
        )
        if not created:
            return Response(
                {"errors": "Рецепт уже в списке покупок"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = RecipeShortSerializer(
            recipe,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        """Удаляет рецепт из списка покупок."""
        recipe = self.get_object()
        deleted, _ = ShoppingCart.objects.filter(
            user=request.user,
            recipe=recipe,
        ).delete()
        if deleted == 0:
            return Response(
                {"errors": "Рецепт не найден в списке покупок"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        """Отдаёт .txt со сводным списком ингредиентов."""
        renderer = ShoppingListRenderer(request.user)
        content = renderer.render()
        if not content:
            return Response(
                {"errors": "Список покупок пуст"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        response = HttpResponse(
            content,
            content_type="text/plain; charset=utf-8",
        )
        response[
            "Content-Disposition"
        ] = f'attachment; filename="{SHOPPING_LIST_FILENAME}"'
        return response

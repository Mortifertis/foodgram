from django.contrib.auth import get_user_model
from django.db.models import Prefetch
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from djoser.views import UserViewSet as DjoserUserViewSet
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from users.models import Subscription
from users.services import delete_avatar_file, set_default_avatar

from .constants import (ERR_CART_EXISTS, ERR_CART_NOT_FOUND, ERR_EMPTY_CART,
                        ERR_FAV_EXISTS, ERR_FAV_NOT_FOUND, ERR_LIMIT_POS_INT,
                        ERR_SELF_SUBSCRIBE, ERR_SUB_EXISTS, ERR_SUB_NOT_FOUND,
                        HDR_CONTENT_DISPOSITION, MIME_TEXT,
                        PARAM_RECIPES_LIMIT, SHOPPING_LIST_FILENAME,
                        SHORT_LINK_RESPONSE_KEY)
from .filters import IngredientFilter, RecipeFilter
from .pagination import LimitPageNumberPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (AvatarSerializer, IngredientSerializer,
                          RecipeReadSerializer, RecipeShortSerializer,
                          RecipeWriteSerializer, SubscriptionSerializer,
                          TagSerializer, UserCreateSerializer)
from .services import ShoppingListRenderer

User = get_user_model()


class CustomUserViewSet(DjoserUserViewSet):
    """
    Расширяет Djoser:
    - публичный create;
    - подписки (list/subscribe/unsubscribe);
    - аватар.
    """

    permission_classes = [AllowAny]

    def get_permissions(self):
        """
        Доступ:
        - list/retrieve/create — публичные;
        - остальное — только аутентифицированным.
        """
        public = {'list', 'retrieve', 'create'}
        private = {
            'me',
            'set_password',
            'subscriptions',
            'subscribe',
            'set_avatar',
            'delete_avatar',
        }
        if self.action in public:
            return [AllowAny()]
        if self.action in private:
            return [IsAuthenticated()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        """
        Создаёт пользователя через UserCreateSerializer.
        """
        serializer = UserCreateSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=['put'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated],
    )
    def set_avatar(self, request):
        """Ставит новый аватар (base64)."""
        serializer = AvatarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        avatar_file = serializer.validated_data['avatar']

        delete_avatar_file(request.user)
        file_name = (
            getattr(avatar_file, 'name', None) or f'avatar_{request.user.pk}'
        )
        request.user.avatar.save(file_name, avatar_file, save=True)
        avatar_url = request.build_absolute_uri(request.user.avatar.url)
        return Response({'avatar': avatar_url})

    @set_avatar.mapping.delete
    def delete_avatar(self, request):
        """Удаляет аватар."""
        set_default_avatar(request.user, force=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        """
        Список авторов, на которых подписан текущий пользователь.
        """
        raw_limit = request.query_params.get(PARAM_RECIPES_LIMIT)
        recipes_limit = None
        if raw_limit is not None:
            if not raw_limit.isdigit() or int(raw_limit) < 1:
                return Response(
                    {'errors': ERR_LIMIT_POS_INT},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            recipes_limit = int(raw_limit)

        queryset = (
            Subscription.objects.filter(user=request.user)
            .select_related('author')
            .prefetch_related(
                Prefetch(
                    'author__recipes',
                    queryset=Recipe.objects.order_by('-id'),
                )
            )
        )
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            page if page is not None else queryset,
            many=True,
            context={
                'request': request,
                PARAM_RECIPES_LIMIT: recipes_limit,
            },
        )
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        """Создаёт подписку на автора."""
        author = self.get_object()
        if author == request.user:
            return Response(
                {'errors': ERR_SELF_SUBSCRIBE},
                status=status.HTTP_400_BAD_REQUEST,
            )
        obj, created = Subscription.objects.get_or_create(
            user=request.user,
            author=author,
        )
        if not created:
            return Response(
                {'errors': ERR_SUB_EXISTS},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = SubscriptionSerializer(
            obj,
            context={'request': request},
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
        if not deleted:
            return Response(
                {'errors': ERR_SUB_NOT_FOUND},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.GenericViewSet):
    queryset = Tag.objects.all().order_by('id')
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

    queryset = Ingredient.objects.all().order_by('id')
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """CRUD по рецептам и связанные действия."""

    queryset = (
        Recipe.objects.all()
        .select_related('author')
        .prefetch_related('tags', 'recipe_ingredients__ingredient')
        .order_by('-pub_date', '-id')
        .distinct()
    )
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = LimitPageNumberPagination
    filterset_class = RecipeFilter

    @staticmethod
    def _add_relation(model, user, recipe, error_msg):
        obj, created = model.objects.get_or_create(user=user, recipe=recipe)
        if not created:
            return None, Response(
                {'errors': error_msg},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return obj, None

    @staticmethod
    def _delete_relation(model, user, recipe, error_msg):
        deleted, _ = model.objects.filter(user=user, recipe=recipe).delete()
        if deleted == 0:
            return Response(
                {'errors': error_msg},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_serializer_class(self):
        if self.action in {'list', 'retrieve'}:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_permissions(self):
        if self.action in {'list', 'retrieve', 'get_link'}:
            return [AllowAny()]
        return super().get_permissions()

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
        permission_classes=[AllowAny],
    )
    def get_link(self, request, pk=None):
        """Возвращает короткую ссылку на рецепт (абсолютный URL)."""
        recipe = self.get_object()
        if not getattr(recipe, 'short_link', None):
            recipe.save(update_fields=['short_link'])
        short_path = reverse(
            'recipes:short-link',
            kwargs={'short_link': recipe.short_link},
        )
        short_url = request.build_absolute_uri(short_path)
        return Response({SHORT_LINK_RESPONSE_KEY: short_url})

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        """Добавляет рецепт в избранное."""
        recipe = self.get_object()
        _, error = self._add_relation(
            Favorite, request.user, recipe, ERR_FAV_EXISTS
        )
        if error:
            return error
        serializer = RecipeShortSerializer(
            recipe,
            context={'request': request},
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        """Удаляет рецепт из избранного."""
        recipe = self.get_object()
        return self._delete_relation(
            Favorite, request.user, recipe, ERR_FAV_NOT_FOUND
        )

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        """Добавляет рецепт в список покупок."""
        recipe = self.get_object()
        _, error = self._add_relation(
            ShoppingCart, request.user, recipe, ERR_CART_EXISTS
        )
        if error:
            return error
        serializer = RecipeShortSerializer(
            recipe,
            context={'request': request},
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        """Удаляет рецепт из списка покупок."""
        recipe = self.get_object()
        return self._delete_relation(
            ShoppingCart, request.user, recipe, ERR_CART_NOT_FOUND
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        """Отдаёт .txt со сводным списком ингредиентов."""
        renderer = ShoppingListRenderer(request.user)
        content = renderer.render()
        if not content:
            return Response(
                {'errors': ERR_EMPTY_CART},
                status=status.HTTP_400_BAD_REQUEST,
            )
        response = HttpResponse(content, content_type=MIME_TEXT)
        response[HDR_CONTENT_DISPOSITION] = (
            f'attachment; filename="{SHOPPING_LIST_FILENAME}"'
        )
        return response


class RecipeShortLinkRedirectView(View):
    """Перенаправляет на страницу рецепта по короткой ссылке."""

    def get(self, request, short_link):
        recipe = get_object_or_404(Recipe, short_link=short_link)
        return redirect(f'/recipes/{recipe.id}/')

from django.contrib.auth import get_user_model
from django.db.models import Prefetch
from django.http import HttpResponse
from django.urls import reverse
from djoser.views import UserViewSet as DjoserUserViewSet
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from users.models import Subscription
from users.services import delete_avatar_file, set_default_avatar

from .filters import IngredientFilter, RecipeFilter
from .services import ShoppingListRenderer
from .permissions import IsAuthorOrReadOnly
from .serializers import (AvatarSerializer, IngredientSerializer,
                          RecipeReadSerializer, RecipeShortSerializer,
                          RecipeWriteSerializer, SubscriptionSerializer,
                          TagSerializer)

User = get_user_model()


class CustomUserViewSet(DjoserUserViewSet):
    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.action in {
            'me',
            'set_password',
            'subscriptions',
            'subscribe',
            'set_avatar',
            'delete_avatar',
        }:
            return [IsAuthenticated()]
        if self.action in {'list', 'retrieve'}:
            return [AllowAny()]
        return super().get_permissions()

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        queryset = (
            Subscription.objects.filter(user=request.user)
            .select_related('author')
            .prefetch_related(
                Prefetch(
                    'author__recipes',
                    queryset=Recipe.objects.order_by('-pub_date'),
                )
            )
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SubscriptionSerializer(
                page,
                many=True,
                context={'request': request},
            )
            return self.get_paginated_response(serializer.data)
        serializer = SubscriptionSerializer(
            queryset,
            many=True,
            context={'request': request},
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated],
    )
    def set_password(self, request, *args, **kwargs):
        response = super().set_password(request, *args, **kwargs)
        if response.status_code == status.HTTP_204_NO_CONTENT:
            Token.objects.filter(user=request.user).delete()
        return response

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        author = self.get_object()
        if author == request.user:
            return Response(
                {'errors': 'Нельзя подписаться на самого себя'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        subscription, created = Subscription.objects.get_or_create(
            user=request.user,
            author=author,
        )
        if not created:
            return Response(
                {'errors': 'Подписка уже существует'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = SubscriptionSerializer(
            subscription,
            context={'request': request},
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        author = self.get_object()
        deleted, _ = Subscription.objects.filter(
            user=request.user,
            author=author,
        ).delete()
        if deleted == 0:
            return Response(
                {'errors': 'Подписка не найдена'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['put'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated],
    )
    def set_avatar(self, request):
        serializer = AvatarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        avatar_file = serializer.validated_data['avatar']
        delete_avatar_file(request.user)
        file_name = getattr(avatar_file, 'name', None) or (
            f'avatar_{request.user.pk}'
        )
        request.user.avatar.save(file_name, avatar_file, save=True)
        avatar_url = request.build_absolute_uri(request.user.avatar.url)
        return Response({'avatar': avatar_url})

    @set_avatar.mapping.delete
    def delete_avatar(self, request):
        set_default_avatar(request.user, force=True)
        avatar_url = request.build_absolute_uri(request.user.avatar.url)
        return Response({'avatar': avatar_url})


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = (
        Recipe.objects.all()
        .select_related('author')
        .prefetch_related('tags', 'recipe_ingredients__ingredient')
    )
    permission_classes = (IsAuthorOrReadOnly,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in {'list', 'retrieve'}:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_permissions(self):
        if self.action in {'list', 'retrieve'}:
            return [AllowAny()]
        return super().get_permissions()

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
        permission_classes=[AllowAny],
    )
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        if not recipe.short_link:
            recipe.save(update_fields=['short_link'])
        short_path = reverse(
            'recipes:short-link',
            kwargs={'short_link': recipe.short_link},
        )
        short_url = request.build_absolute_uri(short_path)
        return Response({'short-link': short_url})

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            recipe=recipe,
        )
        if not created:
            return Response(
                {'errors': 'Рецепт уже в избранном'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = RecipeShortSerializer(
            recipe,
            context={'request': request},
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        recipe = self.get_object()
        deleted, _ = Favorite.objects.filter(
            user=request.user,
            recipe=recipe,
        ).delete()
        if deleted == 0:
            return Response(
                {'errors': 'Рецепт не найден в избранном'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        item, created = ShoppingCart.objects.get_or_create(
            user=request.user,
            recipe=recipe,
        )
        if not created:
            return Response(
                {'errors': 'Рецепт уже в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = RecipeShortSerializer(
            recipe,
            context={'request': request},
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        deleted, _ = ShoppingCart.objects.filter(
            user=request.user,
            recipe=recipe,
        ).delete()
        if deleted == 0:
            return Response(
                {'errors': 'Рецепт не найден в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        renderer = ShoppingListRenderer(request.user)
        content = renderer.render()
        if not content:
            return Response(
                {'errors': 'Список покупок пуст'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        response = HttpResponse(
            content,
            content_type='text/plain; charset=utf-8',
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping-list.txt"'
        )
        return response

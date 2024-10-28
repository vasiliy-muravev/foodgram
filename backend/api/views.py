import hashlib

from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import LimitPagination
from api.permissions import IsAuthorOrRead
from api.serializers import (CreateRecipeSerializer, FavoriteSerializer,
                             GetRecipeSerializer, IngredientSerializer,
                             PasswordChangeSerializer, ShoppingCartSerializer,
                             SubscriptionSerializer, TagSerializer, User,
                             UserCreateSerializer, UserSerializer)
from djoser.views import UserViewSet as BaseUserViewSet
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from users.models import Follow


class UserViewSet(BaseUserViewSet):
    """Вьюсет для пользователей."""

    queryset = User.objects.all()
    pagination_class = LimitOffsetPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer

    @action(
        detail=False, methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False, methods=['put'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar'
    )
    def avatar(self, request):
        user = request.user
        if 'avatar' not in request.data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        serializer = UserSerializer(
            user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        url = serializer.data.get('avatar')
        response = {'avatar': url}
        return Response(response, status=status.HTTP_200_OK)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        user = request.user
        if user.avatar:
            user.avatar.delete()
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def set_password(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data, context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        user = request.user
        subs_list = user.follower.all()
        serializer = SubscriptionSerializer(
            self.paginate_queryset(subs_list),
            many=True
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id):
        user = self.request.user
        following = get_object_or_404(User, id=id)
        if user == following:
            return Response(
                {'errors': 'Нельзя подписаться или отписаться от себя!'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if Follow.objects.filter(
                user=user, following=following
        ).exists():
            return Response(
                {'errors': 'Подписка уже оформлена!'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        queryset = Follow.objects.create(
            user=user, following=following
        )
        serializer = SubscriptionSerializer(queryset)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id):
        user = self.request.user
        following = get_object_or_404(User, id=id)
        if user == following:
            return Response(
                {'errors': 'Нельзя подписаться или отписаться от себя!'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not Follow.objects.filter(
                user=user, following=following
        ).exists():
            return Response(
                {'errors': 'Вы уже отписаны!'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        follow = get_object_or_404(
            Follow, user=user, following=following
        )
        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(ModelViewSet):
    """Вьюсет для тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    http_method_names = ['get']


class IngredientViewSet(ModelViewSet):
    """Вьюсет для ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    http_method_names = ['get']
    permission_classes = (AllowAny,)
    filter_backends = (IngredientFilter,)
    search_fields = ('^name',)


class RecipeViewSet(ModelViewSet):
    """Вьюсет для рецептов."""

    queryset = Recipe.objects.all().order_by('-id')
    pagination_class = LimitPagination
    permission_classes = [IsAuthorOrRead, ]
    http_method_names = (
        'get', 'post', 'patch', 'delete'
    )
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in ['POST', 'PATCH']:
            return CreateRecipeSerializer
        return GetRecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link'
    )
    def get_link(self, request, pk):
        if self.get_object():
            url = request.build_absolute_uri()
            short_link = hashlib.sha256(
                url.encode('utf-8')
            ).hexdigest()
            return Response({'short-link': short_link})
        return Response(status=status.HTTP_404_NOT_FOUND)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = ShoppingCartSerializer(
            data={'user': user.id, 'recipe': recipe.id}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        shopping_cart = ShoppingCart.objects.filter(
            user=user.id,
            recipe=recipe
        )
        if shopping_cart.exists():
            shopping_cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        shopping_cart = ShoppingCart.objects.filter(user=self.request.user)
        recipes = [item.recipe.id for item in shopping_cart]
        buy_objects = (
            RecipeIngredient.objects.filter(recipe__in=recipes)
            .values('ingredient')
            .annotate(amount=Sum('amount'))
        )
        purchase_list = [
            'Список покупок:',
        ]
        for obj in buy_objects:
            ingredient = Ingredient.objects.get(pk=obj['ingredient'])
            amount = obj['amount']
            purchase_list.append(
                f'{ingredient.name}: {amount},'
                f'{ingredient.measurement_unit}'
            )
        purchase_file = "\n".join(purchase_list)

        response = HttpResponse(purchase_file, content_type='text/plain')
        response[
            'Content-Disposition'
        ] = 'attachment; filename=shopping-list.txt'

        return response

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = FavoriteSerializer(
            data={'user': user.id, 'recipe': recipe.id}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        favorite = Favorite.objects.filter(
            user=user.id,
            recipe=recipe
        )
        if favorite.exists():
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

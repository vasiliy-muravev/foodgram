from djoser.views import UserViewSet as BaseUserViewSet
from rest_framework import viewsets

from users.models import User
from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
)

from .serializers import (
    UserSerializer,
    TagSerializer,
    IngredientSerializer,
    RecipeSerializer
)


class UserViewSet(BaseUserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer

from rest_framework import serializers

from users.models import User
from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
)


class UserSerializer(serializers.ModelSerializer):
    """Пользователи."""

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'avatar',
            'first_name',
            'last_name',
        )
        read_only_fields = ('id',)


class TagSerializer(serializers.ModelSerializer):
    """Теги."""

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """"Ингредиенты."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeSerializer(serializers.ModelSerializer):
    """Рецепты."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

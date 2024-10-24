from api.mixins import CurrentRecipeMixin
from django.contrib.auth import get_user_model
from djoser.serializers import PasswordSerializer
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from djoser.serializers import UserSerializer as BaseUserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from rest_framework import serializers
from users.models import Follow

from foodgram.constants import MIN_INGREDIENT_AMOUNT

User = get_user_model()


class UserCreateSerializer(BaseUserCreateSerializer):
    """Сериализатор данных для создания пользователя."""

    class Meta:
        model = User
        fields = (
            'email', 'username', 'first_name',
            'last_name', 'password', 'avatar'
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'avatar': {'required': False},
        }

    def to_representation(self, instance):
        serializer = ShortUserSerializer(instance)
        return serializer.data


class UserSerializer(BaseUserSerializer):
    """Сериализатор данных пользователя."""

    is_subscribed = serializers.SerializerMethodField(read_only=True)
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.follower.filter(user=obj).exists()
        return False


class ShortUserSerializer(serializers.ModelSerializer):
    """Сериализатор данных краткой информации о пользователе."""

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name'
        )


class PasswordChangeSerializer(PasswordSerializer):
    """Сериализатор данных для изменения пароля."""

    new_password = serializers.CharField(write_only=True)
    current_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.check_password(attrs['current_password']):
            raise serializers.ValidationError()
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()
        return user


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор данных для тегов."""

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор данных для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор связанных данных рецепта и ингредиентов."""

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id', 'name',
            'measurement_unit', 'amount',
        )


class CreateIngredientRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор данных для сохранения ингредиентов в рецепт."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(min_value=MIN_INGREDIENT_AMOUNT)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class GetRecipeSerializer(serializers.ModelSerializer, CurrentRecipeMixin):
    """Сериализатор данных для получения информации о рецептах."""

    tags = TagSerializer(
        many=True,
        read_only=True
    )
    ingredients = IngredientRecipeSerializer(
        many=True,
        read_only=True,
        source='ingredient'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()
    author = UserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time',
        )

    def get_is_favorited(self, obj):
        return self.get_current_recipe(obj, Favorite)

    def get_is_in_shopping_cart(self, obj):
        return self.get_current_recipe(obj, ShoppingCart)


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор данных для получения краткой информации о рецепте."""

    class Meta:
        model = Recipe
        fields = (
            'id', 'name',
            'image', 'cooking_time'
        )


class CreateRecipeSerializer(serializers.ModelSerializer, CurrentRecipeMixin):
    """Сериализатор данных для создания и редактирования рецепта."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    ingredients = CreateIngredientRecipeSerializer(
        many=True,
        required=True
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image',
            'name', 'text', 'cooking_time'
        )

    def validate_ingredients(self, value):
        if len(value) == 0:
            raise serializers.ValidationError(
                'Список ингредиентов не может быть пустым!'
            )
        ing_list = []
        for ingredient in value:
            id = ingredient.get('id')
            if ingredient.get('amount') < 1:
                raise serializers.ValidationError(
                    'Количество ингредиента не может быть меньше 1'
                )
            if id not in ing_list:
                ing_list.append(id)
            else:
                raise serializers.ValidationError(
                    'Ингредиенты не могут повторяться'
                )
        return value

    def validate_tags(self, value):
        unique_data: set[int] = set()
        for tag in value:
            if tag.id in unique_data:
                raise serializers.ValidationError(
                    'Теги не должны повторяться'
                )
            unique_data.add(tag.id)
            if not Tag.objects.filter(id=tag.id).exists():
                raise serializers.ValidationError(
                    'Невозможно поставить несуществующий тег'
                )
        return value

    def validate_image(self, value):
        if value is None:
            raise serializers.ValidationError(
                'Изображение обязательное для создания рецепта'
            )
        return value

    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Время готовки не может быть меньше минуты'
            )
        return value

    def validate(self, data):
        if not data.get('ingredients'):
            raise serializers.ValidationError(
                'Необходимо указать ингредиенты'
            )
        if not data.get('tags'):
            raise serializers.ValidationError(
                'Необходимо указать теги'
            )
        return data

    def update_or_create_ingredient(self, recipe, ingredients) -> None:
        recipe.ingredients.clear()
        ingredient_list = []
        for ingredient in ingredients:
            ingredient_list.append(
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=ingredient['id'],
                    amount=ingredient['amount']
                )
            )
        RecipeIngredient.objects.bulk_create(ingredient_list)

    def extract_ingredients_tags(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        return ingredients, tags

    def create(self, validated_data):
        ingredients, tags = self.extract_ingredients_tags(validated_data)
        recipe = Recipe.objects.create(**validated_data)
        self.update_or_create_ingredient(
            recipe=recipe,
            ingredients=ingredients
        )
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        ingredients, tags = self.extract_ingredients_tags(validated_data)
        recipe = super().update(instance, validated_data)
        self.update_or_create_ingredient(
            recipe=instance, ingredients=ingredients
        )
        recipe.tags.clear()
        recipe.tags.set(tags)
        return recipe

    # def delete(self, obj, validated_data):
    #
    #     if not self.get_current_recipe(obj, ShoppingCart):
    #         #
    #     # user = self.context['request'].user
    #     #
    #     # if not ShoppingCart.objects.filter(
    #     #         user=user, recipe=instance
    #     # ).exists():
    #         raise serializers.ValidationError(
    #             'Этого рецепта нет в списке покупок'
    #         )
    #     else:
    #         obj.delete()
    #     return HttpResponse(status=204)

    # return Response(
    #     {'errors': 'Этого рецепта нет в списке покупок'},
    #     status=status.HTTP_400_BAD_REQUEST
    # )

    def to_representation(self, instance):
        serializer = GetRecipeSerializer(instance)
        return serializer.data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """"Сериализатор модели Список покупок."""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        serializer = ShortRecipeSerializer(instance.recipe)
        return serializer.data

    def validate(self, data):
        user = data.get('user')
        recipe = data.get('recipe')
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise ShoppingCart(f'Рецепт {recipe} уже добавлен в список!')
        return data


class FavoriteSerializer(serializers.ModelSerializer):
    """"Сериализатор модели Избранное."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        serializer = ShortRecipeSerializer(instance.recipe)
        return serializer.data

    def validate(self, data):
        """Валидация при добавлении рецепта в избранное."""
        user = data.get('user')
        recipe = data.get('recipe')
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise Favorite(f'Рецепт {recipe} уже добавлен в избранное!')
        return data


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор данных для подписки."""

    email = serializers.ReadOnlyField(source='following.email')
    id = serializers.ReadOnlyField(source='following.id')
    username = serializers.ReadOnlyField(source='following.username')
    first_name = serializers.ReadOnlyField(source='following.first_name')
    last_name = serializers.ReadOnlyField(source='following.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = Base64ImageField(source='following.avatar')

    class Meta:
        model = Follow
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'recipes',
            'recipes_count', 'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request:
            user = request.user
            if user.is_authenticated:
                return Follow.objects.filter(
                    following=obj.following.id, user=user.id
                ).exists()
        return False

    def get_recipes(self, obj):
        request = self.context.get('request')
        if request:
            recipes = obj.following.recipes.all()
            recipes_limit = request.guery_params.get('recipes_limit')
            if recipes_limit:
                recipes = obj.following.recipes.all()[:recipes_limit]
            if recipes:
                serializer = ShortRecipeSerializer(
                    recipes,
                    many=True
                )
                return serializer.data
        return []

    def get_recipes_count(self, obj):
        return obj.following.recipes.count()

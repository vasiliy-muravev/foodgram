from django.contrib import admin

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            RecipeTag, ShoppingCart, Tag)


class RecipeIngredientInLine(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


class RecipeTagInLine(admin.TabularInline):
    model = RecipeTag
    extra = 1


class RecipeAdmin(admin.ModelAdmin):
    inlines = (RecipeIngredientInLine, RecipeTagInLine,)
    list_display = (
        'id', 'name', 'author', 'favorite_count',
        'ingredients_in_recipe', 'tags_in_recipe',
    )
    list_filter = ('author', 'name', 'tags__name')
    search_fields = (
        'name', 'author__username', 'tags__name',
        'ingredients__name',
    )
    empty_value_display = 'Поле не заполнено'

    @admin.display(description='Добавили в избранное')
    def favorite_count(self, obj):
        return obj.favorite.count()

    @admin.display(description='Теги рецепта')
    def tags_in_recipe(self, obj):
        tags = obj.recipe_tag.values('tag__name').order_by('tag__name')
        return ', '.join([tag['tag__name'] for tag in tags])

    @admin.display(description='Ингредиенты рецепта')
    def ingredients_in_recipe(self, obj):
        ingredients = (
            RecipeIngredient.objects.filter(recipe=obj)
            .values(
                'ingredient__name',
                'amount',
                'ingredient__measurement_unit',
            )
            .order_by(
                'ingredient__name',
                'ingredient__measurement_unit',
            )
        )
        return ', '.join(
            [
                (
                    f"{ingredient['ingredient__name']} - "
                    f"{ingredient['amount']} "
                    f"{ingredient['ingredient__measurement_unit']}"
                )
                for ingredient in ingredients
            ]
        )


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    list_filter = ('name',)
    search_fields = ('name',)


class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    list_filter = ('name',)
    search_fields = ('name', 'slug')


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'user', 'favorites')
    search_fields = ('recipe__name', 'user__username')

    @admin.display(description='Количество в избранном')
    def favorites(self, obj):
        return obj.recipe.favorite.count()


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    search_fields = ('id', 'recipe__name', 'ingredient__name', 'amount')


class RecipeTagAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'tag')
    search_fields = ('id', 'recipe__name', 'tag__name')


admin.site.register(Tag, TagAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(RecipeTag, RecipeTagAdmin)
admin.site.register(RecipeIngredient, RecipeIngredientAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.register(Ingredient, IngredientAdmin)

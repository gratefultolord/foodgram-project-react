from django.contrib import admin

from .models import (Favorite, Ingredient, RecipeIngredient,
                     Recipe, ShoppingCart, Tag)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Административный класс для управления рецептами."""

    list_display = (
        'name',
        'author',
    )
    list_filter = ('author', 'name', 'tags',)
    empty_value_display = '-пусто-'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Административный класс для управления ингредиентами."""

    list_display = (
        'name',
        'measurement_unit',
    )
    list_filter = ('name',)
    empty_value_display = '-пусто-'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Административный класс для управления тегами."""

    list_display = (
        'name',
        'color',
        'slug',
    )
    empty_value_display = '-пусто-'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Административный класс для управления списка избранных рецептов."""

    list_display = ('user', 'recipe',)
    empty_value_display = '-пусто-'


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Административный класс для управления ингредиентов в рецептах."""

    list_display = ('recipe', 'ingredient', 'quantity',)
    empty_value_display = '-пусто-'


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Административный класс для управления корзиной покупок."""

    list_display = ('user', 'recipe',)
    empty_value_display = '-пусто-'
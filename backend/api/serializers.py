import base64
import re

from api.validators import validate_username
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db.models import F
from djoser.serializers import UserCreateSerializer, UserSerializer
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from users.models import Subscription

MAX_FIELD_LENGTH = 150
User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Кастомный сериализатор, преобразующий картинки."""

    def to_internal_value(self, image_data):
        if isinstance(image_data, str) and image_data.startswith('data:image'):
            format, imgstr = image_data.split(';base64,')
            ext = format.split('/')[-1]
            image_data = ContentFile(
                base64.b64decode(imgstr), name=f'temp.{ext}')
        return super().to_internal_value(image_data)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тегов."""

    class Meta:
        model = Tag
        fields = '__all__'

    def validate_color(self, color_value):
        if not re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$',
                        color_value):
            raise serializers.ValidationError(
                'Цвет должен быть в формате HEX.'
            )
        return color_value


class UsersSerializer(UserSerializer):
    """Сериализатор пользователей."""

    is_subscribed = SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('email', 'id',
                  'username',
                  'first_name', 'last_name',
                  'is_subscribed',)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return obj.following.filter(user_id=request.user.id).exists()


class MiniRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор короткой формы рецептов."""

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class SubscriptionSerializer(UsersSerializer):
    """Сериализатор подписок."""

    recipes_count = SerializerMethodField()
    recipes = SerializerMethodField()

    class Meta(UsersSerializer.Meta):
        fields = UsersSerializer.Meta.fields + (
            'recipes_count', 'recipes'
        )
        read_only_fields = ('email', 'username',
                            'first_name', 'last_name')

    def validate(self, data):
        following = self.instance
        user = self.context.get('request').user
        subscription = Subscription.objects.filter(
            following=following, user=user
        )
        if self.context.get('request').method == 'POST':
            if subscription.exists():
                raise serializers.ValidationError(
                    'Вы уже подписаны на этого пользователя!')
            if user == following:
                raise serializers.ValidationError(
                    'Вы не можете подписаться на самого себя!')
        if self.context.get('request').method == 'DELETE':
            if not subscription.exists():
                raise serializers.ValidationError(
                    'Нельзя отменить несуществующую подписку!'
                )
        return data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = MiniRecipeSerializer(recipes, many=True, read_only=True)
        return serializer.data


class UserRegistrationSerializer(UserCreateSerializer):
    """Сериализатор регистрации пользователей."""

    username = serializers.CharField(max_length=MAX_FIELD_LENGTH,
                                     validators=[validate_username])

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'password')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов в рецепте."""

    id = serializers.IntegerField(source='ingredients.id')
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount',)

    def validate_amount(self, amount_value):
        if amount_value < 1:
            raise serializers.ValidationError(
                'Количество ингредиентов не может быть меньше 1!'
            )
        return amount_value


class RecipeGetSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов для безопасных запросов."""

    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_ingredients(self, obj):
        recipe = obj
        return recipe.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('recipe_ingredients__amount')
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.favorites.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.shopping_cart.filter(recipe=obj).exists()


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, required=True)
    image = Base64ImageField()
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients', many=True, required=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def validate(self, data):
        ingredients_data = data.get('recipe_ingredients')
        if not ingredients_data:
            raise serializers.ValidationError({
                'recipe_ingredients': 'Поле ингредиентов обязательно!'
            })
        ingredient_ids = []
        for ingredient in ingredients_data:
            if not Ingredient.objects.filter(id=ingredient['ingredients']['id']
                                             ).exists():
                raise serializers.ValidationError(
                    'Данного ингредиента не существует!')
            if ingredient['ingredients']['id'] in ingredient_ids:
                raise serializers.ValidationError(
                    'Ингредиенты не могут повторяться!')
            ingredient_ids.append(ingredient['ingredients']['id'])
        tags_data = data.get('tags')
        if not tags_data:
            raise serializers.ValidationError({
                'tags': 'Поле тегов обязательно!'
            })
        if len(tags_data) != len(set(tags_data)):
            raise serializers.ValidationError('Теги не могут повторяться!')
        return data

    def create_ingredients(self, recipe, ingredients_data):
        recipe_ingredients = (
            RecipeIngredient(
                recipe=recipe,
                ingredients_id=ingredient_data['ingredients']['id'],
                amount=ingredient_data['amount']
            ) for ingredient_data in ingredients_data
        )
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create_tags(self, recipe, tags_data):
        recipe.tags.set(tags_data)

    def create(self, validated_data):
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('recipe_ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self.create_ingredients(recipe, ingredients_data)
        self.create_tags(recipe, tags_data)
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time)

        ingredients_data = validated_data.pop('recipe_ingredients', [])
        instance.recipe_ingredients.all().delete()
        self.create_ingredients(instance, ingredients_data)
        tags_data = validated_data.pop('tags', [])
        instance.tags.clear()
        self.create_tags(instance, tags_data)

        instance.save()
        return instance

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeGetSerializer(instance, context=context).data


class BaseRecipeActionSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для Избранного и Корзины покупок."""

    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        fields = ('recipe', 'user')

    def validate(self, data):
        recipe_value = data.get('recipe')
        user = self.context.get('request').user

        if not Recipe.objects.filter(id=recipe_value.id).exists():
            raise serializers.ValidationError('Данного рецепта не существует!')

        if self.Meta.model.objects.filter(user=user,
                                          recipe=recipe_value).exists():
            raise serializers.ValidationError('Рецепт уже добавлен.')

        return data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['recipe'] = MiniRecipeSerializer(instance.recipe).data
        return representation['recipe']


class FavoriteSerializer(BaseRecipeActionSerializer):
    """Сериализатор Избранного."""

    class Meta(BaseRecipeActionSerializer.Meta):
        model = Favorite


class ShoppingCartSerializer(BaseRecipeActionSerializer):
    """Сериализатор Корзины покупок."""

    class Meta(BaseRecipeActionSerializer.Meta):
        model = ShoppingCart


class ShoppingCartDownloadSerializer(serializers.Serializer):
    """Сериализатор скачивания Корзины покупок."""

    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    def validate(self, shopping_cart_data):
        user = self.context.get('request').user
        if not ShoppingCart.objects.filter(user=user).exists():
            raise serializers.ValidationError('Корзина покупок пуста')
        return shopping_cart_data

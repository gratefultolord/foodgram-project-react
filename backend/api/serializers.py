import base64
import re

from api.validators import validate_username
from django.core.files.base import ContentFile
from django.db.models import F
from djoser.serializers import UserCreateSerializer, UserSerializer
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from users.models import Subscription, User

MAX_FIELD_LENGTH = 150


class Base64ImageField(serializers.ImageField):
    """Кастомный сериализатор, преобразующий картинки."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


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

    def validate_color(self, value):
        if not re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$', value):
            raise serializers.ValidationError(
                "Цвет должен быть в формате HEX."
            )
        return value


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
        if self.context.get('request').user.is_anonymous:
            return False
        return obj.following.filter(user=request.user).exists()


class MiniRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор короткой формы рецептов."""
    image = Base64ImageField()

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
        if Subscription.objects.filter(following=following,
                                       user=user).exists():
            raise ValidationError(
                detail='Вы уже подписаны на этого пользователя!',
                code=status.HTTP_400_BAD_REQUEST
            )
        if user == following:
            raise ValidationError(
                detail='Вы не можете подписаться на самого себя!',
                code=status.HTTP_400_BAD_REQUEST
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
    id = serializers.IntegerField(source='ingredients.id')
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount',)


class RecipeGetSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов для безопасных запросов."""

    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    image = Base64ImageField()
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
        ingredients = recipe.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('recipe_ingredients__amount')
        )
        return ingredients

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

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Поле ингредиентов не может быть пустым!')
        ingredient_ids = []
        for ingredient in value:
            if not Ingredient.objects.filter(id=ingredient['ingredients']['id']
                                             ).exists():
                raise serializers.ValidationError(
                    'Данного ингредиента не существует!')
            if ingredient['amount'] < 1:
                raise serializers.ValidationError(
                    'Количество ингредиентов не может быть меньше 1!'
                )
            if ingredient['ingredients']['id'] in ingredient_ids:
                raise serializers.ValidationError(
                    "Ингредиенты не могут повторяться!")
            ingredient_ids.append(ingredient['ingredients']['id'])
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'Поле тегов не может быть пустым!')
        if len(value) != len(set(value)):
            raise serializers.ValidationError('Теги не могут повторяться!')
        return value

    def create(self, validated_data):
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('recipe_ingredients')
        recipe = Recipe.objects.create(**validated_data)
        for ingredient_data in ingredients_data:
            ingredient = Ingredient.objects.get(
                id=ingredient_data['ingredients']['id'])
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredients=ingredient, amount=ingredient_data['amount'])
        for tag_data in tags_data:
            recipe.tags.add(tag_data)
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time)

        ingredients_data = validated_data.pop('recipe_ingredients', [])
        instance.recipe_ingredients.all().delete()
        for ingredient_data in ingredients_data:
            ingredient = Ingredient.objects.get(
                id=ingredient_data['ingredients']['id'])
            RecipeIngredient.objects.create(
                recipe=instance,
                ingredients=ingredient, amount=ingredient_data['amount'])

        tags_data = validated_data.pop('tags', [])
        instance.tags.clear()
        for tag_data in tags_data:
            instance.tags.add(tag_data)

        instance.save()
        return instance

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeGetSerializer(instance, context=context).data

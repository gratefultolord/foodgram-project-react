from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint

from users.models import User

MAX_LENGTH = 200


class Tag(models.Model):
    name = models.CharField(
        verbose_name='Название',
        max_length=MAX_LENGTH,
        unique=True,
    )
    color = models.CharField(
        verbose_name='Цвет',
        max_length=MAX_LENGTH,
        unique=True,
        db_index=False,
    )
    slug = models.SlugField(
        verbose_name='Слаг',
        unique=True,
        db_index=False,
    )

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Тег'
        verbose_name_plural = 'теги'

    def __str__(self):
        return f'{self.name} (цвет: {self.color})'


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name='Название',
        max_length=MAX_LENGTH,
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=MAX_LENGTH,
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецептов."""

    name = models.CharField(
        verbose_name='Название',
        max_length=MAX_LENGTH,
    )
    image = models.ImageField(
        verbose_name='Картинка',
        upload_to='recipes/images/',)
    text = models.TextField(
        verbose_name='Описание',
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=(
            MinValueValidator(
                1, message='Минимальное время приготовления - 1 минута!'),
        ),
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        related_name='recipes',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'рецепты'

    def __str__(self):
        return self.name


class Favorite(models.Model):
    """Модель избранных рецептов."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'избранные'
        constraints = [
            UniqueConstraint(fields=['user', 'recipe'], name='unique_favorite')
        ]

    def __str__(self) -> str:
        return f'Рецепт "{self.recipe}" добавлен в Избранное'


class ShoppingCart(models.Model):
    """Модель корзины покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'корзина покупок'
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'], name='unique_shopping_cart')
        ]

    def __str__(self) -> str:
        return f'Рецепт "{self.recipe}" добавлен в Корзину покупок'


class RecipeIngredient(models.Model):
    """Модель связи рецепта и ингредиентов."""

    ingredients = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Ингредиент',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(
            1, message='Должен быть минимум 1 ингредиент!')]
    )

    class Meta:
        verbose_name = 'Ингредиенты в рецепте'
        verbose_name_plural = 'ингредиенты в рецепте'
        constraints = [
            models.UniqueConstraint(fields=['ingredients', 'recipe'],
                                    name='unique_recipe_ingredients')
        ]

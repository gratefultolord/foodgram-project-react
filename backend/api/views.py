from datetime import datetime

from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from recipes.models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag)
from api.serializers import (
    IngredientSerializer, RecipeSerializer, RecipeGetSerializer, TagSerializer, UserSerializer, MiniRecipeSerializer, FollowSerializer)
from users.models import Follow, User
from .filters import IngredientSearchFilter, RecipeFilter
from .pagination import FoodgramPagination
from .permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (IngredientSearchFilter,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = FoodgramPagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return RecipeGetSerializer
        return RecipeSerializer

    @action(
            detail=True,
            methods=('post',),
            permission_classes=(permissions.IsAuthenticated,))
    def favorite(self, request, pk):
        return self.modify_membership(Favorite, request.user, pk, True)

    @action(
            detail=True,
            methods=('delete',),
            permission_classes=(permissions.IsAuthenticated,))
    def remove_favorite(self, request, pk):
        return self.modify_membership(Favorite, request.user, pk, False)

    @action(
            detail=True, methods=('post',),
            permission_classes=(permissions.IsAuthenticated,))
    def shopping_cart(self, request, pk):
        return self.modify_membership(ShoppingCart, request.user, pk, True)

    @action(
            detail=True, methods=('delete',),
            permission_classes=(permissions.IsAuthenticated,))
    def remove_shopping_cart(self, request, pk):
        return self.modify_membership(ShoppingCart, request.user, pk, False)

    def modify_membership(self, model, user, pk, add=True):
        recipe = get_object_or_404(Recipe, id=pk)
        membership, created = model.objects.get_or_create(
            user=user, recipe=recipe)

        if add and created:
            serializer = MiniRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif not add and not created:
            membership.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        error_message = 'Рецепт уже добавлен!' if add else 'Рецепт уже удален!'
        return Response(
            {'errors': error_message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, permission_classes=(permissions.IsAuthenticated,))
    def download_shopping_cart(self, request):
        user = request.user
        if not user.shopping_cart.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(quantity=Sum('quantity'))

        today = datetime.today()
        shopping_list = f'Список покупок для: {user.get_full_name()}\n\nДата: '
        f'{today:%Y-%m-%d}\n\n'
        shopping_list += '\n'.join([
            f'- {ingredient["ingredient__name"]} '
            f'({ingredient["ingredient__measurement_unit"]}) - '
            f'{ingredient["quantity"]}'
            for ingredient in ingredients
        ])
        shopping_list += f'\n\nFoodgram ({today:%Y})'

        filename = f'{user.username}_shopping_list.txt'
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'

        return response


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class UserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = FoodgramPagination

    @action(
            detail=True,
            methods=['post', 'delete'],
            permission_classes=(permissions.IsAuthenticated,))
    def subscribe(self, request, id):
        user = request.user
        following = get_object_or_404(User, pk=id)

        if user == following:
            return Response({'errors': 'Нельзя подписаться на самого себя!'},
                            status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'POST':
            if Follow.objects.filter(user=user, following=following).exists():
                return Response(
                    {'errors': 'Вы уже подписаны на этого пользователя!'},
                    status=status.HTTP_400_BAD_REQUEST)

            Follow.objects.create(user=user, following=following)
            serializer = FollowSerializer(
                following, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            follow = get_object_or_404(Follow, user=user, following=following)
            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, permission_classes=(permissions.IsAuthenticated,))
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(following__user=user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

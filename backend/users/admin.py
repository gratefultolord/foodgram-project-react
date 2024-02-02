from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Follow, User


@admin.register(User)
class UserAdmin(UserAdmin):
    """Административный класс для управления пользователями."""

    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
    )
    list_filter = ('email', 'username')
    empty_value_display = '-пусто-'


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Административный класс для управления подписками."""

    list_display = ('user', 'following',)
    empty_value_display = '-пусто-'

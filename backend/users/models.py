from django.contrib.auth.models import AbstractUser
from django.db import models

MAX_EMAIL_LENGTH = 254
MAX_FIELD_LENGTH = 150


class User(AbstractUser):
    """Модель пользователя."""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name',)
    email = models.EmailField(
        verbose_name='Адрес электронной почты',
        unique=True,
        max_length=MAX_EMAIL_LENGTH,
    )
    username = models.CharField(
        verbose_name='Имя пользователя',
        unique=True,
        max_length=MAX_FIELD_LENGTH,
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=MAX_FIELD_LENGTH,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=MAX_FIELD_LENGTH,
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'пользователи'

    def __str__(self) -> str:
        return self.username


class Subscription(models.Model):
    """Модель подписок."""

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             verbose_name='Подписчик',
                             related_name='follower')
    following = models.ForeignKey(User, on_delete=models.CASCADE,
                                  verbose_name='Подписка',
                                  related_name='following')

    class Meta:
        constraints = (
            models.UniqueConstraint(
                name='unique_subscription',
                fields=('user', 'following')
            ),
        )

    def __str__(self) -> str:
        return (
            f'Пользователь {self.user.username} '
            f'подписан на {self.author.username}'
        )

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import CharField

from users.constants import MAX_LENGTH


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'username',
        'first_name',
        'last_name',
        'password',
    )

    email = models.EmailField(
        unique=True,
        blank=False,
        verbose_name='Электронная почта'
    )
    username = models.CharField(
        max_length=MAX_LENGTH,
        blank=False,
        unique=True,
        verbose_name='Никнейм',
    )
    first_name = models.CharField(
        max_length=MAX_LENGTH,
        blank=False,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=MAX_LENGTH,
        blank=False,
        verbose_name='Фамилия'
    )
    password = models.CharField(
        max_length=MAX_LENGTH,
        blank=False,
        verbose_name='Пароль'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='Аватар'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'пользователи'

    def __str__(self) -> CharField:
        return self.username


class Follow(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='follower'
    )
    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='following'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_user_following'
            )
        ]

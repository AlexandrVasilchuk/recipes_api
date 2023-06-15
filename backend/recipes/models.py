from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

from foodgram_backend.models import DefaultModel


User = get_user_model()


class Tag(DefaultModel):
    name = models.CharField(max_length=settings.FIELD_MAX_LENGTH, verbose_name='название тэга')
    color = models.CharField(max_length=settings.FIELD_LOW_LENGTH, verbose_name='цветовой hex')
    slug = models.CharField(max_length=settings.FIELD_MAX_LENGTH, verbose_name='текстовый слаг тэга')

    class Meta:
        unique_together = ['name', 'color', 'slug']

    def __str__(self) -> str:
        return self.name


class Ingredient(DefaultModel):
    name = models.CharField(max_length=settings.FIELD_MAX_LENGTH, verbose_name='название')
    measurement_unit = models.CharField(max_length=settings.FIELD_LOW_LENGTH,
                                        verbose_name='ед.измерения')

    def __str__(self) -> str:
        return f'{self.name} - измеряем в {self.measurement_unit}'

    class Meta:
        ordering = ('name', )


class Recipe(DefaultModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=settings.FIELD_MAX_LENGTH, verbose_name='название')
    image = models.ImageField(upload_to='recipes/images/', verbose_name='изображение')
    text = models.TextField(verbose_name='описание')
    ingredients = models.ManyToManyField(
        Ingredient, related_name='ingredients', through='recipes.RecipeIngredient', verbose_name='ингредиенты')
    tags = models.ManyToManyField(Tag, related_name='tags', verbose_name='тэг', through='RecipeTag')
    cooking_time = models.IntegerField(verbose_name='время приготовления')

    class Meta:
        ordering = ('id',)

    def __str__(self) -> str:
        return f'Рецепт {self.name} от {self.author}'


class RecipeTag(DefaultModel):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f'{self.recipe} с тэгом {self.tag}'


class RecipeIngredient(DefaultModel):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredients = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.IntegerField(verbose_name='количество')

    def __str__(self) -> str:
        return f'{self.ingredient_id} для рецепта {self.recipe}'


class Follow(DefaultModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='author')
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follower')

    def __str__(self) -> str:
        return f'Пользователь {self.follower} подписан на пользователя {self.author}'

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['author', 'follower'], name='unique_follow')
        ]


class Favourite(DefaultModel):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owner')
    recipes = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='recipes')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['owner', 'recipes'], name='unique_favorite')
        ]


class ShoppingCart(DefaultModel):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shopping_cart_owner')
    recipes = models.ForeignKey(Recipe, on_delete=models.CASCADE,related_name='shopping_cart_recipes')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['owner', 'recipes'], name='unique_shopping_cart')
        ]
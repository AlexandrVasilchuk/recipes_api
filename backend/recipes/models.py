from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from foodgram_backend.models import DefaultModel

User = get_user_model()


class Tag(DefaultModel):
    name = models.CharField(
        max_length=settings.FIELD_MAX_LENGTH,
        verbose_name='название тэга',
    )
    color = models.CharField(
        max_length=settings.FIELD_LOW_LENGTH,
        verbose_name='цветовой hex',
    )
    slug = models.CharField(
        max_length=settings.FIELD_MAX_LENGTH,
        verbose_name='текстовый слаг тэга',
    )

    class Meta:
        unique_together = ['name', 'color', 'slug']
        ordering = ('id',)

    def __str__(self) -> str:
        return self.name


class Ingredient(DefaultModel):
    name = models.CharField(
        max_length=settings.FIELD_MAX_LENGTH,
        verbose_name='название',
    )
    measurement_unit = models.CharField(
        max_length=settings.FIELD_LOW_LENGTH,
        verbose_name='ед.измерения',
    )

    class Meta:
        ordering = ('name',)

    def __str__(self) -> str:
        return f'{self.name} - измеряем в {self.measurement_unit}'


class Recipe(DefaultModel):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='автор',
    )
    name = models.CharField(
        max_length=settings.FIELD_MAX_LENGTH,
        verbose_name='название',
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='изображение',
    )
    text = models.TextField(verbose_name='описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        related_name='ingredients',
        through='recipes.RecipeIngredient',
        verbose_name='ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='tags',
        verbose_name='тэг',
        through='RecipeTag',
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='время приготовления',
        validators=(MinValueValidator(1), MaxValueValidator(32000)),
    )

    class Meta:
        ordering = ('-id',)

    def __str__(self) -> str:
        return f'Рецепт {self.name} от {self.author}'


class RecipeTag(DefaultModel):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='рецепт',
    )
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, verbose_name='тэг')

    class Meta:
        ordering = ('id',)

    def __str__(self) -> str:
        return f'{self.recipe} с тэгом {self.tag}'


class RecipeIngredient(DefaultModel):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='рецепт',
        related_name='ingredients_line',
    )
    ingredients = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='количество',
        validators=(MinValueValidator(1), MaxValueValidator(32000)),
    )

    class Meta:
        ordering = ('id',)

    def __str__(self) -> str:
        return f'{self.ingredient_id} для рецепта {self.recipe}'


class Follow(DefaultModel):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='author',
        verbose_name='автор',
    )
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='подписчик',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'follower'],
                name='unique_follow',
            ),
        ]
        ordering = ('id',)

    def __str__(self) -> str:
        return f'Пользователь {self.follower} подписан на {self.author}'


class Favourite(DefaultModel):
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owner',
        verbose_name='владелец избранного',
    )
    recipes = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='рецепт',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['owner', 'recipes'],
                name='unique_favorite',
            ),
        ]
        ordering = ('id',)


class ShoppingCart(DefaultModel):
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart_owner',
        verbose_name='владелец корзины',
    )
    recipes = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart_recipes',
        verbose_name='рецепт',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['owner', 'recipes'],
                name='unique_shopping_cart',
            ),
        ]
        ordering = ('id',)

import base64
from collections import OrderedDict

import webcolors
from django.conf import settings
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from recipes.models import (
    Favourite,
    Follow,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
    User,
)


class CustomUserSerializer(UserSerializer):
    """Сериализатор для отображения информации о пользователе."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj: User) -> bool:
        request = self.context['request']
        author = User.objects.filter(username=obj).first()
        follower = request.user
        if follower.is_authenticated:
            return follower.follower.filter(author=author).exists()
        return False


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор для создания пользователя."""

    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())],
    )
    username = serializers.CharField(
        validators=[UniqueValidator(queryset=User.objects.all())],
    )

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'password',
            'username',
            'first_name',
            'last_name',
        )
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
            'password': {'required': True, 'write_only': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }


class Hex2NameColor(serializers.Field):
    """Методы поля color(представленный в виде hex) модели Tag."""

    def to_representation(self, value: str) -> str:
        return value

    def to_internal_value(self, data: str) -> str:
        try:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError('Для этого цвета нет имени')
        return data


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    color = Hex2NameColor()

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class Base64ImageField(serializers.ImageField):
    """Поле для сохранения картинок в закодированном виде."""

    def to_internal_value(self, data: str) -> str:
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для связанной модели рецепт-ингредиент."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = serializers.ReadOnlyField(source='ingredients.name')
    measurement_unit = serializers.StringRelatedField(
        source='ingredients.measurement_unit',
    )
    amount = serializers.IntegerField(
        min_value=settings.MIN_INTEGER_VALUE,
        max_value=settings.MAX_INTEGER_VALUE,
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class CreateRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=True)
    tags = TagSerializer(read_only=True, many=True)
    ingredients = RecipeIngredientSerializer(
        source='ingredients_line',
        many=True,
    )
    author = CustomUserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    cooking_time = serializers.IntegerField(
        min_value=settings.MIN_INTEGER_VALUE,
        max_value=settings.MAX_INTEGER_VALUE,
    )

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
        read_only_fields = ('author',)

    def get_is_favorited(self, obj: Recipe) -> bool:
        owner = self.context['request'].user
        if owner.is_authenticated:
            return obj.recipes.filter(owner=owner).exists()
        return False

    def get_is_in_shopping_cart(self, obj: Recipe) -> bool:
        owner = self.context['request'].user
        if owner.is_authenticated:
            return obj.shopping_cart_recipes.filter(owner=owner).exists()
        return False

    def validate(self, data: dict) -> dict:
        tags = self.initial_data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                'Убедитесь, что добавлен хотя бы один тег',
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError('Теги должны быть уникальными')
        data['tags'] = tags
        return data

    def ingredients_factory(
        self,
        recipe: Recipe,
        ingredient_data: list,
    ) -> None:
        """Функция для создания объектов промежуточной модели."""
        ingredient_lst = []
        for ingredient in ingredient_data:
            ingredient_lst.append(
                RecipeIngredient(
                    recipe=recipe,
                    ingredients_id=ingredient['id'].pk,
                    amount=ingredient['amount'],
                ),
            )
        RecipeIngredient.objects.bulk_create(ingredient_lst)

    def create(self, validated_data: dict) -> Recipe:
        image = validated_data.pop('image')
        tags_data = validated_data.pop('tags')
        ingredients_line = validated_data.pop('ingredients_line')
        recipe = Recipe.objects.create(image=image, **validated_data)
        Favourite.objects.create(
            owner=validated_data['author'],
            recipes=recipe,
        )
        ShoppingCart.objects.create(
            owner=validated_data['author'],
            recipes=recipe,
        )
        recipe.tags.set(tags_data)
        self.ingredients_factory(recipe, ingredients_line)
        return recipe

    def update(self, instance: Recipe, validated_data: dict) -> Recipe:
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.image = validated_data.get('image', instance.image)
        instance.cooking_time = validated_data.get(
            'cooking_time',
            instance.cooking_time,
        )
        ingredients_data = validated_data.pop('ingredients_line')
        tags = validated_data.pop('tags')
        instance.tags.clear()
        instance.tags.add(*tags)
        instance.ingredients.clear()
        self.ingredients_factory(instance, ingredients_data)
        instance.save()
        return instance


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'image', 'name', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    follower = serializers.HiddenField(
        default=serializers.CurrentUserDefault(),
    )
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = ('author', 'follower', 'recipes', 'recipes_count')

    def validate(self, data: dict) -> dict:
        if (
            get_object_or_404(User, id=self.context['view'].kwargs['user_id'])
            == data['follower']
        ):
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя!',
            )
        return data

    def get_recipes_count(self, obj: Recipe) -> int:
        return Recipe.objects.filter(author=obj.author).count()

    def get_recipes(self, obj: Recipe) -> dict:
        recipe_serializer = ShortRecipeSerializer(
            Recipe.objects.filter(author=obj.author),
            many=True,
        )
        return recipe_serializer.data

    def to_representation(self, instance: Recipe) -> OrderedDict:
        representation = super().to_representation(instance)
        author_data = representation.pop('author')
        recipes_data = representation.pop('recipes')
        recipes_limit = self.context['request'].GET.get('recipes_limit')
        new_representation = OrderedDict()
        new_representation.update(author_data)
        if recipes_limit:
            new_representation['recipes'] = recipes_data[: int(recipes_limit)]
        else:
            new_representation['recipes'] = recipes_data
        new_representation.update(representation)
        return new_representation


class FavouriteSerializer(serializers.ModelSerializer):
    recipes = ShortRecipeSerializer(required=False, read_only=True)

    def validate(self, data: dict) -> dict:
        request = self.context['request']
        recipe = get_object_or_404(
            Recipe,
            id=self.context['view'].kwargs['recipe_id'],
        )
        owner = request.user
        if request.method == 'POST':
            if owner.owner.filter(recipes=recipe).exists():
                raise serializers.ValidationError(
                    {'error': 'Рецепт уже в избранном!'},
                )
        if request.method == 'DELETE':
            if not owner.owner.filter(recipes=recipe).exists():
                raise serializers.ValidationError(
                    {'error': 'Рецепта нет в избранном!'},
                )
        return data

    class Meta:
        model = Favourite
        fields = ('recipes', 'owner')
        read_only_fields = ('owner',)

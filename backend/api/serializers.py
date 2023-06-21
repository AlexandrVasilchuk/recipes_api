import base64
from collections import OrderedDict

import webcolors
from django.core.files.base import ContentFile
from django.db.models import F, QuerySet
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
    """Сериализатор для отображения информации о пользователе"""

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
            return Follow.objects.filter(
                author=author, follower=follower
            ).exists()
        return False


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор для создания пользователя"""

    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    username = serializers.CharField(
        validators=[UniqueValidator(queryset=User.objects.all())]
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
    """Методы поля color(представленный в виде hex) модели Tag"""

    def to_representation(self, value: str):
        return value

    def to_internal_value(self, data: str):
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


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для связанной модели рецепт-ингредиент."""

    class Meta:
        model = RecipeIngredient
        fields = ('recipe', 'ingredients', 'amount')
        read_only_fields = ('recipe',)


class Base64ImageField(serializers.ImageField):
    """Поле для сохранения картинок в закодированном виде."""

    def to_internal_value(self, data: str):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class CreateRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=True)
    tags = TagSerializer(read_only=True, many=True)
    ingredients = serializers.SerializerMethodField()
    author = CustomUserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

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
        if self.context['request'].user.is_authenticated:
            return Favourite.objects.filter(
                owner=self.context['request'].user, recipes=obj
            ).exists()
        return False

    def get_is_in_shopping_cart(self, obj: Recipe) -> bool:
        if self.context['request'].user.is_authenticated:
            return ShoppingCart.objects.filter(
                owner=self.context['request'].user, recipes=obj
            ).exists()
        return False

    def get_ingredients(self, obj: Recipe) -> QuerySet:
        print(
            123123123123,
            type(
                obj.ingredients.values(
                    "id",
                    "name",
                    "measurement_unit",
                    amount=F("recipeingredient__amount"),
                )
            ),
        )
        return obj.ingredients.values(
            "id",
            "name",
            "measurement_unit",
            amount=F("recipeingredient__amount"),
        )

    def validate(self, data: dict) -> dict:
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError()
        data['ingredients'] = ingredients

        tags = self.initial_data.get("tags")
        if not tags:
            raise serializers.ValidationError(
                "Убедитесь, что добавлен хотя бы один тег"
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError("Теги должны быть уникальными")
        data["tags"] = tags

        cooking_time = self.initial_data.get("cooking_time")
        if not int(cooking_time) > 0:
            raise serializers.ValidationError(
                "Убедитесь, что время приготовления больше нуля"
            )
        data["cooking_time"] = cooking_time
        return data

    def ingredients_factory(self, recipe: Recipe, ingredient_data: list):
        """Функция для создания объектов промежуточной модели."""
        ingredient_lst = []
        for ingredient in ingredient_data:
            ingredient_lst.append(
                RecipeIngredient(
                    recipe=recipe,
                    ingredients_id=ingredient['id'],
                    amount=ingredient['amount'],
                )
            )
        RecipeIngredient.objects.bulk_create(ingredient_lst)

    def create(self, validated_data: dict) -> Recipe:
        image = validated_data.pop('image')
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(image=image, **validated_data)
        Favourite.objects.create(
            owner=validated_data['author'], recipes=recipe
        )
        ShoppingCart.objects.create(
            owner=validated_data['author'], recipes=recipe
        )
        recipe.tags.set(tags_data)
        self.ingredients_factory(recipe, ingredients_data)
        return recipe

    def update(self, instance: Recipe, validated_data: dict) -> Recipe:
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.image = validated_data.get('image', instance.image)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        ingredients_data = validated_data.pop('ingredients')
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
    author = CustomUserSerializer()
    follower = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = ('author', 'follower', 'recipes', 'recipes_count')
        extra_kwargs = {'author': {'read_only': True}}

    def get_recipes_count(self, obj: Recipe) -> int:
        return Recipe.objects.filter(author=obj.author).count()

    def get_recipes(self, obj: Recipe) -> dict:
        recipe_serializer = ShortRecipeSerializer(
            Recipe.objects.filter(author=obj.author), many=True
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

    class Meta:
        model = Favourite
        fields = ('recipes', 'owner')
        read_only_fields = ('owner',)

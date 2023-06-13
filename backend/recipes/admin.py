from django.contrib import admin
from django.contrib.auth import get_user_model

from recipes.models import Recipe, Tag, Ingredient, User

from django.contrib import admin


class BaseAdmin(admin.ModelAdmin):
    empty_value_display = '-пусто-'


@admin.register(Recipe)
class RecipesAdmin(BaseAdmin):
    list_display = (
        'pk',
        'author',
        'name',
        'image',
        'text',
        'cooking_time',
    )
    list_editable = ('text', 'name')
    search_fields = ('text', 'name')


@admin.register(Ingredient)
class IngredientsAdmin(BaseAdmin):
    list_display = (
        'name',
        'measurement_unit',
    )


@admin.register(Tag)
class TagAdmin(BaseAdmin):
    list_display = (
        'name',
        'color',
        'slug'
    )

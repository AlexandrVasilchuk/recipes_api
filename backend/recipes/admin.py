from django.contrib import admin
from django.contrib.auth import get_user_model

from recipes.models import (
    Favourite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    RecipeTag,
    Tag,
)

User = get_user_model()


class BaseAdmin(admin.ModelAdmin):
    empty_value_display = '-пусто-'


class RecipeTagAdminInline(admin.TabularInline):
    model = RecipeTag


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    min_num = 1


@admin.register(Recipe)
class RecipesAdmin(BaseAdmin):
    list_display = (
        'pk',
        'author',
        'name',
        'favorited_count',
        'image',
        'text',
        'cooking_time',
    )
    list_editable = ('text', 'name')
    search_fields = (
        'text',
        'name',
    )
    inlines = (RecipeTagAdminInline, RecipeIngredientInline)
    list_filter = ('tags',)

    def favorited_count(self, obj: Recipe) -> int:
        return Favourite.objects.filter(recipes=obj).count()

    favorited_count.short_description = 'Раз в избранном'


@admin.register(Ingredient)
class IngredientsAdmin(BaseAdmin):
    list_display = (
        'name',
        'measurement_unit',
    )
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(BaseAdmin):
    list_display = ('name', 'color', 'slug')

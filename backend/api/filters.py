from django.db.models import QuerySet
from django_filters import rest_framework as filters
from rest_framework.filters import SearchFilter

from recipes.models import Tag, User


class RecipeFilter(filters.FilterSet):
    author = filters.ModelChoiceFilter(
        field_name='author_id',
        queryset=User.objects.all(),
    )
    tags = filters.filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug',
    )
    is_favorited = filters.BooleanFilter(method='favorited_filter')
    is_in_shopping_cart = filters.BooleanFilter(method='shoppingcart_filter')

    def shoppingcart_filter(
        self, queryset: QuerySet, name: str, value: bool
    ) -> QuerySet:
        user = self.request.user
        if value is True and user.is_authenticated:
            return queryset.filter(shopping_cart_recipes__owner_id=user.id)
        return queryset

    def favorited_filter(
        self, queryset: QuerySet, name: str, value: bool
    ) -> QuerySet:
        user = self.request.user
        if value is True and user.is_authenticated:
            return queryset.filter(recipes__owner_id=user.id)
        return queryset


class IngredientSearchFilter(SearchFilter):
    search_param = 'name'

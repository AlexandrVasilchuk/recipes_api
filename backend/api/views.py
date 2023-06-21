from django.db.models import QuerySet, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView, DestroyAPIView, ListAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.viewsets import GenericViewSet

from api.filters import IngredientSearchFilter, RecipeFilter
from api.pagination import PageLimitPagination
from api.permissions import IsOwner
from api.serializers import (
    CreateRecipeSerializer,
    FavouriteSerializer,
    IngredientSerializer,
    ShortRecipeSerializer,
    SubscriptionSerializer,
    TagSerializer,
)
from recipes.models import (
    Favourite,
    Follow,
    Ingredient,
    Recipe,
    ShoppingCart,
    Tag,
    User,
)


class UserViewSet(DjoserUserViewSet):
    """Обновленный DjoserViewSet с кастомной пагинацией."""

    pagination_class = PageLimitPagination


class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для отображения и получение тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для отображения ингредиентов"""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (IngredientSearchFilter,)
    search_fields = ('^name',)


class RecipesViewSet(viewsets.ModelViewSet):
    """Вьюсет для отображения/создания/обновления/удаления рецептов."""

    queryset = Recipe.objects.all()
    serializer_class = CreateRecipeSerializer
    filterset_class = RecipeFilter
    filter_backends = (DjangoFilterBackend,)
    pagination_class = PageLimitPagination
    permission_classes = (permissions.IsAuthenticatedOrReadOnly & IsOwner,)

    def perform_create(self, serializer: Serializer) -> None:
        serializer.save(author=self.request.user)

    @action(methods=['get'], detail=False, url_path='download_shopping_cart')
    def download_shopping_cart(self, request: Request) -> Response:
        user = request.user
        filename = 'shopping_list.txt'
        items = Ingredient.objects.filter(
            recipeingredient__recipe__shopping_cart_recipes__owner=user.id
        ).annotate(amount=Sum('recipeingredient__amount'))
        simple_ingredient_list = [
            f"{obj.name} ({obj.measurement_unit}) — {obj.amount}"
            for obj in items
        ]
        content = '\n'.join(simple_ingredient_list)
        response = HttpResponse(
            content, content_type='text.txt; charset=utf-8'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response

    @action(
        methods=[
            'post',
            'delete',
        ],
        detail=True,
        url_path='shopping_cart',
        permission_classes=[permissions.IsAuthenticated],
    )
    def shopping_cart(self, request: Request, **kwargs: dict) -> Response:
        owner = request.user
        recipe = get_object_or_404(Recipe, pk=kwargs.get('pk'))
        if request.method == 'POST':
            ShoppingCart.objects.create(owner=owner, recipes=recipe)
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        ShoppingCart.objects.filter(owner=owner, recipes=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['post', 'delete'],
        detail=True,
        url_path='favourite',
        permission_classes=[permissions.IsAuthenticated],
    )
    def favourite(self, request: Request, **kwargs: dict) -> Response:
        owner = request.user
        recipe = get_object_or_404(Recipe, kwargs.get('pk'))
        if request.method == 'POST':
            Favourite.objects.create(owner=owner, recipes=recipe)
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        Favourite.objects.filter(owner=owner, recipes=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FollowViewSet(
    ListAPIView, CreateAPIView, DestroyAPIView, GenericViewSet
):
    """Вьюсет для отображения/создания/удаления подписок."""

    queryset = Follow.objects.all()
    serializer_class = SubscriptionSerializer
    pagination_class = PageLimitPagination
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self) -> QuerySet:
        return self.request.user.follower.all()

    def create(
        selfself, request: Request, *args: tuple, **kwargs: dict
    ) -> Response:
        follower = request.user
        author = get_object_or_404(User, id=kwargs.get('user_id'))
        if (
            follower != author
            and not Follow.objects.filter(
                author=author, follower=follower
            ).exists()
        ):
            Follow.objects.create(author=author, follower=follower)
            follow_instance = Follow.objects.get(
                author=author, follower=follower
            )
            serializer = SubscriptionSerializer(
                instance=follow_instance, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
        )

    def destroy(
        self, request: Request, *args: tuple, **kwargs: dict
    ) -> Response:
        follower = request.user
        author = get_object_or_404(User, id=kwargs.get('user_id'))
        if Follow.objects.filter(author=author, follower=follower).exists():
            Follow.objects.filter(author=author, follower=follower).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Ошибка, вы не подписаны на этого автора!'},
            status=status.HTTP_400_BAD_REQUEST,
        )


class FavouriteView(CreateAPIView, DestroyAPIView, GenericViewSet):
    """Вьюсет для создания/удаления подписок."""

    serializer_class = FavouriteSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer: Serializer):
        owner = self.request.user
        recipe = get_object_or_404(Recipe, id=self.kwargs['recipe_id'])
        if (
            recipe
            and not Favourite.objects.filter(
                owner=owner, recipes=recipe
            ).exists()
        ):
            serializer.save(owner=owner, recipes=recipe)
        else:
            raise serializers.ValidationError(
                "Ошибка при добавлении в избранное"
            )

    def delete(
        self, request: Request, *args: tuple, **kwargs: dict
    ) -> Response:
        owner = request.user
        recipe = get_object_or_404(Recipe, id=self.kwargs['recipe_id'])
        if Favourite.objects.filter(owner=owner, recipes=recipe).exists():
            Favourite.objects.filter(owner=owner, recipes=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def create(
        self, request: Request, *args: tuple, **kwargs: dict
    ) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data['recipes'],
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import PasswordSerializer
from djoser.views import UserViewSet
from rest_framework import status, viewsets, permissions, serializers, filters
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView, CreateAPIView, DestroyAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.serializers import Serializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from djoser.views import UserViewSet as DjoserUserViewSet
from api.serializers import TagSerializer, CreateRecipeSerializer, ShortRecipeSerializer, SubscriptionSerializer, RecipeIngredientSerializer, FavouriteSerializer, FollowSerializer, IngredientSerializer, CustomUserSerializer, DisplayRecipeSerializer
from recipes.models import User, Follow, Tag, ShoppingCart, Ingredient, Recipe, Favourite

from djoser import views
from rest_framework.viewsets import GenericViewSet

class UserViewSet(DjoserUserViewSet):
    """Djoser view set for User model."""
    pagination_class = LimitOffsetPagination

class TagsViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    http_method_names = ('get',)

class IngredientSearchFilter(filters.SearchFilter):  # TODO перенести в фильтры
    search_param = 'name'

class IngredientsViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (IngredientSearchFilter,)
    search_fields = ('^name',)
    http_method_names = ('get',)

class RecipesViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = DisplayRecipeSerializer
    pagination_class = LimitOffsetPagination
    ordering = ('-id',)

    def get_serializer_class(self):
        if self.request.method in ['POST', 'PATCH']:
            return CreateRecipeSerializer
        return DisplayRecipeSerializer

    # def perform_create(self, serializer: Serializer):
    #     serializer.save(author=self.request.user)

    @action(methods=['get'], detail=False, url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        user = request.user
        filename = 'shopping_list.txt'
        items = Ingredient.objects.filter(recipeingredient__recipe__shopping_cart_recipes__owner=user.id).annotate(amount=Sum('recipeingredient__amount'))
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

    @action(methods=['post','delete',], detail=True, url_path='shopping_cart')
    def shopping_cart(self, requset, **kwargs):
        owner = requset.user
        recipe = kwargs['pk']
        if requset.method == 'POST':
            recipe = Recipe.objects.filter(id=recipe).first()
            ShoppingCart.objects.create(owner=owner, recipes=recipe)
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        ShoppingCart.objects.filter(owner=owner,
                                    recipes=Recipe.objects.filter(
                                        id=recipe).first()).delete()
        return Response({'message': 'Рецепт удален из списка покупок'},
                        status=status.HTTP_204_NO_CONTENT)

    # @action(methods=['post', 'delete'], detail=True, url_path='favourite')
    # def favourite(self, request, **kwargs):
    #     owner = request.user
    #     recipe = Recipe.objects.filter(id=kwargs['pk']).first()
    #     if request.method == 'POST':
    #         Favourite.objects.create(owner=owner, recipes=Recipe.objects.filter(id=recipe).first())
    #         return Response({''})


class FollowViewSet(CreateAPIView, DestroyAPIView, GenericViewSet):
    queryset = Follow.objects.all()
    serializer_class = FollowSerializer

    def create(self, request, *args, **kwargs):
        follower = request.user
        author = User.objects.filter(id=kwargs['user_id']).first()
        if follower != author and not Follow.objects.filter(author=author, follower=follower).exists():
            Follow.objects.create(author=author, follower=follower)
            follow_instance = Follow.objects.get(author=author,
                                                 follower=follower)
            serializer = SubscriptionSerializer(instance=follow_instance, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response({'errors': 'Ошибка. Вы уже подписались на автора или пытаетесь подписаться на самого себя!'}, status=status.HTTP_400_BAD_REQUEST)


    def destroy(self, request, *args, **kwargs):
        follower = request.user
        author = User.objects.filter(id=kwargs['user_id']).first()
        if Follow.objects.filter(author=author, follower=follower).exists():
            Follow.objects.filter(author=author, follower=follower).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'Ошибка!'}, status=status.HTTP_400_BAD_REQUEST)


class ShowSubscriptionsView(ListAPIView, GenericViewSet):
    """ Отображение подписок. """

    queryset = Follow.objects.all()
    serializer_class = SubscriptionSerializer


class FavouriteView(CreateAPIView, DestroyAPIView, GenericViewSet):  #оставить что-то одно. Либо убрать из рецептов action либо отсавить тут
    serializer_class = FavouriteSerializer

    def perform_create(self, serializer):
        owner = self.request.user
        recipe_id = self.kwargs['recipe_id']
        recipe = Recipe.objects.filter(id=recipe_id).first()
        if recipe and not Favourite.objects.filter(owner=owner,
                                                   recipes=recipe).exists():
            serializer.save(owner=owner, recipes=recipe)
        else:
            raise serializers.ValidationError(
                "Ошибка при добавлении в избранное")

    def delete(self, request, *args, **kwargs):
        owner = request.user
        recipe = Recipe.objects.filter(id=kwargs['recipe_id']).first()
        if Favourite.objects.filter(owner=owner, recipes=recipe).exists():
            Favourite.objects.filter(owner=owner, recipes=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data['recipes'],
                        status=status.HTTP_201_CREATED, headers=headers)
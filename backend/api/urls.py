from django.conf.urls import url
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from api.views import TagsViewSet, FavouriteView, FollowViewSet, IngredientsViewSet, RecipesViewSet, ShowSubscriptionsView
from djoser.views import UserViewSet


router = DefaultRouter()

router.register('recipes', RecipesViewSet)
router.register('tags', TagsViewSet, basename='tags')
router.register('ingredients', IngredientsViewSet, basename='ingredients')
router.register(r'users/(?P<user_id>\d+)/subscribe', FollowViewSet) #Перенести в users/
router.register('users/subscriptions', ShowSubscriptionsView)  #Перенести в users/
router.register(r'recipes/(?P<recipe_id>\d+)/favorite', FavouriteView, basename='favorites')

auth = [
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken'))
]

urlpatterns = [
    path('', include(router.urls)),
    path('', include(auth)),
]
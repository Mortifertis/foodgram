from django.urls import path

from .views import RecipeShortLinkRedirectView

app_name = 'recipes'

urlpatterns = [
    path(
        's/<slug:short_link>/',
        RecipeShortLinkRedirectView.as_view(),
        name='short-link',
    ),
]

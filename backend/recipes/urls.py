from api.views import RecipeShortLinkRedirectView
from django.urls import path

app_name = 'recipes'

urlpatterns = [
    path(
        's/<slug:short_link>/',
        RecipeShortLinkRedirectView.as_view(),
        name='short-link',
    ),
]

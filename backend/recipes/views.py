from django.shortcuts import get_object_or_404, redirect
from django.views import View

from .models import Recipe


class RecipeShortLinkRedirectView(View):
    """Перенаправляет на страницу рецепта по короткой ссылке."""

    def get(self, request, short_link):
        recipe = get_object_or_404(Recipe, short_link=short_link)
        return redirect(f"/recipes/{recipe.id}/")

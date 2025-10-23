from __future__ import annotations

import json
from pathlib import Path

from django.db import migrations


def load_tags(apps, schema_editor):
    Tag = apps.get_model("recipes", "Tag")

    data_path = Path(__file__).resolve().parents[3] / "data" / "tags.json"
    if not data_path.exists():
        return

    with data_path.open(encoding="utf-8") as file:
        tags = json.load(file)

    for tag in tags:
        Tag.objects.update_or_create(
            slug=tag["slug"],
            defaults={
                "name": tag["name"],
                "color": tag["color"],
            },
        )


def unload_tags(apps, schema_editor):
    Tag = apps.get_model("recipes", "Tag")
    data_path = Path(__file__).resolve().parents[3] / "data" / "tags.json"
    if not data_path.exists():
        return

    with data_path.open(encoding="utf-8") as file:
        tags = json.load(file)

    Tag.objects.filter(slug__in=[tag["slug"] for tag in tags]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0002_recipe_short_link"),
    ]

    operations = [
        migrations.RunPython(load_tags, unload_tags),
    ]

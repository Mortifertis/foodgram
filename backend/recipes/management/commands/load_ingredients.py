import csv
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Load ingredients from data/ingredients.json or data/ingredients.csv'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            help='Path to ingredients file (json or csv). Defaults to data/ingredients.json',
        )

    def handle(self, *args, **options):
        file_path = options.get('path')
        if file_path:
            path = Path(file_path)
        else:
            default_json = Path('data') / 'ingredients.json'
            default_csv = Path('data') / 'ingredients.csv'
            path = default_json if default_json.exists() else default_csv

        if not path.exists():
            raise CommandError(f'Файл {path} не найден')

        created = 0
        if path.suffix.lower() == '.json':
            with path.open(encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    obj, is_created = Ingredient.objects.get_or_create(
                        name=item['name'],
                        measurement_unit=item['measurement_unit'],
                    )
                    created += int(is_created)
        elif path.suffix.lower() == '.csv':
            with path.open(encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) < 2:
                        continue
                    obj, is_created = Ingredient.objects.get_or_create(
                        name=row[0],
                        measurement_unit=row[1],
                    )
                    created += int(is_created)
        else:
            raise CommandError('Поддерживаются только файлы CSV или JSON')

        self.stdout.write(self.style.SUCCESS(f'Загружено ингредиентов: {created}'))

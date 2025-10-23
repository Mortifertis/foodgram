import csv
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from recipes.models import Tag


class Command(BaseCommand):
    help = (
        'Load tags from data/tags.json '
        'or data/tags.csv'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            help=(
                'Path to tags file (json or csv). '
                'Defaults to data/tags.json'
            ),
        )

    def handle(self, *args, **options):
        file_path = options.get('path')
        if file_path:
            path = Path(file_path)
        else:
            default_json = Path('data') / 'tags.json'
            default_csv = Path('data') / 'tags.csv'
            path = default_json if default_json.exists() else default_csv

        if not path.exists():
            raise CommandError(f'Файл {path} не найден')

        created = 0
        if path.suffix.lower() == '.json':
            with path.open(encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    obj, is_created = Tag.objects.get_or_create(
                        name=item['name'],
                        defaults={
                            'color': item['color'],
                            'slug': item['slug'],
                        },
                    )
                    if not is_created:
                        updated = False
                        if obj.color != item['color']:
                            obj.color = item['color']
                            updated = True
                        if obj.slug != item['slug']:
                            obj.slug = item['slug']
                            updated = True
                        if updated:
                            obj.save(update_fields=['color', 'slug'])
                    created += int(is_created)
        elif path.suffix.lower() == '.csv':
            with path.open(encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) < 3:
                        continue
                    obj, is_created = Tag.objects.get_or_create(
                        name=row[0],
                        defaults={
                            'color': row[1],
                            'slug': row[2],
                        },
                    )
                    if not is_created:
                        updated = False
                        if obj.color != row[1]:
                            obj.color = row[1]
                            updated = True
                        if obj.slug != row[2]:
                            obj.slug = row[2]
                            updated = True
                        if updated:
                            obj.save(update_fields=['color', 'slug'])
                    created += int(is_created)
        else:
            raise CommandError('Поддерживаются только файлы CSV или JSON')

        self.stdout.write(
            self.style.SUCCESS(f'Загружено тегов: {created}')
        )

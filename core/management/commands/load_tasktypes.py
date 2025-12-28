# core/management/commands/load_tasktypes.py
from django.core.management.base import BaseCommand
from core.models import TaskType


class Command(BaseCommand):
    help = 'Завантажує типи завдань для системи'

    def handle(self, *args, **kwargs):
        # Список типів завдань (можна змінювати)
        task_types = [
            {
                'name': 'Bug',
                'description': 'Виправлення помилок у коді'
            },
            {
                'name': 'New Feature',
                'description': 'Розробка нової функціональності'
            },
            {
                'name': 'Refactoring',
                'description': 'Переробка існуючого коду'
            },
            {
                'name': 'Testing',
                'description': 'Тестування функціональності'
            },
            {
                'name': 'Documentation',
                'description': 'Написання або оновлення документації'
            },
            {
                'name': 'Deployment',
                'description': 'Розгортання на серверах'
            },
            {
                'name': 'Code Review',
                'description': 'Перевірка коду інших розробників'
            },
            {
                'name': 'UI/UX Design',
                'description': 'Дизайн інтерфейсу'
            },
            {
                'name': 'Performance Optimization',
                'description': 'Оптимізація продуктивності'
            },
            {
                'name': 'Security Fix',
                'description': 'Виправлення проблем безпеки'
            }
        ]

        created_count = 0
        updated_count = 0

        for task_type_data in task_types:
            # Створюємо або оновлюємо тип завдання
            task_type, created = TaskType.objects.update_or_create(
                name=task_type_data['name'],
                defaults={'name': task_type_data['name']}
            )

            # Додамо опис через setattr (якщо поле існує)
            try:
                task_type.description = task_type_data.get('description', '')
                task_type.save()
            except AttributeError:
                # Якщо поля description немає в моделі - пропускаємо
                pass

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Створено тип завдання: {task_type_data["name"]}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'📝 Оновлено тип завдання: {task_type_data["name"]}')
                )

        # Виведемо підсумок
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(
            self.style.SUCCESS(
                f'Успішно створено/оновлено {created_count + updated_count} типів завдань!\n'
                f'✅ Створено: {created_count}\n'
                f'📝 Оновлено: {updated_count}'
            )
        )

        # Покажемо всі створені типи
        self.stdout.write('\n' + '-' * 50)
        self.stdout.write('Список всіх типів завдань:')
        for task_type in TaskType.objects.all().order_by('name'):
            self.stdout.write(f'• {task_type.name}')
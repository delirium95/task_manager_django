# tasks/management/commands/load_positions.py
from django.core.management.base import BaseCommand

from core.models import Position


class Command(BaseCommand):
    help = 'Завантажити стандартні посади в базу даних'

    def handle(self, *args, **options):
        """Основний метод, який викликається Django"""

        # Список стандартних посад
        positions = [
            # Технічні посади
            "Frontend Developer",
            "Backend Developer",
            "Full Stack Developer",
            "DevOps Engineer",
            "QA Engineer",
            "Test Engineer",
            "System Administrator",
            "Database Administrator",

            # Дизайн
            "UI Designer",
            "UX Designer",
            "Graphic Designer",

            # Менеджмент
            "Project Manager",
            "Product Owner",
            "Scrum Master",
            "Team Lead",
            "Engineering Manager",

            # Аналітика
            "Business Analyst",
            "System Analyst",
            "Data Analyst",
            "Marketing Analyst",

            # Керівництво
            "CTO (Chief Technology Officer)",
            "CEO (Chief Executive Officer)",
            "CFO (Chief Financial Officer)",
            "COO (Chief Operating Officer)",

            # Інше
            "Customer Support",
            "Technical Support",
            "HR Manager",
            "Recruiter",
            "Marketing Specialist",
        ]

        created_count = 0
        existing_count = 0

        self.stdout.write("🔄 Завантаження посад...")
        self.stdout.write("-" * 50)

        for position_name in positions:
            # get_or_create повертає (об'єкт, булеве_значення)
            # булеве_значення = True якщо створено новий запис
            obj, created = Position.objects.get_or_create(name=position_name)

            if created:
                created_count += 1
                self.stdout.write(f"✅ Створено: {position_name}")
            else:
                existing_count += 1
                self.stdout.write(f"ℹ️  Вже існує: {position_name}")

        # Підсумок
        self.stdout.write("-" * 50)
        self.stdout.write(self.style.SUCCESS(
            f"✨ ГОТОВО! Створено: {created_count}, Існувало: {existing_count}"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"📊 Всього посад у базі: {Position.objects.count()}"
        ))
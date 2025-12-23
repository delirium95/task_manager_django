# core/tasks.py (створимо новий файл)
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Task, Project
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task
def send_task_assignment_email(task_id, user_ids):
    """Надсилає email при призначенні завдання"""
    try:
        task = Task.objects.get(id=task_id)
        users = User.objects.filter(id__in=user_ids)

        for user in users:
            subject = f'🎯 Нове завдання: {task.name}'
            message = f"""
            Вітаємо, {user.get_full_name()}!

            Вам призначено нове завдання:

            📝 Назва: {task.name}
            📋 Опис: {task.description[:100]}...
            ⏰ Дедлайн: {task.deadline.strftime('%d.%m.%Y %H:%M')}
            🚀 Пріоритет: {task.get_priority_display()}

            Переглянути завдання: http://127.0.0.1:8000/core/tasks/{task.id}/

            Гарного дня!
            Команда Task Manager
            """

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            logger.info(f'Email sent to {user.email} about task {task.name}')

    except Exception as e:
        logger.error(f'Error sending task assignment email: {e}')


@shared_task
def send_task_deadline_reminder():
    """Нагадування про наближення дедлайну (запускати щодня)"""
    tomorrow = timezone.now() + timedelta(days=1)
    tasks = Task.objects.filter(
        deadline__date=tomorrow.date(),
        is_completed=False
    )

    for task in tasks:
        for user in task.assignees.all():
            if user.email:
                subject = f'⏰ Нагадування: Завдання "{task.name}" завтра!'
                message = f"""
                Нагадування!

                Завтра дедлайн завдання:

                📝 Назва: {task.name}
                📋 Проєкт: {task.project.name if task.project else "Без проєкту"}
                ⏰ Дедлайн: {task.deadline.strftime('%d.%m.%Y %H:%M')}

                Не забудьте завершити завдання вчасно!

                Посилання: http://127.0.0.1:8000/core/tasks/{task.id}/
                """

                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True,
                )


@shared_task
def send_project_update_email(project_id, message):
    """Надсилає оновлення по проєкту всім учасникам"""
    try:
        project = Project.objects.get(id=project_id)
        users = project.get_all_workers()

        for user in users:
            if user.email:
                subject = f'📢 Оновлення проєкту: {project.name}'

                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True,
                )

    except Exception as e:
        logger.error(f'Error sending project update email: {e}')


@shared_task
def send_daily_digest():
    """Щоденний дайджест завдань"""
    users = User.objects.filter(is_active=True)

    for user in users:
        if user.email:
            # Завдання користувача
            user_tasks = Task.objects.filter(assignees=user, is_completed=False)

            # Прострочені завдання
            overdue_tasks = [t for t in user_tasks if t.is_overdue]

            # Завдання на сьогодні
            today_tasks = [t for t in user_tasks if t.deadline.date() == timezone.now().date()]

            if user_tasks:
                subject = f'📊 Щоденний дайджест завдань'
                message = f"""
                Щоденний дайджест завдань:

                📌 Всього активних завдань: {user_tasks.count()}
                ⚠️ Прострочених: {len(overdue_tasks)}
                📅 На сьогодні: {len(today_tasks)}

                Гарного робочого дня!
                """

                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True,
                )
                
# core/periodic_tasks.py (створимо новий файл)
from celery import shared_task
from django_celery_beat.models import PeriodicTask, CrontabSchedule


@shared_task
def setup_periodic_tasks():
    """Налаштовує періодичні завдання"""

    # Очищення сесій щодня о 3 ночі
    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute='0',
        hour='3',
        day_of_week='*',
        day_of_month='*',
        month_of_year='*',
    )

    PeriodicTask.objects.get_or_create(
        crontab=schedule,
        name='Clear expired sessions daily',
        task='core.tasks.clear_expired_sessions',
    )

    # Нагадування про дедлайни щодня о 9 ранку
    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute='0',
        hour='9',
        day_of_week='*',
        day_of_month='*',
        month_of_year='*',
    )

    PeriodicTask.objects.get_or_create(
        crontab=schedule,
        name='Send deadline reminders',
        task='core.tasks.send_task_deadline_reminder',
    )

    # Щоденний дайджест о 8 ранку
    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute='0',
        hour='8',
        day_of_week='*',
        day_of_month='*',
        month_of_year='*',
    )

    PeriodicTask.objects.get_or_create(
        crontab=schedule,
        name='Send daily digest',
        task='core.tasks.send_daily_digest',
    )
    # Додамо в core/tasks.py
    from django.contrib.sessions.models import Session
    from django.utils import timezone

    @shared_task
    def clear_expired_sessions():
        """Очищення закінчених сесій"""
        try:
            expired_sessions = Session.objects.filter(expire_date__lt=timezone.now())
            count = expired_sessions.count()
            expired_sessions.delete()
            return f'Cleared {count} expired sessions'
        except Exception as e:
            return f'Error: {e}'
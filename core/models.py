from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from sorl.thumbnail import ImageField


class TaskType(models.Model):
    name = models.CharField(max_length=255)


class Position(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = "Посада"
        verbose_name_plural = "Посади"

class Worker(AbstractUser):
    position = models.ForeignKey(
        Position,
        on_delete=models.DO_NOTHING,
        related_name="workers"
    )
    avatar = ImageField(
        upload_to='media/',
        null=True,
        blank=True,
        verbose_name="Аватар"
    )

    @property
    def full_name(self):
        """Повне ім'я користувача"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    class Meta:
        verbose_name = "Працівник"
        verbose_name_plural = "Працівники"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.position})" if self.position else "-"


class Task(models.Model):
    class Priority(models.TextChoices):
        URGENT = "URGENT"
        HIGH = "HIGH"
        MEDIUM = "MEDIUM"
        LOW = "LOW"

    name = models.CharField(max_length=255)
    description = models.TextField()
    deadline = models.DateTimeField()
    is_completed = models.BooleanField(default=False)
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices
    )
    created_by = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_tasks"
    )
    task_type = models.ForeignKey(
        TaskType,
        on_delete=models.CASCADE,
        related_name="tasks"
    )
    project = models.ForeignKey(
        "Project",
        on_delete=models.CASCADE,
        related_name="tasks",
        null=True,
        blank=True
    )

    team = models.ForeignKey(
        "Team",
        on_delete=models.CASCADE,
        related_name="tasks",
        null=True,
        blank=True
    )
    assignees = models.ManyToManyField(
        Worker,
        related_name="tasks",
        blank=True
    )
    finished_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def save(
        self,
        *args,
        **kwargs
    ):
        # Якщо задача тільки що завершена
        if self.is_completed and not self.finished_at:
            self.finished_at = timezone.now()
        # Якщо задача знову стала невиконаною
        elif not self.is_completed and self.finished_at:
            self.finished_at = None

        super().save(*args, **kwargs)

    @property
    def days_until_deadline(self):
        """Залишилось днів до дедлайну"""
        from django.utils import timezone
        if self.deadline:
            delta = self.deadline.date() - timezone.now().date()
            return delta.days
        return None

    @property
    def is_overdue(self):
        """Чи прострочене завдання"""
        return not self.is_completed and self.days_until_deadline is not None and self.days_until_deadline < 0

    @property
    def priority_class(self):
        """CSS клас для пріоритету"""
        classes = {
            'LOW': 'priority-low',
            'MEDIUM': 'priority-medium',
            'HIGH': 'priority-high',
            'URGENT': 'priority-urgent',
        }
        return classes.get(self.priority, '')

class Team(models.Model):
    """Проста модель команди"""
    name = models.CharField(max_length=255, verbose_name="Назва команди")

    # Лідер команди (той хто створив)
    leader = models.ForeignKey(
        "Worker",
        on_delete=models.CASCADE,
        related_name='led_teams',
        verbose_name="Лідер"
    )

    # Учасники команди
    members = models.ManyToManyField(
        "Worker",
        related_name='teams',
        blank=True,
        verbose_name="Учасники"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = "Команда"
        verbose_name_plural = "Команди"


class Project(models.Model):
    STAGE_CHOICES = [
        ('planning', '📋 Планування'),
        ('development', '💻 Розробка'),
        ('testing', '🧪 Тестування'),
        ('deployment', '🚀 Деплой'),
        ('completed', '✅ Завершено'),
        ('on_hold', '⏸️ На паузі'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    owner = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True,
        related_name="owned_projects"
    )
    # Проєкт може мати декілька команд (M2M)
    teams = models.ManyToManyField(Team, related_name="projects", blank=True)
    stage = models.CharField(
        max_length=20,
        choices=STAGE_CHOICES,
        default='planning'
    )
    start_date = models.DateField(default=timezone.now)
    deadline = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    # Методи для шаблонів
    def get_active_tasks(self):
        return self.tasks.filter(is_completed=False)

    def get_completed_tasks(self):
        return self.tasks.filter(is_completed=True)

    def get_progress(self):
        total = self.tasks.count()
        if total == 0:
            return 0
        completed = self.get_completed_tasks().count()
        return int((completed / total) * 100)

    def get_all_workers(self):
        """Всі працівники, які залучені до проєкту (через команди)"""
        workers = set()
        for team in self.teams.all():
            workers.update(team.members.all())
        return list(workers)

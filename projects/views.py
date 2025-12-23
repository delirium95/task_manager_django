# projects/views.py
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Count, Q
from django.http import JsonResponse, HttpResponse
import csv
from datetime import datetime

from .forms import ProjectForm
from core.models import Project


class ProjectListView(LoginRequiredMixin, ListView):
    """Список всіх проєктів"""
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 10

    def get_queryset(self):
        queryset = Project.objects.all().order_by('-created_at')

        # Фільтрація за статусом
        status = self.request.GET.get('status', 'all')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)

        # Фільтрація за етапом
        stage = self.request.GET.get('stage')
        if stage:
            queryset = queryset.filter(stage=stage)

        # Пошук за назвою
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )

        # Фільтрація за власником
        owner = self.request.GET.get('owner')
        if owner:
            queryset = queryset.filter(owner_id=owner)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', 'all')
        context['search_query'] = self.request.GET.get('search', '')
        context['stages'] = Project.STAGE_CHOICES
        return context


class ProjectCreateView(LoginRequiredMixin, CreateView):
    """Створення нового проєкту"""
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'

    def get_success_url(self):
        messages.success(self.request, f'Проєкт "{self.object.name}" створено успішно!')
        return reverse_lazy('projects:detail', kwargs={'pk': self.object.pk})

    def get_initial(self):
        initial = super().get_initial()
        # Встановлюємо поточного користувача як власника за замовчуванням
        initial['owner'] = self.request.user
        return initial

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class ProjectDetailView(LoginRequiredMixin, DetailView):
    """Детальна сторінка проєкту"""
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object

        # Отримуємо завдання з фільтрами
        task_filter = self.request.GET.get('filter', 'all')
        if task_filter == 'completed':
            tasks = project.tasks.filter(is_completed=True)
        elif task_filter == 'active':
            tasks = project.tasks.filter(is_completed=False)
        elif task_filter == 'overdue':
            # Використовуємо Python-фільтрацію для is_overdue
            all_tasks = project.tasks.filter(is_completed=False)
            tasks = [task for task in all_tasks if task.is_overdue]
        else:
            tasks = project.tasks.all()

        # Сортування
        sort_by = self.request.GET.get('sort', 'deadline')
        if sort_by == 'priority':
            # Сортування по пріоритету в Python
            priority_order = {'URGENT': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
            tasks = sorted(tasks, key=lambda t: priority_order.get(t.priority, 4))
        elif sort_by == 'name':
            tasks = tasks.order_by('name')
        else:  # deadline за замовчуванням
            tasks = tasks.order_by('deadline')

        context['tasks'] = tasks
        context['task_filter'] = task_filter
        context['sort_by'] = sort_by

        # Статистика
        context['total_tasks'] = project.tasks.count()
        context['completed_tasks'] = project.get_completed_tasks().count()
        context['active_tasks'] = project.get_active_tasks().count()

        # Всі доступні працівники для призначення
        context['available_workers'] = project.get_all_workers()

        return context


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    """Редагування проєкту"""
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'

    def get_success_url(self):
        messages.success(self.request, f'Проєкт "{self.object.name}" оновлено!')
        return reverse_lazy('projects:detail', kwargs={'pk': self.object.pk})

    def dispatch(self, request, *args, **kwargs):
        # Перевіряємо, чи користувач є власником або суперюзером
        project = self.get_object()
        if not (request.user == project.owner or request.user.is_superuser):
            messages.error(request, 'Ви не маєте дозволу редагувати цей проєкт')
            return redirect('projects:detail', pk=project.pk)
        return super().dispatch(request, *args, **kwargs)


class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    """Видалення проєкту"""
    model = Project
    template_name = 'projects/project_confirm_delete.html'
    success_url = reverse_lazy('projects:list')

    def dispatch(self, request, *args, **kwargs):
        project = self.get_object()
        if not (request.user == project.owner or request.user.is_superuser):
            messages.error(request, 'Ви не маєте дозволу видаляти цей проєкт')
            return redirect('projects:detail', pk=project.pk)
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        project = self.get_object()
        messages.success(request, f'Проєкт "{project.name}" видалено!')
        return super().delete(request, *args, **kwargs)


# ===== ДОДАТКОВІ VIEWS =====

class ProjectToggleActiveView(LoginRequiredMixin, UpdateView):
    """Швидке перемикання активності проєкту"""
    model = Project
    fields = []  # Не потрібні поля

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.is_active = not self.object.is_active
        self.object.save()

        status = "активовано" if self.object.is_active else "деактивовано"
        messages.success(request, f'Проєкт "{self.object.name}" {status}!')

        return redirect('projects:detail', pk=self.object.pk)


class ProjectChangeStageView(LoginRequiredMixin, UpdateView):
    """Швидка зміна етапу проєкту"""
    model = Project
    fields = []  # Не потрібні поля

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        new_stage = request.POST.get('stage')

        if new_stage in dict(Project.STAGE_CHOICES):
            self.object.stage = new_stage
            self.object.save()
            messages.success(request, f'Етап проєкту змінено на "{self.object.get_stage_display()}"')

        return redirect('projects:detail', pk=self.object.pk)


class ProjectAddTeamView(LoginRequiredMixin, UpdateView):
    """Додавання команди до проєкту"""
    model = Project
    fields = []  # Не потрібні поля

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        team_id = request.POST.get('team_id')

        try:
            team = Team.objects.get(id=team_id)
            self.object.teams.add(team)
            messages.success(request, f'Команду "{team.name}" додано до проєкту!')
        except Team.DoesNotExist:
            messages.error(request, 'Команду не знайдено')

        return redirect('projects:detail', pk=self.object.pk)


class ProjectRemoveTeamView(LoginRequiredMixin, UpdateView):
    """Видалення команди з проєкту"""
    model = Project
    fields = []  # Не потрібні поля

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        team_id = kwargs.get('team_id')

        try:
            team = Team.objects.get(id=team_id)
            self.object.teams.remove(team)
            messages.success(request, f'Команду "{team.name}" видалено з проєкту!')
        except Team.DoesNotExist:
            messages.error(request, 'Команду не знайдено')

        return redirect('projects:detail', pk=self.object.pk)


class ExportProjectTasksView(LoginRequiredMixin, DetailView):
    """Експорт завдань проєкту в CSV"""
    model = Project

    def get(self, request, *args, **kwargs):
        project = self.get_object()

        # Створюємо HTTP-відповідь з типом CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{project.name}_tasks_{datetime.now().date()}.csv"'

        writer = csv.writer(response)
        # Заголовки
        writer.writerow([
            'Назва', 'Опис', 'Тип', 'Пріоритет',
            'Дедлайн', 'Статус', 'Виконавці', 'Створено'
        ])

        # Дані
        for task in project.tasks.all():
            assignees = ', '.join([str(a) for a in task.assignees.all()])
            status = 'Виконано' if task.is_completed else 'Активне'

            writer.writerow([
                task.name,
                task.description[:100],  # Обрізаємо довгий опис
                task.task_type.name if task.task_type else '',
                task.get_priority_display(),
                task.deadline.strftime('%d.%m.%Y %H:%M'),
                status,
                assignees,
                task.created_at.strftime('%d.%m.%Y')
            ])

        return response


class ProjectStatsView(LoginRequiredMixin, DetailView):
    """Статистика проєкту (можна для JSON API)"""
    model = Project

    def get(self, request, *args, **kwargs):
        project = self.get_object()

        # Статистика по завданнях
        tasks_by_priority = project.tasks.values('priority').annotate(count=Count('id'))
        tasks_by_status = {
            'total': project.tasks.count(),
            'completed': project.get_completed_tasks().count(),
            'active': project.get_active_tasks().count(),
            'overdue': len([t for t in project.tasks.filter(is_completed=False) if t.is_overdue])
        }

        # Статистика по командах
        teams_stats = []
        for team in project.teams.all():
            team_tasks = project.tasks.filter(team=team)
            teams_stats.append({
                'name': team.name,
                'members': team.members.count(),
                'tasks': team_tasks.count(),
                'completed': team_tasks.filter(is_completed=True).count()
            })

        data = {
            'project': {
                'name': project.name,
                'stage': project.get_stage_display(),
                'progress': project.get_progress(),
                'days_left': (project.deadline - datetime.now().date()).days if project.deadline else None
            },
            'tasks': tasks_by_status,
            'priority_distribution': list(tasks_by_priority),
            'teams': teams_stats
        }

        if request.headers.get('Accept') == 'application/json':
            return JsonResponse(data)

        # Для HTML рендерингу
        context = self.get_context_data(**kwargs)
        context['stats'] = data
        return self.render_to_response(context)


class ProjectTasksAPIView(LoginRequiredMixin, DetailView):
    """API для отримання завдань проєкту (для AJAX)"""
    model = Project

    def get(self, request, *args, **kwargs):
        project = self.get_object()
        filter_status = request.GET.get('status', 'all')

        if filter_status == 'completed':
            tasks = project.tasks.filter(is_completed=True)
        elif filter_status == 'active':
            tasks = project.tasks.filter(is_completed=False)
        else:
            tasks = project.tasks.all()

        # Формуємо JSON відповідь
        tasks_data = []
        for task in tasks:
            tasks_data.append({
                'id': task.id,
                'name': task.name,
                'description': task.description[:100],
                'priority': task.get_priority_display(),
                'deadline': task.deadline.strftime('%d.%m.%Y %H:%M'),
                'is_completed': task.is_completed,
                'is_overdue': task.is_overdue,
                'assignees': [{'id': a.id, 'name': str(a)} for a in task.assignees.all()],
                'type': task.task_type.name if task.task_type else None
            })

        return JsonResponse({
            'project': project.name,
            'tasks': tasks_data,
            'count': len(tasks_data)
        })

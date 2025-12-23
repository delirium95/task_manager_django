# core/views.py (або tasks/views.py)
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DetailView, DeleteView, ListView

from .forms import TaskForm, TaskUpdateForm
from .models import Task
from .tasks import send_task_assignment_email


class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'core/task_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Передаємо project_id з GET параметрів або з форми
        project_id = self.request.GET.get('project') or self.request.POST.get('project')
        if project_id:
            kwargs['project_id'] = project_id
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial['is_completed'] = False
        initial['created_by'] = self.request.user
        return initial

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        if form.cleaned_data.get('assignees'):
            user_ids = [user.id for user in form.cleaned_data['assignees']]
            send_task_assignment_email.delay(self.object.id, user_ids)
        messages.success(self.request, 'Завдання створено!')
        messages.success(self.request, f'Завдання "{form.instance.name}" створено!')
        return response

    def get_success_url(self):
        # Повертаємо на сторінку проєкту, якщо він є
        if self.object.project:
            return reverse_lazy('projects:detail', kwargs={'pk': self.object.project.id})
        return reverse_lazy('tasks:list')


class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskUpdateForm
    template_name = 'core/task_form.html'

    def get_success_url(self):
        if self.object.project:
            return reverse_lazy('projects:detail', kwargs={'pk': self.object.project.id})
        return reverse_lazy('tasks:detail', kwargs={'pk': self.object.id})


class TaskCompleteView(LoginRequiredMixin, UpdateView):
    """Швидке завершення завдання"""
    model = Task
    fields = []  # Не потрібні поля

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.is_completed = True
        self.object.save()

        messages.success(request, f'Завдання "{self.object.name}" виконано!')

        if self.object.project:
            return redirect('projects:detail', pk=self.object.project.id)
        return redirect('tasks:detail', pk=self.object.id)


class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'core/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 20

    def get_queryset(self):
        queryset = Task.objects.all()

        # Фільтрація за статусом
        status = self.request.GET.get('status', 'all')
        if status == 'completed':
            queryset = queryset.filter(is_completed=True)
        elif status == 'active':
            queryset = queryset.filter(is_completed=False)
        elif status == 'overdue':
            queryset = queryset.filter(is_completed=False, deadline__lt=timezone.now())

        # Фільтрація за пріоритетом
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

        # Пошук
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )

        # Сортування
        sort_by = self.request.GET.get('sort', '-deadline')
        if sort_by in ['name', 'deadline', 'priority', '-name', '-deadline', '-priority']:
            queryset = queryset.order_by(sort_by)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', 'all')
        context['search_query'] = self.request.GET.get('search', '')
        context['sort_by'] = self.request.GET.get('sort', '-deadline')
        return context


class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = 'core/task_detail.html'
    context_object_name = 'task'


class TaskDeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    template_name = 'core/task_confirm_delete.html'

    def get_success_url(self):
        if self.object.project:
            return reverse_lazy('projects:detail', kwargs={'pk': self.object.project.id})
        return reverse_lazy('core:task_list')

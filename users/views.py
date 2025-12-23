from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import FormView, DetailView, UpdateView

from core.models import Worker, Task, Team
from users.forms import SignUpForm, WorkerUpdateForm


class SignUpView(FormView):
    form_class = SignUpForm
    template_name = "registration/sign_up.html"
    success_url = reverse_lazy("users:login")
    def form_valid(self, form):
        with transaction.atomic():
            user = form.save()
        return super().form_valid(form)


class ProfileDetailView(LoginRequiredMixin, DetailView):
    """Перегляд профілю"""
    model = Worker
    template_name = 'workers/profile_detail.html'
    context_object_name = 'profile_user'

    def get_object(self):
        # Якщо в URL є username - показуємо того користувача
        # Якщо немає - показуємо поточного
        username = self.kwargs.get('username')
        if username:
            return get_object_or_404(Worker, username=username)
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object

        # Статистика задач
        tasks_stats = Task.objects.filter(assignees=user).aggregate(
            total=Count('id'),
            completed=Count('id', filter=Q(is_completed=True)),
            in_progress=Count('id', filter=Q(is_completed=False))
        )

        # Останні 5 активних задач
        recent_tasks = Task.objects.filter(
            assignees=user,
            is_completed=False
        ).order_by('-deadline')[:5]

        # Команди користувача
        user_teams = Team.objects.filter(members=user)

        # Проєкти через команди
        user_projects = set()
        for team in user_teams:
            user_projects.update(team.projects.all())

        context.update({
            'tasks_stats': tasks_stats,
            'recent_tasks': recent_tasks,
            'user_teams': user_teams,
            'user_projects': user_projects,
            'is_own_profile': self.request.user == user,
        })
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Єдиний view для оновлення профілю"""
    model = get_user_model()
    form_class = WorkerUpdateForm
    template_name = 'workers/profile_update.html'
    success_url = reverse_lazy('users:profile')

    def get_object(self, queryset = ...):
        if self.request.user:
            return self.request.user
        else:
            raise Exception("ERROR")

    def form_valid(self, form):
        """Обробка форми"""
        response = super().form_valid(form)
        # Можна додати повідомлення про успіх
        from django.contrib import messages
        messages.success(self.request, 'Профіль оновлено!')
        return response
# teams/views.py
from django.views import View
from django.views.generic import (
    CreateView, ListView, DetailView,
    UpdateView, DeleteView, FormView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages

from core.models import Team, Worker
from teams.forms import TeamCreateForm, TeamUpdateForm, TeamAddMembersForm


class TeamListView(LoginRequiredMixin, ListView):
    """Список команд, де користувач є учасником"""
    model = Team
    template_name = 'teams/team_list.html'
    context_object_name = 'teams'

    def get_queryset(self):
        # Показуємо тільки команди, де користувач є учасником
        return Team.objects.filter(members=self.request.user).order_by('name')


class TeamCreateView(LoginRequiredMixin, CreateView):
    """Створення нової команди"""
    model = Team
    form_class = TeamCreateForm
    template_name = 'teams/team_create.html'
    success_url = reverse_lazy('teams:team_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['creator'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f'Команду "{form.instance.name}" створено!')
        return super().form_valid(form)


class TeamDetailView(LoginRequiredMixin, DetailView):
    """Детальний перегляд команди"""
    model = Team
    template_name = 'teams/team_detail.html'
    context_object_name = 'team'

    def get_queryset(self):
        # Тільки команди, де користувач є учасником
        return Team.objects.filter(members=self.request.user)


class TeamUpdateView(LoginRequiredMixin, UpdateView):
    """Редагування команди (тільки лідер)"""
    model = Team
    form_class = TeamUpdateForm
    template_name = 'teams/team_form.html'

    def get_queryset(self):
        # Тільки команди, де користувач є лідером
        return Team.objects.filter(leader=self.request.user)

    def get_success_url(self):
        messages.success(self.request, 'Команду оновлено!')
        return reverse_lazy('teams:team_detail', kwargs={'pk': self.object.pk})


class TeamDeleteView(LoginRequiredMixin, DeleteView):
    """Видалення команди (тільки лідер)"""
    model = Team
    template_name = 'teams/team_confirm_delete.html'
    success_url = reverse_lazy('teams:team_list')

    def get_queryset(self):
        # Тільки команди, де користувач є лідером
        return Team.objects.filter(leader=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Команду видалено!')
        return super().delete(request, *args, **kwargs)


class TeamAddMembersView(LoginRequiredMixin, FormView):
    """Додавання учасників до команди"""
    form_class = TeamAddMembersForm
    template_name = 'teams/team_add_members.html'

    def dispatch(self, request, *args, **kwargs):
        # Перевіряємо, що користувач є лідером команди
        self.team = get_object_or_404(Team, pk=self.kwargs['pk'])
        if self.team.leader != request.user:
            messages.error(request, 'Тільки лідер може додавати учасників!')
            return redirect('teams:team_detail', pk=self.team.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['team'] = self.team
        kwargs['current_user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team'] = self.team
        return context

    def form_valid(self, form):
        # Додаємо обраних користувачів до команди
        users = form.cleaned_data['users']
        self.team.members.add(*users)

        messages.success(
            self.request,
            f'Додано {len(users)} учасників до команди!'
        )
        return redirect('teams:team_detail', pk=self.team.pk)


class TeamRemoveMemberView(LoginRequiredMixin, View):
    """Видалення учасника з команди"""

    def post(self, request, pk, user_id):
        team = get_object_or_404(Team, pk=pk, members=request.user)
        user_to_remove = get_object_or_404(Worker, pk=user_id)

        # Перевіряємо права: тільки лідер може видаляти, або сам користувач
        if request.user == team.leader or request.user == user_to_remove:
            team.members.remove(user_to_remove)
            messages.success(request, f'Користувача видалено з команди!')
        else:
            messages.error(request, 'Ви не можете видалити цього користувача!')

        return redirect('teams:team_detail', pk=team.pk)
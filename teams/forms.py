# teams/forms.py
from django import forms
from core.models import Worker, Team


class TeamCreateForm(forms.ModelForm):
    """Форма для створення команди"""

    class Meta:
        model = Team
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Назва команди'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.creator = kwargs.pop('creator', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        team = super().save(commit=False)
        if self.creator:
            team.leader = self.creator

        if commit:
            team.save()
            # Автоматично додаємо творця в учасники
            team.members.add(self.creator)

        return team


class TeamAddMembersForm(forms.Form):
    """Проста форма для додавання учасників"""
    users = forms.ModelMultipleChoiceField(
        queryset=Worker.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        label="Оберіть користувачів"
    )

    def __init__(self, *args, **kwargs):
        self.team = kwargs.pop('team', None)
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)

        if self.team and self.current_user:
            # Показуємо всіх користувачів, крім тих, хто вже в команді
            self.fields['users'].queryset = Worker.objects.exclude(
                id__in=self.team.members.values_list('id', flat=True)
            ).exclude(id=self.current_user.id).order_by('email')


class TeamUpdateForm(forms.ModelForm):
    """Форма для редагування команди (лише лідер)"""

    class Meta:
        model = Team
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }
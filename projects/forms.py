# projects/forms.py
from django import forms
from django.utils import timezone
from core.models import Worker, Team, Project


class ProjectForm(forms.ModelForm):
    teams = forms.ModelMultipleChoiceField(
        queryset=Team.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Команди"
    )

    start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        initial=timezone.now().date()
    )

    deadline = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        required=False
    )

    class Meta:
        model = Project
        fields = [
            'name', 'description', 'owner',
            'teams', 'stage', 'start_date',
            'deadline', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Назва проєкту'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Опис проєкту'
            }),
            'owner': forms.Select(attrs={
                'class': 'form-select'
            }),
            'stage': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Якщо поле owner не було встановлено в widgets, додаємо клас тут
        if 'owner' not in self.fields:
            self.fields['owner'] = forms.ModelChoiceField(
                queryset=Worker.objects.all(),
                widget=forms.Select(attrs={'class': 'form-select'}),
                required=False,
                label="Власник"
            )
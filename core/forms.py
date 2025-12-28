# core/forms.py - ВИПРАВЛЕНА ВЕРСІЯ
from django import forms
from django.utils import timezone
from .models import Task, TaskType, Project, Team, Worker


class TaskForm(forms.ModelForm):
    deadline = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control'
        }),
        input_formats=['%Y-%m-%dT%H:%M'],
        initial=timezone.now() + timezone.timedelta(days=7)
    )

    class Meta:
        model = Task
        fields = [
            'name', 'description', 'deadline',
            'priority', 'task_type', 'project',
            'team', 'assignees'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'task_type': forms.Select(attrs={'class': 'form-select'}),
            'project': forms.Select(attrs={'class': 'form-select'}),
            'team': forms.Select(attrs={'class': 'form-select'}),
            'assignees': forms.SelectMultiple(attrs={'class': 'form-control', 'size': 5}),
        }

    def __init__(self, *args, **kwargs):
        project_id = kwargs.pop('project_id', None)
        super().__init__(*args, **kwargs)

        # Обмежуємо вибір проектів тільки активними
        self.fields['project'].queryset = Project.objects.filter(is_active=True)
        self.fields['task_type'].queryset = TaskType.objects.all()
        self.fields['team'].queryset = Team.objects.all()
        self.fields['assignees'].queryset = Worker.objects.all()

        # Якщо передано project_id, обмежуємо вибір
        if project_id:
            try:
                project = Project.objects.get(id=project_id)
                self.fields['project'].initial = project
                self.fields['team'].queryset = project.teams.all()

                # Отримуємо всіх працівників проекту через команди
                project_workers = set()
                for team in project.teams.all():
                    project_workers.update(team.members.all())
                self.fields['assignees'].queryset = Worker.objects.filter(id__in=[w.id for w in project_workers])
            except Project.DoesNotExist:
                pass


class TaskUpdateForm(TaskForm):
    class Meta:
        model = Task
        fields = [
            'name', 'description', 'deadline',
            'priority', 'task_type', 'project',
            'team', 'assignees', 'is_completed'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'task_type': forms.Select(attrs={'class': 'form-select'}),
            'project': forms.Select(attrs={'class': 'form-select'}),
            'team': forms.Select(attrs={'class': 'form-select'}),
            'assignees': forms.SelectMultiple(attrs={'class': 'form-control', 'size': 5}),
            'is_completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
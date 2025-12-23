# projects/urls.py
from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'projects'

urlpatterns = [
    # Головна сторінка проєктів
    path('', views.ProjectListView.as_view(), name='list'),

    # Створення нового проєкту
    path('create/', views.ProjectCreateView.as_view(), name='create'),

    # Детальна сторінка проєкту
    path('<int:pk>/', views.ProjectDetailView.as_view(), name='detail'),

    # Редагування проєкту
    path('<int:pk>/update/', views.ProjectUpdateView.as_view(), name='update'),

    # Видалення проєкту
    path('<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='delete'),

    # Архівація/активація проєкту
    path('<int:pk>/toggle-active/', views.ProjectToggleActiveView.as_view(), name='toggle-active'),

    # Зміна етапу проєкту
    path('<int:pk>/change-stage/', views.ProjectChangeStageView.as_view(), name='change-stage'),

    # Додавання команди до проєкту
    path('<int:pk>/add-team/', views.ProjectAddTeamView.as_view(), name='add-team'),

    # Видалення команди з проєкту
    path('<int:pk>/remove-team/<int:team_id>/', views.ProjectRemoveTeamView.as_view(), name='remove-team'),

    # Експорт завдань проєкту
    path('<int:pk>/export-tasks/', views.ExportProjectTasksView.as_view(), name='export-tasks'),

    # Статистика проєкту
    path('<int:pk>/stats/', views.ProjectStatsView.as_view(), name='stats'),

    # API ендпоінти (якщо потрібно)
    path('api/<int:pk>/tasks/', views.ProjectTasksAPIView.as_view(), name='api-tasks'),

    # Перенаправлення для старої адреси
    path('details/<int:pk>/', RedirectView.as_view(pattern_name='projects:detail', permanent=True)),
]
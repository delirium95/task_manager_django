# teams/urls.py
from django.urls import path
from . import views

app_name = 'teams'

urlpatterns = [
    path('', views.TeamListView.as_view(), name='team_list'),
    path('create/', views.TeamCreateView.as_view(), name='team_create'),
    path('<int:pk>/', views.TeamDetailView.as_view(), name='team_detail'),
    path('<int:pk>/update/', views.TeamUpdateView.as_view(), name='team_update'),
    path('<int:pk>/delete/', views.TeamDeleteView.as_view(), name='team_delete'),
    path('<int:pk>/add-members/', views.TeamAddMembersView.as_view(), name='team_add_members'),
    path('<int:pk>/remove-member/<int:user_id>/', views.TeamRemoveMemberView.as_view(), name='team_remove_member'),
]
# todo
# 1. celery + redis => queue for sending emails task
# 2. celery beat clear sessions
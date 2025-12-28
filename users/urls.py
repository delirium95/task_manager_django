from django.urls import path, include
from users.views import SignUpView, ProfileDetailView, ProfileUpdateView

app_name = "users"

urlpatterns = [
    path("sign-up/", SignUpView.as_view(), name="sign-up"),
    path("", include("django.contrib.auth.urls")),
    path('profile/', ProfileDetailView.as_view(), name='profile'),
    path('profile/<str:username>/', ProfileDetailView.as_view(), name='profile_detail'),
    path('profile/my/update/', ProfileUpdateView.as_view(), name='profile_update'),

]
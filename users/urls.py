from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views
from .forms import CustomPasswordResetForm, CustomSetPasswordForm

app_name = "users"

urlpatterns = [
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("password-reset/", views.simple_password_reset, name="password_reset"),
    path(
        "password-reset/code/<str:email>/",
        views.enter_verification_code,
        name="enter_code",
    ),
    path(
        "password-reset/new-password/<int:user_id>/",
        views.new_password,
        name="new_password",
    ),
    path("quick-logout/", views.quick_logout, name="quick_logout"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("password-reset/", views.password_reset, name="password_reset"),
    path("profile/", views.AccountDetailView.as_view(), name="profile"),
    path("profile/edit/", views.AccountUpdateView.as_view(), name="user_update"),
    path("profile/delete/", views.AccountDeleteView.as_view(), name="confirm_delete"),
    path("lectors/", views.LectorListView.as_view(), name="lector_list"),
    path("profile/<int:pk>/", views.PublicProfileView.as_view(), name="public_profile"),
]

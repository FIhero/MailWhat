import os
import random
import string

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import (
    DeleteView,
    DetailView,
    FormView,
    ListView,
    UpdateView,
)

from config import settings

from .forms import CustomAuthenticationForm, UserRegistrationForm, UserUpdateForm
from .models import User


class CustomLoginView(LoginView):
    """Инициализирует страницу входа"""

    template_name = "users/login.html"
    form_class = CustomAuthenticationForm
    success_url = "/"


class RegisterView(FormView):
    """Регистрация нового пользователя"""

    template_name = "users/register.html"
    form_class = UserRegistrationForm
    success_url = reverse_lazy("users:login")

    def form_valid(self, form):
        """Создание пользователя и отправка приветственного письма"""
        user = form.save()

        try:
            send_mail(
                "Добро пожаловать в WS!",
                "Спасибо за регистрацию на нашей платформе вебинаров и рассылок.",
                os.getenv("EMAIL_HOST_USER"),
                [user.email],
                fail_silently=False,
            )
        except Exception:
            pass

        messages.success(
            self.request, "Регистрация прошла успешно! Теперь вы можете войти."
        )
        return super().form_valid(form)


class PublicProfileView(DetailView):
    """Показывает профиль лектора"""

    model = User
    template_name = "users/public_profile.html"
    context_object_name = "profile_user"

    def get_queryset(self):
        return User.objects.filter(role__in=["lector"])


class AccountDetailView(LoginRequiredMixin, DetailView):
    """Показывает детали пользователя"""

    model = User
    template_name = "users/user_detail.html"

    def get_object(self, queryset=None):
        """Показывает информацию пользователя"""
        try:
            return self.request.user
        except User.DoesNotExist:
            raise Http404("Пользователь не найден")


class AccountUpdateView(LoginRequiredMixin, UpdateView):
    """Инициализирует страницу для обновления информации о пользователе"""

    model = User
    form_class = UserUpdateForm  # Используем форму, а не модель
    template_name = "users/user_form.html"
    success_url = reverse_lazy("users:profile")

    def get_object(self, queryset=None):
        """Получаем текущего пользователя"""
        return self.request.user

    def form_valid(self, form):
        """Сохраняем данные и показываем сообщение об успехе"""
        response = super().form_valid(form)
        messages.success(self.request, "Профиль успешно обновлен!")
        return response


class AccountDeleteView(LoginRequiredMixin, DeleteView):
    """Инициализирует страницу для удаления пользователя"""

    model = User
    template_name = "users/user_confirm_delete.html"
    success_url = reverse_lazy("home")

    def get_object(self, queryset=None):
        return self.request.user


@login_required
def logout_view(request):
    if request.method == "POST":
        logout(request)
        messages.info(request, "Вы успешно вышли из системы. Возвращайтесь скорее!")
        return redirect("mailing:home")

    return render(request, "users/logout.html")


@login_required
def quick_logout(request):
    logout(request)
    messages.info(request, "Вы успешно вышли из системы.")
    return redirect("users:login")


def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user = authenticate(
                request, username=user.email, password=form.cleaned_data["password1"]
            )
            if user is not None:
                login(request, user)
                messages.success(request, f"Аккаунт создан для {user.email}!")
                return redirect("mailings:mailing_list")
    else:
        form = UserRegistrationForm()
    return render(request, "users/register.html", {"form": form})


@login_required
def profile(request):
    return render(request, "users/user_detail.html")


def password_reset(request):
    return render(request, "users/password_reset.html")


verification_codes = {}


def generate_verification_code():
    """Генерирует 6-значный код"""
    return "".join(random.choices(string.digits, k=6))


def simple_password_reset(request):
    """Сброс пароля шаг 1: ввод email"""
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            user = User.objects.get(email=email)

            code = generate_verification_code()

            verification_codes[email] = {"code": code, "user_id": user.id}

            send_mail(
                subject="Код для сброса пароля - Webinar Service",
                message=f"Ваш код для сброса пароля: {code}\n\nКод действителен 10 минут.",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )

            # Переходим на страницу ввода кода
            return redirect("users:enter_code", email=email)

        except User.DoesNotExist:
            messages.error(request, "Пользователь с таким email не найден")

    return render(request, "users/password_reset.html")


def enter_verification_code(request, email):
    """Шаг 2: ввод кода подтверждения"""
    if request.method == "POST":
        entered_code = request.POST.get("code")

        if email in verification_codes:
            stored_code = verification_codes[email]["code"]

            if entered_code == stored_code:
                user_id = verification_codes[email]["user_id"]
                return redirect("users:new_password", user_id=user_id)
            else:
                return render(
                    request,
                    "users/code_verification.html",
                    {"email": email, "error": "Неверный код"},
                )
        else:
            return render(
                request,
                "users/code_verification.html",
                {"email": email, "error": "Код устарел или не существует"},
            )

    return render(request, "users/code_verification.html", {"email": email})


def new_password(request, user_id):
    """Шаг 3: ввод нового пароля"""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "Пользователь не найден")
        return redirect("users:password_reset")

    if request.method == "POST":
        new_password1 = request.POST.get("new_password1")
        new_password2 = request.POST.get("new_password2")

        if new_password1 and new_password2:
            if new_password1 == new_password2:
                user.set_password(new_password1)
                user.save()

                for email, data in list(verification_codes.items()):
                    if data["user_id"] == user_id:
                        del verification_codes[email]
                        break

                messages.success(
                    request, "Пароль успешно изменен! Теперь вы можете войти."
                )
                return redirect("users:login")
            else:
                messages.error(request, "Пароли не совпадают")
        else:
            messages.error(request, "Заполните оба поля")

    return render(request, "users/new_password.html", {"user": user})


@login_required
def change_password(request):
    """Смена пароля из профиля"""
    if request.method == "POST":
        current_password = request.POST.get("current_password")
        new_password1 = request.POST.get("new_password1")
        new_password2 = request.POST.get("new_password2")

        if not request.user.check_password(current_password):
            messages.error(request, "Текущий пароль неверен")
            return redirect("users:profile")

        if not new_password1 or not new_password2:
            messages.error(request, "Заполните все поля")
            return redirect("users:profile")

        if new_password1 != new_password2:
            messages.error(request, "Новые пароли не совпадают")
            return redirect("users:profile")

        if len(new_password1) < 8:
            messages.error(request, "Пароль должен быть не менее 8 символов")
            return redirect("users:profile")

        request.user.set_password(new_password1)
        request.user.save()

        update_session_auth_hash(request, request.user)

        messages.success(request, "✅ Пароль успешно изменен!")
        return redirect("users:profile")

    return redirect("users:profile")


class LectorListView(ListView):
    """Показывает список лекторов"""

    model = User
    template_name = "webinar/lector_list.html"
    context_object_name = "lectors"

    def get_queryset(self):
        return User.objects.filter(role="lector")

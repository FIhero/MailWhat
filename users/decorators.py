from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def login_required_message(function=None):
    """Декоратор для проверки аутентификации с сообщением"""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(
                    request, "❌ Для доступа к этой странице необходимо войти в систему"
                )
                return redirect("users:login")
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    if function:
        return decorator(function)
    return decorator


def user_required(function=None):
    """Декоратор для проверки роли пользователя"""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "❌ Для доступа необходимо войти в систему")
                return redirect("users:login")

            if request.user.role != "user":
                messages.error(request, "❌ Доступ разрешен только пользователям")
                return redirect("mailing:home")

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    if function:
        return decorator(function)
    return decorator


def manager_required(function=None):
    """Декоратор для проверки роли менеджера"""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "❌ Для доступа необходимо войти в систему")
                return redirect("users:login")

            if request.user.role != "manager":
                messages.error(request, "❌ Доступ разрешен только менеджерам")
                return redirect("mailing:home")

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    if function:
        return decorator(function)
    return decorator

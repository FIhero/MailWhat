from django.contrib import messages
from django.shortcuts import redirect


class AccessControlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request):
        """Список доступных ссылок"""
        public_urls = [
            "home",
            "login",
            "register",
            "password_reset",
            "enter_code",
            "new_password",
            "lector_list",
            "public_profile",
            "password_reset_done",
            "password_reset_confirm",
            "password_reset_complete",
        ]

        url_name = request.resolver_match.url_name if request.resolver_match else None

        if url_name in public_urls:
            return None

        if not request.user.is_authenticated:
            messages.error(
                request, "❌ Для доступа к этой странице необходимо войти в систему"
            )
            return redirect("users:login")

        return self.check_user_permissions(request, url_name)

    def check_user_permissions(self, request, url_name):
        user = request.user

        # URLs доступные только менеджерам
        manager_urls = [
            "user_management",
            "ban_user",
        ]

        # URLs доступные только пользователям
        user_urls = [
            "client_list",
            "client_create",
            "client_update",
            "client_delete",
            "message_list",
            "message_create",
            "message_update",
            "message_delete",
            "unsent_messages",
            "mailing_list",
            "mailing_create",
            "mailing_update",
            "mailing_delete",
            "mailing_send",
            "attempt_list",
            "attempt_details",
            "profile",
            "user_update",
            "change_password",
            "logout",
        ]

        # URLs доступные только лекторам
        lector_urls = []

        if user.role != "manager" and url_name in manager_urls:
            messages.error(request, "❌ Доступ запрещен. Требуются права менеджера.")
            return redirect("mailing:home")

        if user.role == "user" and url_name in lector_urls:
            messages.error(request, "❌ Доступ запрещен. Требуются права лектора.")
            return redirect("mailing:home")

        if user.role == "lector" and url_name in user_urls:
            messages.error(
                request, "❌ Доступ запрещен. Лекторы не могут управлять рассылками."
            )
            return redirect("mailing:home")

        return None

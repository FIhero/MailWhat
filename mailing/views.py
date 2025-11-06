import json

from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
)
from django.core.cache import cache

from mailing.forms import MailingForm, MessageForm
from mailing.models import Client, Mailing, MailingAttempt, MailingTime, Message
from mailing.services import send_mailing_service
from .mixins import UserRoleQuerysetMixin, OwnerAutoSetMixin, CacheInvalidationMixin, CacheMixin


def invalidate_user_cache(user):
    """Очистка кэша для пользователя"""
    if hasattr(cache, 'delete_pattern'):
        patterns = [
            f"*user_{user.id}*",
            f"*role_{user.role}*",
        ]
        for pattern in patterns:
            cache.delete_pattern(pattern)
    else:
        cache_keys = [
            f"HomeView_user_{user.id}_role_{user.role}",
            f"ClientListView_user_{user.id}_role_{user.role}",
            f"MessageListView_user_{user.id}_role_{user.role}",
            f"MailingListView_user_{user.id}_role_{user.role}",
            f"MailingAttemptListView_user_{user.id}_role_{user.role}",
        ]
        for key in cache_keys:
            cache.delete(key)


class HomeView(CacheMixin, TemplateView):
    """Главная страница"""

    template_name = "mailing/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Для неавторизованных пользователей
        if not user.is_authenticated:
            return context

        # Для менеджеров - общая статистика
        if user.role == "manager":
            context["total_mailings"] = Mailing.objects.count()
            context["active_mailings"] = Mailing.objects.filter(
                status="started"
            ).count()
            context["unique_clients"] = Client.objects.count()

        # Для обычных пользователей - личная статистика
        elif user.role == "user":
            context["total_mailings"] = Mailing.objects.filter(owner=user).count()
            context["active_mailings"] = Mailing.objects.filter(
                owner=user, status="started"
            ).count()
            context["total_messages"] = Message.objects.filter(owner=user).count()

        # Для лекторов - статистика по вебинарам (пока раздумывается)
        elif user.role == "lector":
            context["webinar_stats"] = {
                "total_webinars": 0,
                "unique_participants": 0,
                "upcoming_webinars": 0,
            }

        return context


class ClientListView(CacheMixin, UserRoleQuerysetMixin, ListView):
    """Контролер страницы списка клиентов"""

    model = Client
    template_name = "mailing/client_list.html"
    context_object_name = "clients"
    # paginate_by = 18
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()

        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                Q(full_name__icontains=query)
                | Q(email__icontains=query)
                | Q(comment__icontains=query)
            )

        filter_type = self.request.GET.get("filter", "all")
        if filter_type == "with_comments":
            queryset = queryset.exclude(comment__exact="").exclude(comment__isnull=True)
        elif filter_type == "without_comments":
            queryset = queryset.filter(Q(comment__exact="") | Q(comment__isnull=True))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        clients = Client.objects.all()

        query = self.request.GET.get("q")
        if query:
            clients = clients.filter(
                Q(full_name__icontains=query)
                | Q(email__icontains=query)
                | Q(comment__icontains=query)
            )

        current_filter = self.request.GET.get("filter", "all")

        context.update(
            {
                "current_filter": current_filter,
                "query": query,
                "all_count": clients.count(),
                "with_comments_count": clients.exclude(comment__exact="")
                .exclude(comment__isnull=True)
                .count(),
                "without_comments_count": clients.filter(
                    Q(comment__exact="") | Q(comment__isnull=True)
                ).count(),
            }
        )


        return context


class ClientCreateView(OwnerAutoSetMixin, CacheInvalidationMixin, CreateView):
    """Контроллер создания клиента"""

    model = Client
    fields = ["email", "full_name", "comment"]
    template_name = "mailing/client_form.html"
    success_url = reverse_lazy("mailing:client_list")

    def form_invalid(self, form):
        """Ошибка об существующей почте в БД"""
        if "email" in form.errors:
            messages.error(self.request, "Клиент с таким email уже существует!")
        return super().form_invalid(form)


class ClientUpdateView(CacheInvalidationMixin, UpdateView):
    """Контроллер обновления клиента"""

    model = Client
    fields = ["email", "full_name", "comment"]
    template_name = "mailing/client_form.html"
    success_url = reverse_lazy("mailing:client_list")

    def form_invalid(self, form):
        """Ошибка об существующей почте в БД"""
        try:
            return super().form_valid(form)
        except Exception as e:
            if "email" in str(e) and "unique" in str(e).lower():
                form.add_error("email", "Клиент с таким email уже существует")
                return self.form_invalid(form)
            raise e


class ClientDeleteView(CacheInvalidationMixin, DeleteView):
    """Контролер удаления страницы клиента"""

    model = Client
    template_name = "mailing/confirm_delete.html"
    success_url = reverse_lazy("mailing:client_list")



class MessageListView(CacheMixin, UserRoleQuerysetMixin, ListView):
    """Контролер страницы списка сообщений"""

    model = Message
    template_name = "mailing/message_list.html"
    context_object_name = "messages"
    ordering = ["-created_at"]
    # paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()

        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                Q(message_subject__icontains=query) | Q(message_body__icontains=query)
            )

        filter_type = self.request.GET.get("filter", "all")
        if filter_type == "draft":
            queryset = queryset.filter(mailing__isnull=True)
        elif filter_type == "used":
            queryset = queryset.filter(mailing__isnull=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.role == "manager":
            base_queryset = Message.objects.all()
        elif self.request.user.role == "user":
            base_queryset = Message.objects.filter(owner=self.request.user)
        else:
            base_queryset = Message.objects.none()

        query = self.request.GET.get("q")
        if query:
            base_queryset = base_queryset.filter(
                Q(message_subject__icontains=query) | Q(message_body__icontains=query)
            )

        context.update(
            {
                "current_filter": self.request.GET.get("filter", "all"),
                "query": query,
                "all_count": base_queryset.count(),
                "draft_count": base_queryset.filter(mailing__isnull=True).count(),
                "used_count": base_queryset.filter(mailing__isnull=False).count(),
            }
        )

        return context


class MessageCreateView(OwnerAutoSetMixin, CacheInvalidationMixin, CreateView):
    """Контролер страницы написания сообщения"""

    model = Message
    form_class = MessageForm
    template_name = "mailing/message_form.html"
    success_url = reverse_lazy("mailing:message_list")


class MessageUpdateView(CacheInvalidationMixin, UpdateView):
    """Контролер страницы обновления сообщения"""

    model = Message
    form_class = MessageForm
    template_name = "mailing/message_form.html"
    success_url = reverse_lazy("mailing:message_list")


class MessageDeleteView(CacheInvalidationMixin, DeleteView):
    """Контролер страницы удаления сообщения"""

    model = Message
    template_name = "mailing/confirm_delete.html"
    success_url = reverse_lazy("mailing:message_list")


class MailingListView(CacheMixin, UserRoleQuerysetMixin, ListView):
    """Контролер страницы списка рассылки"""

    model = Mailing
    template_name = "mailing/mailing_list.html"
    context_object_name = "mailings"
    # paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()

        # Поиск по теме сообщения
        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                Q(message__message_subject__icontains=query)
                | Q(message__message_body__icontains=query)
            )

        # Фильтрация по статусу
        filter_type = self.request.GET.get("filter", "all")
        if filter_type == "created":
            queryset = queryset.filter(status="created")
        elif filter_type == "started":
            queryset = queryset.filter(status="started")
        elif filter_type == "completed":
            queryset = queryset.filter(status="completed")

        return queryset.order_by("-start_time")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.role == "manager":
            base_queryset = Mailing.objects.all()
        elif self.request.user.role == "user":
            base_queryset = Mailing.objects.filter(owner=self.request.user)
        else:
            base_queryset = Mailing.objects.none()

        context.update(
            {
                "current_filter": self.request.GET.get("filter", "all"),
                "query": self.request.GET.get("q", ""),
                "all_count": base_queryset.count(),
                "created_count": base_queryset.filter(status="created").count(),
                "started_count": base_queryset.filter(status="started").count(),
                "completed_count": base_queryset.filter(status="completed").count(),
            }
        )

        return context


class MailingCreateView(OwnerAutoSetMixin, CacheInvalidationMixin,  CreateView):
    """Контролер страницы написания рассылки"""

    model = Mailing
    form_class = MailingForm
    template_name = "mailing/mailing_form.html"
    success_url = reverse_lazy("mailing:mailing_list")

    def get_initial(self):
        """Устанавливаем начальные значения формы"""
        initial = super().get_initial()

        message_id = self.kwargs.get("message_id") or self.request.GET.get("message")

        if message_id:
            try:
                message = Message.objects.get(id=message_id)
                initial["message"] = message
            except Message.DoesNotExist:
                pass

        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        if self.request.user.role == "user":
            form.fields["message"].queryset = Message.objects.filter(
                owner=self.request.user
            )

        message_id = self.kwargs.get("message_id") or self.request.GET.get("message")
        if message_id and Message.objects.filter(id=message_id).exists():
            form.fields["message"].initial = message_id

        return form

    def get_context_data(self, **kwargs):
        """Добавляем информацию о предвыбранном сообщении в контекст"""
        context = super().get_context_data(**kwargs)

        message_id = self.kwargs.get("message_id") or self.request.GET.get("message")
        if message_id:
            try:
                context["preselected_message"] = Message.objects.get(id=message_id)
            except Message.DoesNotExist:
                context["preselected_message"] = None

        return context


class MailingUpdateView(CacheInvalidationMixin, UpdateView):
    """Контролер страницы обновления рассылки"""

    model = Mailing
    form_class = MailingForm
    template_name = "mailing/mailing_form.html"
    success_url = reverse_lazy("mailing:mailing_list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.user.role == "user":
            form.fields["message"].queryset = Message.objects.filter(
                owner=self.request.user
            )
        return form

    def form_valid(self, form):
        """Сохраняет времена отправки при обновлении"""
        response = super().form_valid(form)

        send_times = self.request.POST.getlist("send_times")

        if self.object and send_times:
            self.object.sending_times.all().delete()

            for time_str in send_times:
                if time_str.strip():
                    try:
                        from datetime import datetime

                        from django.utils import timezone

                        send_time = datetime.fromisoformat(time_str)
                        send_time = timezone.make_aware(send_time)

                        MailingTime.objects.create(
                            mailing=self.object, send_time=send_time
                        )
                    except (ValueError, TypeError) as e:
                        print(f"Ошибка сохранения времени: {e}")
                        continue
        return response


class MailingDeleteView(CacheInvalidationMixin, DeleteView):
    """Контролер страницы удаления рассылки"""

    model = Mailing
    template_name = "mailing/confirm_delete.html"
    success_url = reverse_lazy("mailing:mailing_list")


class MailingAttemptListView(OwnerAutoSetMixin, UserRoleQuerysetMixin, ListView):
    """Контролер страницы списка логов отправки"""

    model = MailingAttempt
    template_name = "mailing/attempt_list.html"
    context_object_name = "attempts"
    # paginate_by = 10
    ordering = ["-created_at"]


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attempts = context["attempts"]

        context["total_attempts"] = attempts.count()
        context["successful_attempts"] = attempts.filter(status="success").count()
        context["failed_attempts"] = attempts.filter(status="failure").count()

        mailing_id = self.request.GET.get("mailing")
        if mailing_id:
            try:
                from mailing.models import Mailing

                context["filtered_mailing"] = Mailing.objects.get(id=mailing_id)
            except Mailing.DoesNotExist:
                context["filtered_mailing"] = None

        return context


def send_mailing_now(request, pk):
    """Ручная отправка рассылки"""
    print(f"Вызвана отправка рассылки #{pk}")

    mailing = get_object_or_404(Mailing, pk=pk)
    print(f"Найдена рассылка: {mailing.message.message_subject}")

    clients = mailing.clients.all()
    print(f"Клиентов: {clients.count()}")

    success, result_message = send_mailing_service(mailing)

    print(f"Результат отправки: {success} - {result_message}")

    if success:
        messages.success(request, f"Рассылка отправлена! {result_message}")
        print(f"✅ Сообщение об успехе: {result_message}")
    else:
        messages.error(request, f"Ошибка отправки: {result_message}")
        print(f"❌ Сообщение об ошибке: {result_message}")

    invalidate_user_cache(request.user)
    return redirect("mailing:mailing_list")


def get_attempt_details(request, pk):
    """Получение деталей попытки отправки"""
    attempt = get_object_or_404(MailingAttempt, pk=pk)

    recipient_details = []
    if attempt.recipient_details:
        try:
            recipient_details = json.loads(attempt.recipient_details)
        except json.JSONDecodeError:
            recipient_details = []

    success_count = sum(1 for r in recipient_details if r["status"] == "success")
    failure_count = sum(1 for r in recipient_details if r["status"] == "failure")

    details = {
        "attempt_id": attempt.id,
        "status": attempt.status,
        "created_at": attempt.created_at.strftime("%d.%m.%Y %H:%M:%S"),
        "mailing_subject": (
            attempt.mailing_list.message.message_subject
            if attempt.mailing_list and attempt.mailing_list.message
            else "Без темы"
        ),
        "mailing_body": (
            attempt.mailing_list.message.message_body
            if attempt.mailing_list and attempt.mailing_list.message
            else "Без текста"
        ),
        "recipients": recipient_details,
        "stats": {
            "total": len(recipient_details),
            "success": success_count,
            "failure": failure_count,
        },
    }

    return JsonResponse(details)


class WebinarListView(ListView):
    """Контроллер страницы списка вебинаров"""

    model = None
    template_name = "webinar/webinar_list.html"
    context_object_name = "webinars"

    def get_queryset(self):
        return []

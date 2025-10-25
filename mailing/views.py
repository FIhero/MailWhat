import json

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DeleteView, UpdateView, TemplateView

from mailing.forms import MessageForm, MailingForm
from mailing.models import Client, Message, Mailing, MailingAttempt
from mailing.services import send_mailing_service


class HomeView(TemplateView):
    """Главная страница"""
    template_name = 'mailing/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_mailings'] = Mailing.objects.count()
        context['active_mailings'] = Mailing.objects.filter(status='started').count()
        context['unique_clients'] = Client.objects.count()
        return context

class ClientListView(ListView):
    """Контролер страницы списка клиентов"""
    model = Client
    template_name = 'mailing/client_list.html'
    context_object_name = 'clients'

    def get_queryset(self):
        return Client.objects.all()

class ClientCreateView(CreateView):
    """Контроллер создания клиента"""
    model = Client
    fields = ['email', 'full_name', 'comment']
    template_name = 'mailing/client_form.html'
    success_url = reverse_lazy('mailing:client_list')

    def form_invalid(self, form):
        """Ошибка об существующей почте в БД"""
        if 'email' in form.errors:
            messages.error(self.request, 'Клиент с таким email уже существует!')
        return super().form_invalid(form)

class ClientUpdateView(UpdateView):
    """Контроллер обновления клиента"""
    model = Client
    fields = ['email', 'full_name', 'comment']
    template_name = 'mailing/client_form.html'
    success_url = reverse_lazy('mailing:client_list')

    def form_invalid(self, form):
        """Ошибка об существующей почте в БД"""
        try:
            return super().form_valid(form)
        except Exception as e:
            if 'email' in str(e) and 'unique' in str(e).lower():
                form.add_error('email', 'Клиент с таким email уже существует')
                return self.form_invalid(form)
            raise e

class ClientDeleteView(DeleteView):
    """Контролер удаления страницы клиента"""
    model = Client
    template_name = 'mailing/confirm_delete.html'
    success_url = reverse_lazy('mailing:client_list')

    def client_delete_api(request, pk):
        if request.method == 'POST':
            client = get_object_or_404(Client, pk=pk)
            client.delete()
            return JsonResponse({'success': True})
        return JsonResponse({'error': 'Method not allowed'}, status=405)


class MessageListView(ListView):
    """Контролер страницы списка сообщений"""
    model = Message
    template_name = 'mailing/message_list.html'
    context_object_name = 'notifications'
    ordering = ['-created_at']

    def get_queryset(self):
        return Message.objects.all()


class UnsentMessagesListView(ListView):
    """Неотправленные уведомления (для создания рассылок)"""
    model = Message
    template_name = 'mailing/unsent_messages.html'
    context_object_name = 'messages'
    ordering = ['-created_at']

    def get_queryset(self):
        return Message.objects.filter(mailing__isnull=True)

class MessageCreateView(CreateView):
    """Контролер страницы написания сообщения"""
    model = Message
    form_class = MessageForm
    template_name = 'mailing/message_form.html'
    success_url = reverse_lazy('mailing:message_list')

class MessageUpdateView(UpdateView):
    """Контролер страницы обновления сообщения"""
    model = Message
    form_class = MessageForm
    template_name = 'mailing/message_form.html'
    success_url = reverse_lazy('mailing:message_list')

class MessageDeleteView(DeleteView):
    """Контролер страницы удаления сообщения"""
    model = Message
    template_name = 'mailing/confirm_delete.html'
    success_url = reverse_lazy('mailing:message_list')

class MailingListView(ListView):
    """Контролер страницы списка рассылки"""
    model = Mailing
    template_name = 'mailing/mailing_list.html'
    context_object_name = 'mailings'

    def get_queryset(self):
        return Mailing.objects.all()

class MailingCreateView(CreateView):
    """Контролер страницы написания рассылки"""
    model = Mailing
    form_class = MailingForm
    template_name = 'mailing/mailing_form.html'
    success_url = reverse_lazy('mailing:mailing_list')



class MailingUpdateView(UpdateView):
    """Контролер страницы обновления рассылки"""
    model = Mailing
    form_class = MailingForm
    template_name = 'mailing/mailing_form.html'
    success_url = reverse_lazy('mailing:mailing_list')

class MailingDeleteView(DeleteView):
    """Контролер страницы удаления рассылки"""
    model = Mailing
    template_name = 'mailing/confirm_delete.html'
    success_url = reverse_lazy('mailing:mailing_list')


class MailingAttemptListView(ListView):
    """Контролер страницы списка логов отправки"""
    model = MailingAttempt
    template_name = 'mailing/attempt_list.html'
    context_object_name = 'attempts'
    ordering = ['-created_at']

    def get_queryset(self):
        mailing_id = self.request.GET.get('mailing')
        if mailing_id:
            return MailingAttempt.objects.filter(mailing_list_id=mailing_id)
        return MailingAttempt.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attempts = context['attempts']

        context['total_attempts'] = attempts.count()
        context['successful_attempts'] = attempts.filter(status='success').count()
        context['failed_attempts'] = attempts.filter(status='failure').count()

        mailing_id = self.request.GET.get('mailing')
        if mailing_id:
            try:
                from mailing.models import Mailing
                context['filtered_mailing'] = Mailing.objects.get(id=mailing_id)
            except Mailing.DoesNotExist:
                context['filtered_mailing'] = None

        return context


def send_mailing_now(request, pk):
    """Ручная отправка рассылки"""
    print(f"🖱️ Вызвана отправка рассылки #{pk}")

    mailing = get_object_or_404(Mailing, pk=pk)
    print(f"📨 Найдена рассылка: {mailing.message.message_subject}")

    clients = mailing.clients.all()
    print(f"👥 Клиентов: {clients.count()}")

    success, result_message = send_mailing_service(mailing)

    print(f"📊 Результат отправки: {success} - {result_message}")

    if success:
        messages.success(request, f"Рассылка отправлена! {result_message}")
        print(f"✅ Сообщение об успехе: {result_message}")
    else:
        messages.error(request, f"Ошибка отправки: {result_message}")
        print(f"❌ Сообщение об ошибке: {result_message}")

    return redirect('mailing:mailing_list')


def get_attempt_details(request, pk):
    """Получение деталей попытки отправки"""
    attempt = get_object_or_404(MailingAttempt, pk=pk)

    # Добавим статистику
    recipient_details = []
    if attempt.recipient_details:
        try:
            recipient_details = json.loads(attempt.recipient_details)
        except json.JSONDecodeError:
            recipient_details = []

    success_count = sum(1 for r in recipient_details if r['status'] == 'success')
    failure_count = sum(1 for r in recipient_details if r['status'] == 'failure')

    details = {
        'attempt_id': attempt.id,
        'status': attempt.status,
        'created_at': attempt.created_at.strftime("%d.%m.%Y %H:%M:%S"),
        'mailing_subject': attempt.mailing_list.message.message_subject if attempt.mailing_list and attempt.mailing_list.message else 'Без темы',
        'mailing_body': attempt.mailing_list.message.message_body if attempt.mailing_list and attempt.mailing_list.message else 'Без текста',
        'recipients': recipient_details,
        'stats': {
            'total': len(recipient_details),
            'success': success_count,
            'failure': failure_count
        }
    }

    return JsonResponse(details)
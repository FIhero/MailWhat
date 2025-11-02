from django.db import models

from users.models import User


class Client(models.Model):
    email = models.EmailField(unique=True, verbose_name='Email')
    full_name = models.CharField(max_length=100, verbose_name='ФИО')
    comment = models.TextField(blank=True, null=True, verbose_name='Комментарий')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Владелец')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    class Meta:
        verbose_name = "Получатель"
        verbose_name_plural = "Получатели"


class Message(models.Model):
    message_subject = models.CharField(max_length=100)
    message_body = models.TextField(max_length=500)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Владелец')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message_subject

    class Meta:
        verbose_name = "Письмо"
        verbose_name_plural = "Письма"


class Mailing(models.Model):
    STATUS_CREATED = 'created'
    STATUS_STARTED = 'started'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = [
        (STATUS_CREATED, 'Создана'),
        (STATUS_STARTED, 'Запущена'),
        (STATUS_COMPLETED, 'Завершена'),
    ]

    start_time = models.DateTimeField(verbose_name='Время начала')
    end_time = models.DateTimeField(verbose_name='Время окончания')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_CREATED, verbose_name='Статус')
    message = models.ForeignKey('Message', on_delete=models.CASCADE, verbose_name='Сообщение')
    clients = models.ManyToManyField('Client', verbose_name='Клиенты')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Владелец')

    def __str__(self):
        return f"Рассылка {self.id} ({self.status})"

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"

    @property
    def success_count(self):
        return self.mailingattempt_set.filter(status='success').count()

    @property
    def failure_count(self):
        return self.mailingattempt_set.filter(status='failure').count()


class MailingAttempt(models.Model):
    STATUS_SUCCESS = 'success'
    STATUS_FAILURE = 'failure'

    STATUS_CHOICES = [
        (STATUS_SUCCESS, 'Успешно'),
        (STATUS_FAILURE, 'Не успешно'),
    ]

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Время попытки')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name='Статус')
    answer = models.TextField(blank=True, null=True, verbose_name='Ответ сервера')
    mailing_list = models.ForeignKey(Mailing, on_delete=models.CASCADE, verbose_name='Рассылка')
    recipient_details = models.TextField(blank=True, null=True, verbose_name='Детали получателей')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Владелец')

    def __str__(self):
        return f"Попытка {self.id} ({self.status})"

    class Meta:
        verbose_name = "Попытка рассылки"
        verbose_name_plural = "Попытки рассылки"

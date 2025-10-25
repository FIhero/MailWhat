from django.contrib import admin
from .models import Client, Message, Mailing, MailingAttempt

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('email', 'full_name', 'created_at')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('message_subject', 'created_at')

@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'start_time', 'end_time')

@admin.register(MailingAttempt)
class MailingAttemptAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'status', 'mailing_list')
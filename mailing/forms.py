from django import forms
from .models import Message, Mailing


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['message_subject', 'message_body']
        widgets = {
            'message_subject': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Введите тему уведомления'
            }),
            'message_body': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Введите текст уведомления',
                'rows': 6
            }),
        }
        labels = {
            'message_subject': 'Тема',
            'message_body': 'Текст',
        }


class MailingForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ['start_time', 'end_time', 'status', 'message', 'clients']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-input'
            }),
            'end_time': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-input'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'message': forms.Select(attrs={'class': 'form-select'}),
            'clients': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': 10
            }),
        }
        labels = {
            'start_time': 'Время начала',
            'end_time': 'Время окончания',
            'status': 'Статус',
            'message': 'Сообщение',
            'clients': 'Получатели'
        }

    def clean_clients(self):
        """Проверяем что выбран хотя бы один клиент"""
        clients = self.cleaned_data.get('clients')
        if not clients:
            raise forms.ValidationError("Выберите хотя бы одного клиента для рассылки")
        return clients

    def clean(self):
        """Дополнительные проверки"""
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError("Время окончания должно быть позже времени начала")

        return cleaned_data

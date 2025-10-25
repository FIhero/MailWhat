import json
from django.core.mail import send_mail
from django.conf import settings
from mailing.models import MailingAttempt


def send_mailing_service(mailing):
    """Сервис для отправки рассылки с детальным логированием"""
    print(f"Начало отправки рассылки #{mailing.id}")

    try:
        clients = mailing.clients.all()
        print(f"Клиентов для отправки: {clients.count()}")

        if not clients:
            error_msg = "Ошибка: Нет клиентов для отправки"
            MailingAttempt.objects.create(
                mailing_list=mailing,
                status='failure',
                answer=error_msg,
                recipient_details="[]"
            )
            return False, error_msg

        sent_count = 0
        failed_count = 0
        recipient_details = []

        for client in clients:
            try:
                print(f"Отправка для: {client.email}")

                send_mail(
                    subject=mailing.message.message_subject,
                    message=mailing.message.message_body,
                    from_email=settings.DEFAULT_FROM_EMAIL or 'noreply@example.com',
                    recipient_list=[client.email],
                    fail_silently=False,
                )
                sent_count += 1
                recipient_details.append({
                    'email': client.email,
                    'full_name': client.full_name,
                    'status': 'success',
                    'message': 'Успешно отправлено',
                    'timestamp': None
                })
                print(f"✅ Успешно отправлено для: {client.email}")

            except Exception as e:
                failed_count += 1
                error_msg = str(e)
                recipient_details.append({
                    'email': client.email,
                    'full_name': client.full_name,
                    'status': 'failure',
                    'message': error_msg,
                    'timestamp': None
                })
                print(f"Ошибка для {client.email}: {e}")

        recipient_details.sort(key=lambda x: (x['status'] != 'failure', x['email']))

        if failed_count == 0:
            status = 'success'
            short_response = f"Успешно отправлено {sent_count} писем"
        else:
            status = 'failure'
            short_response = f"Отправлено: {sent_count}, Ошибок: {failed_count}"

        print(f"Создаем запись MailingAttempt с деталями")

        attempt = MailingAttempt.objects.create(
            mailing_list=mailing,
            status=status,
            answer=short_response,
            recipient_details=json.dumps(recipient_details, ensure_ascii=False)
        )

        print(f"Запись создана с ID: {attempt.id}")

        return (failed_count == 0), short_response

    except Exception as e:
        error_msg = f"Критическая ошибка: {str(e)}"
        print(f"🚨 {error_msg}")

        MailingAttempt.objects.create(
            mailing_list=mailing,
            status='failure',
            answer=error_msg,
            recipient_details="[]"
        )
        return False, error_msg
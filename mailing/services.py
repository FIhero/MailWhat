import json
import logging

from django.conf import settings
from django.core.mail import send_mail

from mailing.models import MailingAttempt

logger = logging.getLogger("mailing")


def send_mailing_service(mailing):
    """Сервис для отправки рассылки с детальным логированием"""
    logger.info(f"Начало отправки рассылки #{mailing.id}")

    try:
        clients = mailing.clients.all()
        print(f"Клиентов для отправки: {clients.count()}")

        if not clients:
            error_msg = "Ошибка: Нет клиентов для отправки"
            MailingAttempt.objects.create(
                mailing_list=mailing,
                status="failure",
                answer=error_msg,
                recipient_details="[]",
                owner=mailing.owner,
            )
            return False, error_msg

        sent_count = 0
        failed_count = 0
        recipient_details = []

        if not settings.EMAIL_HOST_USER:
            raise Exception("EMAIL_HOST_USER не настроен в settings.py")

        if not settings.EMAIL_HOST_PASSWORD:
            raise Exception("EMAIL_HOST_PASSWORD не настроен в settings.py")

        for client in clients:
            try:
                print(f"Отправка для: {client.email}")

                send_mail(
                    subject=mailing.message.message_subject,
                    message=mailing.message.message_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[client.email],
                    fail_silently=False,
                )
                sent_count += 1
                recipient_details.append(
                    {
                        "email": client.email,
                        "full_name": client.full_name,
                        "status": "success",
                        "message": "Успешно отправлено",
                        "timestamp": None,
                    }
                )
                print(f"✅ Успешно отправлено для: {client.email}")

            except Exception as e:
                failed_count += 1
                error_msg = str(e)
                recipient_details.append(
                    {
                        "email": client.email,
                        "full_name": client.full_name,
                        "status": "failure",
                        "message": error_msg,
                        "timestamp": None,
                    }
                )
                print(f"Ошибка для {client.email}: {e}")

        recipient_details.sort(key=lambda x: (x["status"] != "failure", x["email"]))

        if failed_count == 0:
            status = "success"
            short_response = f"Успешно отправлено {sent_count} писем"
        else:
            status = "failure"
            short_response = f"Отправлено: {sent_count}, Ошибок: {failed_count}"

        print(f"Создаем запись MailingAttempt с деталями")

        attempt = MailingAttempt.objects.create(
            mailing_list=mailing,
            status=status,
            answer=short_response,
            recipient_details=json.dumps(recipient_details, ensure_ascii=False),
            owner=mailing.owner,
        )

        print(f"Запись создана с ID: {attempt.id}")

        return (failed_count == 0), short_response

    except Exception as e:
        error_msg = f"Критическая ошибка: {str(e)}"
        print(f"🚨 {error_msg}")

        MailingAttempt.objects.create(
            mailing_list=mailing,
            status="failure",
            answer=error_msg,
            recipient_details="[]",
            owner=mailing.owner,
        )
        return False, error_msg


def check_mailing_schedule():
    """Проверяет и обновляет статусы рассылок по расписанию"""
    from django.utils import timezone

    from .models import Mailing

    now = timezone.now()

    mailings_to_start = Mailing.objects.filter(
        status=Mailing.STATUS_CREATED, start_time__lte=now
    )

    for mailing in mailings_to_start:
        mailing.status = Mailing.STATUS_STARTED
        mailing.save()
        send_mailing_service(mailing)

    mailings_to_complete = Mailing.objects.filter(
        status=Mailing.STATUS_STARTED, end_time__lt=now
    )

    for mailing in mailings_to_complete:
        mailing.status = Mailing.STATUS_COMPLETED
        mailing.save()

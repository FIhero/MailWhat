from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import VerificationCode


def send_verification_code(email, purpose):
    """Отправляет код подтверждения на email"""
    try:
        verification_code = VerificationCode.generate_code(email, purpose)

        purpose_display = verification_code.get_purpose_display_name()

        subject = f"Код подтверждения для {purpose_display}"
        html_message = render_to_string('users/emails/simple_code_email.html', {
            'code': verification_code.code,
            'purpose': purpose_display,
            'email': email
        })

        send_mail(
            subject=subject,
            message=f"Ваш код для {purpose_display}: {verification_code.code}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )

        return True, "Код отправлен"

    except Exception as e:
        return False, f"Ошибка отправки: {str(e)}"


def verify_code(email, code, purpose):
    """Проверяет код подтверждения"""
    try:
        verification_code = VerificationCode.objects.get(
            email=email,
            code=code,
            purpose=purpose
        )

        if verification_code.is_valid():
            verification_code.mark_used()
            return True, "Код подтвержден"
        else:
            return False, "Код недействителен или истек"

    except VerificationCode.DoesNotExist:
        return False, "Неверный код"

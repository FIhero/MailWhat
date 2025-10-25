from django.core.management.base import BaseCommand
from mailing.models import Mailing
from mailing.services import send_mailing_service


class Command(BaseCommand):
    help = 'Отправка активных рассылок'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mailing-id',
            type=int,
            help='ID конкретной рассылки для отправки',
        )

    def handle(self, *args, **options):
        mailing_id = options.get('mailing_id')

        if mailing_id:
            mailings = Mailing.objects.filter(pk=mailing_id)
        else:
            mailings = Mailing.objects.filter(status='started')

        for mailing in mailings:
            self.stdout.write(f"Отправка рассылки #{mailing.id}...")
            success, message = send_mailing_service(mailing)

            if success:
                self.stdout.write(
                    self.style.SUCCESS(f"Рассылка #{mailing.id} отправлена: {message}")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"Ошибка рассылки #{mailing.id}: {message}")
                )

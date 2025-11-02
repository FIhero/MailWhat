import random
import string
from django.utils import timezone
from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    username = None

    ROLE_CHOICES = [
        ('user', 'Пользователь'),
        ('lector', 'Лектор'),
        ('manager', 'Менеджер'),
    ]

    email = models.EmailField("Email", max_length=254, unique=True)
    phone = models.CharField("Телефон", max_length=15, blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    is_blocked = models.BooleanField("Заблокирован", default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class UserProfile(models.Model):
    """Модель создания профиля пользователя"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    avatar = models.ImageField(
        upload_to="users/",
        blank=True,
        null=True,
        default="users/default_user.png",
        verbose_name="Аватар",
    )
    bio = models.TextField("О себе", blank=True, null=True)
    company = models.CharField("Компания", max_length=100, blank=True)
    experience = models.TextField("Опыт работы", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Профиль {self.user.email}"

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"


class LectorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lector_profile')
    specialization = models.CharField(max_length=100)
    education = models.TextField()

    class Meta:
        verbose_name = "Лектор"
        verbose_name_plural = "Лекторы"


class ManagerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='manager_profile')
    department = models.CharField(max_length=100)
    access_level = models.CharField(max_length=50)

    class Meta:
        verbose_name = "Менеджер"
        verbose_name_plural = "Менеджеры"


class VerificationCode(models.Model):
    """Модель для хранения кодов подтверждения"""
    email = models.EmailField()
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=[
        ('password_reset', 'Сброс пароля'),
        ('email_confirm', 'Подтверждение почты'),
        ('change_password', 'Смена пароля'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        """Проверяет, действителен ли код (10 минут)"""
        return (not self.is_used) and (
                timezone.now() - self.created_at < timedelta(minutes=10)
        )

    @classmethod
    def generate_code(cls, email, purpose):
        """Генерирует новый код подтверждения"""
        cls.objects.filter(email=email, purpose=purpose).delete()

        code = ''.join(random.choices(string.digits, k=6))

        return cls.objects.create(
            email=email,
            code=code,
            purpose=purpose
        )

    def mark_used(self):
        """Помечает код как использованный"""
        self.is_used = True
        self.save()

    def get_purpose_display_name(self):
        """Возвращает понятное название цели"""
        purposes = {
            'password_reset': 'сброса пароля',
            'email_confirm': 'подтверждения email',
            'change_password': 'смены пароля'
        }
        return purposes.get(self.purpose, 'подтверждения')

    class Meta:
        verbose_name = "Код подтверждения"
        verbose_name_plural = "Коды подтверждения"

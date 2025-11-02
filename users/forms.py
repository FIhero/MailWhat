from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm, PasswordResetForm

from config import settings

User = get_user_model()


class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label='Email адрес',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'your@email.com',
            'autocomplete': 'email'
        })
    )

    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        """Переопределяем метод отправки, чтобы исправить from_email"""
        if from_email is None:
            from_email = settings.EMAIL_HOST_USER

        super().send_mail(
            subject_template_name=subject_template_name,
            email_template_name=email_template_name,
            context=context,
            from_email=from_email,
            to_email=to_email,
            html_email_template_name=html_email_template_name,
        )

class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="Новый пароль",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Не менее 8 символов',
            'autocomplete': 'new-password'
        }),
    )
    new_password2 = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Повторите новый пароль',
            'autocomplete': 'new-password'
        }),
    )

class UserUpdateForm(forms.ModelForm):
    """Форма для обновления основных данных пользователя"""

    class Meta:
        from .models import User  # Импортируем внутри Meta
        model = User
        fields = ['first_name', 'last_name', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }


class UserRegistrationForm(forms.Form):
    """Простая форма регистрации"""

    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label="Пароль")
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label="Подтвердите пароль")

    role = forms.ChoiceField(
        choices=[
            ('user', 'Пользователь'),
            ('lector', 'Лектор'),
            ('manager', 'Менеджер'),
        ],
        initial='user',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def clean_email(self):
        from .models import User
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с таким Email уже существует")
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Пароли не совпадают")
        return password2

    def save(self):
        from .models import User, UserProfile
        user = User(
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            email=self.cleaned_data['email'],
            phone=self.cleaned_data['phone'],
            role=self.cleaned_data['role']
        )
        user.set_password(self.cleaned_data["password1"])
        user.save()

        UserProfile.objects.create(user=user)
        return user


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Введите ваш email"})
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Введите ваш пароль"})
    )


class CodeVerificationForm(forms.Form):
    """Форма для ввода кода подтверждения"""
    code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '123456',
            'style': 'text-align: center; font-size: 1.5em; letter-spacing: 10px;',
            'autocomplete': 'off'
        }),
        label="Код из письма"
    )


class SimplePasswordResetForm(forms.Form):
    """Упрощенная форма сброса пароля (только email)"""
    email = forms.EmailField(
        label='Email адрес',
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'your@email.com',
            'autocomplete': 'email'
        })
    )


class NewPasswordForm(forms.Form):
    """Форма для ввода нового пароля после подтверждения кода"""
    new_password1 = forms.CharField(
        label="Новый пароль",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Не менее 8 символов',
            'autocomplete': 'new-password'
        }),
    )
    new_password2 = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Повторите новый пароль',
            'autocomplete': 'new-password'
        }),
    )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("new_password1")
        password2 = cleaned_data.get("new_password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Пароли не совпадают")

        return cleaned_data


from django.views.generic import TemplateView


class UsersUnderDevelopmentView(TemplateView):
    template_name = 'users/under_development.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': '👥 Система пользователей',
            'features': [
                'Регистрация и авторизация',
                'Личные кабинеты',
                'Управление профилями',
                'Восстановление паролей',
                'Ролевая модель доступа'
            ],
            'progress': 0
        })
        return context
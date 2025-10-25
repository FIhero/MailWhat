from django.urls import path
from .views import UsersUnderDevelopmentView

app_name = 'users'

urlpatterns = [
    path('login/', UsersUnderDevelopmentView.as_view(), name='login'),
    path('logout/', UsersUnderDevelopmentView.as_view(), name='logout'),
    path('register/', UsersUnderDevelopmentView.as_view(), name='register'),
    path('profile/', UsersUnderDevelopmentView.as_view(), name='profile'),
]
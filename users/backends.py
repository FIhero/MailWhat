from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        print(f"=== BACKEND AUTH ===")
        print(f"Username: {username}")
        print(f"Password provided: {bool(password)}")

        if username is None:
            username = kwargs.get('email')

        try:
            user = User.objects.get(email=username)
            print(f"User found: {user.email}")
            print(f"Password check: {user.check_password(password)}")
            if user.check_password(password):
                print("Authentication SUCCESS")
                return user
            else:
                print("Authentication FAILED - wrong password")
        except User.DoesNotExist:
            print(f"User with email {username} not found")
            return None
        except Exception as e:
            print(f"Auth error: {e}")
            return None

        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
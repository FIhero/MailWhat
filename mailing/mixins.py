from django.core.cache import cache


class CacheMixin:
    """Миксин для кэширования"""

    cache_timeout = 60 * 5

    def get_cache_key(self, **kwargs):
        request = self.request
        user = request.user

        base_key = f"{self.__class__.__name__}"

        if user.is_authenticated:
            base_key += f"_user_{user.id}_role_{user.role}"
        else:
            base_key += "_anonymous"

        params = []
        for key in ['q', 'filter', 'mailing', 'page']:
            value = request.GET.get(key)
            if value:
                params.append(f"{key}_{value}")

        if params:
            base_key += "_" + "_".join(params)

        return base_key

    def dispatch(self, request, *args, **kwargs):
        self.request = request

        if request.method == 'GET':
            cache_key = self.get_cache_key(**kwargs)
            cached_data = cache.get(cache_key)

            if cached_data:
                if isinstance(cached_data, dict):
                    return self.render_to_response(cached_data)
                else:
                    return cached_data

        response = super().dispatch(request, *args, **kwargs)

        if (request.method == 'GET' and
                response.status_code == 200 and
                not getattr(response, 'streaming', False)):

            cache_key = self.get_cache_key(**kwargs)

            if hasattr(self, 'get_context_data'):
                try:
                    context_data = self.get_context_data()
                    cache.set(cache_key, context_data, self.cache_timeout)
                except Exception as e:
                    print(f"Ошибка кэширования контекста: {e}")
            else:
                try:
                    cache.set(cache_key, response.content, self.cache_timeout)
                except Exception as e:
                    print(f"Ошибка кэширования контента: {e}")

        return response


class CacheInvalidationMixin:
    """Миксин для инвалидации кэша при изменениях"""

    def invalidate_user_cache(self, user):
        """Очистка кэша для пользователя"""
        if hasattr(cache, 'delete_pattern'):
            patterns = [
                f"*user_{user.id}*",
                f"*role_{user.role}*",
            ]
            for pattern in patterns:
                cache.delete_pattern(pattern)
        else:
            cache_keys = [
                f"HomeView_user_{user.id}_role_{user.role}",
                f"ClientListView_user_{user.id}_role_{user.role}",
                f"MessageListView_user_{user.id}_role_{user.role}",
                f"MailingListView_user_{user.id}_role_{user.role}",
                f"MailingAttemptListView_user_{user.id}_role_{user.role}",
            ]
            for key in cache_keys:
                cache.delete(key)

    def form_valid(self, form):
        """Удаление кэша при успешной форме"""
        response = super().form_valid(form)
        self.invalidate_user_cache(self.request.user)
        return response

    def delete(self, request, *args, **kwargs):
        """Удаление кэша при удалении"""
        response = super().delete(request, *args, **kwargs)
        self.invalidate_user_cache(request.user)
        return response


class OwnerAutoSetMixin:
    """Миксин для автоматической установки владельца"""

    def form_valid(self, form):
        """Устанавливает владельца и инвалидирует кэш"""
        form.instance.owner = self.request.user
        response = super().form_valid(form)

        if hasattr(self, 'invalidate_user_cache'):
            self.invalidate_user_cache(self.request.user)
        return response


class UserRoleQuerysetMixin:
    """Миксин для фильтрации queryset по роли пользователя"""

    def get_queryset(self):
        queryset = super().get_queryset()

        if not self.request.user.is_authenticated:
            return queryset.none()

        if self.request.user.role == "manager":
            return queryset
        elif self.request.user.role == "user":
            return queryset.filter(owner=self.request.user)

        return queryset.none()
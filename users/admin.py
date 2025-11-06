from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import LectorProfile, ManagerProfile, User, UserProfile


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "email",
        "first_name",
        "last_name",
        "role",
        "get_groups",
        "is_blocked",
        "is_active",
    )
    list_filter = ("role", "is_blocked", "is_active", "is_staff", "groups")
    search_fields = ("email", "first_name", "last_name")
    ordering = ["email"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "phone")}),
        (
            "Permissions",
            {
                "fields": (
                    "role",
                    "is_blocked",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                    "phone",
                    "role",
                ),
            },
        ),
    )

    def get_groups(self, obj):
        return ", ".join([g.name for g in obj.groups.all()])

    get_groups.short_description = "Группы"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "company", "created_at")
    search_fields = ("user__email", "user__first_name", "user__last_name")
    list_filter = ("created_at",)


@admin.register(LectorProfile)
class LectorProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "specialization")
    search_fields = ("user__email", "user__first_name", "user__last_name")


@admin.register(ManagerProfile)
class ManagerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "department", "access_level")
    search_fields = ("user__email", "user__first_name", "user__last_name")

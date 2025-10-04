from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from src.apps.chat.models import Chat

from .models import Profile

admin.site.register(Chat)


class ProfileInline(admin.StackedInline):
    """
    Inline admin for Profile model to display within User admin.
    """

    model = Profile
    can_delete = False
    verbose_name_plural = "Perfil"


class UserAdmin(BaseUserAdmin):
    """
    Custom User admin that includes Profile information.
    """

    inlines = (ProfileInline,)
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_account_activated",
        "is_otp_verified",
    )
    list_filter = (
        "profile__is_account_activated",
        "profile__is_otp_verified",
        "is_staff",
        "is_superuser",
    )

    def is_account_activated(self, obj: User) -> bool:
        """
        Check if user account is activated from Profile.
        Creates Profile if it doesn't exist.
        """
        try:
            return obj.profile.is_account_activated
        except:
            Profile.objects.create(user=obj)
            return False

    def is_otp_verified(self, obj: User) -> bool:
        """
        Check if user account has been OTP verified.
        Creates Profile if it doesn't exist.
        """
        try:
            return obj.profile.is_otp_verified
        except:
            Profile.objects.create(user=obj)
            return False

    # Configure display properties for custom fields
    is_account_activated.boolean = True
    is_otp_verified.boolean = True
    is_account_activated.short_description = "Account activated"
    is_otp_verified.short_description = "OTP code verified"


# Replace default User admin with custom UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

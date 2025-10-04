import random
import string
from datetime import timedelta
from typing import Any, Type

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import activate, get_language
from django.utils.translation import gettext as _


class Profile(models.Model):
    """
    Extension of the User model with additional authentication features.
    Supports account activation, OTP verification, and language preference.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_account_activated = models.BooleanField(default=False)
    is_otp_verified = models.BooleanField(default=False)
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_expiry = models.DateTimeField(blank=True, null=True)
    language = models.CharField(
        max_length=10,
        default="en",
        choices=[
            ("en", "English"),
            ("es", "Spanish"),
            ("gl", "Galician"),
        ],
    )

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Override save method to handle OTP generation when account is activated.
        Prevents recursion during save operations.
        """
        # Check if this is being called during an update_fields operation to prevent recursion
        is_update_operation = kwargs.get("update_fields") is not None

        # Save the old state to check if modified
        if self.pk and not is_update_operation:
            try:
                _old_profile = Profile.objects.get(pk=self.pk)
                self._old_activation_status = _old_profile.is_account_activated
                self._old_otp_verified = _old_profile.is_otp_verified
            except Profile.DoesNotExist:
                self._old_activation_status = False
                self._old_otp_verified = False
        else:
            self._old_activation_status = False
            self._old_otp_verified = False

        super().save(*args, **kwargs)

        if not is_update_operation:
            has_been_activated = (
                not self._old_activation_status and self.is_account_activated
            )
            otp_code_not_sent = not self.is_otp_verified

            # Only send OTP if account was just activated
            if has_been_activated and otp_code_not_sent:
                generate_and_send_otp(self)

    def generate_otp(self) -> str:
        """
        Generate a 6-digit OTP code with 30-minute expiry.
        """
        otp_code = "".join(random.choices(string.digits, k=6))
        expiry = timezone.now() + timedelta(minutes=30)

        # Update database directly to avoid recursion
        Profile.objects.filter(pk=self.pk).update(otp_code=otp_code, otp_expiry=expiry)

        self.otp_code = otp_code
        self.otp_expiry = expiry

        return otp_code

    def verify_otp(self, code: str) -> bool:
        """
        Verify provided OTP code against stored code.
        Handles expiry checking and updates verification status.
        Returns True if verification succeeds, False otherwise.
        """
        if not self.otp_code or not self.otp_expiry:
            return False

        if timezone.now() > self.otp_expiry:
            return False

        if self.otp_code != code:
            return False

        Profile.objects.filter(pk=self.pk).update(
            is_otp_verified=True, otp_code=None, otp_expiry=None
        )

        self.is_otp_verified = True
        self.otp_code = None
        self.otp_expiry = None

        send_confirmation_email(self)

        return True


def generate_and_send_otp(profile: Profile) -> None:
    """
    Generate OTP and send verification email in user's preferred language.
    """
    current_language = get_language()

    try:
        activate(profile.language)

        otp_code = profile.generate_otp()

        subject = _("Your verification code for PharmaDock AI")

        message = (
            _(
                """Hello %(name)s,

                Your PharmaDock AI account has been activated. To complete
                the process, please enter the following
                verification code on the verification page:

                %(otp)s

                This code will expire in 30 minutes. If you did not request
                this activation, please contact our support
                team immediately.

                Regards,
                The PharmaDock AI team"""
            )
            % {
                "name": profile.user.first_name or profile.user.username,
                "otp": otp_code,
            }
        )

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [profile.user.email],
            fail_silently=False,
        )

    finally:
        activate(current_language)


def send_confirmation_email(profile: Profile) -> None:
    """
    Send confirmation email after successful OTP verification.
    Email is sent in user's preferred language.
    """
    current_language = get_language()

    try:
        activate(profile.language)
        subject = _("Welcome to PharmaDock AI")

        message = (
            _(
                """Hello %(name)s,

                Your PharmaDock AI account has been successfully verified.
                You now have full access to our platform.

                Regards,
                The PharmaDock AI team"""
            )
            % {"name": profile.user.first_name or profile.user.username}
        )

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [profile.user.email],
            fail_silently=False,
        )

    finally:
        activate(current_language)


@receiver(post_save, sender=User)
def create_user_profile(
    sender: Type[User], instance: User, created: bool, **kwargs: Any
) -> None:
    """
    Signal handler to create Profile when a new User is created.
    """
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender: Type[User], instance: User, **kwargs: Any) -> None:
    """
    Signal handler to save Profile when User is saved.
    Creates Profile if it doesn't exist.
    """
    try:
        instance.profile.save()
    except:
        Profile.objects.create(user=instance)

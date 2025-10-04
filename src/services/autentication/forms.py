from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class ChatbotUserCreationForm(UserCreationForm):
    """
    Custom user registration that includes standard
    user fields and validates email uniqueness.
    """

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        ]

    def clean_email(self) -> str:
        """
        Validates that the email is not already in use.
        """
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_("A user with this email already exists"))
        return email


class OTPVerificationForm(forms.Form):
    """
    Form for verifying one-time passwords during
    two-factor authentication.
    Accepts a 6-digit numeric code.
    """

    otp_code = forms.CharField(
        label=_("Verification Code"),
        max_length=6,
        min_length=6,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "pattern": "[0-9]{6}",
                "autocomplete": "off",
                "placeholder": _("Enter 6-digit code"),
            }
        ),
    )

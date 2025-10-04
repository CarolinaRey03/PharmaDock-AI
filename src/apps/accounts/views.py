from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _

from src.services.autentication.forms import (
    ChatbotUserCreationForm,
    OTPVerificationForm,
)

from .models import Profile, generate_and_send_otp


def logout_view(request: HttpRequest) -> HttpResponse:
    """
    Logout the user and redirect to home page.
    """
    logout(request)
    return redirect("/")


def register(request: HttpRequest) -> HttpResponse:
    """
    Handle user registration process.
    Renders registration form and processes form submission.
    Sets user's language based on browser preference.
    """
    new_user_data = {"form": ChatbotUserCreationForm()}

    user_creation_form = ChatbotUserCreationForm(data=request.POST)

    if request.method != "POST":
        return render(request, "registration/register.html", new_user_data)

    if not user_creation_form.is_valid():
        return render(
            request, "registration/register.html", {"form": user_creation_form}
        )

    user = user_creation_form.save()
    browser_lang = request.LANGUAGE_CODE

    if browser_lang in ["es", "gl"]:
        user.profile.language = browser_lang
        user.profile.save()

    request.session["email"] = user.email
    request.session.save()

    return redirect("otp_verification")


def otp_verification(request: HttpRequest) -> HttpResponse:
    """
    Handle OTP verification for newly registered users.
    Validates the OTP code entered by the user.
    Redirects to login page on successful verification.
    """
    email = request.session.get("email")

    if not email:
        messages.error(request, _("Session expired. Please register again."))
        return redirect("register")

    form = OTPVerificationForm(request.POST)
    if request.method != "POST":
        return _load_verification_view(request, email)

    if not form.is_valid():
        return _load_verification_view(request, email)

    otp_code = form.cleaned_data["otp_code"]

    try:
        user = User.objects.get(email=email)
        profile = user.profile

        if profile.is_otp_verified:
            messages.success(request, _("Your account is already verified."))
            return redirect("login")

        if not profile.is_account_activated:
            messages.error(request, _("Your account has not been activated yet."))
            return _load_verification_view(request, email)

        if profile.verify_otp(otp_code):
            messages.success(request, _("Your account has been successfully verified."))
            # Clear the session variable after successful verification
            if "email" in request.session:
                del request.session["email"]
            return redirect("chat")
        else:
            messages.error(request, _("Invalid or expired verification code."))
            return _load_verification_view(request, email)

    except User.DoesNotExist:
        messages.error(request, _("No account found with this email address."))
        form = OTPVerificationForm()


def _load_verification_view(request: HttpRequest, email: str) -> HttpResponse:
    """
    Renders the OTP verification view with the verification form.
    """

    form = OTPVerificationForm()
    request.session.save()
    return render(
        request,
        "registration/verification.html",
        {"form": form, "email": email},
    )


def resend_otp(request: HttpRequest) -> HttpResponse:
    """
    Resends OTP verification code to the user's email.
    """

    email = request.session.get("email")

    if not email:
        messages.error(request, _("Session expired. Please register again."))
        return redirect("register")

    try:
        user = User.objects.get(email=email)
        profile = user.profile

        if profile.is_otp_verified:
            messages.success(request, _("Your account is already verified."))
            return redirect("login")

        if not profile.is_account_activated:
            messages.error(request, _("Your account has not been activated yet."))
            return redirect("otp_verification")

        generate_and_send_otp(profile)

        messages.success(
            request, _("A new verification code has been sent to your email.")
        )
        return redirect("otp_verification")

    except User.DoesNotExist:
        messages.error(request, _("No account found with this email address."))
        return redirect("otp_verification")


class CustomLoginView(LoginView):
    """
    Adds verification checks to ensure users have activated accounts before login.
    Staff users are exempt from activation requirements.
    """

    def form_valid(self, form: AuthenticationForm) -> HttpResponse:
        """
        Check account activation status.
        Creates user profile if missing and validates activation requirements.
        """
        user = form.get_user()

        try:
            profile = user.profile

            is_staff = user.is_staff
            is_activated = profile.is_account_activated and profile.is_otp_verified

            if not is_activated and not is_staff:
                messages.error(
                    self.request,
                    _("Your account is not activated"),
                )
                return self.form_invalid(form)
        except:
            Profile.objects.create(user=user)
            if not is_staff:
                messages.error(
                    self.request,
                    _("Your account is not activated"),
                )
                return self.form_invalid(form)

        return super().form_valid(form)

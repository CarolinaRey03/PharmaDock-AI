from functools import wraps
from typing import Any, Callable

from django.contrib import messages
from django.contrib.auth import logout
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.utils.translation import gettext as _


def account_activated_required(
    function: Callable[..., HttpResponse],
) -> Callable[..., HttpResponse]:
    """
    Decorator that checks if the user is authenticated
    and has an activated account.
    Staff users bypass the activation check.
    Redirects to login page if requirements are not met.
    """

    @wraps(function)
    def wrap(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not request.user.is_authenticated:
            return redirect("login")

        if request.user.is_staff:
            return function(request, *args, **kwargs)

        try:
            account_not_activated = (
                not request.user.profile.is_account_activated
                or not request.user.profile.is_otp_verified
            )
            if account_not_activated:
                messages.error(
                    request,
                    _("Your account is not activated"),
                )
                logout(request)
                return redirect("login")
        except:
            messages.error(
                request,
                _(
                    "There's been an error with your account. Please, contact with the administrator."
                ),
            )
            logout(request)
            return redirect("login")

        return function(request, *args, **kwargs)

    return wrap

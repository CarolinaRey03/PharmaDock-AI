"""
URL configuration for web project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from django.views.i18n import JavaScriptCatalog

from src.apps.chat.views import (
    chat,
    chat_message,
    end_conversation,
    get_docking_file,
    get_docking_log,
    home,
)

from src.apps.accounts.views import (
    logout_view,
    register,
    otp_verification,
    resend_otp,
    CustomLoginView
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("i18n/", include("django.conf.urls.i18n")),
    path("jsi18n/", JavaScriptCatalog.as_view(), name="js-catalog"),
    path("chat/", chat, name="chat"),
    path("chat/message/", chat_message, name="chat_message"),
    path(
        "chat/get-docking-file/<path:file_path>/",
        get_docking_file,
        name="get_docking_file",
    ),
    path(
        "chat/get-docking-log/<path:file_path>/",
        get_docking_log,
        name="get_docking_log",
    ),
    path("chat/end/", end_conversation, name="end_conversation"),
    path("accounts/", include("django.contrib.auth.urls")),
    path(
        "accounts/login/",
        CustomLoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("logout/", logout_view, name="logout"),
    path("accounts/register/", register, name="register"),
    path("verify/", otp_verification, name="otp_verification"),
    path("verify/resend/", resend_otp, name="resend_otp"),
]

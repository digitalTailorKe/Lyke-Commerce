from django.urls import path
from userauths import views
from django.conf import settings
from django.conf.urls.static import static

app_name = "userauths"

urlpatterns = [
    path("sign-up/", views.register_view, name="sign-up"),
    path("sign-in/", views.login_view, name="sign-in"),

    # =======  Password reset =========


    # =======  end Password reset =========
    path("sign-out/", views.logout_view, name="sign-out"),

    path("profile/update/", views.profile_update, name="profile-update"),
    path('auth-receiver', views.auth_receiver, name='auth_receiver'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
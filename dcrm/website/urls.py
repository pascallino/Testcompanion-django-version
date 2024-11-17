from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("about/", views.about, name="about"),
    path("features/", views.features, name="features"),
    path("contact/", views.contact, name="contact"),
    path("login_view/", views.login_view, name="login_view"),
    path("signup/", views.signup, name="signup"),
    path("signup_post/", views.signup_post, name="signup_post"),
    path("get_id/<email>/<pwd>", views.get_id, name="get_id"),
    path("testcompanion_confirm/<user_id>", views.testcompanion_confirm, name="testcompanion_confirm"),
    path("Registrationsuccess/<user_id>", views.Registrationsuccess, name="Registrationsuccess"),
    path("resend_confirm_mail/<user_id>", views.resend_confirm_mail, name="resend_confirm_mail"),
    path("sendcontactform/", views.send_contact_form, name="sendcontactform"),
     path("mainboard/<user_id>", views.mainboard, name="mainboard"),
    # path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("test/", views.test, name="test"),
]
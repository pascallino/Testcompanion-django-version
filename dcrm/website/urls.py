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
    path("saveuser/<user_id>", views.saveuser, name="saveuser"),
    path("deleteuser/<user_id>", views.deleteuser, name="deleteuser"),
    path("testcompanion_confirm/<user_id>", views.testcompanion_confirm, name="testcompanion_confirm"),
    path("Registrationsuccess/<user_id>", views.Registrationsuccess, name="Registrationsuccess"),
    path("resend_confirm_mail/<user_id>", views.resend_confirm_mail, name="resend_confirm_mail"),
    path("sendcontactform/", views.send_contact_form, name="sendcontactform"),
    path("mainboard/<user_id>", views.mainboard, name="mainboard"),
    path("get_user/<user_id>", views.get_user, name="get_user"),
    path("userboard/<user_id>", views.userboard, name="userboard"),
    path("emailboard/<user_id>", views.emailboard, name="emailboard"),
    path("profileboard/<user_id>", views.profileboard, name="profileboard"),
    path("updatemailstatus/", views.updatemailstatus, name="updatemailstatus"),
    path("savemail/<user_id>", views.savemail, name="savemail"),
    path("get_mail/<email_id>", views.get_mail, name="get_mail"),
    path("deletemail/<email_id>", views.deletemail, name="deletemail"),
    path("testmail/<email_id>/<user_id>", views.testmail, name="testmail"),
    path("get_profile/<user_id>", views.get_profile, name="get_profile"),
    path("get_company/<user_id>", views.get_company, name="get_company"),
    path("savecompany/<user_id>", views.savecompany, name="savecompany"),
    path("saveprofile/<user_id>", views.saveprofile, name="saveprofile"),
    path("dashboard/<user_id>", views.dashboard, name="dashboard"),
    path("deletemaintest/<test_id>", views.deletemaintest, name="deletemaintest"),
    path("Addtestuser/<test_id>/<user_id>", views.Addtestuser, name="Addtestuser"),
    path("editquestion/<test_id>/<user_id>", views.editquestion, name="editquestion"),
    path("testlist/<test_id>", views.testlist, name="testlist"),
    path("rescheduletestget/<test_day_id>", views.rescheduletestget, name="rescheduletestget"),
    path("deletetestday/<test_day_id>", views.deletetestday, name="deletetestday"),
    path("resendmailget/<test_day_id>/<user_id>", views.resendmailget, name="resendmailget"),
    path("applicant/<test_day_id>", views.applicant, name="applicant"),
    path("rescheduletestpost/<test_day_id>", views.rescheduletestpost, name="rescheduletestpost"),
    path("resendmailpost/<test_day_id>/<user_id>", views.resendmailpost, name="resendmailpost"),
    path("savetest/<user_id>", views.savetest, name="savetest"),
    path("computescore/<test_day_id>", views.computescore, name="computescore"),
    path("testsummary/<test_id>/<test_day_id>/<user_id>", views.testsummary, name="testsummary"),
    path("get_test/<user_id>", views.get_test, name="get_test"),
    path("question_post/", views.question_post, name="question_post"),
    path("question_post_delete/", views.question_post_delete, name="question_post_delete"),
    path("get_data/<test_id>/<user_id>", views.get_data, name="get_data"),
    path("uploadimages/<test_id>", views.uploadimages, name="uploadimages"),
    path("posttest_getquestions/", views.posttest_getquestions, name="posttest_getquestions"),
    path("authenticate_applicant/<user_id>/<secret_key>", views.authenticate_applicant, name="authenticate_applicant"),
    path("Addtestuserpost/<test_id>/<user_id>", views.Addtestuserpost, name="Addtestuserpost"),
    path("get_question/<question_num>/<test_day_id>/<user_id>", views.get_question, name="get_question"),
    path("question_count/<test_day_id>/<user_id>", views.question_count, name="question_count"),
    path("post_selection/", views.post_selection, name="post_selection"),
    path("taketest/<user_id>/<key>", views.taketest, name="taketest"),
    path("Timeout/<test_day_id>/<user_id>", views.Timeout, name="Timeout"),
    path("set_timezone/", views.set_timezone, name="set_timezone"),
    # path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("test/", views.test, name="test"),
]
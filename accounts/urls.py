from django.urls import path
# from .views import CustomLoginView, complete_profile_view, post_login_redirect_view, signup_view, SignUpView
from .views import CompleteProfileView, LoginCBV, PostLoginRedirectView, SignUpView
# from django.contrib.auth.views import PasswordResetView, LogoutView

# urlpatterns = [
#     path("signup/", signup_view, name="signup"),
#     path("login/", CustomLoginView.as_view(), name="login"),
#     path("tester/", SignUpView.as_view(), name="tester"),
#     path("post-login/", post_login_redirect_view, name="post_login_redirect"),
#     path("complete-profile/", complete_profile_view, name="complete_profile"),
# ]

urlpatterns = [
    path("login/", LoginCBV.as_view(), name="accounts.login"),
    path("signup/", SignUpView.as_view(), name="accounts.signup"),
    # path("logout/", SignUpView.as_view(), name="accounts.signup"),
    path("post-login/", PostLoginRedirectView.as_view(), name="accounts.post_login_redirect"),
    path("complete-profile/", CompleteProfileView.as_view(), name="accounts.complete_profile"),
    # path("password-reset/", PasswordResetView.as_view(), name="accounts.password_reset"),
    # help page later:
    # path("help/", HelpView.as_view(), name="help"),
]
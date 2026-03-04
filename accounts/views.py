# from django.contrib.auth import login
# from django.contrib.auth.decorators import login_required
# from django.contrib.auth.views import LoginView
# from django.db import transaction
# from django.shortcuts import redirect, render
# from django.urls import reverse_lazy
# from django.views.generic import (
#     DetailView,
#     UpdateView,
#     CreateView,
#     DeleteView,
# )

# from .forms import ProfileCompletionForm, SignUpForm
# from .models import UserProfile
# from .utils import is_profile_complete


# class SignUpView(CreateView):
#     model = UserProfile
#     fields = ("phone_number", "phone_number")


#     def get_success_url(self):
#         return reverse_lazy("accounts.post_login_redirect")


# def signup_view(request):
#     breakpoint()
#     if request.user.is_authenticated:
#         return redirect("accounts.post_login_redirect")

#     if request.method == "POST":
#         form = SignUpForm(request.POST)
#         if form.is_valid():
#             user = form.save()
#             login(request, user)
#             return redirect("accounts.post_login_redirect")
#     else:
#         form = SignUpForm()

#     return render(request, "accounts/signup.html", {"form": form})


# class CustomLoginView(LoginView):
#     template_name = "accounts/login.html"

#     def get_success_url(self):
#         return reverse_lazy("accounts.post_login_redirect")


# @login_required
# def post_login_redirect_view(request):
#     """
#     Single place to decide where users land after login/signup.
#     Uses select_related('profile') to avoid extra queries.
#     """
#     user = (
#         request.user.__class__.objects  # works even with custom user
#         .select_related("profile")
#         .get(pk=request.user.pk)
#     )

#     # Ensure profile exists (in case user was created via admin/shell)
#     # If you *always* create profile in create_user/registration, this is rarely hit.
#     profile = getattr(user, "profile", None)
#     if profile is None:
#         profile = UserProfile.objects.create(user=user)

#     if not is_profile_complete(profile):
#         return redirect("complete_profile")

#     # Role-based redirect example
#     if profile.role == UserProfile.RUNNER:
#         return redirect("runner_dashboard")
#     return redirect("customer_dashboard")


# @login_required
# def complete_profile_view(request):
#     """
#     Lets the user fill in remaining profile fields after signup/login.
#     """
#     # Query with select_related for consistency
#     user = request.user.__class__.objects.select_related("profile").get(pk=request.user.pk)
#     profile = getattr(user, "profile", None)
#     if profile is None:
#         profile = UserProfile.objects.create(user=user)

#     if request.method == "POST":
#         form = ProfileCompletionForm(request.POST, instance=profile)
#         if form.is_valid():
#             form.save()
#             return redirect("accounts.post_login_redirect")
#     else:
#         form = ProfileCompletionForm(instance=profile)

#     return render(request, "accounts/complete_profile.html", {"form": form, "profile": profile})

from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, RedirectView, TemplateView

from .forms import ProfileCompletionForm, SignupForm, EmailAuthenticationForm
from .models import UserProfile
from .utils import is_profile_complete


# def is_htmx(request) -> bool:
#     return request.headers.get("HX-Request") == "true"


class HomeView(TemplateView):
    template_name = "home/index.html"


class LoginCBV(LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailAuthenticationForm

    def get_success_url(self):
        return reverse_lazy("accounts.post_login_redirect")

    def form_invalid(self, form):
        # breakpoint()
        # if self.request.htmx:
            # breakpoint()
            # return self.render_to_response({"form": form, "mode": "login"})
            # return render(
            #     self.request,
            #     "accounts/partials/_auth_form.html",
            #     {"form": form, "mode": "login"},
            #     status=400,
        #     # )

        # if self.request.htmx:
        #     return render(
        #         self.request,
        #         "accounts/partials/_auth_form.html",
        #         {
        #             "form": form,
        #             "form_action": self.request.path,
        #             "form_id": "login-form",
        #             "submit_label": "Login",
        #             "is_login": True,
        #             "is_signup": False,
        #             "mode": "login",
        #         },
        #         status=400,
        #     )

        # return super().form_invalid(form)
    

        if self.request.htmx:
            return render(
                self.request,
                "accounts/partials/_auth_form.html",
                {
                    "form": form,
                    "form_action": self.request.path,
                    "form_id": "login-form",
                    "submit_label": "Login",
                    "is_login": True,
                    "is_signup": False,
                    "mode": "login",
                },
                status=200,  # ← HTMX swaps on 200 by default
            )
        return super().form_invalid(form)


        # return super().form_invalid(form)


class SignUpView(FormView):
    template_name = "accounts/signup.html"
    form_class = SignupForm
    success_url = reverse_lazy("accounts.post_login_redirect")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("accounts.post_login_redirect")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, "Welcome to AfroYege!")
        return super().form_valid(form)

    def form_invalid(self, form):
        # if is_htmx(self.request):
        if self.request.htmx:
            return self.render_to_response({"form": form, "mode": "signup"}, template_name="accounts/partials/_auth_form.html")
        return super().form_invalid(form)


class PostLoginRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        user_model = self.request.user.__class__
        user = user_model.objects.select_related("profile").get(pk=self.request.user.pk)

        profile = getattr(user, "profile", None)
        if profile is None or not is_profile_complete(profile):
            return reverse_lazy("accounts.complete_profile")

        if profile.role == UserProfile.RUNNER:
            return reverse_lazy("runner_dashboard")  # create later
        return reverse_lazy("customer_dashboard")  # create later


class CompleteProfileView(LoginRequiredMixin, FormView):
    template_name = "accounts/complete_profile.html"
    form_class = ProfileCompletionForm
    success_url = reverse_lazy("accounts.post_login_redirect")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user_model = self.request.user.__class__
        user = user_model.objects.select_related("profile").get(pk=self.request.user.pk)
        profile = getattr(user, "profile", None)

        # If user created via admin/shell, create profile now (not for system/anonymous because they shouldn’t log in)
        if profile is None:
            profile = UserProfile.objects.create(user=user, role=UserProfile.CUSTOMER, phone_number="")

        kwargs["instance"] = profile
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Profile updated.")
        return super().form_valid(form)

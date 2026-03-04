from django import forms
# from django.contrib.auth import authenticate, get_user_model
# from django.db import transaction

from .models import UserProfile

# User = get_user_model()


# class SignUpForm(forms.Form):
#     email = forms.EmailField()
#     password1 = forms.CharField(widget=forms.PasswordInput)
#     password2 = forms.CharField(widget=forms.PasswordInput)

#     # minimal profile fields at signup
#     role = forms.ChoiceField(choices=UserProfile.USER_ROLES)
#     phone_number = forms.CharField(max_length=20)

#     def clean_email(self):
#         email = self.cleaned_data["email"].lower().strip()
#         if User.objects.filter(email=email).exists():
#             raise forms.ValidationError("An account with this email already exists.")
#         return email

#     def clean(self):
#         cleaned = super().clean()
#         if cleaned.get("password1") != cleaned.get("password2"):
#             self.add_error("password2", "Passwords do not match.")
#         return cleaned

#     @transaction.atomic
#     def save(self):
#         user = User.objects.create_user(
#             email=self.cleaned_data["email"],
#             password=self.cleaned_data["password1"],
#         )
#         UserProfile.objects.create(
#             user=user,
#             role=self.cleaned_data["role"],
#             phone_number=self.cleaned_data["phone_number"],
#         )
#         return user


class ProfileCompletionForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = (
            "address_line",
            "postcode",
            "preferred_areas",
        )
        widgets = {
            "address_line": forms.Textarea(attrs={"rows": 3}),
            "preferred_areas": forms.Textarea(attrs={"rows": 3}),
        }




# accounts/forms.py
# ─────────────────────────────────────────────────────────────
# All form fields inject Tailwind classes via widget attrs
# so the _auth_form.html partial just calls {{ field }} and
# gets a fully styled input — no manual wrapping needed.
# ─────────────────────────────────────────────────────────────

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model

User = get_user_model()

# ── Shared Tailwind classes for inputs ──────────────────────
INPUT_CLASSES = (
    "w-full bg-white border-2 border-sand rounded-xl px-4 py-3 "
    "text-brand placeholder-brand-muted/50 text-sm "
    "focus:outline-none focus:border-gold transition "
    "disabled:opacity-50 disabled:cursor-not-allowed"
)

INPUT_ERROR_CLASSES = (
    "w-full bg-white border-2 border-red-300 rounded-xl px-4 py-3 "
    "text-brand placeholder-brand-muted/50 text-sm "
    "focus:outline-none focus:border-red-400 transition pr-10"
)


def styled(widget_cls, **kwargs):
    """Helper: returns a widget instance with Tailwind classes applied."""
    attrs = kwargs.pop("attrs", {})
    attrs.setdefault("class", INPUT_CLASSES)
    return widget_cls(attrs=attrs, **kwargs)


# ── Login Form ───────────────────────────────────────────────
class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=styled(forms.EmailInput, attrs={
            "class": INPUT_CLASSES,
            "placeholder": "you@example.com",
            "autocomplete": "email",
        }),
    )
    password = forms.CharField(
        label="Password",
        widget=styled(forms.PasswordInput, attrs={
            "class": INPUT_CLASSES,
            "placeholder": "••••••••",
            "autocomplete": "current-password",
        }),
    )

    error_messages = {
        "invalid_login": "Incorrect email or password. Please try again.",
        "inactive": "This account is inactive.",
    }


class SignupForm(forms.ModelForm):
    first_name = forms.CharField(
        label="First Name",
        widget=styled(forms.TextInput, attrs={"placeholder": "First name"}),
    )
    last_name = forms.CharField(
        label="Last Name",
        widget=styled(forms.TextInput, attrs={"placeholder": "Last name"}),
    )
    email = forms.EmailField(
        label="Email",
        widget=styled(forms.EmailInput, attrs={
            "placeholder": "you@example.com",
            "autocomplete": "email",
        }),
    )
    phone = forms.CharField(
        label="Phone",
        widget=styled(forms.TextInput, attrs={"type": "tel", "placeholder": "+44 7700 000000"}),
    )
    password = forms.CharField(
        label="Password",
        widget=styled(forms.PasswordInput, attrs={
            "placeholder": "Min. 8 characters",
            "autocomplete": "new-password",
        }),
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=styled(forms.PasswordInput, attrs={
            "placeholder": "Repeat password",
            "autocomplete": "new-password",
        }),
    )
    address = forms.CharField(
        label="Address",
        widget=styled(forms.TextInput, attrs={"placeholder": "Your delivery address"}),
    )
    postcode = forms.CharField(
        label="Postcode",
        max_length=10,
        widget=styled(forms.TextInput, attrs={"placeholder": "e.g. E11 1AA"}),
    )
    # account_type is handled in the template via radio buttons
    # and posted as a plain POST value — not a ModelForm field
    account_type = forms.ChoiceField(
        choices=UserProfile.USER_ROLES,
        widget=forms.HiddenInput(),  # actual UI is in _auth_form.html
        initial="customer",
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone",
                  "password", "confirm_password", "address", "postcode", "account_type"]

    def clean(self):
        cleaned = super().clean()
        pw  = cleaned.get("password")
        cpw = cleaned.get("confirm_password")
        if pw and cpw and pw != cpw:
            self.add_error("confirm_password", "Passwords do not match.")
        return cleaned

    def clean_email(self):
        email = self.cleaned_data.get("email", "").lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email      = self.cleaned_data["email"]
        user.set_password(self.cleaned_data["password"])
        user.account_type = self.cleaned_data.get("account_type", "customer")
        if commit:
            user.save()
        return user

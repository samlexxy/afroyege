import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from lib_util.models import BaseModel
from .managers import UserManager


class User(AbstractUser):
    """
    Auth user: keep this lean.
    Login via email (no username).
    """
    username = None  # remove the field entirely
    email = models.EmailField(_("email address"), unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    objects = UserManager()

    def __str__(self):
        return self.email
    
    def get_initials(self):
        parts = self.get_full_name().split()
        return "".join(p[0].upper() for p in parts[:2]) or self.email[0].upper()


class UserProfile(BaseModel):
    """
    Business/domain fields live here.
    One-to-one with the auth User.
    """
    CUSTOMER = "CUSTOMER"
    RUNNER = "RUNNER"

    USER_ROLES = (
        (CUSTOMER, _("Customer")),
        (RUNNER, _("Runner")),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    # Core business identity
    role = models.CharField(max_length=20, choices=USER_ROLES, default=CUSTOMER)

    phone_number = models.CharField(max_length=20, unique=True)
    phone_verified = models.BooleanField(default=False)

    address_line = models.TextField(blank=True, default="")
    postcode = models.CharField(max_length=16, blank=True, default="")

    # Runner-specific verification flags
    is_runner_verified = models.BooleanField(default=False)
    runner_id_verified = models.BooleanField(default=False)
    runner_suspension_count = models.PositiveIntegerField(default=0)
    is_suspended = models.BooleanField(default=False)
    suspension_reason = models.TextField(blank=True, default="")
    preferred_areas = models.TextField(blank=True, default="")

    # Reputation
    rating_total = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    rating_count = models.PositiveIntegerField(default=0)

    @property
    def average_rating(self):
        if self.rating_count == 0:
            return None
        return round(self.rating_total / self.rating_count, 2)

    def __str__(self):
        return f"{self.user.email} ({self.role})"
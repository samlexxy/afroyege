from django.db import models
import uuid

# from __future__ import annotations

from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone
from lib_util.models import BaseModel
from accounts.models import User
from django.utils.translation import gettext_lazy as _


class Order(BaseModel):
    ALLOW_SUBSTITUTE = "ALLOW_SUBSTITUTE"
    ASK_FIRST = "ASK_FIRST"
    NO_SUBSTITUTE = "NO_SUBSTITUTE"

    SUBSTITUTION_MODES = (
        (ALLOW_SUBSTITUTE, _("Allow Substitute")),
        (ASK_FIRST, _("Ask First")),
        (NO_SUBSTITUTE, _("No Substitute")),
    )

    CREATED = "CREATED"
    PREAUTHORIZED = "PREAUTHORIZED"
    RUNNER_ACCEPTED = "RUNNER_ACCEPTED"
    SHOPPING = "SHOPPING"
    PROOF_UPLOADED = "PROOF_UPLOADED"
    DELIVERING = "DELIVERING"
    DELIVERED = "DELIVERED"
    AWAITING_CONFIRMATION = "AWAITING_CONFIRMATION"
    CONFIRMED = "CONFIRMED"
    CAPTURED = "CAPTURED"
    DISPUTED = "DISPUTED"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"

    STATUSES = (
        (CREATED, _("Created")),
        (PREAUTHORIZED, _("Preauthorized")),
        (RUNNER_ACCEPTED, _("Runner accepted")),
        (SHOPPING, _("Shopping")),
        (PROOF_UPLOADED, _("Proof uploaded")),
        (DELIVERING, _("Delivering")),
        (DELIVERED, _("Delivered")),
        (AWAITING_CONFIRMATION, _("Awaiting confirmation")),
        (CONFIRMED, _("Confirmed")),
        (CAPTURED, _("Captured")),
        (DISPUTED, _("Disputed")),
        (REFUNDED, _("Refunded")),
        (CANCELLED, _("Cancelled"))
    )


    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        User, related_name="customer_orders", on_delete=models.PROTECT
    )
    runner = models.ForeignKey(
        User, related_name="runner_orders", null=True, blank=True, on_delete=models.PROTECT
    )

    status = models.CharField(max_length=32, choices=STATUSES, default=CREATED)
    completed_at = models.DateTimeField(null=True, blank=True),  

    currency = models.CharField(max_length=3, default="GBP")

    # Store(s)
    preferred_store_1 = models.CharField(max_length=255, blank=True)
    preferred_store_2 = models.CharField(max_length=255, blank=True)

    # Delivery
    delivery_address  = models.TextField()
    delivery_postcode = models.CharField(max_length=10)

    # Controls
    spending_limit = models.DecimalField(max_digits=10, decimal_places=2)
    substitution_mode = models.CharField(
        max_length=32, choices=SUBSTITUTION_MODES, default=ASK_FIRST
    )
    notes = models.TextField(blank=True)

    # Timers / deadlines (store deadlines, not "minutes")
    acceptance_deadline_at = models.DateTimeField(null=True, blank=True)
    substitution_deadline_at = models.DateTimeField(null=True, blank=True)
    confirmation_deadline_at = models.DateTimeField(null=True, blank=True)

    # Delivery code
    delivery_code_hash = models.CharField(max_length=128, blank=True)
    delivery_code_attempts = models.PositiveSmallIntegerField(default=0)
    delivery_code_locked = models.BooleanField(default=False)

    # Financials (populated when proof is confirmed)
    total_spend  = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    delivery_fee = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    # created_at = models.DateTimeField(default=timezone.now)
    # updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creation_date"]

    def __str__(self):
        return f"Order #{self.pk} — {self.customer} [{self.status}]"

    @property
    def item_count(self):
        return self.items.count()
    
    @property
    def store_count(self):
        return 2 if self.preferred_store_2 else 1
    
    @property
    def is_active(self):
        return self.status in (
            self.CREATED,
            self.SHOPPING,
            self.DELIVERING,
            self.DELIVERED,
        )
    
    # ── Progress steps for tracking template ────────────────
    def get_progress_steps(self):
        order = [
            self.CREATED,
            self.SHOPPING,
            self.DELIVERING,
            self.DELIVERED,
        ]
        labels = {
            self.CREATED:     ("Created",     "📝"),
            self.SHOPPING:   ("Shopping",   "🛒"),
            self.DELIVERING: ("Delivering", "🚗"),
            self.DELIVERED:  ("Delivered",  "✅"),
        }
        try:
            current_index = order.index(self.status)
        except ValueError:
            current_index = len(order)  # completed/cancelled

        steps = []
        for i, s in enumerate(order):
            label, emoji = labels[s]
            steps.append({
                "label":  label,
                "emoji":  emoji,
                "done":   i < current_index,
                "active": i == current_index,
            })
        return steps

    def complete(self):
        self.status = self.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at", "last_modified_date"])

    def can_customer_cancel(self) -> bool:
        return self.status in {self.CREATED, self.PREAUTHORIZED}

    def can_runner_cancel(self) -> bool:
        return self.status in {self.PREAUTHORIZED, self.RUNNER_ACCEPTED}

    def require_no_customer_cancel_after_accept(self) -> None:
        # aligned with: "Customer cancellation disabled after RUNNER_ACCEPTED" :contentReference[oaicite:2]{index=2}
        not_allowed_statuses = (self.RUNNER_ACCEPTED, self.SHOPPING, self.PROOF_UPLOADED, self.DELIVERED, self.AWAITING_CONFIRMATION, self.CONFIRMED)
        if self.status in not_allowed_statuses:
            raise ValueError("Customer cancellation not allowed after runner acceptance.")


# class OrderItem(models.Model):
#     order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
#     name = models.CharField(max_length=255)
#     notes = models.TextField(blank=True)
#     # keep status simple for MVP
#     status = models.CharField(max_length=32, default="REQUESTED")
#     created_at = models.DateTimeField(default=timezone.now)



class OrderItem(BaseModel):
    REQUESTED = "REQUESTED"
    PURCHASED = "PURCHASED"
    SUBSTITUTED = "SUBSTITUTED"
    REMOVED = "REMOVED"

    ITEM_STATUSES = (
        (REQUESTED, "Requested"),
        (PURCHASED, "Purchased"),
        (SUBSTITUTED, "Substituted"),
        (REMOVED, "Removed"),
    )

    uuid    = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    name  = models.CharField(max_length=255, blank="")
    quantity = models.PositiveSmallIntegerField(default=1)
    notes = models.TextField(
        blank=True,
        default="",
    )
    status = models.CharField(
        max_length=20,
        choices=ITEM_STATUSES,
        default=REQUESTED,
    )

    # Substitution tracking
    substitution_requested_at = models.DateTimeField(null=True, blank=True)
    substitution_resolved_at  = models.DateTimeField(null=True, blank=True)
    substitution_note         = models.TextField(blank=True)

    # Photos (stored in object storage; URLs saved here)
    photo_url = models.URLField(blank=True)

    def __str__(self):
        return f"{self.quantity}x {self.name} [{self.status}]"


class SubstitutionRequest(BaseModel):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"

    STATUSES = (
        (PENDING, _("PENDING")),
        (APPROVED, _("APPROVED")),
        (DECLINED, _("DECLINED"))
    )

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="substitutions")
    original_item  = models.CharField(max_length=200)
    suggested_item = models.CharField(max_length=200)
    status         = models.CharField(max_length=10, choices=STATUSES, default=PENDING)
    resolved_at    = models.DateTimeField(null=True, blank=True)

    def approve(self):
        self.status      = self.Status.APPROVED
        self.resolved_at = timezone.now()
        self.save(update_fields=["status", "resolved_at"])

    def decline(self):
        self.status      = self.Status.DECLINED
        self.resolved_at = timezone.now()
        self.save(update_fields=["status", "resolved_at"])

    def __str__(self):
        return f"Sub: {self.original_item} → {self.suggested_item} [{self.status}]"


class ChatMessage(BaseModel):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order      = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="messages")
    sender     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content    = models.TextField()

    class Meta:
        ordering = ["creation_date"]

    def __str__(self):
        return f"[{self.order_id}] {self.sender}: {self.content[:40]}"


class ProofOfPurchase(BaseModel):

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order         = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="proof")
    preferred_store_1    = models.CharField(max_length=120, blank=True)
    total_amount  = models.DecimalField(max_digits=8, decimal_places=2)
    receipt_image = models.ImageField(upload_to="proofs/receipts/", null=True, blank=True)
    basket_photo  = models.ImageField(upload_to="proofs/baskets/",  null=True, blank=True)

    def __str__(self):
        return f"Proof for Order #{self.order_id} — £{self.total_amount}"


class ProofItemPhoto(BaseModel):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    proof = models.ForeignKey(ProofOfPurchase, on_delete=models.CASCADE, related_name="item_photos")
    image = models.ImageField(upload_to="proofs/items/")
    created_at = models.DateTimeField(auto_now_add=True)


class RunnerRating(BaseModel):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order      = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="rating")
    runner     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ratings_received",
    )
    customer   = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ratings_given",
    )
    score      = models.PositiveSmallIntegerField()          # 1–5
    attributes = models.JSONField(default=list, blank=True)  # ["On time", "Friendly"]
    feedback   = models.TextField(blank=True)

    def __str__(self):
        return f"Rating {self.score}★ for {self.runner} on Order #{self.order_id}"
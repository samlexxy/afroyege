from django import forms
from .models import Order, OrderItem, RunnerRating

# ── Shared Tailwind input class ──────────────────────────────
INPUT = (
    "w-full bg-white border-2 border-sand rounded-xl px-4 py-3 "
    "text-brand placeholder-brand-muted/50 text-sm "
    "focus:outline-none focus:border-gold transition"
)
INPUT_SM = INPUT.replace("py-3", "py-2.5")
TEXTAREA = INPUT + " resize-none"


# ─────────────────────────────────────────────────────────────
# CREATE ERRAND FORM
# ─────────────────────────────────────────────────────────────
class CreateOrderForm(forms.ModelForm):

    # Second store is optional, not on model directly
    store_name_2 = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": INPUT_SM,
            "placeholder": "e.g. Waitrose, Aldi",
        }),
    )

    class Meta:
        model  = Order
        fields = [
            "delivery_address",
            "delivery_postcode",
            "preferred_store_1",
            "spending_limit",
            "substitution_mode",
            "notes",
        ]
        widgets = {
            "delivery_address": forms.TextInput(attrs={
                "class": INPUT_SM,
                "placeholder": "Full delivery address",
                "autocomplete": "street-address",
            }),
            "delivery_postcode": forms.TextInput(attrs={
                "class": INPUT_SM,
                "placeholder": "e.g. E11 1AA",
                "autocomplete": "postal-code",
            }),
            "preferred_store_1": forms.TextInput(attrs={
                "class": INPUT_SM,
                "placeholder": "e.g. Tesco, Lidl, Sainsbury's",
            }),
            "spending_limit": forms.NumberInput(attrs={
                "class": INPUT_SM + " pl-7",  # space for £ prefix
                "placeholder": "0.00",
                "min": "1",
                "step": "0.01",
            }),
            "substitution_mode": forms.HiddenInput(),  # handled by radio UI
            "notes": forms.Textarea(attrs={
                "class": TEXTAREA,
                "placeholder": "Any special instructions for your runner…",
                "rows": 3,
            }),
        }

    def clean_spending_limit(self):
        limit = self.cleaned_data.get("spending_limit")
        if limit is not None and limit <= 0:
            raise forms.ValidationError("Spending limit must be greater than £0.")
        return limit

    def save_with_items(self, customer, items_data):
        """
        Call instead of plain .save() to atomically create
        the order and its items.
        items_data: list of {"name": str, "quantity": int}
        """
        order = self.save(commit=False)
        order.customer = customer
        # persist second store
        order.store_name_2 = self.cleaned_data.get("store_name_2", "")
        order.save()

        for item in items_data:
            name = item.get("name", "").strip()
            if name:
                OrderItem.objects.create(
                    order=order,
                    name=name,
                    quantity=max(1, int(item.get("quantity") or 1)),
                )
        return order


# ─────────────────────────────────────────────────────────────
# COMPLETE PROFILE FORM  (accounts app uses this too)
# ─────────────────────────────────────────────────────────────
class CompleteProfileForm(forms.Form):
    substitution_mode = forms.ChoiceField(
        choices=Order.SUBSTITUTION_MODES,
        initial="Allow Substitute",
        widget=forms.RadioSelect(),  # custom UI in template
    )
    allergy_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "class": TEXTAREA,
            "placeholder": "e.g. Nut allergy, dairy free, gluten intolerance…",
            "rows": 2,
        }),
    )
    address = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": INPUT_SM,
            "placeholder": "Your default delivery address",
            "autocomplete": "street-address",
        }),
    )
    postcode = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            "class": INPUT_SM,
            "placeholder": "e.g. E11 1AA",
            "autocomplete": "postal-code",
        }),
    )


# ─────────────────────────────────────────────────────────────
# RUNNER RATING FORM
# ─────────────────────────────────────────────────────────────
class RunnerRatingForm(forms.ModelForm):

    ATTRIBUTE_CHOICES = [
        ("On time",    "On time"),
        ("Good comms", "Good comms"),
        ("Accurate",   "Accurate"),
        ("Friendly",   "Friendly"),
        ("Helpful",    "Helpful"),
        ("Fast",       "Fast"),
    ]

    attributes = forms.MultipleChoiceField(
        choices=ATTRIBUTE_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(),  # custom chip UI in template
    )

    class Meta:
        model  = RunnerRating
        fields = ["score", "attributes", "feedback"]
        widgets = {
            "score": forms.HiddenInput(),  # set by star click in template
            "feedback": forms.Textarea(attrs={
                "class": TEXTAREA,
                "placeholder": "Tell us about your experience…",
                "rows": 3,
            }),
        }

    def clean_score(self):
        score = self.cleaned_data.get("score")
        if score not in range(1, 6):
            raise forms.ValidationError("Please select a rating between 1 and 5 stars.")
        return score

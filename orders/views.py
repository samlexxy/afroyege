from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.utils import timezone
from django.views import View
from django.utils.decorators import method_decorator

from .models import Order, OrderItem, SubstitutionRequest, ChatMessage, RunnerRating
from .forms  import CreateOrderForm, RunnerRatingForm


# ── HTMX helper ─────────────────────────────────────────────
def is_htmx(request):
    return request.headers.get("HX-Request") == "true"

def htmx_redirect(url):
    """204 + HX-Redirect — no HTML body, HTMX navigates the page."""
    r = HttpResponse(status=204)
    r["HX-Redirect"] = url
    return r


# ─────────────────────────────────────────────────────────────
# MY ORDERS LIST
# ─────────────────────────────────────────────────────────────
@method_decorator(login_required, name="dispatch")
class OrderListView(View):

    def get(self, request):
        qs = Order.objects.filter(customer=request.user).select_related("runner")

        status_filter = request.GET.get("status", "all")
        if status_filter == "active":
            qs = qs.filter(status__in=[
                Order.CREATED, Order.SHOPPING,
                Order.DELIVERING, Order.DELIVERED,
            ])
        elif status_filter == "completed":
            qs = qs.filter(status=Order.CONFIRMED)

        has_active = Order.objects.filter(
            customer=request.user,
            status__in=[Order.CREATED, Order.SHOPPING,
                        Order.DELIVERING, Order.DELIVERED],
        ).exists()

        ctx = {
            "orders": qs,
            "current_filter": status_filter,
            "has_active_orders": has_active,
        }

        # HTMX partial poll — return just the list fragment
        if is_htmx(request) and request.GET.get("partial"):
            return render(request, "orders/partials/_order_list.html", ctx)

        return render(request, "orders/list.html", ctx)


# ─────────────────────────────────────────────────────────────
# CREATE ERRAND
# ─────────────────────────────────────────────────────────────
@method_decorator(login_required, name="dispatch")
class OrderCreateView(View):

    def get(self, request):
        # Pre-fill address/postcode from user profile
        user = request.user
        initial = {}
        if hasattr(user, "profile"):
            initial["delivery_address"]  = user.profile.address_line  or ""
            initial["delivery_postcode"] = user.profile.postcode or ""
            # initial["substitution_mode"] = user.profile.substitution_mode or "ask"
            initial["substitution_mode"] = "ask"

        form = CreateOrderForm(initial=initial)
        return render(request, "orders/create.html", {"form": form})

    def post(self, request):
        form = CreateOrderForm(data=request.POST)

        # breakpoint()

        if form.is_valid():
            # Parse dynamic item rows from POST
            # Template posts item_name[] and item_qty[] arrays
            names = request.POST.getlist("item_name[]")
            qtys  = request.POST.getlist("item_qty[]")
            items_data = [
                {"name": n, "quantity": q}
                for n, q in zip(names, qtys)
                if n.strip()
            ]
            
            breakpoint()

            if not items_data:
                form.add_error(None, "Please add at least one item to your errand.")
                return render(request, "orders/create.html", {"form": form}, status=422)

            order = form.save_with_items(
                customer=request.user,
                items_data=items_data,
            )
            messages.success(request, f"Errand #{order.pk} submitted! We're finding you a runner.")

            # Major action → full redirect
            return redirect("orders.tracking", pk=order.pk)

        return render(request, "orders/create.html", {"form": form}, status=422)


# ─────────────────────────────────────────────────────────────
# ORDER TRACKING
# ─────────────────────────────────────────────────────────────
@method_decorator(login_required, name="dispatch")
class OrderTrackingView(View):

    def get(self, request, pk):
        order = get_object_or_404(Order, uuid=pk, customer=request.user)
        ctx   = self._build_ctx(request, order)
        return render(request, "orders/tracking.html", ctx)

    @staticmethod
    def _build_ctx(request, order):
        pending_sub = (
            SubstitutionRequest.objects
            .filter(order=order, status=SubstitutionRequest.Status.PENDING)
            .first()
        )
        # Rough ETA display (replace with real logic)
        eta_display = None
        if order.status in (Order.Status.SHOPPING, Order.Status.DELIVERING):
            eta_display = "25:00"

        return {
            "order":                  order,
            "pending_substitution":   pending_sub,
            "estimated_delivery_display": eta_display,
            "messages":               order.messages.select_related("sender").order_by("created_at"),
        }


class OrderTrackingPartialView(View):
    """Polled by HTMX every 15s — returns just the status partial."""

    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk, customer=request.user)
        return render(request, "orders/partials/_tracking_status.html", {"order": order})


# ─────────────────────────────────────────────────────────────
# SUBSTITUTION  (approve / decline / partial)
# ─────────────────────────────────────────────────────────────
@method_decorator(login_required, name="dispatch")
class SubstitutionPartialView(View):
    """HTMX poll — returns alert partial (empty if nothing pending)."""

    def get(self, request, pk):
        order  = get_object_or_404(Order, pk=pk, customer=request.user)
        pending = SubstitutionRequest.objects.filter(
            order=order, status=SubstitutionRequest.Status.PENDING
        ).first()
        return render(request, "orders/partials/_substitution_alert.html", {
            "order": order, "pending_substitution": pending,
        })


@method_decorator(login_required, name="dispatch")
class ApproveSubstitutionView(View):

    def post(self, request, pk):
        sub = get_object_or_404(SubstitutionRequest, pk=pk, order__customer=request.user)
        sub.approve()
        # Return empty partial — alert disappears
        return render(request, "orders/partials/_substitution_alert.html", {
            "order": sub.order, "pending_substitution": None,
        })


@method_decorator(login_required, name="dispatch")
class DeclineSubstitutionView(View):

    def post(self, request, pk):
        sub = get_object_or_404(SubstitutionRequest, pk=pk, order__customer=request.user)
        sub.decline()
        return render(request, "orders/partials/_substitution_alert.html", {
            "order": sub.order, "pending_substitution": None,
        })


# ─────────────────────────────────────────────────────────────
# CHAT
# ─────────────────────────────────────────────────────────────
@method_decorator(login_required, name="dispatch")
class ChatPartialView(View):
    """HTMX poll — returns latest messages."""

    def get(self, request, pk):
        order    = get_object_or_404(Order, pk=pk, customer=request.user)
        msgs     = order.messages.select_related("sender").order_by("created_at")
        return render(request, "orders/partials/_chat_messages.html", {
            "order": order, "messages": msgs,
        })


@method_decorator(login_required, name="dispatch")
class SendMessageView(View):

    def post(self, request, pk):
        order   = get_object_or_404(Order, pk=pk, customer=request.user)
        content = request.POST.get("message", "").strip()
        if content:
            ChatMessage.objects.create(order=order, sender=request.user, content=content)
        msgs = order.messages.select_related("sender").order_by("created_at")
        return render(request, "orders/partials/_chat_messages.html", {
            "order": order, "messages": msgs,
        })


# ─────────────────────────────────────────────────────────────
# PROOF OF PURCHASE
# ─────────────────────────────────────────────────────────────
@method_decorator(login_required, name="dispatch")
class ProofReviewView(View):

    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk, customer=request.user)
        if order.status != Order.Status.DELIVERED:
            return redirect("orders:tracking", pk=pk)

        proof = getattr(order, "proof", None)
        if not proof:
            messages.error(request, "No proof of purchase has been submitted yet.")
            return redirect("orders:tracking", pk=pk)

        # Auto-confirm in 5 minutes from proof submission
        elapsed  = (timezone.now() - proof.created_at).total_seconds()
        remaining = max(0, 300 - int(elapsed))
        mins, secs = divmod(remaining, 60)
        auto_confirm_display = f"{mins}:{secs:02d}"

        return render(request, "orders/proof_review.html", {
            "order":                order,
            "proof":                proof,
            "auto_confirm_display": auto_confirm_display,
        })


@method_decorator(login_required, name="dispatch")
class ConfirmPurchaseView(View):

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, customer=request.user)
        if order.status != Order.Status.DELIVERED:
            raise Http404

        # Set total_spend from proof
        proof = getattr(order, "proof", None)
        if proof:
            order.total_spend = proof.total_amount

        order.complete()
        messages.success(request, "Purchase confirmed! Payment has been released to your runner.")
        return redirect("orders:completion", pk=pk)


# ─────────────────────────────────────────────────────────────
# ORDER COMPLETION + RATING
# ─────────────────────────────────────────────────────────────
@method_decorator(login_required, name="dispatch")
class OrderCompletionView(View):

    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk, customer=request.user)
        if order.status != Order.Status.CONFIRMED:
            return redirect("orders:tracking", pk=pk)
        form = RunnerRatingForm()
        return render(request, "orders/completion.html", {"order": order, "form": form})


@method_decorator(login_required, name="dispatch")
class SubmitRatingView(View):

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, customer=request.user)
        form  = RunnerRatingForm(data=request.POST)

        if form.is_valid():
            # Guard: don't allow duplicate ratings
            if not RunnerRating.objects.filter(order=order).exists():
                RunnerRating.objects.create(
                    order=order,
                    runner=order.runner,
                    customer=request.user,
                    score=form.cleaned_data["score"],
                    attributes=form.cleaned_data.get("attributes", []),
                    feedback=form.cleaned_data.get("feedback", ""),
                )

            if is_htmx(request):
                # Swap the rating form with a thank-you message
                return render(request, "orders/partials/_rating_success.html", {"order": order})

            messages.success(request, "Thanks for rating your runner!")
            return redirect("orders:list")

        # Validation error — swap form back
        if is_htmx(request):
            return render(request, "orders/completion.html", {"order": order, "form": form}, status=422)
        return render(request, "orders/completion.html", {"order": order, "form": form}, status=422)


# ─────────────────────────────────────────────────────────────
# HTMX MICRO-PARTIALS  (item row / second store)
# ─────────────────────────────────────────────────────────────
@method_decorator(login_required, name="dispatch")
class AddItemRowView(View):
    """Returns a blank item row HTML fragment, appended to #items-container."""

    def get(self, request):
        # Count existing rows so name attributes stay unique
        index = int(request.GET.get("index", 0))
        return render(request, "orders/partials/_item_row.html", {"index": index})


@method_decorator(login_required, name="dispatch")
class SecondStorePartialView(View):

    def get(self, request):
        return render(request, "orders/partials/_second_store.html")

    def delete(self, request):
        # Return the "+ Add Second Store" button again
        return HttpResponse(
            '<button type="button" '
            'hx-get="{% url \'orders:second_store_partial\' %}" '
            'hx-target="#second-store-wrapper" hx-swap="innerHTML" '
            'class="text-sm font-semibold text-gold-dim hover:text-gold transition">'
            '+ Add Second Store</button>'
        )

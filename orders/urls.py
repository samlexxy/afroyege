from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path, include
from orders.views import (
    OrderListView, 
    OrderCreateView,
    SecondStorePartialView,
    AddItemRowView,
    OrderTrackingView,
    OrderTrackingPartialView
)

urlpatterns = [
    path('', OrderListView.as_view(), name='orders.list'),
    path('create/', OrderCreateView.as_view(), name='orders.create'),
    path('<int:pk>/tracking/', OrderTrackingView.as_view(), name='orders.tracking'),
    path('<int:pk>/tracking/partial/', OrderTrackingPartialView.as_view(), name='orders.tracking_partial'),
    # path('<int:pk>/proof/', ProofReviewView.as_view(), name='orders.proof_review'),
    # path('<int:pk>/confirm/', ConfirmPurchaseView.as_view(), name='orders.confirm_purchase'),
    # path('<int:pk>/complete/', CompletionView.as_view(), name='orders.completion'),
    # path('<int:pk>/rate/', SubmitRatingView.as_view(), name='orders.submit_rating'),
    # path('<int:pk>/chat/', ChatPartialView.as_view(), name='orders.chat_partial'),
    # path('<int:pk>/chat/send/', SendMessageView.as_view(), name='orders.send_message'),
    # path('<int:pk>/substitution/', SubstitutionPartialView.as_view(), name='orders.substitution_partial'),
    # path('substitution/<int:pk>/approve/', ApproveSubstitutionView.as_view(), name='orders.approve_substitution'),
    # path('substitution/<int:pk>/decline/', DeclineSubstitutionView.as_view(), name='orders.decline_substitution'),
    path('partials/item-row/', AddItemRowView.as_view(), name='orders.add_item_row'),
    path('partials/second-store/', SecondStorePartialView.as_view(), name='orders.second_store_partial'),
]


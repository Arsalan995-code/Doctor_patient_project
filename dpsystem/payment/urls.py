from django.urls import path
from .views import *

urlpatterns = [
    path('create-subscription-product/', CreateSubscriptionProductView.as_view(), name='create_subscription_product'),
    path('create-customer-subscription/', CreateCustomerSubscription, name="create-subscription"),
    path('checkout/', checkout_session, name='checkout'),
]

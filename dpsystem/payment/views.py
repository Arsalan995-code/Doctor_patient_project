from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import SubscriptionProduct,StripeCustomer
from rest_framework.decorators import api_view
from dpsystem import settings
import stripe
from django.shortcuts import render
from account.models import customuser
# from django.conf import settings
stripe.api_key = settings.STRIPE_SECRET_KEY

@method_decorator(csrf_exempt, name='dispatch')
class CreateSubscriptionProductView(View):
    def post(self, request, *args, **kwargs):
        product_name = request.POST.get('product_name')
        product_description = request.POST.get('product_description')
        product_price = request.POST.get('product_price')  # Price in cents
        currency = request.POST.get('currency', 'usd')  # Default to USD
        interval = request.POST.get('interval', 'month')  # Default to month

        # Ensure valid data
        if not product_name or not product_price:
            return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)

        try:
            product_price = int(product_price)  # Ensure it's an integer

            # Create product on Stripe
            product = stripe.Product.create(
                name=product_name,
                description=product_description
            )

            # Create recurring price for the subscription
            price = stripe.Price.create(
                product=product.id,
                unit_amount=product_price,
                currency=currency,
                recurring={'interval': interval}
            )

            # Save product details in the database
            subscription_product = SubscriptionProduct.objects.create(
                product_name=product_name,
                product_description=product_description,
                product_price=product_price,
                product_id=product.id,
                price_id=price.id
            )

            return JsonResponse({
                'success': True,
                'message': 'Subscription product created successfully',
                'product_id': subscription_product.product_id,
                'price_id': subscription_product.price_id
            }, status=201)

        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid price format'}, status=400)

        except stripe.error.StripeError as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
# File: dpsystem/payment/views.py

@api_view(['GET'])
def CreateCustomerSubscription(request):
    try:
        # Use request.GET to retrieve the parameters since the JS is sending a GET request
        price_id = request.GET.get('price_id')
        doctor_id = request.GET.get('user_id')

        user_data = customuser.objects.get(id=doctor_id)
        email = user_data.email
        username = user_data.username

        customer = stripe.Customer.create(
            email=email,
            name=username,
        )
        print('Customer created successfully:', customer)

        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{'price': price_id}],
            payment_behavior='default_incomplete',
            payment_settings={'save_default_payment_method': 'on_subscription'},
            expand=['latest_invoice.payment_intent'],
        )
        StripeCustomer.objects.create(
            doctor=user_data,
            stripeCustomerId=customer.id,
            stripeSubscriptionId=subscription.id,
        )

        stripe_config = {'clientsecret': subscription.latest_invoice.payment_intent.client_secret}
        return JsonResponse(stripe_config, safe=False)
    except Exception as e:
        print('Error:', str(e))
        return JsonResponse({'error': str(e)}, status=500)

def checkout_session(request):
    user_id = request.GET.get('user_id')
    price_id = request.GET.get('price_id')
    product = SubscriptionProduct.objects.get(price_id=price_id)
    user = customuser.objects.get(id=user_id)
    print(settings.STRIPE_PUBLIC_KEY)

     # You can add additional logic here based on the price_id

    context = {
        'price_id': price_id,
        'username': user.username,
        'email': user.email,
        'pro_name': product.product_name,
        'pro_price': str(product.product_price)[:2],
        'user_id': user.id,
        'pkey': settings.STRIPE_PUBLIC_KEY,
        # Add any other context variables you need for the checkout page
    }

    return render(request, 'checkout.html', context=context)






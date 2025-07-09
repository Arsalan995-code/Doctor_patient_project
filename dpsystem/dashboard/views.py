from django.shortcuts import render
import stripe

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from stripe.error import StripeError
from django.contrib import messages
from dpsystem import settings
from payment.models import SubscriptionProduct, StripeCustomer
from account.models import customuser, Doctor, Patient, DoctorPrescription
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseServerError

stripe.api_key = settings.STRIPE_SECRET_KEY


@csrf_exempt
def doctor_dashboard(request):
    user_id = request.GET.get('user_id')
    user = customuser.objects.get(id=user_id)
    record = False
    status = "new"
    doctor_rec = Doctor.objects.filter(user_id=user_id).first()  # Safe query

    # Initialize these variables to avoid undefined errors.
    firstname = lastname = dob = refid = image = user.id = None
    pat_rec = None

    if doctor_rec:
        record = True
        status = 'update'
        firstname = doctor_rec.first_name
        lastname = doctor_rec.last_name
        dob = doctor_rec.dob
        refid = doctor_rec.referral_id
        image = doctor_rec.profile_image
        user.id = user.id
        # id = doctor_rec.id
        patient_queryset = Patient.objects.filter(doctor_referral_id=refid)
        if patient_queryset.exists():
            pat_rec = patient_queryset

    subs_rec = StripeCustomer.objects.filter(doctor=user_id).first()
    customer = stripe.Customer.retrieve(subs_rec.stripeCustomerId) if subs_rec else None
    email = user.email
    username = user.username

    # Retrieve the last 6 payment intents associated with the customer
    payment_intents = stripe.PaymentIntent.list(
        customer=customer.id if customer else None,
        limit=6,
    ) if customer else []

    transaction_data = [{
        'transaction_id': pi.id,
        'invoice_id': pi.invoice,
        'invoice_amount': pi.amount_received,
        'invoice_status': pi.status,
        'transaction_date': datetime.utcfromtimestamp(pi.created).strftime('%Y-%m-%d %H:%M:%S'),
    } for pi in payment_intents.data] if customer else []

    if record:
        context = {
            'transactions': transaction_data,
            'record': record,
            'firstname': firstname,
            'lastname': lastname,
            'dob': dob,
            'refid': refid,
            'image': image,
            'username': username,
            'email': email,
            'id': user.id,
            'status': status,
            'pat_rec': pat_rec,
        }
    else:
        context = {
            'transactions': transaction_data,
            'record': record,
            'status': status,
        }
    return render(request, 'doctor_dashboard.html', context=context)



@login_required
def patient_dashboard(request):
    """
    View for patient dashboard that displays and processes patient profile form.
    If the patient hasn't completed their profile, they'll be prompted to do so.
    """
    # Get user ID from the logged-in user
    user_id = request.user.id

    # Check if the user is a patient (role 2)
    if request.user.role != 2:
        messages.error(request, "This dashboard is only for patients.")
        return redirect('home')  # Redirect to home or appropriate page

    record = False
    status = "new"
    profile_complete = False

    try:
        user = customuser.objects.get(id=user_id)
        # Check if patient record already exists
        patient_rec = Patient.objects.filter(user_id=user_id).first()

        # Initialize variables to avoid undefined errors
        firstname = lastname = dob = refid = image = None
        prescriptions = None

        if patient_rec:
            record = True
            status = 'update'
            profile_complete = True
            firstname = patient_rec.first_name
            lastname = patient_rec.last_name
            dob = patient_rec.dob
            refid = patient_rec.doctor_referral_id
            image = patient_rec.profile_image

            # Get prescriptions for this patient if any
            prescriptions = DoctorPrescription.objects.filter(patient=patient_rec).order_by('-created_at')

        # Handle form submission
        if request.method == 'POST':
            # Process the form data
            doctor_referral_id = request.POST.get('doctor_referral_id')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            dob_str = request.POST.get('dob')

            # Convert string date to datetime object
            try:
                dob_date = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, "Invalid date format. Please use YYYY-MM-DD.")
                return redirect('patient_dashboard')

            # Handle file upload if provided
            profile_image = None
            if 'profile_image' in request.FILES:
                profile_image = request.FILES['profile_image']

            # Create or update patient record
            if record:
                # Update existing patient record
                patient_rec.doctor_referral_id = doctor_referral_id
                patient_rec.first_name = first_name
                patient_rec.last_name = last_name
                patient_rec.dob = dob_date
                if profile_image:
                    patient_rec.profile_image = profile_image
                patient_rec.save()

                messages.success(request, "Profile updated successfully!")
                profile_complete = True
            else:
                # Create new patient record
                try:
                    # Validate referral ID
                    doctor = Doctor.objects.get(referral_id=doctor_referral_id)

                    # Create new patient
                    new_patient = Patient(
                        user=user,
                        doctor_referral_id=doctor_referral_id,
                        first_name=first_name,
                        last_name=last_name,
                        dob=dob_date
                    )
                    if profile_image:
                        new_patient.profile_image = profile_image
                    new_patient.save()

                    messages.success(request, "Profile created successfully!")
                    profile_complete = True

                    # Update flags for template
                    record = True
                    status = 'update'
                    firstname = first_name
                    lastname = last_name
                    dob = dob_date
                    refid = doctor_referral_id
                    image = profile_image if profile_image else None

                except Doctor.DoesNotExist:
                    messages.error(request, "Invalid doctor referral ID. Please check and try again.")

        context = {
            'record': record,
            'firstname': firstname,
            'lastname': lastname,
            'dob': dob,
            'refid': refid,
            'image': image,
            'status': status,
            'user': user,
            'prescriptions': prescriptions,
            'profile_complete': profile_complete,
        }

        return render(request, 'patient_dashboard.html', context=context)

    except customuser.DoesNotExist:
        # Handle case where user ID is invalid
        return HttpResponseServerError("User not found.")



def subscription_package(request):
    # Assuming SubscriptionProduct is your model for subscription packages
    user_id = request.GET.get('user_id')
    products = SubscriptionProduct.objects.all()

    # Create a list to store information about all packages
    packages = []

    # Loop through each product and store its information in the packages list
    for product in products:
        package_info = {
            'name': product.product_name,
            'desc': product.product_description,
            'id': product.price_id,
            'price': str(product.product_price)[:2],

        }
        packages.append(package_info)

    context = {
        'packages': packages,
        'user_id': user_id,
    }

    return render(request, 'subscription_package.html', context=context)






from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import generics

from .serializers import *
#jwt
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate,login
from .forms import *
from django.shortcuts import get_object_or_404
from .models import *
from django.contrib.auth.decorators import login_required
from payment.models import StripeCustomer
from django.contrib.auth import logout
from django.shortcuts import redirect
@login_required
def logout_view(request):
    logout(request)
    return redirect('/')

def home(request):
    return render(request,'index.html',context={})

def login_page(request):
    return render(request, 'login.html', context={})

def doctor_signup(request):
    return render(request, 'signup_doctor.html', context={})

def patient_signup(request):
    return render(request, 'signup_patient.html', context={})



def home3(request):
    return HttpResponse("hello this is my third page2")
def home1(request):
    context={'name':'arslan','age': 45,
              'father' : 'shakeel',
             'list': ['arslan','nimra','nayab','atiya']
             }
    return render(request,'firstpage.html',context)

def home2(request):
    return render(request,'firstpage.html',context={'name':'arslan','age': 45,
              'father' : 'shakeel',
             'list': ['arslan','nimra','nayab','atiya']
             })

def contact_view(request):
    if request.method == 'POST' :
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']
            return render(request, 'account/thank_you.html', {'name': name,'email': email})
    else:
        form = ContactForm()
    return render(request,'account/contact_form.html',{'form': form})



class CustomUserListCreateAPIView(generics.ListCreateAPIView):
    queryset = customuser.objects.all()
    serializer_class = CustomUserSerializer
class CustomUserRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = customuser.objects.all()
    serializer_class = CustomUserSerializer


@api_view(['POST'])
def login_view(request):
    """
    API endpoint for user login.
    Expected input: JSON with email and password fields
    """
    try:
        data = request.data
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return Response({'message': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            package = False

            if user.role == 1:  # Doctor role
                try:
                    StripeCustomer.objects.get(doctor=user.id)
                    package = True
                except StripeCustomer.DoesNotExist:
                    package = False

            return Response({
                'access_token': access_token,
                'role': user.role,
                'user_id': user.id,
                'package': package,
            }, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response({'message': f'Login error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DoctorListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """If it's a GET request, only return the doctor profile of the current user"""
        if self.request.method == 'GET':
            return Doctor.objects.filter(user=self.request.user)
        return Doctor.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DoctorRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated]




class PatientListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Limit queryset to the authenticated user's profile."""
        return Patient.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Ensure the patient profile is tied to the authenticated user."""
        user = self.request.user

        # Ensure only authenticated patients can create profiles
        if user.role != 2:  # Role 2 corresponds to 'patient'
            raise serializers.ValidationError("Only authenticated patients can create profiles.")

        # Ensure no duplicate profiles for the same user
        if Patient.objects.filter(user=user).exists():
            raise serializers.ValidationError("A profile for this user already exists.")

        serializer.save(user=user)

class PatientDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """Retrieve the authenticated patient's object only."""
        user = self.request.user

        # Ensure the user has the 'patient' role
        if user.role != 2:  # 2 corresponds to 'patient'
            raise serializers.ValidationError("Only authenticated patients can access or modify their profile.")

        # Get the patient's profile for the authenticated user
        patient = get_object_or_404(Patient, user=user)
        self.check_object_permissions(self.request, patient)
        return patient

    def put(self, request, *args, **kwargs):
        """Handle full updates."""
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        """Handle partial updates."""
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """Handle deletion of the authenticated patient's profile."""
        return self.destroy(request, *args, **kwargs)


class PatientPrescriptionListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = DoctorPrescriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == 1:  # Doctor
            doctor = getattr(user, 'doctor_profile', None)
            if not doctor:
                return DoctorPrescription.objects.none()
            return DoctorPrescription.objects.filter(doctor=doctor)

        if user.role == 2:  # Patient
            patient = getattr(user, 'patient_profile', None)
            if not patient:
                return DoctorPrescription.objects.none()
            return DoctorPrescription.objects.filter(patient=patient)

        return DoctorPrescription.objects.none()

    def perform_create(self, serializer):
        user = self.request.user

        # Check if the logged-in user is a doctor
        if user.role != 1:  # 1 corresponds to 'doctor' in your role choices
            raise serializers.ValidationError("Only authenticated doctors can create prescriptions.")

        doctor = getattr(user, 'doctor_profile', None)  # Use related_name to access Doctor profile
        if not doctor:
            raise serializers.ValidationError("This user does not have a doctor profile.")

        patient_id = self.kwargs.get('patient_id')
        patient = get_object_or_404(Patient, pk=patient_id)

        # Check if the patient is assigned to the doctor
        if patient.doctor_referral_id != doctor.referral_id:
            raise serializers.ValidationError("This doctor is not authorized to prescribe for this patient.")

        serializer.save(doctor=doctor, patient=patient)


class PatientPrescriptionDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DoctorPrescriptionSerializer
    permission_classes = [IsAuthenticated]  # Ensure the user is authenticated

    def get_object(self):
        """Retrieve a prescription for a specific patient, restricted to the authenticated doctor."""
        user = self.request.user

        # Ensure the user has the 'doctor' role
        if not hasattr(user, 'doctor_profile'):
            raise serializers.ValidationError("Only authenticated doctors can access or modify prescriptions.")

        patient_id = self.kwargs.get('patient')  # Patient ID passed in the URL
        prescription = get_object_or_404(DoctorPrescription, patient_id=patient_id, doctor=user.doctor_profile)

        # Check permissions and return the prescription object
        self.check_object_permissions(self.request, prescription)
        return prescription

    def put(self, request, *args, **kwargs):
        """Handle full updates."""
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        """Handle partial updates."""
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """Handle deletion of prescriptions."""
        return self.destroy(request, *args, **kwargs)




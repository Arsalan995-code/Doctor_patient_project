from django.shortcuts import redirect
from django.urls import resolve, reverse
from django.contrib import messages
from account.models import Patient


class PatientProfileMiddleware:
    """
    Middleware to ensure patients complete their profile before accessing other pages.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only apply middleware logic if user is authenticated and is a patient
        if request.user.is_authenticated and hasattr(request.user,
                                                     'role') and request.user.role == 2:  # Assuming 2 is patient role
            # Get current path
            current_url = resolve(request.path_info).url_name

            # Exclude these paths from redirection
            excluded_paths = [
                'patient_dashboard',
                'logout',
                'login',
                'static',
                'media',
                'admin',
                None,  # For URLs that don't have a name
            ]

            # Check if user has completed their profile
            has_profile = Patient.objects.filter(user=request.user).exists()

            # If user hasn't completed profile and not on an excluded path, redirect to dashboard
            if not has_profile and current_url not in excluded_paths:
                messages.warning(request, "Please complete your profile before continuing.")
                return redirect('patient_dashboard')

        response = self.get_response(request)
        return response

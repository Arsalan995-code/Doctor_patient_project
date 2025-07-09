from django.urls import path
from .views import *


urlpatterns = [
    path('doctor_dashboard/',doctor_dashboard, name = 'doctor_dashboard'),
    path('patient_dashboard/',patient_dashboard, name = 'patient_dashboard'),
    path('subscription_package/', subscription_package, name='subscription_package'),

]
from django.urls import path
# from . import views
from .views import *

urlpatterns = [
    path('index/',home3, name='index'),
    path('logout/', logout_view, name='logout'),
    path('login/', login_page, name = 'login'),
    path('signup/doctor/', doctor_signup),
    path('signup/patient/', patient_signup),
    # path('account1/', views.index),
    path('account2/', home),
    path('account3/', home1),
    path('account4/', home2),
    path('users/', CustomUserListCreateAPIView.as_view(),name='customuser-list-create'),
    path('users/<int:pk>/', CustomUserRetrieveUpdateDestroyAPIView.as_view(),name='customuser-detail'),
    path('api/login/',login_view,name='api-login'),
    path('doctors/',DoctorListCreateAPIView.as_view(),name='doctor-list-create'),
    path('doctors/<int:pk>/',DoctorRetrieveUpdateDestroyAPIView.as_view(),name='doctor-detail'),
    path('contact/',contact_view, name='contact'),
    path('patients/',PatientListCreateAPIView.as_view(),name='patient-list-create'),
    path('patients/<int:user_id>/',PatientDetailAPIView.as_view(),name='patient-detail'),
    path('patients/<int:patient_id>/prescriptions/', PatientPrescriptionListCreateAPIView.as_view(), name='patient-prescription-create'),
    path('prescription/<int:patient>/', PatientPrescriptionDetailAPIView.as_view(), name='patient-prescription-detail'),
]

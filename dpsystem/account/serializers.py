from rest_framework import serializers
from .models import *
from django.shortcuts import get_object_or_404
import datetime

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model=customuser
        fields=('id','email','username','role','password')
        extra_kwargs={'password':{'write_only':True}}

    def create(self,validated_data):
        user=customuser.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            role= validated_data['role'],
            password=validated_data['password']


        )
        return user

class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model=Doctor
        fields=('id','user','referral_id','first_name','last_name','dob','profile_image')
        read_only_fields = ('id', 'referral_id','user')
    def validate_dob(self, value):
        # Custom validation for 'dob' field
        # Example: Check if the date of birth is in the past
        if value and value > datetime.date.today():
            raise serializers.ValidationError("Date of birth must be in the past.")
        return value
class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model=Patient
        fields=('id','doctor_referral_id','first_name','last_name','dob','profile_image')

    def validate_doctor_referral_id(self,value):
        try:
            Doctor.objects.get(referral_id = value)
        except Doctor.DoesNotExist:
            raise serializers.ValidationError('Invalid referral id ')
        return value



class DoctorPrescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorPrescription
        fields = ('id', 'doctor', 'patient', 'issue_description', 'prescription_text', 'next_visit_date', 'created_at')
        read_only_fields = ('id', 'created_at')


from django import forms
import datetime


class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField(max_length=100)
    message = forms.CharField(widget=forms.Textarea)
    phone_number = forms.CharField(max_length=15, required=True, label='phone number')
    birth_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True, label='Birth date')
    # profile_picture = forms.ImageField(required=True, label='Profile Picture')

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number.isdigit():
            raise forms.ValidationError('invalid phone number')
        return phone_number

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date and birth_date > datetime.date.today():
            raise forms.ValidationError('invalid birth date')
        return birth_date

from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

class RegistrationForm(forms.Form):

    username = forms.CharField(max_length=30, min_length=4, required=True, widget=forms.TextInput(attrs={'type': 'text', 'name': 'username',
                                                             'class': 'form-control required',
                                                             'autofocus': 'true'}), label='')

    password = forms.CharField(max_length=30, min_length=8, required=True, widget=forms.PasswordInput(attrs={'type': 'password', 'name': 'password', 'id':'password',
                                                             'class': 'form-control required',
                                                             'autofocus': 'true'}), label='')

    conf_password = forms.CharField(max_length=30, min_length=8, required=True, widget=forms.PasswordInput(attrs={'type': 'password', 'name': 'conf_password', 'id':'password',
                                                             'class': 'form-control required',
                                                             'autofocus': 'true'}), label='')

    email = forms.EmailField(required=True, widget=forms.TextInput(attrs={'type': 'email', 'name': 'email', 'id': 'email',
                                                             'class': 'form-control required',
                                                             'autofocus': 'true'}), label='')


from django import forms

from winServer.models import *
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist


class ProfileUserForm(forms.ModelForm):
    class Meta:
        model = ProfileUser
        fields = ( 'srcCodes', )

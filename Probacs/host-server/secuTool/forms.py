from django import forms

from secuTool.models import *
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist


class ProfileUserForm(forms.ModelForm):
    class Meta:
        model = ProfileUser
        fields = ( 'srcCodes', 'task_file')
        # widgets = {
        #     'bio': forms.Textarea(attrs={'cols': 70, 'rows': 10,}),
        # }

    # def clean_picture(self):
    #     picture = self.cleaned_data['picture']
    #     if not picture:
    #         raise forms.ValidationError('You must upload a picture')
    #     if not picture.content_type or not picture.content_type.startswith('image'):
    #         raise forms.ValidationError('File type is not image')
    #     if picture.size > MAX_UPLOAD_SIZE:
    #         raise forms.ValidationError('File too big (max size is {0} bytes)'.format(MAX_UPLOAD_SIZE))
    #     return picture


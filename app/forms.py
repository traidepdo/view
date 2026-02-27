from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class CustomerSignupForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text='Bắt buộc nhập email để nhận thông báo.')
    first_name = forms.CharField(max_length=30, label='Họ và tên đệm')
    last_name = forms.CharField(max_length=30, label='Tên')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email')
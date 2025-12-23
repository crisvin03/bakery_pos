# core/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Product

class ProductForm(forms.ModelForm):
    image_upload = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
            'id': 'id_image_upload',
        })
    )
    
    class Meta:
        model = Product
        fields = ['image', 'name', 'price', 'stock', 'ingredients', 'is_active', 'expiration_date']
        widgets = {
            'image': forms.HiddenInput(),  # Hidden field for storing the URL
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '1'}),
            'ingredients': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'expiration_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
        }


class CashierForm(UserCreationForm):
    """Form for creating new cashier accounts"""
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email (optional)'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})
    
    def save(self, commit=True):
        # UserCreationForm.save(commit=False) automatically hashes the password
        # and sets it on the user object, but doesn't save to database yet
        user = super().save(commit=False)
        
        # Set cashier-specific attributes
        user.is_staff = False  # Cashiers are not staff (only admins are staff)
        user.is_superuser = False  # Cashiers are not superusers
        
        # Explicitly ensure password is set (UserCreationForm should handle this, but be explicit)
        if self.cleaned_data.get('password1'):
            user.set_password(self.cleaned_data['password1'])
        
        # Save to database
        if commit:
            user.save()
        
        return user


class ProfileEditForm(forms.ModelForm):
    """Form for editing user profile information"""
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
            'id': 'id_profile_picture',
        })
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email'
            }),
        }

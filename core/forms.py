# core/forms.py
from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['image', 'name', 'price', 'ingredients', 'is_active']
        widgets = {
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',   # so it matches your bootstrap style
                'accept': 'image/*',
                'id': 'id_image',
            }),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'ingredients': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

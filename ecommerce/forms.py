# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Produk, Pengiriman

class UserRegistrationForm(UserCreationForm):
    nama = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    alamat = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    noHP = forms.CharField(max_length=15, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ('username', 'nama', 'email', 'alamat', 'noHP', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('nama', 'email', 'alamat', 'noHP')
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'alamat': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'noHP': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ProdukForm(forms.ModelForm):
    class Meta:
        model = Produk
        fields = ['nama', 'kategori', 'harga', 'stock']
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'form-control'}),
            'kategori': forms.TextInput(attrs={'class': 'form-control'}),
            'harga': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class PengirimanForm(forms.ModelForm):
    class Meta:
        model = Pengiriman
        fields = ['alamat', 'ongkir', 'status']
        widgets = {
            'alamat': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ongkir': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

class TransaksiFilterForm(forms.Form):
    STATUS_CHOICES = [
        ('', 'Semua Status'),
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    tanggal_mulai = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    tanggal_akhir = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
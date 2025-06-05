from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

# Import model Anda
from .models import User, Produk, Pengiriman, Transaksi, UlasanProduk, Buyer

# Import allauth forms
from allauth.account.forms import SignupForm # Untuk form pendaftaran standar allauth
from allauth.socialaccount.forms import SignupForm as SocialSignupForm # Untuk form pendaftaran sosial allauth


# Form Pendaftaran Pengguna (Ini adalah form kustom lama Anda,
# yang diganti oleh CustomSignupForm dari allauth)
# Saya pertahankan ini agar tidak ada masalah import jika ada bagian lain yang masih menggunakannya,
# tetapi sebaiknya tidak digunakan lagi.
class UserRegistrationForm(UserCreationForm):
    nama = forms.CharField(max_length=100, help_text="Nama Lengkap")
    email = forms.EmailField(help_text="Alamat Email")
    alamat = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), help_text="Alamat Lengkap")
    noHP = forms.CharField(max_length=15, help_text="Nomor Telepon")
    
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('nama', 'email', 'alamat', 'noHP',)

# Form Update Profil Pengguna
class UserProfileForm(UserChangeForm):
    password = None # Jangan tampilkan field password untuk keamanan

    class Meta:
        model = User
        fields = ['nama', 'email', 'alamat', 'noHP']
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'alamat': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'noHP': forms.TextInput(attrs={'class': 'form-control'}),
        }


# Form untuk Ulasan Produk
class UlasanProdukForm(forms.ModelForm):
    rating = forms.IntegerField(
        label='Rating',
        min_value=1,
        max_value=5,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '5',
            'placeholder': '1-5 bintang'
        })
    )
    komentar = forms.CharField(
        label='Komentar',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Tulis ulasan Anda di sini (opsional)'
        })
    )

    class Meta:
        model = UlasanProduk
        fields = ['rating', 'komentar']


# Form Checkout
class CheckoutForm(forms.Form):
    alamat_pengiriman = forms.CharField(
        label='Alamat Pengiriman',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        help_text="Pastikan alamat Anda lengkap dan benar."
    )
    ekspedisi = forms.ChoiceField(
        label='Pilih Ekspedisi Pengiriman',
        choices=Pengiriman.EKSPEDISI_CHOICES, # Mengambil dari model Pengiriman
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    catatan = forms.CharField(
        label='Catatan untuk Kurir (Opsional)',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control', 
            'rows': 2,
            'placeholder': 'Catatan pengiriman (opsional)'
        }),
        help_text="Contoh: Titip ke tetangga jika tidak ada di rumah."
    )

# Form Produk (untuk admin)
class ProdukForm(forms.ModelForm):
    class Meta:
        model = Produk
        fields = ['nama', 'kategori', 'harga', 'stock', 'berat', 'gambar']
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'form-control'}),
            'kategori': forms.TextInput(attrs={'class': 'form-control'}),
            'harga': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'berat': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'Berat dalam kg'}),
        }

# Form Pengiriman (untuk admin)
class PengirimanForm(forms.ModelForm):
    class Meta:
        model = Pengiriman
        fields = ['alamat_penerima', 'ekspedisi', 'ongkir', 'status', 'no_resi', 'estimasi_hari', 'catatan']
        widgets = {
            'alamat_penerima': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ekspedisi': forms.Select(attrs={'class': 'form-control'}),
            'ongkir': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'no_resi': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contoh: JNE1234567890'}),
            'estimasi_hari': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '30'}),
            'catatan': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Catatan pengiriman (opsional)'}),
        }

class TransaksiFilterForm(forms.Form):
    status = forms.ChoiceField(
        choices=[('', 'All')] + list(Transaksi._meta.get_field('status').choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

class UpdatePengirimanForm(forms.ModelForm):
    class Meta:
        model = Pengiriman
        fields = ['status', 'no_resi', 'tanggal_kirim', 'tanggal_terkirim', 'catatan']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'no_resi': forms.TextInput(attrs={'class': 'form-control'}),
            'tanggal_kirim': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'tanggal_terkirim': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'catatan': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].label = 'Status Pengiriman'
        self.fields['no_resi'].label = 'Nomor Resi'
        self.fields['tanggal_kirim'].label = 'Tanggal Kirim'
        self.fields['tanggal_terkirim'].label = 'Tanggal Terkirim'
        self.fields['catatan'].label = 'Catatan'

class PengirimanFilterForm(forms.Form):
    status = forms.ChoiceField(
        choices=[('', 'All')] + Pengiriman.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    ekspedisi = forms.ChoiceField(
        choices=[('', 'All')] + Pengiriman.EKSPEDISI_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    no_resi = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Cari berdasarkan nomor resi'
        })
    )


# Custom Signup Form untuk Allauth
class CustomSignupForm(SignupForm):
    nama = forms.CharField(max_length=100, label='Nama Lengkap', widget=forms.TextInput(attrs={'class': 'form-control'}))
    noHP = forms.CharField(max_length=15, label='No. HP', widget=forms.TextInput(attrs={'class': 'form-control'}))
    alamat = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), label='Alamat')

    def save(self, request):
        user = super(CustomSignupForm, self).save(request)
        user.nama = self.cleaned_data['nama']
        user.noHP = self.cleaned_data['noHP']
        user.alamat = self.cleaned_data['alamat']
        user.save()
        Buyer.objects.create(user=user)
        return user

# Custom Social Signup Form untuk Allauth
class CustomSocialSignupForm(SocialSignupForm):
    nama = forms.CharField(max_length=100, label='Nama Lengkap', widget=forms.TextInput(attrs={'class': 'form-control'}))
    noHP = forms.CharField(max_length=15, label='No. HP', widget=forms.TextInput(attrs={'class': 'form-control'}))
    alamat = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), label='Alamat')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self.user, 'extra_data') and 'first_name' in self.user.extra_data and 'last_name' in self.user.extra_data:
            self.fields['nama'].initial = f"{self.user.extra_data.get('first_name', '')} {self.user.extra_data.get('last_name', '')}".strip()
        elif hasattr(self.user, 'extra_data') and 'name' in self.user.extra_data:
            self.fields['nama'].initial = self.user.extra_data.get('name', '')

        if self.user and self.user.email:
            self.fields['email'].widget = forms.HiddenInput()
            self.fields['email'].required = False

    def save(self, request):
        user = super(CustomSocialSignupForm, self).save(request)
        user.nama = self.cleaned_data['nama']
        user.noHP = self.cleaned_data['noHP']
        user.alamat = self.cleaned_data['alamat']
        user.save()
        Buyer.objects.create(user=user)
        return user
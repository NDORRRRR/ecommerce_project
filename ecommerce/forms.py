from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

# Import model Anda
from .models import User, Produk, Pengiriman, Transaksi, UlasanProduk, Buyer

# Import allauth forms (pastikan path ini benar)
from allauth.account.forms import SignupForm # Untuk form pendaftaran standar allauth
from allauth.socialaccount.forms import SignupForm as SocialSignupForm # Untuk form pendaftaran sosial allauth


# Form Pendaftaran Pengguna (Kustom, diganti oleh allauth tapi strukturnya bisa jadi referensi)
class UserRegistrationForm(UserCreationForm):
    nama = forms.CharField(max_length=100, help_text="Nama Lengkap")
    email = forms.EmailField(unique=True, help_text="Alamat Email")
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
        choices=Pengiriman.EKSPEDISI_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    catatan = forms.CharField(
        label='Catatan untuk Kurir (Opsional)',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        help_text="Contoh: Titip ke tetangga jika tidak ada di rumah."
    )

# Form Produk (untuk admin)
class ProdukForm(forms.ModelForm):
    class Meta:
        model = Produk
        fields = '__all__'
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'form-control'}),
            'kategori': forms.TextInput(attrs={'class': 'form-control'}),
            'harga': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'berat': forms.NumberInput(attrs={'class': 'form-control'}),
            # 'gambar': forms.FileInput(attrs={'class': 'form-control'}), # Untuk input file
        }

# Form Pengiriman (untuk admin)
class PengirimanForm(forms.ModelForm):
    class Meta:
        model = Pengiriman
        fields = '__all__'
        widgets = {
            'alamat_pengirim': forms.TextInput(attrs={'class': 'form-control'}),
            'alamat_penerima': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ongkir': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'ekspedisi': forms.Select(attrs={'class': 'form-select'}),
            'no_resi': forms.TextInput(attrs={'class': 'form-control'}),
            'estimasi_hari': forms.NumberInput(attrs={'class': 'form-control'}),
            'tanggal_kirim': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'tanggal_terkirim': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'catatan': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class TransaksiFilterForm(forms.Form):
    status = forms.ChoiceField(
        choices=[('', 'All')] + Transaksi.STATUS_CHOICES,
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
        fields = ['status', 'no_resi', 'ekspedisi', 'tanggal_kirim', 'tanggal_terkirim', 'catatan']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'no_resi': forms.TextInput(attrs={'class': 'form-control'}),
            'ekspedisi': forms.Select(attrs={'class': 'form-select'}),
            'tanggal_kirim': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'tanggal_terkirim': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'catatan': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

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


# Custom Signup Form untuk Allauth
# Ini penting untuk menambahkan field kustom Anda saat pendaftaran allauth
class CustomSignupForm(SignupForm):
    # Field yang akan diambil dari user model kustom
    nama = forms.CharField(max_length=100, label='Nama Lengkap', widget=forms.TextInput(attrs={'class': 'form-control'}))
    noHP = forms.CharField(max_length=15, label='No. HP', widget=forms.TextInput(attrs={'class': 'form-control'}))
    alamat = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), label='Alamat')

    def save(self, request):
        user = super(CustomSignupForm, self).save(request)
        user.nama = self.cleaned_data['nama']
        user.noHP = self.cleaned_data['noHP']
        user.alamat = self.cleaned_data['alamat']
        user.save()
        # Pastikan objek Buyer dibuat untuk pengguna baru
        Buyer.objects.create(user=user)
        return user

# Custom Social Signup Form untuk Allauth
class CustomSocialSignupForm(SocialSignupForm):
    nama = forms.CharField(max_length=100, label='Nama Lengkap', widget=forms.TextInput(attrs={'class': 'form-control'}))
    noHP = forms.CharField(max_length=15, label='No. HP', widget=forms.TextInput(attrs={'class': 'form-control'}))
    alamat = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), label='Alamat')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Isi field 'nama' jika tersedia dari social provider
        if 'first_name' in self.user.extra_data and 'last_name' in self.user.extra_data:
            self.fields['nama'].initial = f"{self.user.extra_data.get('first_name', '')} {self.user.extra_data.get('last_name', '')}".strip()
        elif 'name' in self.user.extra_data: # Untuk Google, nama bisa langsung di 'name'
            self.fields['nama'].initial = self.user.extra_data.get('name', '')

        # Sembunyikan field yang mungkin tidak relevan atau sudah diisi dari social account
        # Contoh: Jika email sudah diverifikasi dari Google, sembunyikan field email
        if self.user and self.user.email:
            self.fields['email'].widget = forms.HiddenInput()
            self.fields['email'].required = False

    def save(self, request):
        user = super(CustomSocialSignupForm, self).save(request)
        user.nama = self.cleaned_data['nama']
        user.noHP = self.cleaned_data['noHP']
        user.alamat = self.cleaned_data['alamat']
        user.save()
        # Pastikan objek Buyer dibuat untuk pengguna baru
        Buyer.objects.create(user=user)
        return user
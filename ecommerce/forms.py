from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from .models import User, Produk, Pengiriman, Transaksi, TransaksiProduk, Buyer, Cart, CartItem, Laporan1, UlasanProduk, GambarProduk, Ongkir
from allauth.account.forms import SignupForm
from allauth.socialaccount.forms import SignupForm as SocialSignupForm 

User = get_user_model()

class CustomSignupForm(SignupForm):
    nama = forms.CharField(max_length=100, label='Nama Lengkap', required=True)
    noHP = forms.CharField(max_length=15, label='Nomor HP', required=True)
    alamat = forms.CharField(label='Alamat', widget=forms.Textarea(attrs={'rows': 3}), required=True)

    def save(self, request):
        user = super(CustomSignupForm, self).save(request)
        
        user.nama = self.cleaned_data['nama']
        user.noHP = self.cleaned_data['noHP']
        user.alamat = self.cleaned_data['alamat']
        user.save()
        return user


class ProfilUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['foto_profil', 'nama', 'email', 'noHP', 'alamat']
        labels = {
            'foto_profil': 'Ganti Foto Profil',
            'nama': 'Nama Lengkap',
            'email': 'Alamat Email',
            'noHP': 'Nomor HP',
            'alamat': 'Alamat Lengkap',
        }
        widgets = {
            'alamat': forms.Textarea(attrs={'rows': 3}),
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
        fields = ['nama', 'kategori', 'harga', 'stock', 'berat', 'gambar', 'deskripsi']
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'form-control'}),
            'kategori': forms.TextInput(attrs={'class': 'form-control'}),
            'harga': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'berat': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'Berat dalam kg'}),
            # TAMBAHKAN WIDGET UNTUK DESKRIPSI
            'deskripsi': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
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

class OngkirForm(forms.ModelForm):
    class Meta:
        model = Ongkir
        fields = ['provinsi', 'kabupaten_kota', 'kecamatan', 'biaya']


class TransaksiFilterForm(forms.Form):
    start_date = forms.DateField(label='Dari Tanggal', required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(label='Sampai Tanggal', required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    status = forms.ChoiceField(
        label='Status Transaksi',
        required=False,
        choices=[('', 'Semua Status')] + Transaksi.STATUS_CHOICES,
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
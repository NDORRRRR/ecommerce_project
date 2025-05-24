from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Produk, Pengiriman, Transaksi

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
        fields = ['nama', 'kategori', 'harga', 'stock', 'berat']
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'form-control'}),
            'kategori': forms.TextInput(attrs={'class': 'form-control'}),
            'harga': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'berat': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'Berat dalam kg'}),
        }

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

# NEW: Form untuk pemilihan pengiriman saat checkout
class CheckoutForm(forms.Form):
    EKSPEDISI_CHOICES = [
        ('jne', 'JNE - Rp 9,000'),
        ('pos', 'Pos Indonesia - Rp 8,000'),
        ('tiki', 'TIKI - Rp 9,500'),
        ('j&t', 'J&T Express - Rp 8,500'),
        ('sicepat', 'SiCepat - Rp 8,000'),
        ('anteraja', 'AnterAja - Rp 7,500'),
        ('ninja', 'Ninja Express - Rp 7,000'),
        ('gosend', 'GoSend (Same Day) - Rp 15,000'),
        ('grab', 'GrabExpress - Rp 12,000'),
    ]
    
    ekspedisi = forms.ChoiceField(
        choices=EKSPEDISI_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Pilih Ekspedisi Pengiriman'
    )
    
    alamat_pengiriman = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control', 
            'rows': 3,
            'placeholder': 'Masukkan alamat lengkap untuk pengiriman'
        }),
        label='Alamat Pengiriman',
        help_text='Pastikan alamat lengkap dan benar'
    )
    
    catatan = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control', 
            'rows': 2,
            'placeholder': 'Catatan untuk kurir (opsional)'
        }),
        label='Catatan Pengiriman'
    )

# NEW: Form untuk update status pengiriman (Admin)
class UpdatePengirimanForm(forms.ModelForm):
    class Meta:
        model = Pengiriman
        fields = ['status', 'no_resi', 'catatan']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'no_resi': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Masukkan nomor resi'
            }),
            'catatan': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Catatan update status'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].label = 'Status Pengiriman'
        self.fields['no_resi'].label = 'Nomor Resi'
        self.fields['catatan'].label = 'Catatan'

# NEW: Form filter untuk halaman admin pengiriman
class PengirimanFilterForm(forms.Form):
    status = forms.ChoiceField(
        choices=[('', 'Semua Status')] + Pengiriman.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    ekspedisi = forms.ChoiceField(
        choices=[('', 'Semua Ekspedisi')] + Pengiriman.EKSPEDISI_CHOICES,
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
    
    no_resi = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Cari berdasarkan nomor resi'
        })
    )
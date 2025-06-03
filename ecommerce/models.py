from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from decimal import Decimal

class User(AbstractUser):
    nama = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    alamat = models.TextField()
    password = models.CharField(max_length=128)
    noHP = models.CharField(max_length=15)
    
    def login(self):
        # Login logic akan dihandle oleh Django authentication
        pass
    
    def ubstart(self):
        # Update start method
        pass
    
    def ubahprofil(self):
        # Update profile method
        pass
    
    def logout(self):
        # Logout logic akan dihandle oleh Django authentication
        pass

class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nama = models.CharField(max_length=100)

class Buyer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    def frequent(self):
        # Method untuk mendapatkan frequent items
        pass
    
    def riwayatTransaksi(self):
        # Method untuk melihat riwayat transaksi
        return Transaksi.objects.filter(buyer=self)
    
    def konfirmasiPembayaran(self):
        # Method untuk konfirmasi pembayaran
        pass
    
    def lihhatdatapengiriman(self):
        # Method untuk melihat data pengiriman
        pass

class Produk(models.Model):
    nama = models.CharField(max_length=200)
    kategori = models.CharField(max_length=100)
    harga = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    stock = models.IntegerField(validators=[MinValueValidator(0)])
    berat = models.DecimalField(max_digits=8, decimal_places=2, default=1.0, help_text="Berat dalam kg")  # NEW
    gambar = models.ImageField(upload_to='produk_images/', blank=True, null=True) # TAMBAHKAN BARIS INI
    
    def updatestock(self):
        # Method untuk update stock
        pass
    
    def __str__(self):
        return self.nama

class Pengiriman(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Sedang Diproses'),
        ('shipped', 'Dikirim'),
        ('in_transit', 'Dalam Perjalanan'),
        ('out_for_delivery', 'Keluar untuk Pengiriman'),
        ('delivered', 'Terkirim'),
        ('failed', 'Gagal Kirim'),
        ('returned', 'Dikembalikan')
    ]
    
    EKSPEDISI_CHOICES = [
        ('jne', 'JNE'),
        ('pos', 'Pos Indonesia'),
        ('tiki', 'TIKI'),
        ('j&t', 'J&T Express'),
        ('sicepat', 'SiCepat'),
        ('anteraja', 'AnterAja'),
        ('ninja', 'Ninja Express'),
        ('gosend', 'GoSend'),
        ('grab', 'GrabExpress')
    ]
    
    alamat_pengirim = models.TextField(default="Toko E-Commerce, Surabaya")
    alamat_penerima = models.TextField()
    ongkir = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    ekspedisi = models.CharField(max_length=20, choices=EKSPEDISI_CHOICES, default='jne')  # NEW
    no_resi = models.CharField(max_length=50, blank=True, null=True)  # NEW
    estimasi_hari = models.IntegerField(default=3, help_text="Estimasi pengiriman dalam hari")  # NEW
    tanggal_kirim = models.DateTimeField(blank=True, null=True)  # NEW
    tanggal_terkirim = models.DateTimeField(blank=True, null=True)  # NEW
    catatan = models.TextField(blank=True, null=True)  # NEW
    created_at = models.DateTimeField(auto_now_add=True)  # NEW
    updated_at = models.DateTimeField(auto_now=True)  # NEW
    
    def totalongkir(self):
        return self.ongkir
    
    def tampilkanstatus(self):
        return self.get_status_display()
    
    def get_status_badge_color(self):
        """Return Bootstrap badge color based on status"""
        status_colors = {
            'pending': 'secondary',
            'processing': 'warning',
            'shipped': 'info',
            'in_transit': 'primary',
            'out_for_delivery': 'primary',
            'delivered': 'success',
            'failed': 'danger',
            'returned': 'dark'
        }
        return status_colors.get(self.status, 'secondary')
    
    def __str__(self):
        return f"Pengiriman {self.no_resi or self.id} - {self.get_status_display()}"

class LaporanPengiriman(models.Model):
    pengiriman = models.ForeignKey(Pengiriman, on_delete=models.CASCADE)
    jenis = models.CharField(max_length=100)
    tanggal_date = models.DateField()
    isi = models.TextField()
    
    def buatlaporanpengiriman(self):
        # Method untuk membuat laporan pengiriman
        pass

class Laporan1(models.Model):
    jenis = models.CharField(max_length=100)
    tanggal_date = models.DateField()
    isi = models.TextField()
    
    def buatlaporan(self):
        # Method untuk membuat laporan
        pass

class Transaksi(models.Model):
    buyer = models.ForeignKey(Buyer, on_delete=models.CASCADE)
    pembeli = models.CharField(max_length=100)  # Nama pembeli
    status = models.CharField(max_length=50, choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ])
    total_double = models.DecimalField(max_digits=12, decimal_places=2)
    tanggal_date = models.DateTimeField(auto_now_add=True)
    pengiriman = models.OneToOneField(Pengiriman, on_delete=models.SET_NULL, null=True, blank=True)  # NEW
    
    def pengeloladatakategori(self):
        # Method untuk mengelola data kategori
        pass
    
    def dataongkir(self):
        # Method untuk mendapatkan data ongkir
        return self.pengiriman.ongkir if self.pengiriman else 0
    
    def statuslv(self):
        # Method untuk status level
        pass
    
    def selesaikantransaksi(self):
        # Method untuk menyelesaikan transaksi
        self.status = 'completed'
        self.save()
    
    def hitungtotal(self):
        # Method untuk menghitung total
        return self.total_double
    
    def get_total_berat(self):
        """Calculate total weight of all products in transaction"""
        total_berat = 0
        for item in self.transaksiproduk_set.all():
            total_berat += (item.produk.berat * item.quantity)
        return total_berat

# Junction table untuk many-to-many relationship antara produk dan transaksi
class TransaksiProduk(models.Model):
    transaksi = models.ForeignKey(Transaksi, on_delete=models.CASCADE)
    produk = models.ForeignKey(Produk, on_delete=models.CASCADE)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    harga_satuan = models.DecimalField(max_digits=10, decimal_places=2)
    
    def get_subtotal(self):
        return self.harga_satuan * self.quantity
    
    def get_berat_total(self):
        return self.produk.berat * self.quantity
    
    class Meta:
        unique_together = ('transaksi', 'produk')

# Untuk model dari keranjangnya
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.username}"

    def get_total_items(self):
        return self.cartitem_set.aggregate(total_qty=models.Sum('quantity'))['total_qty'] or 0

    def get_total_price(self):
        total = Decimal(0)
        for item in self.cartitem_set.all():
            total += item.get_subtotal()
        return total

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    produk = models.ForeignKey(Produk, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        unique_together = ('cart', 'produk') # Pastikan satu produk hanya ada sekali di satu keranjang

    def __str__(self):
        return f"{self.quantity} x {self.produk.nama} in {self.cart.user.username}'s cart"

    def get_subtotal(self):
        return self.produk.harga * self.quantityy
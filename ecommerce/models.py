# ecommerce/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator # Tambahkan MaxValueValidator
from decimal import Decimal

class User(AbstractUser):
    nama = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    alamat = models.TextField()
    password = models.CharField(max_length=128)
    noHP = models.CharField(max_length=15)
    
    # Perbaikan metode login, ubstart, ubahprofil, logout:
    # Metode ini tidak perlu didefinisikan jika Anda mengandalkan fitur bawaan Django/allauth.
    # Jika ingin tetap ada, pastikan isinya tidak kosong dan memiliki logika.
    # Untuk saat ini, saya akan mengomentarinya atau menghapusnya jika tidak ada gunanya.
    # def login(self): pass
    # def ubstart(self): pass
    # def ubahprofil(self): pass
    # def logout(self): pass

class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nama = models.CharField(max_length=100)

class Buyer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Perbaikan metode:
    # def frequent(self): pass
    # def konfirmasiPembayaran(self): pass
    # def lihhatdatapengiriman(self): pass
    
    def riwayatTransaksi(self):
        # Method untuk melihat riwayat transaksi
        return Transaksi.objects.filter(buyer=self)
    
    def __str__(self):
        return self.user.username # Representasi string untuk Buyer

class Produk(models.Model):
    nama = models.CharField(max_length=200)
    kategori = models.CharField(max_length=100)
    harga = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    stock = models.IntegerField(validators=[MinValueValidator(0)])
    berat = models.DecimalField(max_digits=8, decimal_places=2, default=1.0, help_text="Berat dalam kg")
    gambar = models.ImageField(upload_to='produk_images/', blank=True, null=True)
    rating_rata_rata = models.DecimalField(max_digits=3, decimal_places=2, default=0.00) # BARU: Untuk rating rata-rata

    def updatestock(self):
        # Method untuk update stock, mungkin memerlukan logika lebih lanjut
        pass

    def update_average_rating(self): # BARU: Fungsi untuk update rating rata-rata
        reviews = self.ulasanproduk_set.all()
        if reviews.exists():
            total_rating = sum(review.rating for review in reviews)
            self.rating_rata_rata = total_rating / len(reviews)
        else:
            self.rating_rata_rata = Decimal('0.00') # Menggunakan Decimal untuk konsistensi
        self.save()

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
    ekspedisi = models.CharField(max_length=20, choices=EKSPEDISI_CHOICES, default='jne')
    no_resi = models.CharField(max_length=50, blank=True, null=True)
    estimasi_hari = models.IntegerField(default=3, help_text="Estimasi pengiriman dalam hari")
    tanggal_kirim = models.DateTimeField(blank=True, null=True)
    tanggal_terkirim = models.DateTimeField(blank=True, null=True)
    catatan = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
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
        pass

class Laporan1(models.Model):
    jenis = models.CharField(max_length=100)
    tanggal_date = models.DateField()
    isi = models.TextField()
    
    def buatlaporan(self):
        pass

class Transaksi(models.Model):
    buyer = models.ForeignKey(Buyer, on_delete=models.CASCADE)
    pembeli = models.CharField(max_length=100)
    status = models.CharField(max_length=50, choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ])
    total_double = models.DecimalField(max_digits=12, decimal_places=2)
    tanggal_date = models.DateTimeField(auto_now_add=True)
    pengiriman = models.OneToOneField(Pengiriman, on_delete=models.SET_NULL, null=True, blank=True)
    
    def pengeloladatakategori(self):
        pass
    
    def dataongkir(self):
        return self.pengiriman.ongkir if self.pengiriman else 0
    
    def statuslv(self):
        pass
    
    def selesaikantransaksi(self):
        self.status = 'completed'
        self.save()
    
    def hitungtotal(self):
        return self.total_double
    
    def get_total_berat(self):
        """Calculate total weight of all products in transaction"""
        total_berat = Decimal(0)
        for item in self.transaksiproduk_set.all():
            total_berat += (item.produk.berat * item.quantity)
        return total_berat

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

# BARU: Model Cart
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

    def get_total_berat(self):
        total_berat = Decimal(0)
        for item in self.cartitem_set.all():
            if item.produk and item.produk.berat:
                total_berat += (item.produk.berat * item.quantity)
        return total_berat

# BARU: Model CartItem
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    produk = models.ForeignKey(Produk, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        unique_together = ('cart', 'produk')

    def __str__(self):
        return f"{self.quantity} x {self.produk.nama} in {self.cart.user.username}'s cart"

    def get_subtotal(self):
        return self.produk.harga * self.quantity

# BARU: Model UlasanProduk (Review)
class UlasanProduk(models.Model):
    produk = models.ForeignKey(Produk, on_delete=models.CASCADE)
    buyer = models.ForeignKey(Buyer, on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Peringkat 1 (terburuk) hingga 5 (terbaik)"
    )
    komentar = models.TextField(blank=True, null=True)
    tanggal_ulasan = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('produk', 'buyer')

    def __str__(self):
        return f"Ulasan untuk {self.produk.nama} oleh {self.buyer.user.username} - {self.rating} bintang"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.produk.update_average_rating()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.produk.update_average_rating()
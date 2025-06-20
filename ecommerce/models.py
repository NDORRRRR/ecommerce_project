from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from django.utils.text import slugify

class User(AbstractUser):
    nama = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    alamat = models.TextField()
    #password = models.CharField(max_length=128)
    noHP = models.CharField(max_length=15)
    foto_profil = models.ImageField(upload_to='foto_profil/', null=True, blank=True, default='foto_profil/default.png')
    
    def __str__(self):
        return self.username

class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nama = models.CharField(max_length=100)

    def __str__(self):
        return self.nama

class Buyer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    def riwayatTransaksi(self):
        return Transaksi.objects.filter(buyer=self)
    
    def __str__(self):
        return self.user.username

class Kategori(models.Model):
    nama = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nama)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nama

    class Meta:
        verbose_name_plural = "Kategori"

class Produk(models.Model):
    nama = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True) 
    #kategori = models.CharField(max_length=100)
    kategori = models.ForeignKey(Kategori, on_delete=models.SET_NULL, null=True, related_name='produk')
    harga = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    stock = models.IntegerField(validators=[MinValueValidator(0)])
    deskripsi = models.TextField(blank=True, null=True)
    berat = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('1.0'), help_text="Berat dalam kg") # Pastikan Decimal
    gambar = models.ImageField(upload_to='produk_images/', blank=True, null=True)
    rating_rata_rata = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('0.00'))
    stok = models.PositiveIntegerField(default=0)

    def is_available(self):
        return self.stock > 0
    is_available.boolean = True
    is_available.short_description = 'Tersedia?'

    # FUNGSI SAVE UNTUK MENGISI SLUG OTOMATIS
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nama)
        super().save(*args, **kwargs)

    def update_average_rating(self):
        reviews = self.ulasanproduk_set.all()
        if reviews.exists():
            total_rating = sum(review.rating for review in reviews)
            self.rating_rata_rata = Decimal(total_rating) / Decimal(len(reviews))
        else:
            self.rating_rata_rata = Decimal('0.00')
        self.save()

    def updatestock(self):
        pass
    
    def __str__(self):
        return self.nama

class GambarProduk(models.Model):
    produk = models.ForeignKey(Produk, related_name='gambar_tambahan', on_delete=models.CASCADE)
    gambar = models.ImageField(upload_to='produk_images/details/', help_text="Unggah gambar detail produk")
    alt_text = models.CharField(max_length=255, blank=True, help_text="Teks alternatif untuk gambar (SEO)")

    class Meta:
        verbose_name = "Gambar Produk"
        verbose_name_plural = "Gambar-gambar Produk"

    def __str__(self):
        return f"Gambar untuk {self.produk.nama}"

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

class Ongkir(models.Model):
    provinsi = models.CharField(max_length=100)
    kabupaten_kota = models.CharField(max_length=100, verbose_name="Kabupaten/Kota")
    kecamatan = models.CharField(max_length=100)
    biaya = models.DecimalField(max_digits=10, decimal_places=0, help_text="Biaya dalam Rupiah")

    class Meta:
        verbose_name = "Ongkos Kirim"
        verbose_name_plural = "Daftar Ongkos Kirim"
        unique_together = ('provinsi', 'kabupaten_kota', 'kecamatan') # Mencegah data ongkir duplikat untuk lokasi yang sama

    def __str__(self):
        return f"{self.kecamatan}, {self.kabupaten_kota} - Rp {self.biaya:,.0f}"

class Alamat_penerima(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nama_lengkap = models.CharField(max_length=255)
    alamat_lengkap = models.TextField()
    kota = models.CharField(max_length=100)
    kode_pos = models.CharField(max_length=10)
    nomor_telepon = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return self.nama_lengkap + " - " + self.alamat_lengkap

    class Meta:
        verbose_name_plural = "Alamat Penerima"

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
    STATUS_CHOICES = [
        ('pending', 'Menunggu Pembayaran'),
        ('paid', 'Terbayar'),
        ('shipped', 'Dikirim'),
        ('completed', 'Selesai'),
        ('cancelled', 'Dibatalakn'),
        ('refunded', 'Dikembalikan')
    ]
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    tanggal_transaksi = models.DateTimeField(auto_now_add=True)
    total_harga = models.DecimalField(max_digits=12, decimal_places=2)
    status_pembayaran = models.CharField(max_length=20, choices=STATUS_TRANSAKSI, default='pending')
    # Tambahkan field untuk informasi pengiriman
    nama_penerima = models.CharField(max_length=255)
    alamat_lengkap = models.TextField()
    kota = models.CharField(max_length=100)
    kode_pos = models.CharField(max_length=10)
    nomor_telepon = models.CharField(max_length=20)
    catatan_pengiriman = models.TextField(blank=True, null=True)
    ongkir = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    nomor_resi = models.CharField(max_length=255, blank=True, null=True, unique=True)
    tanggal_pengiriman = models.DateTimeField(blank=True, null=True)
    
    def pengeloladatakategori(self):
        pass
    
    def dataongkir(self):
        return self.pengiriman.ongkir if self.pengiriman else Decimal('0.00')
    
    def statuslv(self):
        pass
    
    def selesaikantransaksi(self):
        self.status = 'completed'
        self.save()
    
    def hitungtotal(self):
        return self.total_double
    
    def get_total_berat(self):
        total_berat = Decimal(0)
        for item in self.transaksiproduk_set.all():
            if item.produk and item.produk.berat:
                total_berat += (item.produk.berat * item.quantity)
        return total_berat

    def get_subtotal(self):
        if self.pengiriman:
            return self.total_double - self.pengiriman.ongkir
        return self.total_double

class DetailTransaksi(models.Model):
    transaksi = models.ForeignKey(Transaksi, on_delete=models.CASCADE, related_name='detail_transaksi')
    produk = models.ForeignKey(Produk, on_delete=models.CASCADE)
    kuantitas = models.PositiveIntegerField()
    harga_per_unit = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.kuantitas} x {self.produk.nama_produk} (Transaksi #{self.transaksi.id})"

    def get_total_item_price(self):
        return self.kuantitas * self.harga_per_unit

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

# Model Cart
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

# Model CartItem
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

    def clean(self):
        if self.kuantitas > self.produk.stok:
            from django.core.exceptions import ValidationError
            raise ValidationError(f"Kuantitas yang diminta ({self.kuantitas}) melebihi stok yang tersedia ({self.produk.stok}).")

# Model UlasanProduk (Review)
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


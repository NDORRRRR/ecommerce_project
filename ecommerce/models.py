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
    
    def updatestock(self):
        # Method untuk update stock
        pass
    
    def __str__(self):
        return self.nama

class Pengiriman(models.Model):
    alamat = models.TextField()
    ongkir = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered')
    ])
    
    def totalongkir(self):
        return self.ongkir
    
    def tampilkanstatus(self):
        return self.status

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
    
    def pengeloladatakategori(self):
        # Method untuk mengelola data kategori
        pass
    
    def dataongkir(self):
        # Method untuk mendapatkan data ongkir
        pass
    
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

# Junction table untuk many-to-many relationship antara produk dan transaksi
class TransaksiProduk(models.Model):
    transaksi = models.ForeignKey(Transaksi, on_delete=models.CASCADE)
    produk = models.ForeignKey(Produk, on_delete=models.CASCADE)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    harga_satuan = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        unique_together = ('transaksi', 'produk')
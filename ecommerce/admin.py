from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import *

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'nama', 'email', 'noHP', 'is_staff', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'date_joined']
    search_fields = ['username', 'nama', 'email']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informasi Tambahan', {'fields': ('nama', 'alamat', 'noHP')}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informasi Tambahan', {'fields': ('nama', 'email', 'alamat', 'noHP')}),
    )

@admin.register(Admin)
class AdminAdmin(admin.ModelAdmin):
    list_display = ['user', 'nama']
    search_fields = ['user__username', 'nama']

@admin.register(Buyer)
class BuyerAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_nama', 'get_email']
    search_fields = ['user__username', 'user__nama', 'user__email']
    
    def get_nama(self, obj):
        return obj.user.nama
    get_nama.short_description = 'Nama'
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'

@admin.register(Produk)
class ProdukAdmin(admin.ModelAdmin):
    list_display = ['nama', 'kategori', 'harga', 'stock']
    list_filter = ['kategori']
    search_fields = ['nama', 'kategori']
    list_editable = ['harga', 'stock']

@admin.register(Pengiriman)
class PengirimanAdmin(admin.ModelAdmin):
    list_display = ['alamat', 'ongkir', 'status']
    list_filter = ['status']
    search_fields = ['alamat']
    list_editable = ['status']

@admin.register(LaporanPengiriman)
class LaporanPengirimanAdmin(admin.ModelAdmin):
    list_display = ['pengiriman', 'jenis', 'tanggal_date']
    list_filter = ['jenis', 'tanggal_date']
    search_fields = ['jenis', 'isi']

@admin.register(Laporan1)
class Laporan1Admin(admin.ModelAdmin):
    list_display = ['jenis', 'tanggal_date']
    list_filter = ['jenis', 'tanggal_date']
    search_fields = ['jenis', 'isi']

class TransaksiProdukInline(admin.TabularInline):
    model = TransaksiProduk
    extra = 0

@admin.register(Transaksi)
class TransaksiAdmin(admin.ModelAdmin):
    list_display = ['id', 'pembeli', 'status', 'total_double', 'tanggal_date']
    list_filter = ['status', 'tanggal_date']
    search_fields = ['pembeli', 'buyer__user__nama']
    list_editable = ['status']
    inlines = [TransaksiProdukInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('buyer__user')

@admin.register(TransaksiProduk)
class TransaksiProdukAdmin(admin.ModelAdmin):
    list_display = ['transaksi', 'produk', 'quantity', 'harga_satuan', 'get_total']
    list_filter = ['transaksi__status', 'produk__kategori']
    search_fields = ['transaksi__pembeli', 'produk__nama']
    
    def get_total(self, obj):
        return obj.quantity * obj.harga_satuan
    get_total.short_description = 'Total'
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
    list_display = ['nama', 'kategori', 'harga', 'stock', 'berat']  # UPDATED: Added berat
    list_filter = ['kategori']
    search_fields = ['nama', 'kategori']
    list_editable = ['harga', 'stock', 'berat']  # UPDATED: Added berat

@admin.register(Pengiriman)
class PengirimanAdmin(admin.ModelAdmin):
    # FIXED: Updated field names to match new model structure
    list_display = ['id', 'get_short_address', 'ekspedisi', 'ongkir', 'status', 'no_resi', 'created_at']
    list_filter = ['status', 'ekspedisi', 'created_at']
    search_fields = ['alamat_penerima', 'no_resi']  # UPDATED: Changed from 'alamat' to 'alamat_penerima'
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informasi Pengiriman', {
            'fields': ('ekspedisi', 'no_resi', 'ongkir', 'estimasi_hari')
        }),
        ('Alamat', {
            'fields': ('alamat_pengirim', 'alamat_penerima')
        }),
        ('Status & Tanggal', {
            'fields': ('status', 'tanggal_kirim', 'tanggal_terkirim')
        }),
        ('Catatan', {
            'fields': ('catatan',)
        }),
        ('Timestamp', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_short_address(self, obj):
        """Show shortened address for list display"""
        return obj.alamat_penerima[:50] + "..." if len(obj.alamat_penerima) > 50 else obj.alamat_penerima
    get_short_address.short_description = 'Alamat Tujuan'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()

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
    readonly_fields = ['get_subtotal', 'get_berat_total']
    
    def get_subtotal(self, obj):
        return f"Rp {obj.get_subtotal():,.0f}" if obj.id else "-"
    get_subtotal.short_description = 'Subtotal'
    
    def get_berat_total(self, obj):
        return f"{obj.get_berat_total():.1f} kg" if obj.id else "-"
    get_berat_total.short_description = 'Berat Total'

@admin.register(Transaksi)
class TransaksiAdmin(admin.ModelAdmin):
    list_display = ['id', 'pembeli', 'status', 'total_double', 'get_pengiriman_status', 'tanggal_date']
    list_filter = ['status', 'tanggal_date', 'pengiriman__status']  # UPDATED: Added pengiriman status filter
    search_fields = ['pembeli', 'buyer__user__nama', 'pengiriman__no_resi']  # UPDATED: Added resi search
    list_editable = ['status']
    inlines = [TransaksiProdukInline]
    
    fieldsets = (
        ('Informasi Transaksi', {
            'fields': ('buyer', 'pembeli', 'status', 'total_double')
        }),
        ('Pengiriman', {
            'fields': ('pengiriman',),
            'description': 'Data pengiriman terkait transaksi ini'
        }),
        ('Timestamp', {
            'fields': ('tanggal_date',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['tanggal_date']
    
    def get_pengiriman_status(self, obj):
        """Show shipping status in transaction list"""
        if obj.pengiriman:
            colors = {
                'pending': 'orange',
                'processing': 'blue', 
                'shipped': 'green',
                'in_transit': 'purple',
                'out_for_delivery': 'teal',
                'delivered': 'darkgreen',
                'failed': 'red',
                'returned': 'gray'
            }
            color = colors.get(obj.pengiriman.status, 'black')
            return f'<span style="color: {color}; font-weight: bold;">{obj.pengiriman.tampilkanstatus()}</span>'
        return '<span style="color: gray;">-</span>'
    get_pengiriman_status.short_description = 'Status Pengiriman'
    get_pengiriman_status.allow_tags = True
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('buyer__user', 'pengiriman')

@admin.register(TransaksiProduk)
class TransaksiProdukAdmin(admin.ModelAdmin):
    list_display = ['transaksi', 'produk', 'quantity', 'harga_satuan', 'get_subtotal', 'get_berat_total']
    list_filter = ['transaksi__status', 'produk__kategori']
    search_fields = ['transaksi__pembeli', 'produk__nama']
    
    def get_subtotal(self, obj):
        return f"Rp {obj.get_subtotal():,.0f}"
    get_subtotal.short_description = 'Subtotal'
    
    def get_berat_total(self, obj):
        return f"{obj.get_berat_total():.1f} kg"
    get_berat_total.short_description = 'Berat Total'
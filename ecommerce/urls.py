from django.urls import path
from . import views

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('produk/<int:produk_id>/', views.produk_detail, name='produk_detail'),
    
    # Authentication
    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    
    # User pages
    path('profile/', views.profile, name='profile'),
    path('transaksi/buat/', views.buat_transaksi, name='buat_transaksi'),
    path('transaksi/riwayat/', views.riwayat_transaksi, name='riwayat_transaksi'),
    path('transaksi/<int:transaksi_id>/', views.detail_transaksi, name='detail_transaksi'),
    path('transaksi/<int:transaksi_id>/konfirmasi/', views.konfirmasi_pembayaran, name='konfirmasi_pembayaran'),
    
    # NEW: Pengiriman URLs
    path('pengiriman/<int:transaksi_id>/', views.detail_pengiriman, name='detail_pengiriman'),
    path('pengiriman/<int:transaksi_id>/track/', views.track_pengiriman, name='track_pengiriman'),
    
    # Admin pages - Mengelola Data
    path('admin/kelola-pengguna/', views.mengelola_data_pengguna, name='kelola_pengguna'),
    path('admin/kelola-kategori/', views.mengelola_data_kategori, name='kelola_kategori'),
    path('admin/kelola-produk/', views.mengelola_data_produk, name='kelola_produk'),
    path('admin/kelola-ongkir/', views.mengelola_data_ongkir, name='kelola_ongkir'),
    path('admin/kelola-pelanggan/', views.mengelola_data_pelanggan, name='kelola_pelanggan'),
    path('admin/kelola-transaksi/', views.mengelola_data_transaksi, name='kelola_transaksi'),
    
    # NEW: Admin Pengiriman URLs
    path('admin/kelola-pengiriman/', views.kelola_pengiriman, name='kelola_pengiriman'),
    path('admin/pengiriman/<int:pengiriman_id>/update/', views.update_status_pengiriman, name='update_status_pengiriman'),
    
    # Admin pages - Melihat Data
    path('admin/data-pengiriman/', views.melihat_data_pengiriman, name='data_pengiriman'),
    path('admin/laporan-pelanggan/', views.melihat_laporan_pelanggan, name='laporan_pelanggan'),
    path('admin/laporan-transaksi/', views.melihat_laporan_transaksi, name='laporan_transaksi'),
    
    # Admin pages - Melakukan Transaksi
    path('admin/transaksi-langsung/', views.melakukan_transaksi_langsung, name='transaksi_langsung'),
]
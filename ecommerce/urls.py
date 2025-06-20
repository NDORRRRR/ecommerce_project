from django.urls import path, include
from . import views

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('produk/<int:produk_id>/', views.produk_detail, name='produk_detail'),
    path('produk/<int:produk_id>/tambah-ulasan/', views.tambah_ulasan, name='tambah_ulasan'),

    # URL untuk Ulasan Produk
    path('produk/<int:produk_id>/ulasan/tambah/', views.tambah_ulasan, name='tambah_ulasan'),

    # Authentication (DITANGANI OLEH DJANGO-ALLAUTH)
    #path('accounts/', include('allauth.urls')),
    #path('login/', views.user_login, name='login'),
    #path('register/', views.user_register, name='register'),
    #path('logout/', views.user_logout, name='logout'),
    
    # User pages
    path('profile/', views.profile, name='profile'),
    path('resend-verification/', views.resend_verification_email, name='resend_verification_email'),
    path('check-verification-status/', views.check_verification_status, name='check_verification_status'),
    # path('transaksi/buat/', views.buat_transaksi, name='buat_transaksi'),
    path('transaksi/riwayat/', views.riwayat_transaksi, name='riwayat_transaksi'),
    path('transaksi/<int:transaksi_id>/', views.detail_transaksi, name='detail_transaksi'),
    path('transaksi/<int:transaksi_id>/konfirmasi/', views.konfirmasi_pembayaran, name='konfirmasi_pembayaran'),
    
    # Keranjang Belanja & Checkout
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:produk_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('checkout/', views.checkout, name='checkout'),

    # Pengiriman URLs
    path('pengiriman/<int:transaksi_id>/', views.detail_pengiriman, name='detail_pengiriman'),
    #path('pengiriman/<int:transaksi_id>/track/', views.track_pengiriman, name='track_pengiriman'),
    path('pengiriman/<int:pengiriman_id>/track/', views.track_pengiriman, name='track_pengiriman'),
    
    # CUSTOM ADMIN pages - Ubah dari 'admin/' menjadi 'dashboard/'
    path('dashboard/kelola-pengguna/', views.mengelola_data_pengguna, name='kelola_pengguna'),
    path('dashboard/kelola-kategori/', views.mengelola_data_kategori, name='kelola_kategori'),
    path('dashboard/kelola-produk/', views.mengelola_data_produk, name='kelola_produk'),
    path('dashboard/kelola-produk/edit/<int:produk_id>/', views.edit_produk, name='edit_produk'),
    path('dashboard/produk/tambah/', views.tambah_produk, name='tambah_produk'),
    path('dashboard/produk/edit/<int:produk_id>/', views.edit_produk, name='edit_produk'),
    path('dashboard/produk/hapus/<int:produk_id>/', views.hapus_produk, name='hapus_produk'),
    path('dashboard/kelola-ongkir/', views.mengelola_data_ongkir, name='kelola_ongkir'),
    path('dashboard/kelola-pelanggan/', views.mengelola_data_pelanggan, name='kelola_pelanggan'),
    path('dashboard/kelola-transaksi/', views.mengelola_data_transaksi, name='kelola_transaksi'),
    path('dashboard/laporan-transaksi/', views.melihat_laporan_transaksi, name='laporan_transaksi'),
    path('dashboard/transaksi-langsung/proses/', views.proses_transaksi_langsung, name='proses_transaksi_langsung'),

    # Admin Pengiriman URLs
    path('dashboard/kelola-pengiriman/', views.melihat_data_pengiriman, name='kelola_pengiriman'), # Menuju view data pengiriman
    path('dashboard/pengiriman/<int:pengiriman_id>/update/', views.update_status_pengiriman, name='update_status_pengiriman'),
    path('dashboard/pengiriman/<int:pengiriman_id>/label/', views.cetak_label_pengiriman, name='cetak_label_pengiriman'),

    # Admin pages - Melihat Data
    # path('dashboard/data-pengiriman/', views.melihat_data_pengiriman, name='data_pengiriman'), # Ini duplikat jika kelola_pengiriman sudah ke sini
    path('dashboard/laporan-pelanggan/', views.melihat_laporan_pelanggan, name='laporan_pelanggan'),
    path('dashboard/pengiriman/<int:pengiriman_id>/label/', views.cetak_label_pengiriman, name='cetak_label_pengiriman'),
    
    # Admin pages - Melakukan Transaksi
    path('dashboard/transaksi-langsung/', views.melakukan_transaksi_langsung, name='transaksi_langsung'),
]
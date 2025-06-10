from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test, login_required
from allauth.account.utils import send_email_confirmation
from allauth.account.models import EmailAddress
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.forms import inlineformset_factory
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Avg, F, Q 
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import random
import string
from .models import User, Produk, Kategori, Pengiriman, Transaksi, TransaksiProduk, Buyer, Cart, CartItem, Laporan1, UlasanProduk, GambarProduk
from .forms import UlasanProdukForm, CheckoutForm, UpdatePengirimanForm, PengirimanFilterForm, ProdukForm, ProfilUpdateForm, UserProfileForm


def home(request):
    """Homepage dengan daftar produk"""
    produk_list = Produk.objects.all()
    search_query = request.GET.get('search')
    kategori_filter = request.GET.get('kategori')

    if search_query:
	matching_kategori_ids = Kategori.objects.filter(nama__icontains=search_query).values_list('id', flat=True)

    produk_list = produk_list.filter(
	Q(nama__icontains=search_query) |
	Q(deskripsi__icontains=search_query) |
	Q(kategori__in=list(matching_kategori_ids))
    )

   if kategori_filter:
	produk_list = produk_list.filter(kaegori__nama=kategori_filter)

   paginator = Paginator(produk_list, 10)
   page = request.GET.get('page')

   try:
	produk_list = paginator.page(page)

   except PageNotIsNotAnInteger:
	produk_list = paginato.page(1)

   except EmptyPage:
	produk_list = paginator.page(paginator.num_pages)

   all_kategori = Kategori.objects.all()

   context = {
	'produk_list': produk_list,
	'kategori_filter': kategori_filter,
	'search_query': search_query,
	'all_kategori': all_kategori,
   }
   return render(request, 'ecommerce/home.html', context)

def is_staff_user(user):
    return user.is_staff

@login_required
@user_passes_test(is_staff_user)
def tambah_produk(request):
    if request.method == 'POST':
        form = ProdukForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Produk baru berhasil ditambahkan!')
            return redirect('kelola_produk')
    else:
        form = ProdukForm()
    
    context = {
        'form': form,
        'title': 'Tambah Produk Baru'
    }
    return render(request, 'ecommerce/admin/form_produk.html', context)

@login_required
@user_passes_test(is_staff_user)
@staff_member_required
def edit_produk(request, produk_id):
    produk = get_object_or_404(Produk, id=produk_id)
    
    # Membuat Formset untuk GambarProduk yang terhubung dengan Produk
    # extra=1 artinya tampilkan 1 form kosong tambahan
    # can_delete=True artinya kita bisa menghapus gambar yang sudah ada
    GambarProdukFormSet = inlineformset_factory(
        Produk, 
        GambarProduk, 
        fields=('gambar', 'alt_text'), 
        extra=1, 
        can_delete=True
    )

    if request.method == 'POST':
        form = ProdukForm(request.POST, request.FILES, instance=produk)
        # Buat instance formset dengan data dari request juga
        formset = GambarProdukFormSet(request.POST, request.FILES, instance=produk, prefix='gambar')
        
        # Validasi keduanya, form utama dan formset
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save() # Simpan juga perubahan pada gambar-gambar
            
            messages.success(request, f'Produk "{produk.nama}" berhasil diperbarui.')
            return redirect('kelola_produk')
        else:
            messages.error(request, 'Terjadi kesalahan. Mohon periksa kembali data yang Anda masukkan.')
            
    else:
        form = ProdukForm(instance=produk)
        # Buat instance formset untuk produk yang ada
        formset = GambarProdukFormSet(instance=produk, prefix='gambar')
        
    context = {
        'form': form,
        'formset': formset, # <-- Kirim formset ke template
        'produk': produk
    }
    return render(request, 'ecommerce/admin/form_produk.html', context)

@login_required
@user_passes_test(is_staff_user)
def hapus_produk(request, produk_id):
    """View untuk menghapus produk."""
    produk = get_object_or_404(Produk, id=produk_id)
    if request.method == 'POST':
        nama_produk = produk.nama
        produk.delete()
        messages.success(request, f'Produk "{nama_produk}" telah dihapus.')
        return redirect('kelola_produk')
    
    return redirect('kelola_produk')

@login_required
def profile(request):
    if request.method == 'POST':
        # Kirim request.POST dan request.FILES untuk menangani data teks dan file
        form = ProfilUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil Anda berhasil diperbarui.')
            return redirect('profile') # Redirect ke nama URL 'profile'
    else:
        form = ProfilUpdateForm(instance=request.user)
        
    context = {
        'form': form
    }
    return render(request, 'ecommerce/profile.html', context)


@login_required
def resend_verification_email(request):
    """
    Mengirim ulang email verifikasi dan memberikan debug di terminal.
    """
    print("=============================================")
    print("--- FUNGSI KIRIM ULANG VERIFIKASI DIPANGGIL ---")

    try:
        # Ambil alamat email utama pengguna
        email_address = EmailAddress.objects.get(user=request.user, primary=True)
        
        print(f"DEBUG: Email Pengguna: {email_address.email}")
        print(f"DEBUG: Status Verifikasi Saat Ini: {email_address.verified}")

        # Cek apakah emailnya BENAR-BENAR belum terverifikasi
        if not email_address.verified:
            print(">>> STATUS: Belum terverifikasi. Mencoba mengirim email...")
            send_email_confirmation(request, request.user)
            messages.success(request, f'Email verifikasi telah dikirim ulang ke {email_address.email}. Silakan cek terminal.')
            print("--- PROSES SELESAI. Cek isi email di atas baris ini jika ada. ---")
        else:
            print(">>> STATUS: SUDAH terverifikasi. Tidak ada email yang dikirim.")
            messages.warning(request, f'Email {email_address.email} Anda sudah terverifikasi sebelumnya.')
    
    except EmailAddress.DoesNotExist:
        print(">>> ERROR: Pengguna tidak memiliki data EmailAddress.")
        messages.error(request, 'Tidak ditemukan data alamat email untuk akun Anda.')

    print("=============================================\n")
    return redirect('profile')

@login_required
def check_verification_status(request):
    """
    View yang diakses oleh JavaScript untuk mengecek status verifikasi email.
    """
    try:
        email_address = EmailAddress.objects.get(user=request.user, primary=True)
        is_verified = email_address.verified
    except EmailAddress.DoesNotExist:
        is_verified = False
    
    return JsonResponse({'is_verified': is_verified})

def produk_detail(request, produk_id):
    """Detail produk view, menampilkan ulasan dan form ulasan"""
    produk = get_object_or_404(Produk, id=produk_id)
    ulasan_produk = UlasanProduk.objects.filter(produk=produk).select_related('buyer__user').order_by('-tanggal_ulasan')
    
    form_ulasan = None
    sudah_ulasan = False
    
    if request.user.is_authenticated and hasattr(request.user, 'buyer'):
        buyer = request.user.buyer
        if UlasanProduk.objects.filter(produk=produk, buyer=buyer).exists():
            sudah_ulasan = True
        else:
            if TransaksiProduk.objects.filter(
                produk=produk, 
                transaksi__buyer=buyer, 
                transaksi__status__in=['completed', 'shipped']
            ).exists():
                form_ulasan = UlasanProdukForm()
        
    context = {
        'produk': produk,
        'ulasan_produk': ulasan_produk,
        'form_ulasan': form_ulasan,
        'sudah_ulasan': sudah_ulasan,
    }
    return render(request, 'ecommerce/produk_detail.html', context)

@login_required
def tambah_ulasan(request, produk_id):
    produk = get_object_or_404(Produk, id=produk_id)
    
    if request.method == 'POST':
        # Pastikan user adalah seorang Buyer
        if not hasattr(request.user, 'buyer'):
            messages.error(request, 'Hanya pembeli yang bisa memberikan ulasan.')
            return redirect('produk_detail', produk_id=produk.id)

        buyer = request.user.buyer

        # Cek apakah pembeli telah membeli produk ini
        if not TransaksiProduk.objects.filter(
            produk=produk, 
            transaksi__buyer=buyer, 
            transaksi__status__in=['completed', 'shipped']
        ).exists():
            messages.error(request, 'Anda harus membeli produk ini untuk memberi ulasan.')
            return redirect('produk_detail', produk_id=produk.id)

        # Cek apakah sudah pernah mengulas
        if UlasanProduk.objects.filter(produk=produk, buyer=buyer).exists():
            messages.warning(request, 'Anda sudah memberikan ulasan untuk produk ini.')
            return redirect('produk_detail', produk_id=produk.id)

        form = UlasanProdukForm(request.POST)
        if form.is_valid():
            ulasan = form.save(commit=False)
            ulasan.produk = produk
            ulasan.buyer = buyer
            ulasan.save()
            messages.success(request, 'Ulasan Anda berhasil ditambahkan!')
            return redirect('produk_detail', produk_id=produk.id)
        else:
            # Jika form tidak valid, kembali ke halaman detail dengan pesan error
            # (Untuk implementasi lebih lanjut, Anda bisa meneruskan form error ke template)
            messages.error(request, 'Gagal menambahkan ulasan. Periksa kembali input Anda.')
            return redirect('produk_detail', produk_id=produk.id)
            
    return redirect('produk_detail', produk_id=produk.id)

# --- Keranjang Belanja & Checkout ---
@login_required
def add_to_cart(request, produk_id):
    produk = get_object_or_404(Produk, id=produk_id)
    quantity = int(request.POST.get('quantity', 1))

    buyer, created_buyer = Buyer.objects.get_or_create(user=request.user)
    cart, created_cart = Cart.objects.get_or_create(user=request.user)

    if produk.stock < quantity:
        messages.error(request, f'Stok {produk.nama} tidak mencukupi. Tersedia: {produk.stock}.')
        return redirect('produk_detail', produk_id=produk.id)

    cart_item, created_item = CartItem.objects.get_or_create(
        cart=cart,
        produk=produk,
        defaults={'quantity': quantity}
    )

    if not created_item:
        new_quantity = cart_item.quantity + quantity
        if produk.stock < new_quantity:
            messages.error(request, f'Tidak bisa menambahkan lebih banyak {produk.nama}. Stok tidak cukup untuk kuantitas yang diminta.')
        else:
            cart_item.quantity = new_quantity
            cart_item.save()
            messages.success(request, f'{quantity} {produk.nama} ditambahkan ke keranjang.')
    else:
        messages.success(request, f'{produk.nama} berhasil ditambahkan ke keranjang.')

    return redirect('cart_detail')

@login_required
def cart_detail(request):
    buyer, created_buyer = Buyer.objects.get_or_create(user=request.user)
    cart, created_cart = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart).select_related('produk')

    total_price = cart.get_total_price()
    total_items = cart.get_total_items()

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': total_price,
        'total_items': total_items,
    }
    return render(request, 'ecommerce/cart_detail.html', context)

@login_required
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    action = request.POST.get('action')
    new_quantity = int(request.POST.get('quantity', cart_item.quantity))

    if action == 'remove':
        cart_item.delete()
        messages.success(request, f'{cart_item.produk.nama} berhasil dihapus dari keranjang.')
    elif action == 'set_quantity':
        if new_quantity <= 0:
            cart_item.delete()
            messages.success(request, f'{cart_item.produk.nama} berhasil dihapus dari keranjang.')
        elif new_quantity > cart_item.produk.stock:
            messages.error(request, f'Stok {cart_item.produk.nama} tidak mencukupi untuk kuantitas {new_quantity}. Tersedia: {cart_item.produk.stock}.')
        else:
            cart_item.quantity = new_quantity
            cart_item.save()
            messages.success(request, f'Kuantitas {cart_item.produk.nama} diperbarui menjadi {new_quantity}.')
    elif action == 'increase':
        if cart_item.quantity + 1 > cart_item.produk.stock:
            messages.error(request, f'Stok {cart_item.produk.nama} tidak mencukupi. Tersedia: {cart_item.produk.stock}.')
        else:
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, f'Kuantitas {cart_item.produk.nama} diperbarui.')
    elif action == 'decrease':
        if cart_item.quantity - 1 <= 0:
            cart_item.delete()
            messages.success(request, f'{cart_item.produk.nama} berhasil dihapus dari keranjang.')
        else:
            cart_item.quantity -= 1
            cart_item.save()
            messages.success(request, f'Kuantitas {cart_item.produk.nama} diperbarui.')

    return redirect('cart_detail')

@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = CartItem.objects.filter(cart=cart).select_related('produk')

    if not cart_items.exists():
        messages.warning(request, 'Keranjang belanja Anda kosong.')
        return redirect('cart_detail')

    if request.method == 'POST':
        ekspedisi = request.POST.get('ekspedisi', 'jne')
        alamat_pengiriman = request.POST.get('alamat_pengiriman', request.user.alamat)
        catatan = request.POST.get('catatan', '')

        total_berat_kg = Decimal(0)
        total_produk_price = Decimal(0)
        
        items_to_process = []
        for item in cart_items:
            if item.quantity > item.produk.stock:
                messages.error(request, f'Stok {item.produk.nama} tidak cukup ({item.produk.stock} tersedia). Mohon sesuaikan kuantitas di keranjang.')
                return redirect('cart_detail')
            total_berat_kg += item.produk.berat * item.quantity
            total_produk_price += item.produk.harga * item.quantity
            items_to_process.append(item)

        ongkir = calculate_ongkir(total_berat_kg, ekspedisi)
        grand_total = total_produk_price + ongkir

        try:
            pengiriman = Pengiriman.objects.create(
                alamat_penerima=alamat_pengiriman,
                ongkir=ongkir,
                ekspedisi=ekspedisi,
                status='pending',
                catatan=catatan
            )

            transaksi = Transaksi.objects.create(
                buyer=request.user.buyer,
                pembeli=request.user.nama,
                status='pending',
                total_double=grand_total,
                pengiriman=pengiriman
            )

            for item in items_to_process:
                TransaksiProduk.objects.create(
                    transaksi=transaksi,
                    produk=item.produk,
                    quantity=item.quantity,
                    harga_satuan=item.produk.harga
                )
                item.produk.stock -= item.quantity
                item.produk.save()

            cart_items.all().delete()

            messages.success(request, 'Checkout berhasil! Transaksi Anda sedang diproses.')
            return redirect('detail_transaksi', transaksi_id=transaksi.id)

        except Exception as e:
            messages.error(request, f'Terjadi kesalahan saat checkout: {e}.')
            return redirect('cart_detail')

    else:
        initial_ongkir = calculate_ongkir(cart.get_total_berat(), 'jne')
        
        form = CheckoutForm(initial={
            'alamat_pengiriman': request.user.alamat,
            'ekspedisi': 'jne'
        })

        context = {
            'cart': cart,
            'cart_items': cart_items,
            'total_price': cart.get_total_price(),
            'initial_ongkir': initial_ongkir,
            'form': form,
        }
        return render(request, 'ecommerce/checkout.html', context)

@login_required
def riwayat_transaksi(request):
    """Melihat riwayat transaksi"""
    buyer, created = Buyer.objects.get_or_create(user=request.user)
    if created:
        messages.info(request, 'Profile buyer telah dibuat otomatis.')
    
    transaksi_list = Transaksi.objects.filter(buyer=buyer).order_by('-tanggal_date')
    
    paginator = Paginator(transaksi_list, 10)
    page_number = request.GET.get('page')
    transaksi_list = paginator.get_page(page_number)
    
    return render(request, 'ecommerce/riwayat_transaksi.html', {
        'transaksi_list': transaksi_list
    })

# ecommerce/views.py

@login_required
def detail_transaksi(request, transaksi_id):
    """Detail transaksi, bisa diakses oleh buyer pemilik atau staff."""

    if request.user.is_staff:
        # Jika user adalah staff/admin, cari transaksi hanya berdasarkan ID
        transaksi = get_object_or_404(Transaksi, id=transaksi_id)
    else:
        # Jika user adalah pembeli biasa, pastikan mereka punya profil Buyer
        buyer, created = Buyer.objects.get_or_create(user=request.user)
        if created:
            messages.info(request, 'Profil buyer Anda telah dibuat otomatis.')

        # Cari transaksi berdasarkan ID DAN kepemilikan buyer
        transaksi = get_object_or_404(Transaksi, id=transaksi_id, buyer=buyer)

    # Logika untuk mengambil item produk di dalam transaksi tetap sama
    transaksi_produk = TransaksiProduk.objects.filter(transaksi=transaksi)

    context = {
        'transaksi': transaksi,
        'transaksi_produk': transaksi_produk
    }
    return render(request, 'ecommerce/detail_transaksi.html', context)

@login_required
def konfirmasi_pembayaran(request, transaksi_id):
    """Konfirmasi pembayaran"""
    buyer, created = Buyer.objects.get_or_create(user=request.user)
    if created:
        messages.info(request, 'Profile buyer telah dibuat otomatis.')
    
    transaksi = get_object_or_404(Transaksi, id=transaksi_id, buyer=buyer)
    
    if transaksi.status == 'pending':
        transaksi.status = 'paid'
        transaksi.save()
        
        if transaksi.pengiriman:
            transaksi.pengiriman.status = 'processing'
            transaksi.pengiriman.save()
        
        messages.success(request, 'Pembayaran berhasil dikonfirmasi!')
    else:
        messages.error(request, 'Transaksi tidak dapat dikonfirmasi!')
    
    return redirect('detail_transaksi', transaksi_id=transaksi.id)

@login_required
def detail_pengiriman(request, transaksi_id):
    # Cek apakah pengguna adalah staff/superuser
    if request.user.is_staff:
        # Jika staff, bisa lihat transaksi apa saja berdasarkan ID
        transaksi = get_object_or_404(Transaksi, id=transaksi_id)
    else:
        # Jika bukan staff (pengguna biasa), hanya bisa lihat transaksi miliknya
        buyer, created = Buyer.objects.get_or_create(user=request.user)
        transaksi = get_object_or_404(Transaksi, id=transaksi_id, buyer=buyer)

    # Cek apakah transaksi punya data pengiriman
    if not hasattr(transaksi, 'pengiriman'):
        messages.error(request, 'Data pengiriman tidak ditemukan untuk transaksi ini!')
        # Redirect ke halaman detail transaksi jika ada, atau ke riwayat jika tidak
        return redirect('detail_transaksi', transaksi_id=transaksi.id)

    return render(request, 'ecommerce/detail_pengiriman.html', {
        'transaksi': transaksi,
        'pengiriman': transaksi.pengiriman
    })

@login_required
def track_pengiriman(request, pengiriman_id): # Diubah ke pengiriman_id
    if request.user.is_staff:
        # Staff bisa melacak pengiriman manapun
        pengiriman = get_object_or_404(Pengiriman, id=pengiriman_id)
    else:
        # Pembeli hanya bisa melacak pengirimannya sendiri
        pengiriman = get_object_or_404(Pengiriman, id=pengiriman_id, transaksi__buyer__user=request.user)

    transaksi = pengiriman.transaksi
    if not transaksi:
        messages.error(request, 'Data transaksi untuk pengiriman ini tidak ditemukan!')
        return redirect('home')
    
    tracking_history = generate_tracking_history(pengiriman)
    
    return render(request, 'ecommerce/track_pengiriman.html', {
        'transaksi': transaksi,
        'pengiriman': pengiriman,
        'tracking_history': tracking_history
    })

def generate_tracking_history(pengiriman):
    """Generate sample tracking history"""
    history = []
    base_date = pengiriman.created_at
    
    status_flow = [
        ('pending', 'Pesanan diterima'),
        ('processing', 'Sedang Diproses'),
        ('shipped', 'Dikirim'),
        ('in_transit', 'Dalam Perjalanan'),
        ('out_for_delivery', 'Keluar untuk Pengiriman'),
        ('delivered', 'Terkirim')
    ]
    
    current_status_index = next((i for i, (status, _) in enumerate(status_flow) 
                                if status == pengiriman.status), 0)
    
    for i, (status, description) in enumerate(status_flow):
        if i <= current_status_index:
            history.append({
                'status': status,
                'description': description,
                'timestamp': base_date + timedelta(days=i),
                'location': f'Hub {pengiriman.ekspedisi.upper()}',
                'is_current': status == pengiriman.status
            })
    
    return history

def generate_resi_number():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

# Fungsi pembantu untuk menghitung ongkos kirim
def calculate_ongkir(berat_kg, ekspedisi):
    base_rates = {
        'jne' : Decimal('9000'),
        'pos' : Decimal('8000'),
        'tiki' : Decimal('9500'),
        'j&t' : Decimal('8500'),
        'sicepat' : Decimal('7900'),
        'anteraja' : Decimal('7500'),
        'ninja' : Decimal('7000'),
        'grab' : Decimal('12000'),
        'gosend' : Decimal('17000'),
    }

    base_rate = base_rates.get(ekspedisi, Decimal('9000')) # Default ke JNE jika tidak ditemukan

    if berat_kg <= Decimal('1.0'):
        return base_rate
    else:
        # Biaya tambahan per kg, misalnya 50% dari tarif dasar per kg untuk setiap kg tambahan
        additional_cost_per_kg = base_rate * Decimal('0.5')
        additional_weight = berat_kg - Decimal('1.0')
        return base_rate + (additional_weight * additional_cost_per_kg)

@login_required
def cetak_label_pengiriman(request, pengiriman_id):
    """View untuk menampilkan halaman cetak label pengiriman."""
    if not request.user.is_staff:
        messages.error(request, 'Akses ditolak!')
        return redirect('home')

    pengiriman = get_object_or_404(Pengiriman, id=pengiriman_id)
    context = {
        'pengiriman': pengiriman,
    }
    return render(request, 'ecommerce/admin/label_pengiriman.html', context)

# --- ADMIN VIEWS ---
def mengelola_data_pengguna(request):
    """Mengelola data pengguna (admin only)"""
    if not request.user.is_staff:
        messages.error(request, 'Akses ditolak!')
        return redirect('home')
    
    users = User.objects.all()
    return render(request, 'ecommerce/admin/kelola_pengguna.html', {'users': users})

def mengelola_data_kategori(request):
    """Mengelola data kategori produk"""
    if not request.user.is_staff:
        messages.error(request, 'Akses ditolak!')
        return redirect('home')
    
    kategori_list = Produk.objects.values_list('kategori', flat=True).distinct()
    return render(request, 'ecommerce/admin/kelola_kategori.html', {'kategori_list': kategori_list})

def mengelola_data_produk(request):
    """Mengelola data produk"""
    if not request.user.is_staff:
        messages.error(request, 'Akses ditolak!')
        return redirect('home')
    
    produk_list = Produk.objects.all()
    return render(request, 'ecommerce/admin/kelola_produk.html', {'produk_list': produk_list})

@login_required
def kelola_pengiriman(request):
    if not request.user.is_staff:
        messages.error(request, 'Akses ditolak!')
        return redirect('home')

    # Ambil filter status dari URL
    selected_status = request.GET.get('status')
    
    pengiriman_list = Pengiriman.objects.all().order_by('-created_at')
    if selected_status:
        pengiriman_list = pengiriman_list.filter(status=selected_status)

    # Hitung statistik untuk summary cards
    status_counts = Pengiriman.objects.values('status').annotate(count=Count('id'))
    status_counts_dict = {item['status']: item['count'] for item in status_counts}
    
    # Paginasi
    paginator = Paginator(pengiriman_list, 15) # 15 item per halaman
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'pengiriman_list': page_obj,
        'selected_status': selected_status,
        'status_counts': status_counts_dict
    }
    
    return render(request, 'ecommerce/admin/kelola_pengiriman.html', context)

def mengelola_data_ongkir(request):
    """Mengelola data ongkir"""
    if not request.user.is_staff:
        messages.error(request, 'Akses ditolak!')
        return redirect('home')
    
    ekspedisi_choices = Pengiriman.EKSPEDISI_CHOICES
    
    tarif_list = [
        {'ekspedisi': 'jne', 'nama': 'JNE', 'tarif_dasar': Decimal('9000'), 'tarif_tambahan_per_kg': Decimal('4500'), 'estimasi': '1-3 hari', 'status': 'Aktif'},
        {'ekspedisi': 'pos', 'nama': 'Pos Indonesia', 'tarif_dasar': Decimal('8000'), 'tarif_tambahan_per_kg': Decimal('4000'), 'estimasi': '2-4 hari', 'status': 'Aktif'},
        {'ekspedisi': 'tiki', 'nama': 'TIKI', 'tarif_dasar': Decimal('9500'), 'tarif_tambahan_per_kg': Decimal('4750'), 'estimasi': '1-3 hari', 'status': 'Aktif'},
        {'ekspedisi': 'j&t', 'nama': 'J&T Express', 'tarif_dasar': Decimal('8500'), 'tarif_tambahan_per_kg': Decimal('4250'), 'estimasi': '1-3 hari', 'status': 'Aktif'},
        {'ekspedisi': 'sicepat', 'nama': 'SiCepat', 'tarif_dasar': Decimal('8000'), 'tarif_tambahan_per_kg': Decimal('4000'), 'estimasi': '1-2 hari', 'status': 'Aktif'},
        {'ekspedisi': 'anteraja', 'nama': 'AnterAja', 'tarif_dasar': Decimal('7500'), 'tarif_tambahan_per_kg': Decimal('3750'), 'estimasi': '1-3 hari', 'status': 'Aktif'},
        {'ekspedisi': 'ninja', 'nama': 'Ninja Express', 'tarif_dasar': Decimal('7000'), 'tarif_tambahan_per_kg': Decimal('3500'), 'estimasi': '1-3 hari', 'status': 'Aktif'},
        {'ekspedisi': 'gosend', 'nama': 'GoSend', 'tarif_dasar': Decimal('17000'), 'tarif_tambahan_per_kg': Decimal('8500'), 'estimasi': 'Same Day', 'status': 'Aktif'},
        {'ekspedisi': 'grab', 'nama': 'GrabExpress', 'tarif_dasar': Decimal('12000'), 'tarif_tambahan_per_kg': Decimal('6000'), 'estimasi': 'Same Day', 'status': 'Aktif'},
    ]
    
    pengiriman_terbaru = Pengiriman.objects.all().order_by('-created_at')[:10]

    context = {
        'tarif_list': tarif_list,
        'pengiriman_list': pengiriman_terbaru,
    }
    return render(request, 'ecommerce/admin/kelola_ongkir.html', context)

@login_required
def data_pengiriman(request):
    # Mengoptimalkan query dengan select_related
    pengiriman_list = Pengiriman.objects.select_related('transaksi', 'transaksi__buyer__user').all().order_by('-created_at')

    # Menghitung data statistik untuk ringkasan
    total_pengiriman = pengiriman_list.count()
    perlu_dikirim = pengiriman_list.filter(status='pending').count()
    dalam_perjalanan = pengiriman_list.filter(status='shipped').count()
    tiba_di_tujuan = pengiriman_list.filter(status='delivered').count()

    context = {
        'pengiriman_list': pengiriman_list,
        'total_pengiriman': total_pengiriman,
        'perlu_dikirim': perlu_dikirim,
        'dalam_perjalanan': dalam_perjalanan,
        'tiba_di_tujuan': tiba_di_tujuan,
    }
    return render(request, 'ecommerce/admin/data_pengiriman.html', context)

def melihat_data_pengiriman(request):
    if not request.user.is_staff:
        messages.error(request, 'Akses ditolak!')
        return redirect('home')
    
    pengiriman_list = Pengiriman.objects.all().select_related('transaksi__buyer__user')

    status_filter = request.GET.get('status')
    if status_filter:
        pengiriman_list = pengiriman_list.filter(status=status_filter)

    ekspedisi_filter = request.GET.get('ekspedisi')
    if ekspedisi_filter:
        pengiriman_list = pengiriman_list.filter(ekspedisi=ekspedisi_filter)

    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            pengiriman_list = pengiriman_list.filter(
                created_at__date__range=[start_date, end_date]
            )
        except ValueError:
            messages.error(request, "Format tanggal tidak valid. Gunakan YYYY-MM-DD.")
    
    stats = {
        'pending': pengiriman_list.filter(status='pending').count(),
        'processing': pengiriman_list.filter(status='processing').count(), # SUDAH DIPERBAIKI
        'shipped': pengiriman_list.filter(status='shipped').count(),
        'in_transit': pengiriman_list.filter(status='in_transit').count(),
        'delivered': pengiriman_list.filter(status='delivered').count(),
        'failed': pengiriman_list.filter(status='failed').count(),
    }
    
    status_chart_labels = [label for value, label in Pengiriman.STATUS_CHOICES]
    status_chart_data = [pengiriman_list.filter(status=value).count() for value, _ in Pengiriman.STATUS_CHOICES]

    ekspedisi_chart_labels = [label for value, label in Pengiriman.EKSPEDISI_CHOICES]
    ekspedisi_chart_data = [pengiriman_list.filter(ekspedisi=value).count() for value, _ in Pengiriman.EKSPEDISI_CHOICES]

    for pengiriman in pengiriman_list:
        if pengiriman.tanggal_kirim and pengiriman.tanggal_terkirim:
            delta = pengiriman.tanggal_terkirim - pengiriman.tanggal_kirim
            pengiriman.get_duration = delta.days

    return render(request, 'ecommerce/admin/data_pengiriman.html', {
        'pengiriman_list': pengiriman_list,
        'status_choices': Pengiriman.STATUS_CHOICES,
        'ekspedisi_choices': Pengiriman.EKSPEDISI_CHOICES,
        'stats': stats,
        'status_chart_labels': status_chart_labels,
        'status_chart_data': status_chart_data,
        'ekspedisi_chart_labels': ekspedisi_chart_labels,
        'ekspedisi_chart_data': ekspedisi_chart_data,
        'request_params': request.GET,
    })

@login_required
def update_status_pengiriman(request, pengiriman_id):
    if not request.user.is_staff:
        messages.error(request, 'Akses ditolak!')
        return redirect('home')

    pengiriman = get_object_or_404(Pengiriman, id=pengiriman_id)
    
    if request.method == 'POST':
        form = UpdatePengirimanForm(request.POST, instance=pengiriman)
        if form.is_valid():
            updated_pengiriman = form.save(commit=False)
            
            if updated_pengiriman.status == 'shipped' and not updated_pengiriman.tanggal_kirim:
                updated_pengiriman.tanggal_kirim = timezone.now()
            
            if updated_pengiriman.status == 'delivered' and not updated_pengiriman.tanggal_terkirim:
                updated_pengiriman.tanggal_terkirim = timezone.now()
                
                if hasattr(updated_pengiriman, 'transaksi'):
                    transaksi = updated_pengiriman.transaksi
                    transaksi.status = 'completed'
                    transaksi.save()

            updated_pengiriman.save()
            messages.success(request, f'Status pengiriman #{pengiriman.id} berhasil diupdate!')
            return redirect('kelola_pengiriman')
    else:
        form = UpdatePengirimanForm(instance=pengiriman)

    context = {
        'form': form,
        'pengiriman': pengiriman,
        'status_choices': Pengiriman.STATUS_CHOICES, # Untuk preview di template
    }
    
    return render(request, 'ecommerce/admin/update_pengiriman.html', context)

def mengelola_data_pelanggan(request):
    if not request.user.is_staff:
        messages.error(request, 'Akses ditolak!')
        return redirect('home')
    
    buyer_list = Buyer.objects.all().select_related('user')

    if request.method == 'POST':
        username = request.POST.get('username')
        nama = request.POST.get('nama')
        email = request.POST.get('email')
        noHP = request.POST.get('noHP')
        alamat = request.POST.get('alamat')
        password = request.POST.get('password')

        try:
            user = User.objects.create_user(
                username=username,
                nama=nama,
                email=email,
                noHP=noHP,
                alamat=alamat,
                password=password,
            )
            Buyer.objects.create(user=user)
            messages.success(request, f'Pelanggan {nama} berhasil ditambahkan!')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

        return redirect('kelola_pelanggan')

    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', '')
    status_filter = request.GET.get('status', '')

    if search_query:
        buyer_list = buyer_list.filter(
            Q(user__nama__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__noHP__icontains=search_query) |
            Q(user__username__icontains=search_query)
        )
    
    if status_filter == 'active':
        buyer_list = buyer_list.filter(user__is_active=True)
    elif status_filter == 'inactive':
        buyer_list = buyer_list.filter(user__is_active=False)

    if sort_by == 'name':
        buyer_list = buyer_list.order_by('user__nama')
    elif sort_by == 'date':
        buyer_list = buyer_list.order_by('user__date_joined')
    elif sort_by == 'transactions':
        buyer_list = buyer_list.annotate(transaction_count=Count('transaksi')).order_by('-transaction_count')
    elif sort_by == 'total':
        buyer_list = buyer_list.annotate(total_spent=Sum('transaksi__total_double')).order_by('-total_spent')

    active_buyers = Transaksi.objects.filter(
        tanggal_date__gte=timezone.now() - timedelta(days=30)
    ).values('buyer').distinct().count()

    new_buyers = Buyer.objects.filter(
        user__date_joined__gte=timezone.now() - timedelta(days=7)
    ).count()

    avg_transactions = Transaksi.objects.values('buyer').annotate(
        count=Count('id')
    ).aggregate(avg=Avg('count'))['avg'] or 0

    for buyer in buyer_list:
        buyer.get_total_purchases = Transaksi.objects.filter(
            buyer=buyer, status__in=['completed', 'shipped']
        ).aggregate(total=Sum('total_double'))['total'] or 0
        buyer.is_active = Transaksi.objects.filter(
            buyer=buyer,
            tanggal_date__gte=timezone.now() - timedelta(days=30)
        ).exists()

    context = {
        'buyer_list': buyer_list,
        'active_buyers': active_buyers,
        'new_buyers': new_buyers,
        'avg_transactions': int(avg_transactions),
        'request': request,
    }

    return render(request, 'ecommerce/admin/kelola_pelanggan.html', context)

def melakukan_transaksi_langsung(request):
    """Melakukan transaksi langsung (admin)"""
    if not request.user.is_staff:
        messages.error(request, 'Akses ditolak!')
        return redirect('home')
    
    produk_list = Produk.objects.all()
    buyer_list = Buyer.objects.all().select_related('user')
    kategori_list = Produk.objects.values_list('kategori', flat=True).distinct()

    context = {
        'produk_list': produk_list,
        'buyer_list': buyer_list,
        'kategori_list': kategori_list,
    }
    return render(request, 'ecommerce/admin/transaksi_langsung.html', context)

def mengelola_data_transaksi(request):
    """Mengelola data transaksi"""
    if not request.user.is_staff:
        messages.error(request, 'Akses ditolak!')
        return redirect('home')
    
    transaksi_list = Transaksi.objects.all().order_by('-tanggal_date')
    return render(request, 'ecommerce/admin/kelola_transaksi.html', {'transaksi_list': transaksi_list})

def melihat_laporan_pelanggan(request):
    """Melihat laporan pelanggan"""
    if not request.user.is_staff:
        messages.error(request, 'Akses ditolak!')
        return redirect('home')
    
    laporan_list = Laporan1.objects.all()
    return render(request, 'ecommerce/admin/laporan_pelanggan.html', {'laporan_list': laporan_list})

def melihat_laporan_transaksi(request):
    """Melihat laporan transaksi"""
    if not request.user.is_staff:
        messages.error(request, 'Akses ditolak!')
        return redirect('home')
    
    transaksi_list = Transaksi.objects.all()
    
    period = request.GET.get('period', 'month')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    status_filter = request.GET.get('status')

    today = timezone.localdate()
    if period == 'today':
        start_date = today
        end_date = today
        period_label = 'Hari Ini'
    elif period == 'week':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
        period_label = 'Minggu Ini'
    elif period == 'month':
        start_date = today.replace(day=1)
        end_date = (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        period_label = 'Bulan Ini'
    elif period == 'year':
        start_date = today.replace(month=1, day=1)
        end_date = today.replace(month=12, day=31)
        period_label = 'Tahun Ini'
    elif period == 'custom' and start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            period_label = f'{start_date_str} s/d {end_date_str}'
        except ValueError:
            messages.error(request, "Format tanggal tidak valid. Gunakan YYYY-MM-DD.")
            start_date = today.replace(day=1)
            end_date = (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            period_label = 'Bulan Ini'
    else:
        start_date = today.replace(day=1)
        end_date = (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        period_label = 'Bulan Ini'

    transaksi_list = transaksi_list.filter(tanggal_date__date__range=[start_date, end_date])

    if status_filter:
        transaksi_list = transaksi_list.filter(status=status_filter)

    total_transactions = transaksi_list.count()
    total_revenue = transaksi_list.aggregate(Sum('total_double'))['total_double__sum'] or Decimal(0)
    total_subtotal = transaksi_list.annotate(
        calculated_subtotal=F('total_double') - F('pengiriman__ongkir')
    ).aggregate(Sum('calculated_subtotal'))['calculated_subtotal__sum'] or Decimal(0)
    total_shipping = transaksi_list.aggregate(Sum('pengiriman__ongkir'))['pengiriman__ongkir__sum'] or Decimal(0)

    avg_transaction = total_revenue / total_transactions if total_transactions else Decimal(0)
    success_rate = (transaksi_list.filter(status='completed').count() / total_transactions * 100) if total_transactions else 0

    date_counts = transaksi_list.extra({'date_created': "date(tanggal_date)"}).values('date_created').annotate(count=Count('id')).order_by('date_created')
    chart_labels = [str(item['date_created']) for item in date_counts]
    chart_data = [item['count'] for item in date_counts]

    revenue_counts = transaksi_list.extra({'date_created': "date(tanggal_date)"}).values('date_created').annotate(total=Sum('total_double')).order_by('date_created')
    revenue_data = [float(item['total']) / 1000 for item in revenue_counts]

    status_counts_dict = {status: 0 for status, _ in Transaksi.STATUS_CHOICES}
    for status, count in transaksi_list.values('status').annotate(count=Count('id')):
        status_counts_dict[status] = count
    status_data = [status_counts_dict[status] for status, _ in Transaksi.STATUS_CHOICES]

    category_revenue = TransaksiProduk.objects.filter(transaksi__in=transaksi_list).values('produk__kategori').annotate(total_revenue=Sum(F('harga_satuan') * F('quantity'))).order_by('-total_revenue')
    category_labels = [item['produk__kategori'] for item in category_revenue]
    category_data = [float(item['total_revenue']) for item in category_revenue]

    top_products = TransaksiProduk.objects.filter(transaksi__in=transaksi_list).values('produk__nama').annotate(
        sold=Sum('quantity'),
        revenue=Sum(F('harga_satuan') * F('quantity'))
    ).order_by('-sold')[:10]

    top_customers = Transaksi.objects.filter(id__in=transaksi_list).values('buyer__user__nama').annotate(
        count=Count('id'),
        total=Sum('total_double')
    ).order_by('-total')[:10]

    ekspedisi_data_raw = Pengiriman.objects.filter(transaksi__in=transaksi_list).values('ekspedisi').annotate(count=Count('id'))
    ekspedisi_labels = [item['ekspedisi'] for item in ekspedisi_data_raw]
    ekspedisi_data = [item['count'] for item in ekspedisi_data_raw]

    hour_bins = [0, 0, 0, 0]  # 00-06, 06-12, 12-18, 18-24
    for transaksi in transaksi_list:
        hour = transaksi.tanggal_date.hour
        if 0 <= hour < 6:
            hour_bins[0] += 1
        elif 6 <= hour < 12:
            hour_bins[1] += 1
        elif 12 <= hour < 18:
            hour_bins[2] += 1
        else:  # 18-23
            hour_bins[3] += 1
    hour_data = hour_bins

    context = {
        'transaksi_list': transaksi_list,
        'total_transactions': total_transactions,
        'total_revenue': total_revenue,
        'avg_transaction': avg_transaction,
        'success_rate': success_rate,
        'period_label': period_label,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'revenue_data': revenue_data,
        'status_data': status_data,
        'category_labels': category_labels,
        'category_data': category_data,
        'top_products': top_products,
        'top_customers': top_customers,
        'ekspedisi_labels': ekspedisi_labels,
        'ekspedisi_data': ekspedisi_data,
        'hour_data': hour_data,
        'total_subtotal': total_subtotal,
        'total_shipping': total_shipping,
        'empty_list': [],
        'request': request,
    }
    return render(request, 'ecommerce/admin/laporan_transaksi.html', context)

@csrf_exempt # Gunakan csrf_exempt untuk kemudahan, atau implementasi CSRF token di AJAX Anda
@login_required
def proses_transaksi_langsung(request):
    if request.method == 'POST' and request.user.is_staff:
        try:
            data = json.loads(request.body)
            items = data.get('items', [])
            total = float(data.get('total', 0))
            
            if not items or total == 0:
                return JsonResponse({'status': 'error', 'message': 'Tidak ada item atau total nol.'}, status=400)

            # Buat objek transaksi baru
            # Asumsi pelanggan default atau "walk-in" jika tidak ada data pelanggan
            # Anda mungkin perlu menambahkan field pelanggan di sini
            transaksi = Transaksi.objects.create(
                user=request.user,  # Atau user pelanggan jika ada
                total_harga=total,
                status_pembayaran='Lunas', # Langsung lunas
                metode_pembayaran='Tunai' # Asumsi tunai
            )

            # Simpan setiap item transaksi dan kurangi stok
            for item in items:
                try:
                    produk = Produk.objects.get(id=item['id'])
                    jumlah = int(item['quantity'])
                    
                    if produk.stok < jumlah:
                        # Sebaiknya ada penanganan error yang lebih baik di sini
                        # Untuk sekarang kita batalkan transaksi
                        transaksi.delete()
                        return JsonResponse({'status': 'error', 'message': f'Stok produk {produk.nama} tidak mencukupi.'}, status=400)
                    
                    TransaksiProduk.objects.create(
                        transaksi=transaksi,
                        produk=produk,
                        jumlah=jumlah,
                        harga_saat_transaksi=produk.harga
                    )
                    # Kurangi stok produk
                    produk.stok -= jumlah
                    produk.save()
                except Produk.DoesNotExist:
                    transaksi.delete()
                    return JsonResponse({'status': 'error', 'message': f'Produk dengan ID {item["id"]} tidak ditemukan.'}, status=404)

            return JsonResponse({'status': 'success', 'message': 'Transaksi berhasil disimpan!', 'transaksi_id': transaksi.id})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

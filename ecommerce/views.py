from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Avg, F, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import random
import string

from .models import User, Produk, Pengiriman, Transaksi, TransaksiProduk, Buyer, Cart, CartItem, Laporan1, UlasanProduk # Pastikan semua model diimpor
from .forms import UserProfileForm, UlasanProdukForm, CheckoutForm # Pastikan semua form diimpor


def home(request):
    """Homepage dengan daftar produk"""
    produk_list = Produk.objects.all()

    # Search functionality (sudah dipindahkan ke navbar)
    search = request.GET.get('search')
    if search:
        produk_list = produk_list.filter(
            Q(nama__icontains=search) | Q(kategori__icontains=search)
        )
    
    # Filter berdasarkan kategori (dihapus dari sidebar, bisa ditambahkan lagi di navbar jika perlu)
    # kategori_list = Produk.objects.values_list('kategori', flat=True).distinct()
    # kategori = request.GET.get('kategori')
    # if kategori:
    #     produk_list = produk_list.filter(kategori=kategori)
    
    paginator = Paginator(produk_list, 12)
    page_number = request.GET.get('page')
    produk_list = paginator.get_page(page_number)
    
    context = {
        'produk_list': produk_list,
        # 'kategori_list': kategori_list, # Nonaktifkan jika tidak ada filter kategori di UI
        # 'selected_kategori': kategori,
        'search_query': search
    }
    return render(request, 'ecommerce/home.html', context)

# --- Autentikasi (DITANGANI OLEH DJANGO-ALLAUTH) ---
# Fungsi user_login dan user_register kustom Anda tidak lagi digunakan
# karena allauth akan mengelola proses login/register.
# Saya akan mempertahankan user_logout untuk pesan kustom.

def user_logout(request):
    """Logout view"""
    logout(request)
    messages.success(request, 'Logout berhasil!')
    return redirect('home')

@login_required
def profile(request):
    """User profile view"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile berhasil diupdate!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'ecommerce/profile.html', {'form': form})

def produk_detail(request, produk_id):
    """Detail produk view, menampilkan ulasan dan form ulasan"""
    produk = get_object_or_404(Produk, id=produk_id)
    ulasan_produk = UlasanProduk.objects.filter(produk=produk).select_related('buyer__user').order_by('-tanggal_ulasan')
    
    form_ulasan = None
    sudah_ulasan = False
    
    if request.user.is_authenticated and hasattr(request.user, 'buyer'):
        buyer = request.user.buyer
        # Cek apakah pengguna sudah pernah mengulas produk ini
        if UlasanProduk.objects.filter(produk=produk, buyer=buyer).exists():
            sudah_ulasan = True
        else:
            # Pastikan pembeli telah membeli produk ini sebelum bisa mengulas
            if TransaksiProduk.objects.filter(
                produk=produk, 
                transaksi__buyer=buyer, 
                transaksi__status__in=['completed', 'shipped']
            ).exists():
                form_ulasan = UlasanProdukForm()
            # else:
                # messages.info(request, "Anda harus membeli dan menyelesaikan transaksi produk ini untuk dapat memberikan ulasan.")
        
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
    
    if not hasattr(request.user, 'buyer'):
        messages.error(request, 'Anda harus memiliki profil pembeli untuk dapat mengulas.')
        return redirect('produk_detail', produk_id=produk.id)

    buyer = request.user.buyer

    # Cek apakah pembeli telah membeli produk ini dan transaksi selesai
    if not TransaksiProduk.objects.filter(
        produk=produk, 
        transaksi__buyer=buyer, 
        transaksi__status__in=['completed', 'shipped']
    ).exists():
        messages.error(request, 'Anda hanya dapat mengulas produk yang telah Anda beli dan selesaikan transaksinya.')
        return redirect('produk_detail', produk_id=produk.id)

    if request.method == 'POST':
        form = UlasanProdukForm(request.POST)
        if form.is_valid():
            # Cek jika user sudah mengulas produk ini sebelumnya (race condition)
            if UlasanProduk.objects.filter(produk=produk, buyer=buyer).exists():
                messages.warning(request, 'Anda sudah memberikan ulasan untuk produk ini.')
                return redirect('produk_detail', produk_id=produk.id)

            ulasan = UlasanProduk.objects.create(
                produk=produk,
                buyer=buyer,
                rating=form.cleaned_data['rating'],
                komentar=form.cleaned_data['komentar']
            )
            messages.success(request, 'Ulasan Anda berhasil ditambahkan!')
            return redirect('produk_detail', produk_id=produk.id)
        else:
            messages.error(request, 'Ada kesalahan dalam formulir ulasan Anda.')
    
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

# --- Transaksi & Pengiriman ---
# Fungsi buat_transaksi sebelumnya dihapus/dimodifikasi karena sudah digantikan oleh alur keranjang belanja.
# Jika ada kebutuhan untuk transaksi tanpa keranjang, fungsi ini harus didefinisikan ulang secara terpisah.

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

@login_required
def detail_transaksi(request, transaksi_id):
    """Detail transaksi"""
    buyer, created = Buyer.objects.get_or_create(user=request.user)
    if created:
        messages.info(request, 'Profile buyer telah dibuat otomatis.')
    
    transaksi = get_object_or_404(Transaksi, id=transaksi_id, buyer=buyer)
    transaksi_produk = TransaksiProduk.objects.filter(transaksi=transaksi)
    
    return render(request, 'ecommerce/detail_transaksi.html', {
        'transaksi': transaksi,
        'transaksi_produk': transaksi_produk
    })

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
    buyer, created = Buyer.objects.get_or_create(user=request.user)
    transaksi = get_object_or_404(Transaksi, id=transaksi_id, buyer=buyer)

    if not transaksi.pengiriman:
        messages.error(request, 'Data pengiriman tidak ditemukan!')
        return redirect('detail_transaksi', transaksi_id=transaksi.id)

    return render(request, 'ecommerce/detail_pengiriman.html', {
        'transaksi': transaksi,
        'pengiriman': transaksi.pengiriman
    })

@login_required
def track_pengiriman(request, transaksi_id):
    buyer, created = Buyer.objects.get_or_create(user=request.user)
    transaksi = get_object_or_404(Transaksi, id=transaksi_id, buyer=buyer)
    
    if not transaksi.pengiriman:
        messages.error(request, 'Data pengiriman tidak ditemukan!')
        return redirect('detail_transaksi', transaksi_id=transaksi.id)
    
    tracking_history = generate_tracking_history(transaksi.pengiriman)
    
    return render(request, 'ecommerce/track_pengiriman.html', {
        'transaksi': transaksi,
        'pengiriman': transaksi.pengiriman,
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

def mengelola_data_ongkir(request):
    """Mengelola data ongkir"""
    if not request.user.is_staff:
        messages.error(request, 'Akses ditolak!')
        return redirect('home')
    
    pengiriman_list = Pengiriman.objects.all()
    return render(request, 'ecommerce/admin/kelola_ongkir.html', {'pengiriman_list': pengiriman_list})

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

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        pengiriman_list = pengiriman_list.filter(
            created_at__date__range=[start_date, end_date]
        )

    stats = {
        'pending': pengiriman_list.filter(status='pending').count(),
        'processing': pengiriman_list.filter(status='processing').count(),
        'shipped': pengiriman_list.filter(status='shipped').count(),
        'in_transit': pengiriman_list.filter(status='in_transit').count(),
        'delivered': pengiriman_list.filter(status='delivered').count(),
        'failed': pengiriman_list.filter(status='failed').count(),
    }
    
    for pengiriman in pengiriman_list:
        if pengiriman.tanggal_kirim and pengiriman.tanggal_terkirim:
            delta = pengiriman.tanggal_terkirim - pengiriman.tanggal_kirim
            pengiriman.get_duration = delta.days

    return render(request, 'ecommerce/admin/data_pengiriman.html', {
        'pengiriman_list': pengiriman_list,
        'status_choices': Pengiriman.STATUS_CHOICES,
        'ekspedisi_choices': Pengiriman.EKSPEDISI_CHOICES,
        'stats': stats,
    })


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
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
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
    elif period == 'custom' and start_date and end_date:
        period_label = f'{start_date} s/d {end_date}'
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

    hour_data_raw = transaksi_list.extra({'hour': "strftime('%H', tanggal_date)"}).values('hour').annotate(count=Count('id')).order_by('hour')
    
    hour_bins = [0, 0, 0, 0] # 00-06, 06-12, 12-18, 18-24
    for item in hour_data_raw:
        hour = int(item['hour'])
        if 0 <= hour < 6:
            hour_bins[0] += item['count']
        elif 6 <= hour < 12:
            hour_bins[1] += item['count']
        elif 12 <= hour < 18:
            hour_bins[2] += item['count']
        else: # 18-24
            hour_bins[3] += item['count']
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
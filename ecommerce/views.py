from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse  # This is the correct import
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Avg, F, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import *
from .forms import *
from decimal import Decimal
import random
import string

def home(request):
    """Homepage dengan daftar produk"""
    produk_list = Produk.objects.all()
    kategori_list = Produk.objects.values_list('kategori', flat=True).distinct()
    
    # Filter berdasarkan kategori (ini akan tetap berfungsi jika parameter kategori dikirim)
    kategori = request.GET.get('kategori')
    if kategori:
        produk_list = produk_list.filter(kategori=kategori)
    
    # Search functionality
    search = request.GET.get('search')
    if search:
        produk_list = produk_list.filter(
            Q(nama__icontains=search) | Q(kategori__icontains=search)
        )
    
    paginator = Paginator(produk_list, 12) # Sesuaikan per halaman
    page_number = request.GET.get('page')
    produk_list = paginator.get_page(page_number)
    
    context = {
        'produk_list': produk_list,
        'kategori_list': kategori_list, # Tetap sediakan jika mungkin digunakan di tempat lain
        'selected_kategori': kategori,
        'search_query': search
    }
    return render(request, 'ecommerce/home.html', context)


def user_login(request):
    """Login view"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # FIX: Auto-create Buyer if doesn't exist
            if not user.is_staff and not user.is_superuser:
                buyer, created = Buyer.objects.get_or_create(user=user)
                if created:
                    messages.info(request, 'Profile buyer telah dibuat otomatis.')
            
            messages.success(request, 'Login berhasil!')
            return redirect('home')
        else:
            messages.error(request, 'Username atau password salah!')
    
    return render(request, 'ecommerce/login.html')

def user_register(request):
    """Register view"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # FIX: Always create buyer profile for new users
            Buyer.objects.create(user=user)
            messages.success(request, 'Registrasi berhasil! Silakan login.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'ecommerce/register.html', {'form': form})

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
    """Detail produk view"""
    produk = get_object_or_404(Produk, id=produk_id)
    return render(request, 'ecommerce/produk_detail.html', {'produk': produk})

@login_required
def add_to_cart(request, produk_id):
    produk = get_object_or_404(Produk, id=produk_id)
    quantity = int(request.POST.get('quantity', 1))

    # Pastikan pembeli memiliki objek Buyer
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
        # Jika item sudah ada di keranjang, tambahkan kuantitasnya
        new_quantity = cart_item.quantity + quantity
        if produk.stock < new_quantity:
            messages.error(request, f'Tidak bisa menambahkan lebih banyak {produk.nama}. Stok tidak cukup untuk kuantitas yang diminta.')
        else:
            cart_item.quantity = new_quantity
            cart_item.save()
            messages.success(request, f'{quantity} {produk.nama} ditambahkan ke keranjang.')
    else:
        messages.success(request, f'{produk.nama} berhasil ditambahkan ke keranjang.')

    return redirect('cart_detail') # Arahkan ke halaman detail keranjang

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
    action = request.POST.get('action') # 'increase', 'decrease', 'remove', 'set_quantity'
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
        # Proses checkout:
        # 1. Validasi stok untuk setiap item di keranjang
        # 2. Hitung total berat dan ongkir
        # 3. Buat objek Pengiriman
        # 4. Buat objek Transaksi
        # 5. Pindahkan item dari CartItem ke TransaksiProduk
        # 6. Kurangi stok produk
        # 7. Hapus item dari keranjang
        # 8. Redirect ke halaman detail transaksi atau riwayat transaksi

        ekspedisi = request.POST.get('ekspedisi', 'jne')
        alamat_pengiriman = request.POST.get('alamat_pengiriman', request.user.alamat) # Gunakan alamat user default
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
            # Buat objek Pengiriman
            pengiriman = Pengiriman.objects.create(
                alamat_penerima=alamat_pengiriman,
                ongkir=ongkir,
                ekspedisi=ekspedisi,
                status='pending',
                catatan=catatan
            )

            # Buat objek Transaksi
            transaksi = Transaksi.objects.create(
                buyer=request.user.buyer, # Pastikan user memiliki buyer profile
                pembeli=request.user.nama,
                status='pending', # Atau 'paid' jika ini adalah transaksi langsung yang sudah dibayar
                total_double=grand_total,
                pengiriman=pengiriman
            )

            # Pindahkan item dari CartItem ke TransaksiProduk
            for item in items_to_process:
                TransaksiProduk.objects.create(
                    transaksi=transaksi,
                    produk=item.produk,
                    quantity=item.quantity,
                    harga_satuan=item.produk.harga
                )
                # Kurangi stok produk
                item.produk.stock -= item.quantity
                item.produk.save()

            # Hapus item dari keranjang setelah berhasil checkout
            cart_items.all().delete()

            messages.success(request, 'Checkout berhasil! Transaksi Anda sedang diproses.')
            return redirect('detail_transaksi', transaksi_id=transaksi.id)

        except Exception as e:
            messages.error(request, f'Terjadi kesalahan saat checkout: {e}.')
            return redirect('cart_detail')

    else:
        # Untuk metode GET, tampilkan halaman checkout
        # Hitung ongkir awal berdasarkan alamat default user dan JNE
        initial_ongkir = calculate_ongkir(cart.get_total_berat(), 'jne')
        
        # Inisialisasi form checkout
        form = CheckoutForm(initial={
            'alamat_pengiriman': request.user.alamat,
            'ekspedisi': 'jne' # Default ekspedisi
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
def buat_transaksi(request):
    """Membuat transaksi baru"""
    if request.method == 'POST':
        produk_id = request.POST.get('produk_id')
        quantity = int(request.POST.get('quantity', 1))
        ekspedisi = request.POST.get('ekspedisi', 'jne')
        
        produk = get_object_or_404(Produk, id=produk_id)
        
        # FIX: Auto-create Buyer if doesn't exist
        buyer, created = Buyer.objects.get_or_create(user=request.user)
        if created:
            messages.info(request, 'Profile buyer telah dibuat otomatis.')
        
        if produk.stock >= quantity:
            total_berat = produk.berat * quantity
            ongkir = calculate_ongkir(total_berat, ekspedisi) #error

            pengiriman = Pengiriman.objects.create(
                alamat_penerima=request.user.alamat,
                ongkir=ongkir,
                ekspedisi=ekspedisi,
                status='pending'
            )
            # Buat transaksi
            transaksi = Transaksi.objects.create(
                buyer=buyer,
                pembeli=request.user.nama,
                status='pending',
                total_double=(produk.harga * quantity) + ongkir,
                pengiriman=pengiriman
            )
            
            # Buat relasi transaksi-produk
            TransaksiProduk.objects.create(
                transaksi=transaksi,
                produk=produk,
                quantity=quantity,
                harga_satuan=produk.harga
            )
            
            # Update stock
            produk.stock -= quantity
            produk.save()
            
            messages.success(request, 'Transaksi berhasil dibuat!')
            return redirect('riwayat_transaksi')
        else:
            messages.error(request, 'Stock tidak mencukupi!')
    
    return redirect('home')

@login_required
def riwayat_transaksi(request):
    """Melihat riwayat transaksi"""
    # FIX: Auto-create Buyer if doesn't exist
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
    # FIX: Auto-create Buyer if doesn't exist
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
    # FIX: Auto-create Buyer if doesn't exist
    buyer, created = Buyer.objects.get_or_create(user=request.user)
    if created:
        messages.info(request, 'Profile buyer telah dibuat otomatis.')
    
    transaksi = get_object_or_404(Transaksi, id=transaksi_id, buyer=buyer)
    
    if transaksi.status == 'pending':
        transaksi.status = 'paid'
        transaksi.save()
        messages.success(request, 'Pembayaran berhasil dikonfirmasi!')
    else:
        messages.error(request, 'Transaksi tidak dapat dikonfirmasi!')
    
    return redirect('detail_transaksi', transaksi_id=transaksi.id)

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
    
    pengiriman_list = Pengiriman.objects.all().select_related('transaksi', 'transaksi_buyer_user')

    status_filter = request.GET.get('status')
    if status_filter:
        pengiriman_list = pengiriman_list.filter(status=status_filter)

    ekspedisi_filter = request.GET.get('ekspedisi')
    if ekspedisi_filter:
        pengiriman_list = pengiriman_list.filter(ekspedisi=ekspedisi_filter)

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_gate')
    if start_gate and end_gate:
        pengiriman_list = pengiriman_list.filter(
            created_at__date__range=[start_date, end_gate]
        )

    stats = {
    'pending': pengiriman_list.filter(status='pending').count(),
    'processing': pengiriman_list.filter(status='processing').count(),
    'shipped': pengiriman_list.filter(status='shipped').count(),
    'in_transit': pengiriman_list.filter(status='in_transit').count(),
    'delivered': pengiriman_list.filter(status='delivered').count(),
    'failed': pengiriman_list.filter(status='failed').count(),
    }
#LANJUT BOSS
    for pengiriman in pengiriman_list:
        if pengiriman.tanggal_kirim and pengiriman.tanggal_terkirim:
            delta = pengiriman.tanggal_terkirim - pengiriman.tanggal_kirim

    return render(request, 'ecommerce/admin/data_pengiriman.html', {'pengiriman_list': pengiriman_list})

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

    # Calculate statistics
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
        'avg_transactions': int(avg_transactions)
    }

    return render(request, 'ecommerce/admin/kelola_pelanggan.html', context)

def melakukan_transaksi_langsung(request):
    """Melakukan transaksi langsung (admin)"""
    if not request.user.is_staff:
        messages.error(request, 'Akses ditolak!')
        return redirect('home')
    
    if request.method == 'POST':
        # Logic untuk transaksi langsung
        pass
    
    return render(request, 'ecommerce/admin/transaksi_langsung.html')

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
    
    transaksi_list = Transaksi.objects.all().order_by('-tansaksi_date')
    return render(request, 'ecommerce/admin/laporan_transaksi.html', {'transaksi_list': transaksi_list})

def calculate_ongkir(berat_kg, ekspedisi):
    base_rates = {
        'jne' : 9000,
        'pos indonesia' : 8000,
        'tiki' : 9500,
        'j&t' : 8500,
        'sicepat' : 7900,
        'anteraja' : 7500,
        'ninja' : 7000,
        'gosend' : 17000,
        'GrabExpress' : 12000,
    }

    base_rate = base_rates.get(ekspedisi, 9000)

    if berat_kg <=1:
        return base_rate
    else:
        additional_cost = (berat_kg - 1) * (base_rate * Decimal('0.5')) #error
        return base_rate + additional_cost

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
    from datetime import datetime, timedelta
    
    history = []
    base_date = pengiriman.created_at
    
    status_flow = [
        ('pending', 'Pesanan diterima'),
        ('processing', 'Pesanan sedang diproses'),
        ('shipped', 'Paket telah dikirim'),
        ('in_transit', 'Paket dalam perjalanan'),
        ('out_for_delivery', 'Paket keluar untuk pengiriman'),
        ('delivered', 'Paket telah terkirim')
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

# Admin views untuk pengiriman
def kelola_pengiriman(request):
    if not request.user.is_staff:
        messages.error(request, 'Akses ditolak!')
        return redirect('home')
    
    pengiriman_list = Pengiriman.objects.all().order_by('-created_at')
    
    # Calculate status counts
    status_counts = {
        'pending': pengiriman_list.filter(status='pending').count(),
        'processing': pengiriman_list.filter(status='processing').count(),
        'shipped': pengiriman_list.filter(status='shipped').count(),
        'delivered': pengiriman_list.filter(status='delivered').count(),
        'in_transit': pengiriman_list.filter(status='in_transit').count(),
        'failed': pengiriman_list.filter(status='failed').count(),
    }
    
    status_filter = request.GET.get('status')
    if status_filter:
        pengiriman_list = pengiriman_list.filter(status=status_filter)
    
    ekspedisi_filter = request.GET.get('ekspedisi')
    if ekspedisi_filter:
        pengiriman_list = pengiriman_list.filter(ekspedisi=ekspedisi_filter)
    
    paginator = Paginator(pengiriman_list, 20)
    page_number = request.GET.get('page')
    pengiriman_list = paginator.get_page(page_number)
    
    return render(request, 'ecommerce/admin/kelola_pengiriman.html', {
        'pengiriman_list': pengiriman_list,
        'status_choices': Pengiriman.STATUS_CHOICES,
        'ekspedisi_choices': Pengiriman.EKSPEDISI_CHOICES,
        'selected_status': status_filter,
        'selected_ekspedisi': ekspedisi_filter,
        'status_counts': status_counts,  # Add this line
    })

def update_status_pengiriman(request, pengiriman_id):
    if not request.user.is_staff:
        messages.error(request, 'Akses ditolak!')
        return redirect('home')
    
    pengiriman = get_object_or_404(Pengiriman, id=pengiriman_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        no_resi = request.POST.get('no_resi')
        catatan = request.POST.get('catatan', '')
        
        pengiriman.status = new_status
        if no_resi:
            pengiriman.no_resi = no_resi
        pengiriman.catatan = catatan
        
        if new_status == 'shipped' and not pengiriman.tanggal_kirim:
            pengiriman.tanggal_kirim = timezone.now()
            if not pengiriman.no_resi:
                pengiriman.no_resi = generate_resi_number()
        
        if new_status == 'delivered' and not pengiriman.tanggal_terkirim:
            pengiriman.tanggal_terkirim = timezone.now()
        
        pengiriman.save()
        
        try:
            transaksi = pengiriman.transaksi
            if new_status == 'delivered':
                transaksi.status = 'completed'
                transaksi.save()
        except:
            pass
        
        messages.success(request, 'Status pengiriman berhasil diupdate!')
        return redirect('kelola_pengiriman')
    
    return render(request, 'ecommerce/admin/update_pengiriman.html', {
        'pengiriman': pengiriman,
        'status_choices': Pengiriman.STATUS_CHOICES
    })

# Update views lama agar kompatibel dengan pengiriman
@login_required
def konfirmasi_pembayaran(request, transaksi_id):
    buyer, created = Buyer.objects.get_or_create(user=request.user)
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
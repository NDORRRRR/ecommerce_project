from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from .models import *
from .forms import *
import random
import string

def home(request):
    """Homepage dengan daftar produk"""
    produk_list = Produk.objects.all()
    kategori_list = Produk.objects.values_list('kategori', flat=True).distinct()
    
    # Filter berdasarkan kategori
    kategori = request.GET.get('kategori')
    if kategori:
        produk_list = produk_list.filter(kategori=kategori)
    
    # Search functionality
    search = request.GET.get('search')
    if search:
        produk_list = produk_list.filter(
            Q(nama__icontains=search) | Q(kategori__icontains=search)
        )
    
    paginator = Paginator(produk_list, 12)
    page_number = request.GET.get('page')
    produk_list = paginator.get_page(page_number)
    
    context = {
        'produk_list': produk_list,
        'kategori_list': kategori_list,
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
            ongkir = calculate_ongkir(total_berat, ekspedisi)

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
    """Melihat data pengiriman"""
    if not request.user.is_staff:
        messages.error(request, 'Akses ditolak!')
        return redirect('home')
    
    pengiriman_list = Pengiriman.objects.all()
    return render(request, 'ecommerce/admin/data_pengiriman.html', {'pengiriman_list': pengiriman_list})

def mengelola_data_pelanggan(request):
    """Mengelola data pelanggan"""
    if not request.user.is_staff:
        messages.error(request, 'Akses ditolak!')
        return redirect('home')
    
    buyer_list = Buyer.objects.all()
    return render(request, 'ecommerce/admin/kelola_pelanggan.html', {'buyer_list': buyer_list})

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
        additional_cost = (berat_kg - 1) * (base_rate * 0.5)
        return base_rate + additional_cost

@login_required
def detail_pengiriman(request, transaksi_id):
    buyer, created = Buyer.objects_or_404(Transaksi, id=transaksi_id, buyer=buyer)

    if not transaksi.pengiriman:
        messages.error(request, 'Data pengiriman tidak ditemukan!.')
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
        'selected_ekspedisi': ekspedisi_filter
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
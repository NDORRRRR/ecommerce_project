from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import *
from .forms import *

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
            # Create buyer profile
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
        
        produk = get_object_or_404(Produk, id=produk_id)
        buyer = get_object_or_404(Buyer, user=request.user)
        
        if produk.stock >= quantity:
            # Buat transaksi
            transaksi = Transaksi.objects.create(
                buyer=buyer,
                pembeli=request.user.nama,
                status='pending',
                total_double=produk.harga * quantity
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
    try:
        buyer = Buyer.objects.get(user=request.user)
        transaksi_list = Transaksi.objects.filter(buyer=buyer).order_by('-tanggal_date')
        
        paginator = Paginator(transaksi_list, 10)
        page_number = request.GET.get('page')
        transaksi_list = paginator.get_page(page_number)
        
        return render(request, 'ecommerce/riwayat_transaksi.html', {
            'transaksi_list': transaksi_list
        })
    except Buyer.DoesNotExist:
        messages.error(request, 'Profile buyer tidak ditemukan!')
        return redirect('home')

@login_required
def detail_transaksi(request, transaksi_id):
    """Detail transaksi"""
    try:
        buyer = Buyer.objects.get(user=request.user)
        transaksi = get_object_or_404(Transaksi, id=transaksi_id, buyer=buyer)
        transaksi_produk = TransaksiProduk.objects.filter(transaksi=transaksi)
        
        return render(request, 'ecommerce/detail_transaksi.html', {
            'transaksi': transaksi,
            'transaksi_produk': transaksi_produk
        })
    except Buyer.DoesNotExist:
        messages.error(request, 'Profile buyer tidak ditemukan!')
        return redirect('home')

@login_required
def konfirmasi_pembayaran(request, transaksi_id):
    """Konfirmasi pembayaran"""
    try:
        buyer = Buyer.objects.get(user=request.user)
        transaksi = get_object_or_404(Transaksi, id=transaksi_id, buyer=buyer)
        
        if transaksi.status == 'pending':
            transaksi.status = 'paid'
            transaksi.save()
            messages.success(request, 'Pembayaran berhasil dikonfirmasi!')
        else:
            messages.error(request, 'Transaksi tidak dapat dikonfirmasi!')
        
        return redirect('detail_transaksi', transaksi_id=transaksi.id)
    except Buyer.DoesNotExist:
        messages.error(request, 'Profile buyer tidak ditemukan!')
        return redirect('home')

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
    
    transaksi_list = Transaksi.objects.all().order_by('-tanggal_date')
    return render(request, 'ecommerce/admin/laporan_transaksi.html', {'transaksi_list': transaksi_list})
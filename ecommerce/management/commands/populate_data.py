from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ecommerce.models import *
from decimal import Decimal
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate database with sample data'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create admin user
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                password='admin123',
                email='admin@example.com',
                nama='Administrator',
                alamat='Jl. Admin No. 1',
                noHP='081234567890'
            )
            Admin.objects.create(user=admin_user, nama='Administrator')
            self.stdout.write(self.style.SUCCESS('Created admin user'))

        # Create sample buyers
        buyer_data = [
            {
                'username': 'buyer1', 'password': 'buyer123', 'email': 'buyer1@example.com',
                'nama': 'Andi Pratama', 'alamat': 'Jl. Merdeka No. 10, Surabaya', 'noHP': '081234567891'
            },
            {
                'username': 'buyer2', 'password': 'buyer123', 'email': 'buyer2@example.com',
                'nama': 'Sari Indah', 'alamat': 'Jl. Pahlawan No. 15, Surabaya', 'noHP': '081234567892'
            },
        ]

        for data in buyer_data:
            if not User.objects.filter(username=data['username']).exists():
                user = User.objects.create_user(
                    username=data['username'],
                    password=data['password'],
                    email=data['email'],
                    nama=data['nama'],
                    alamat=data['alamat'],
                    noHP=data['noHP']
                )
                Buyer.objects.create(user=user)
                self.stdout.write(f'Created buyer: {data["nama"]}')

        # Create sample products
        products_data = [
            # Elektronik
            {'nama': 'Laptop Gaming ASUS ROG Zephyrus G14', 'kategori': 'Elektronik', 'harga': 25999000, 'stock': 15, 'berat': 1.6, 'deskripsi': 'Laptop gaming ultra-portabel dengan AMD Ryzen 9 dan NVIDIA GeForce RTX 4060. Layar Nebula Display 165Hz.'},
            {'nama': 'Monitor Dell UltraSharp U2723QE 4K', 'kategori': 'Elektronik', 'harga': 9850000, 'stock': 25, 'berat': 6.3, 'deskripsi': 'Monitor 27 inci 4K UHD dengan teknologi IPS Black, 98% DCI-P3, dan konektivitas USB-C.'},
            {'nama': 'Smart TV Samsung Neo QLED 55 inch', 'kategori': 'Elektronik', 'harga': 18500000, 'stock': 10, 'berat': 21.0, 'deskripsi': 'Televisi 4K dengan teknologi Quantum Mini LED untuk kontras yang luar biasa dan warna yang akurat.'},

            # Aksesoris
            {'nama': 'Mouse Wireless Logitech MX Master 3S', 'kategori': 'Aksesoris', 'harga': 1350000, 'stock': 50, 'berat': 0.2, 'deskripsi': 'Mouse ergonomis dengan sensor 8K DPI dan klik yang senyap. Sempurna untuk profesional dan kreator.'},
            {'nama': 'Keyboard Mechanical Keychron Q1 Pro', 'kategori': 'Aksesoris', 'harga': 2800000, 'stock': 30, 'berat': 1.8, 'deskripsi': 'Keyboard mekanikal full-metal gasket mount yang dapat dikustomisasi sepenuhnya, konektivitas nirkabel dan kabel.'},
            {'nama': 'Powerbank Anker 737 PowerCore 24K', 'kategori': 'Aksesoris', 'harga': 1999000, 'stock': 40, 'berat': 0.6, 'deskripsi': 'Powerbank 24,000mAh dengan output maksimal 140W. Dapat mengisi daya laptop, tablet, dan smartphone dengan cepat.'},
            {'nama': 'SanDisk Extreme PRO Portable SSD 2TB', 'kategori': 'Aksesoris', 'harga': 3500000, 'stock': 35, 'berat': 0.1, 'deskripsi': 'SSD eksternal super cepat dengan kecepatan baca/tulis hingga 2000MB/s. Tahan banting dan air.'},

            # Smartphone
            {'nama': 'Samsung Galaxy S25 Ultra 512GB', 'kategori': 'Smartphone', 'harga': 22999000, 'stock': 20, 'berat': 0.23, 'deskripsi': 'Flagship terbaru dari Samsung dengan kamera 200MP, S Pen terintegrasi, dan performa AI yang ditingkatkan.'},
            {'nama': 'Apple iPhone 16 Pro 256GB', 'kategori': 'Smartphone', 'harga': 24500000, 'stock': 18, 'berat': 0.19, 'deskripsi': 'iPhone terbaru dengan chip A18 Pro, Dynamic Island, dan sistem kamera Pro yang lebih canggih.'},
            {'nama': 'Google Pixel 9 Pro 256GB', 'kategori': 'Smartphone', 'harga': 19500000, 'stock': 22, 'berat': 0.21, 'deskripsi': 'Smartphone dengan pengalaman Android murni dan fitur AI kamera terbaik di kelasnya dari Google.'},
            
            # Kamera
            {'nama': 'Sony Alpha 7 IV (Body Only)', 'kategori': 'Kamera', 'harga': 35000000, 'stock': 12, 'berat': 0.65, 'deskripsi': 'Kamera mirrorless full-frame hybrid dengan sensor 33MP, perekaman video 4K 60p, dan autofokus real-time terbaik.'},
            {'nama': 'Fujifilm X-T5 (Body Only)', 'kategori': 'Kamera', 'harga': 28000000, 'stock': 16, 'berat': 0.55, 'deskripsi': 'Kamera mirrorless APS-C dengan sensor 40MP, simulasi film klasik Fujifilm, dan desain retro yang ikonik.'},

            # Audio
            {'nama': 'Sony WH-1000XM5 Wireless Headphones', 'kategori': 'Audio', 'harga': 4999000, 'stock': 45, 'berat': 0.25, 'deskripsi': 'Headphone noise-cancelling terbaik di industri dengan kualitas suara Hi-Res dan desain yang ringan.'},
            {'nama': 'Apple AirPods Pro (2nd generation)', 'kategori': 'Audio', 'harga': 3499000, 'stock': 80, 'berat': 0.05, 'deskripsi': 'True wireless earbuds dengan Active Noise Cancellation yang superior, Adaptive Transparency, dan Personalized Spatial Audio.'},

            # Baju
            {'nama': 'Kaos Polos Cotton Combed 24s Oversized', 'kategori': 'Baju', 'harga': 125000, 'stock': 150, 'berat': 0.25, 'deskripsi': 'Kaos polos bahan premium dengan potongan oversized yang modern dan nyaman.'},
            {'nama': 'Kemeja Flanel Uniqlo Lengan Panjang', 'kategori': 'Baju', 'harga': 499000, 'stock': 70, 'berat': 0.4, 'deskripsi': 'Kemeja flanel lembut dengan berbagai motif kotak-kotak yang stylish untuk gaya kasual.'},
            {'nama': 'Celana Chino Erigo Slim Fit', 'kategori': 'Baju', 'harga': 299000, 'stock': 120, 'berat': 0.5, 'deskripsi': 'Celana chino dengan potongan slim fit yang modern, terbuat dari bahan katun stretch yang nyaman.'},

            # Buku
            {'nama': 'Buku "Sapiens: A Brief History of Humankind"', 'kategori': 'Buku', 'harga': 148000, 'stock': 90, 'berat': 0.6, 'deskripsi': 'Buku non-fiksi karya Yuval Noah Harari yang membahas sejarah umat manusia dari Zaman Batu hingga sekarang.'},
            {'nama': 'Buku "Filosofi Teras" - Henry Manampiring', 'kategori': 'Buku', 'harga': 98000, 'stock': 110, 'berat': 0.4, 'deskripsi': 'Pengantar filsafat Stoisisme yang relevan untuk mengatasi kekhawatiran dan emosi negatif di era modern.'},
            {'nama': 'Novel "Laskar Pelangi" - Andrea Hirata', 'kategori': 'Buku', 'harga': 88000, 'stock': 130, 'berat': 0.5, 'deskripsi': 'Novel inspiratif tentang perjuangan 10 anak di Belitung untuk mendapatkan pendidikan yang layak.'},
        ]

        for data in products_data:
            if not Produk.objects.filter(nama=data['nama']).exists():
                kategori_obj = kategori_objects.get(data['kategori'])
                if kategori_obj:
                    Produk.objects.create(
                        nama=data['nama'],
                        kategori=kategori_obj,
                        harga=Decimal(data['harga']),
                        stock=data['stock'],
                        berat=Decimal(data['berat']),
                        deskripsi=data['deskripsi']
                    )
                    self.stdout.write(f'Produk "{data["nama"]}" berhasil dibuat.')

        self.stdout.write(self.style.SUCCESS('Successfully populated database!'))
        self.stdout.write(self.style.WARNING('Login credentials:'))
        self.stdout.write('Admin: username=admin, password=admin123')
        self.stdout.write('Buyer: username=buyer1, password=buyer123')
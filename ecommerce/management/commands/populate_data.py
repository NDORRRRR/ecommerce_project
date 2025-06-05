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
            {'nama': 'Laptop Gaming ASUS', 'kategori': 'Elektronik', 'harga': 15000000, 'stock': 15},
            {'nama': 'Mouse Wireless Logitech', 'kategori': 'Elektronik', 'harga': 250000, 'stock': 20},
            {'nama': 'Keyboard Mechanical', 'kategori': 'Elektronik', 'harga': 500000, 'stock': 15},
            {'nama': 'Tas Laptop', 'kategori': 'Aksesoris', 'harga': 150000, 'stock': 25},
            {'nama': 'Powerbank 20000mAh', 'kategori': 'Aksesoris', 'harga': 200000, 'stock': 30},
            {'nama': 'Iphone XR', 'kategori': 'Smartphone', 'harga': 3600000, 'stock': 10}
        ]

        for product_data in products_data:
            if not Produk.objects.filter(nama=product_data['nama']).exists():
                Produk.objects.create(**product_data)
                self.stdout.write(f'Created product: {product_data["nama"]}')

        self.stdout.write(self.style.SUCCESS('Successfully populated database!'))
        self.stdout.write(self.style.WARNING('Login credentials:'))
        self.stdout.write('Admin: username=admin, password=admin123')
        self.stdout.write('Buyer: username=buyer1, password=buyer123')
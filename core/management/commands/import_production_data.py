import json
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Product, SalesTransaction, SalesItem, LoginHistory, UserProfile
from django.db import transaction


class Command(BaseCommand):
    help = 'Import exported local data to production database'

    def handle(self, *args, **options):
        export_file = 'data_export/local_data_export.json'
        
        if not os.path.exists(export_file):
            self.stdout.write(self.style.ERROR(f'❌ Export file not found: {export_file}'))
            self.stdout.write('❗ Run "python manage.py export_local_data" first')
            return
        
        # Load the exported data
        with open(export_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        imported_counts = {}
        
        with transaction.atomic():
            # Import Users
            for user_data in data.get('users', []):
                user, created = User.objects.get_or_create(
                    username=user_data['username'],
                    defaults={
                        'email': user_data['email'],
                        'first_name': user_data['first_name'],
                        'last_name': user_data['last_name'],
                        'is_staff': user_data['is_staff'],
                        'is_active': user_data['is_active'],
                        'date_joined': datetime.fromisoformat(user_data['date_joined']),
                    }
                )
                if created:
                    # Set a default password for imported users
                    user.set_password('imported123')
                    user.save()
            
            imported_counts['users'] = len(data.get('users', []))
            
            # Import Products
            for product_data in data.get('products', []):
                product, created = Product.objects.get_or_create(
                    name=product_data['name'],
                    defaults={
                        'price': product_data['price'],
                        'ingredients': product_data['ingredients'],
                        'stock': product_data['stock'],
                        'is_active': product_data['is_active'],
                        'is_archived': product_data['is_archived'],
                        'expiration_date': datetime.fromisoformat(product_data['expiration_date']) if product_data['expiration_date'] else None,
                        'image': product_data['image'],
                        'created_at': datetime.fromisoformat(product_data['created_at']),
                        'updated_at': datetime.fromisoformat(product_data['updated_at']),
                    }
                )
            
            imported_counts['products'] = len(data.get('products', []))
            
            # Import SalesTransactions
            for sale_data in data.get('sales_transactions', []):
                try:
                    cashier = User.objects.get(username=sale_data['cashier_username'])
                    sale, created = SalesTransaction.objects.get_or_create(
                        cashier=cashier,
                        total_amount=sale_data['total_amount'],
                        discount=sale_data['discount'],
                        payment_method=sale_data['payment_method'],
                        created_at=datetime.fromisoformat(sale_data['created_at']),
                    )
                except User.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'⚠️  User {sale_data["cashier_username"]} not found, skipping sales transaction'))
            
            imported_counts['sales_transactions'] = len(data.get('sales_transactions', []))
            
            # Import SalesItems
            for item_data in data.get('sales_items', []):
                try:
                    sale = SalesTransaction.objects.get(id=item_data['sale_id'])
                    product = Product.objects.get(name=item_data['product_name'])
                    SalesItem.objects.get_or_create(
                        sale=sale,
                        product=product,
                        qty=item_data['qty'],
                        unit_price=item_data['unit_price'],
                        line_total=item_data['line_total'],
                    )
                except (SalesTransaction.DoesNotExist, Product.DoesNotExist):
                    self.stdout.write(self.style.WARNING(f'⚠️  Sale or Product not found, skipping sales item'))
            
            imported_counts['sales_items'] = len(data.get('sales_items', []))
            
            # Import LoginHistory
            for history_data in data.get('login_history', []):
                try:
                    user = User.objects.get(username=history_data['username'])
                    LoginHistory.objects.get_or_create(
                        user=user,
                        login_time=datetime.fromisoformat(history_data['login_time']),
                        defaults={
                            'ip_address': history_data['ip_address'],
                            'user_agent': history_data['user_agent'],
                            'logout_time': datetime.fromisoformat(history_data['logout_time']) if history_data['logout_time'] else None,
                        }
                    )
                except User.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'⚠️  User {history_data["username"]} not found, skipping login history'))
            
            imported_counts['login_history'] = len(data.get('login_history', []))
            
            # Import UserProfiles
            for profile_data in data.get('user_profiles', []):
                try:
                    user = User.objects.get(username=profile_data['username'])
                    UserProfile.objects.get_or_create(
                        user=user,
                        defaults={
                            'profile_picture': profile_data['profile_picture'],
                            'created_at': datetime.fromisoformat(profile_data['created_at']),
                            'updated_at': datetime.fromisoformat(profile_data['updated_at']),
                        }
                    )
                except User.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'⚠️  User {profile_data["username"]} not found, skipping user profile'))
            
            imported_counts['user_profiles'] = len(data.get('user_profiles', []))
        
        # Print summary
        self.stdout.write(self.style.SUCCESS('✅ Data imported successfully!'))
        self.stdout.write('')
        self.stdout.write('📊 Import Summary:')
        for model, count in imported_counts.items():
            self.stdout.write(f'  {model}: {count}')
        
        self.stdout.write('')
        self.stdout.write('🔑 Default passwords for imported users: "imported123"')
        self.stdout.write('⚠️  Please change passwords after first login')

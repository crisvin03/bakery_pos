import json
import os
from django.core.management.base import BaseCommand
from django.core.serializers.json import DjangoJSONEncoder
from core.models import Product, SalesTransaction, SalesItem, LoginHistory, UserProfile
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Export all local data to JSON file for production import'

    def handle(self, *args, **options):
        # Create export directory if it doesn't exist
        export_dir = 'data_export'
        os.makedirs(export_dir, exist_ok=True)
        
        export_data = {}
        
        # Export Users (excluding superusers to avoid conflicts)
        users = User.objects.filter(is_superuser=False)
        export_data['users'] = [
            {
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_staff': user.is_staff,
                'is_active': user.is_active,
                'date_joined': user.date_joined.isoformat(),
            }
            for user in users
        ]
        
        # Export Products
        products = Product.objects.all()
        export_data['products'] = [
            {
                'name': product.name,
                'price': str(product.price),
                'ingredients': product.ingredients,
                'stock': product.stock,
                'is_active': product.is_active,
                'is_archived': product.is_archived,
                'expiration_date': product.expiration_date.isoformat() if product.expiration_date else None,
                'image': product.image,
                'created_at': product.created_at.isoformat(),
                'updated_at': product.updated_at.isoformat(),
            }
            for product in products
        ]
        
        # Export SalesTransactions
        sales = SalesTransaction.objects.all()
        export_data['sales_transactions'] = [
            {
                'cashier_username': sale.cashier.username,
                'total_amount': str(sale.total_amount),
                'discount': str(sale.discount),
                'payment_method': sale.payment_method,
                'created_at': sale.created_at.isoformat(),
            }
            for sale in sales
        ]
        
        # Export SalesItems
        sales_items = SalesItem.objects.all()
        export_data['sales_items'] = [
            {
                'sale_id': item.sale.id,
                'product_name': item.product.name,
                'qty': item.qty,
                'unit_price': str(item.unit_price),
                'line_total': str(item.line_total),
            }
            for item in sales_items
        ]
        
        # Export LoginHistory
        login_history = LoginHistory.objects.all()
        export_data['login_history'] = [
            {
                'username': history.user.username,
                'login_time': history.login_time.isoformat(),
                'ip_address': history.ip_address,
                'user_agent': history.user_agent,
                'logout_time': history.logout_time.isoformat() if history.logout_time else None,
            }
            for history in login_history
        ]
        
        # Export UserProfiles
        user_profiles = UserProfile.objects.all()
        export_data['user_profiles'] = [
            {
                'username': profile.user.username,
                'profile_picture': profile.profile_picture.name if profile.profile_picture else None,
                'created_at': profile.created_at.isoformat(),
                'updated_at': profile.updated_at.isoformat(),
            }
            for profile in user_profiles
        ]
        
        # Save to JSON file
        export_file = os.path.join(export_dir, 'local_data_export.json')
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, cls=DjangoJSONEncoder)
        
        # Print summary
        self.stdout.write(self.style.SUCCESS(f'✅ Data exported to {export_file}'))
        self.stdout.write('')
        self.stdout.write('📊 Export Summary:')
        self.stdout.write(f'  Users: {len(export_data["users"])}')
        self.stdout.write(f'  Products: {len(export_data["products"])}')
        self.stdout.write(f'  Sales Transactions: {len(export_data["sales_transactions"])}')
        self.stdout.write(f'  Sales Items: {len(export_data["sales_items"])}')
        self.stdout.write(f'  Login History: {len(export_data["login_history"])}')
        self.stdout.write(f'  User Profiles: {len(export_data["user_profiles"])}')
        self.stdout.write('')
        self.stdout.write('📁 File location: ' + os.path.abspath(export_file))

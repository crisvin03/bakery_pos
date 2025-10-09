from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Product, SalesTransaction, SalesItem
from django.utils import timezone
import random, datetime

class Command(BaseCommand):
    help = "Seed demo products and random sales data"

    def handle(self, *args, **kwargs):
        # Admin (staff) + Cashier user
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin','admin@example.com','admin123')
            self.stdout.write(self.style.SUCCESS("Created superuser: admin / admin123"))
        if not User.objects.filter(username='cashier').exists():
            u = User.objects.create_user('cashier','cashier@example.com','cashier123')
            u.is_staff = False
            u.save()
            self.stdout.write(self.style.SUCCESS("Created cashier: cashier / cashier123"))

        # Products
        products = [
            ('Pandesal', 3.0),
            ('Ensaymada', 25.0),
            ('Spanish Bread', 15.0),
            ('Cheese Bread', 12.0),
            ('Ube Loaf', 70.0),
        ]
        objs = []
        for name, price in products:
            p, _ = Product.objects.get_or_create(name=name, defaults={'price':price, 'ingredients':'', 'is_active': True})
            p.price = price; p.save()
            objs.append(p)
        self.stdout.write(self.style.SUCCESS(f"Ensured {len(objs)} products."))

        # Random sales for last 60 days
        cashier = User.objects.get(username='cashier')
        now = timezone.now()
        for d in range(60, -1, -1):
            day = now - datetime.timedelta(days=d)
            # 5-25 transactions per day
            for _ in range(random.randint(5,25)):
                items_count = random.randint(1,3)
                discount = round(random.choice([0, 2, 5]), 2)
                sale = SalesTransaction.objects.create(
                    cashier=cashier,
                    total_amount=0,
                    discount=discount,
                    payment_method=random.choice(['CASH','CARD','E_WALLET']),
                    created_at=day
                )
                total = 0
                for __ in range(items_count):
                    p = random.choice(objs)
                    qty = random.randint(1,6)
                    line = round(p.price*qty, 2)
                    SalesItem.objects.create(sale=sale, product=p, qty=qty, unit_price=p.price, line_total=line)
                    total += line
                sale.total_amount = max(0, round(total - discount, 2))
                sale.save()
        self.stdout.write(self.style.SUCCESS("Seeded random sales for last 60 days."))

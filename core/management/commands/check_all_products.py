from django.core.management.base import BaseCommand
from core.models import Product


class Command(BaseCommand):
    help = 'Check all products and their current images'

    def handle(self, *args, **options):
        products = Product.objects.all()
        
        if not products.exists():
            self.stdout.write(self.style.WARNING('No products found in database'))
            return
        
        self.stdout.write(f'Found {products.count()} products:')
        self.stdout.write('')
        
        for product in products:
            self.stdout.write(f'• {product.name}')
            if product.image:
                self.stdout.write(f'  Image: {product.image}')
            else:
                self.stdout.write(f'  Image: [EMPTY]')
            self.stdout.write('')

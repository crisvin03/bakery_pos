from django.core.management.base import BaseCommand
from core.models import Product


class Command(BaseCommand):
    help = 'Check all product image paths in the database'

    def handle(self, *args, **options):
        products = Product.objects.all()
        
        if not products.exists():
            self.stdout.write(self.style.WARNING('No products found in database'))
            return
        
        self.stdout.write(f'Found {products.count()} products:')
        self.stdout.write('')
        
        for product in products:
            self.stdout.write(f'Product: {product.name}')
            self.stdout.write(f'Image path: {product.image}')
            self.stdout.write('---')
        
        # Check for products with specific image patterns
        logo_products = products.filter(image__icontains='logo')
        bg_products = products.filter(image__icontains='background')
        
        self.stdout.write('')
        self.stdout.write(f'Products with "logo" in image: {logo_products.count()}')
        self.stdout.write(f'Products with "background" in image: {bg_products.count()}')

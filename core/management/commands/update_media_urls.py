import os
from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import Product


class Command(BaseCommand):
    help = 'Update local media URLs to Cloudinary URLs'

    def handle(self, *args, **options):
        # Check environment variables directly
        cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME')
        if not cloud_name:
            self.stdout.write(self.style.ERROR('Cloudinary is not configured'))
            return
        
        # Update products with local media paths
        products = Product.objects.filter(image__startswith='media/')
        
        for product in products:
            old_path = product.image.name
            filename = old_path.split('/')[-1]  # Get just the filename
            
            # Create Cloudinary URL
            cloudinary_url = f'https://res.cloudinary.com/{cloud_name}/image/upload/{filename}'
            
            # Update the product
            product.image = cloudinary_url
            product.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'Updated {product.name}: {old_path} -> {cloudinary_url}')
            )
        
        if products.count() == 0:
            self.stdout.write(self.style.WARNING('No products with local media paths found'))
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Updated {products.count()} products to use Cloudinary URLs')
            )

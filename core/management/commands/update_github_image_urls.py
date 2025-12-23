import os
from django.core.management.base import BaseCommand
from core.models import Product


class Command(BaseCommand):
    help = 'Update production database with GitHub Pages image URLs'

    def handle(self, *args, **options):
        # GitHub Pages base URL (replace with your actual GitHub Pages URL)
        github_pages_url = "https://crisvin03.github.io/bakery_pos/static/images/"
        
        # Map products to their image files
        product_images = {
            'Pandesal': f'{github_pages_url}pandesal.jpg',
            'Ensaymada': f'{github_pages_url}ensaymada.jpg',
            'Spanish Bread': f'{github_pages_url}spanish_bread.jpg',
            'Cheese Bread': f'{github_pages_url}cheese_bread.jpg',
            'Ube Loaf': f'{github_pages_url}ube_loaf.jpg',
        }
        
        updated_count = 0
        for product_name, image_url in product_images.items():
            try:
                product = Product.objects.get(name=product_name)
                product.image = image_url
                product.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated {product.name}: {image_url}')
                )
                updated_count += 1
            except Product.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Product {product_name} not found')
                )
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {updated_count} products with GitHub Pages images')
        )
        
        self.stdout.write('')
        self.stdout.write('📋 Template URLs to update manually:')
        self.stdout.write(f'Logo: {github_pages_url}logo.png')
        self.stdout.write(f'Background: {github_pages_url}background.jpg')

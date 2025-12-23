import os
from django.core.management.base import BaseCommand
from core.models import Product


class Command(BaseCommand):
    help = 'Update all products with GitHub Pages image URLs'

    def handle(self, *args, **options):
        # GitHub Pages base URL
        github_pages_url = "https://crisvin03.github.io/bakery_pos/static/images/"
        
        # Map all products to their image files
        product_images = {
            'Pan de Coco': f'{github_pages_url}pan_de_coco.jpg',
            'Steven': f'{github_pages_url}steven.jpg',
            'Pandecoco': f'{github_pages_url}pandecoco.jpg',
            "'Tinpay ni Uwan'": f'{github_pages_url}tinpay_ni_uwan.jpg',
            'Slicebread': f'{github_pages_url}slicebread.jpg',
            'Kabayan': f'{github_pages_url}kabayan.jpg',
            'Pandesal': f'{github_pages_url}pandesal.jpg',
            'Ensaymada': f'{github_pages_url}ensaymada.jpg',
            'Spanish Bread': f'{github_pages_url}spanish_bread.jpg',
            'Ube Loaf': f'{github_pages_url}ube_loaf.jpg',
            'Cheese Bread': f'{github_pages_url}cheese_bread_alt.jpg',
        }
        
        updated_count = 0
        for product_name, image_url in product_images.items():
            try:
                product = Product.objects.get(name=product_name)
                product.image = image_url
                product.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Updated {product.name}')
                )
                updated_count += 1
            except Product.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Product {product_name} not found')
                )
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(f'🎉 Successfully updated {updated_count} products with GitHub Pages images!')
        )

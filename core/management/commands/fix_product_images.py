import os
from django.core.management.base import BaseCommand
from core.models import Product


class Command(BaseCommand):
    help = 'Update all products with reliable placeholder images'

    def handle(self, *args, **options):
        # Map products to placeholder images
        product_images = {
            'Pandesal': 'https://picsum.photos/seed/pandesal/300/200.jpg',
            'Ensaymada': 'https://picsum.photos/seed/ensaymada/300/200.jpg',
            'Spanish Bread': 'https://picsum.photos/seed/spanishbread/300/200.jpg',
            'Cheese Bread': 'https://picsum.photos/seed/cheesebread/300/200.jpg',
            'Ube Loaf': 'https://picsum.photos/seed/ubeloaf/300/200.jpg',
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
            self.style.SUCCESS(f'Successfully updated {updated_count} products with placeholder images')
        )

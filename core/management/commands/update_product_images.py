import os
from django.core.management.base import BaseCommand
from core.models import Product


class Command(BaseCommand):
    help = 'Update all products with Cloudinary image URLs'

    def handle(self, *args, **options):
        cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME')
        if not cloud_name:
            self.stdout.write(self.style.ERROR('Cloudinary is not configured'))
            return

        # Map products to appropriate Cloudinary images
        product_images = {
            'Pandesal': 'https://res.cloudinary.com/djk8ulhlp/image/upload/filipino-bread-640-500x500.jpg',
            'Ensaymada': 'https://res.cloudinary.com/djk8ulhlp/image/upload/ensaymada-3.jpg',
            'Spanish Bread': 'https://res.cloudinary.com/djk8ulhlp/image/upload/pan-de-coco-1200t.jpg',
            'Cheese Bread': 'https://res.cloudinary.com/djk8ulhlp/image/upload/Basket-with-Brazilian-Cheese-Bread.jpg',
            'Ube Loaf': 'https://res.cloudinary.com/djk8ulhlp/image/upload/How-to-Use-the-Whole-Loaf-of-Bread-Including-the-Ends-FB.jpg'
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
            self.style.SUCCESS(f'Successfully updated {updated_count} products with Cloudinary images')
        )

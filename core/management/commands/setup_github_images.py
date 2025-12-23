import os
import shutil
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Copy local images to static directory for GitHub Pages hosting'

    def handle(self, *args, **options):
        # Create static images directory
        static_images_dir = Path(settings.BASE_DIR) / 'static' / 'images'
        static_images_dir.mkdir(parents=True, exist_ok=True)
        
        # Local images to copy
        media_dir = Path(settings.MEDIA_ROOT) / 'products'
        images_to_copy = {
            'Logo.png': 'logo.png',
            'Background.jpg': 'background.jpg',
            'ensaymada-3.jpg': 'ensaymada.jpg',
            'filipino-bread-640-500x500.jpg': 'pandesal.jpg',
            'pan-de-coco-1200t.jpg': 'spanish_bread.jpg',
            'Basket-with-Brazilian-Cheese-Bread.jpg': 'cheese_bread.jpg',
            'How-to-Use-the-Whole-Loaf-of-Bread-Including-the-Ends-FB.jpg': 'ube_loaf.jpg',
        }
        
        copied_files = []
        
        for source_filename, target_filename in images_to_copy.items():
            source_path = media_dir / source_filename
            target_path = static_images_dir / target_filename
            
            if source_path.exists():
                try:
                    shutil.copy2(source_path, target_path)
                    copied_files.append(target_filename)
                    self.stdout.write(self.style.SUCCESS(f'✅ Copied {source_filename} → static/images/{target_filename}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Error copying {source_filename}: {str(e)}'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠️  Source file not found: {source_path}'))
        
        if copied_files:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(f'✅ Successfully copied {len(copied_files)} images to static/images/'))
            self.stdout.write('')
            self.stdout.write('📋 Next steps:')
            self.stdout.write('1. Run: git add . && git commit -m "Add static images for GitHub Pages"')
            self.stdout.write('2. Run: git push origin master')
            self.stdout.write('3. Enable GitHub Pages in your repository settings')
            self.stdout.write('4. Run: python manage.py update_github_image_urls')
        else:
            self.stdout.write(self.style.ERROR('❌ No files were copied'))

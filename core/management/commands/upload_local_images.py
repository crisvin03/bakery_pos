import os
import json
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import Product


class Command(BaseCommand):
    help = 'Upload local images to ImgBB and update production database'

    def handle(self, *args, **options):
        # ImgBB API key (you need to get this from https://api.imgbb.com/)
        API_KEY = "your_imgbb_api_key_here"
        
        # Local images to upload
        media_dir = settings.MEDIA_ROOT / 'products'
        images_to_upload = {
            'Logo.png': 'logo',
            'Background.jpg': 'background',
            'ensaymada-3.jpg': 'ensaymada',
            'filipino-bread-640-500x500.jpg': 'pandesal',
            'pan-de-coco-1200t.jpg': 'spanish_bread',
            'Basket-with-Brazilian-Cheese-Bread.jpg': 'cheese_bread',
            'How-to-Use-the-Whole-Loaf-of-Bread-Including-the-Ends-FB.jpg': 'ube_loaf',
        }
        
        uploaded_urls = {}
        
        for filename, image_type in images_to_upload.items():
            file_path = media_dir / filename
            if file_path.exists():
                self.stdout.write(f'Uploading {filename}...')
                
                # Upload to ImgBB
                try:
                    with open(file_path, 'rb') as image_file:
                        response = requests.post(
                            'https://api.imgbb.com/1/upload',
                            params={
                                'key': API_KEY,
                                'expiration': 0,  # No expiration
                            },
                            files={
                                'image': image_file,
                            }
                        )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data['success']:
                            url = data['data']['url']
                            uploaded_urls[image_type] = url
                            self.stdout.write(self.style.SUCCESS(f'✅ {filename} uploaded: {url}'))
                        else:
                            self.stdout.write(self.style.ERROR(f'❌ Failed to upload {filename}: {data}'))
                    else:
                        self.stdout.write(self.style.ERROR(f'❌ HTTP error uploading {filename}: {response.status_code}'))
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Error uploading {filename}: {str(e)}'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠️  File not found: {file_path}'))
        
        # Save uploaded URLs to file
        if uploaded_urls:
            urls_file = 'uploaded_image_urls.json'
            with open(urls_file, 'w') as f:
                json.dump(uploaded_urls, f, indent=2)
            
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(f'✅ Uploaded URLs saved to {urls_file}'))
            self.stdout.write('')
            self.stdout.write('📋 Next steps:')
            self.stdout.write('1. Get a free ImgBB API key from https://api.imgbb.com/')
            self.stdout.write('2. Replace API_KEY in this command with your key')
            self.stdout.write('3. Run this command again')
            self.stdout.write('4. Run "python manage.py update_production_images"')
        else:
            self.stdout.write(self.style.ERROR('❌ No images were uploaded'))

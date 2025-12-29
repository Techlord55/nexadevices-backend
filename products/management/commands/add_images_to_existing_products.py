# products/management/commands/add_images_to_existing_products.py
from django.core.management.base import BaseCommand
from django.core.files import File
from products.models import Product, ProductImage
import json
import os
import cloudinary
import cloudinary.uploader
from django.conf import settings

class Command(BaseCommand):
    help = 'Add images to existing products from JSON file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to JSON file with SKU and images')
        parser.add_argument('--images-dir', type=str, default='product_images', help='Directory containing images')
        parser.add_argument('--cloudinary', action='store_true', help='Upload to Cloudinary')

    def handle(self, *args, **options):
        file_path = options['file_path']
        images_dir = options['images_dir']
        use_cloudinary = options['cloudinary']

        # Configure Cloudinary if needed
        if use_cloudinary:
            cloudinary_config = settings.CLOUDINARY_STORAGE
            cloudinary.config(
                cloud_name=cloudinary_config['CLOUD_NAME'],
                api_key=cloudinary_config['API_KEY'],
                api_secret=cloudinary_config['API_SECRET'],
                secure=True
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Cloudinary configured'))

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
                for item in data:
                    sku = item.get('sku')
                    images = item.get('images', [])
                    
                    if not sku:
                        self.stdout.write(self.style.WARNING('⚠ Skipping item without SKU'))
                        continue
                    
                    try:
                        product = Product.objects.get(sku=sku)
                        self.stdout.write(f'\n📦 Processing: {product.name} ({sku})')
                        
                        # Delete existing images if you want to replace them
                        # product.images.all().delete()
                        
                        for idx, filename in enumerate(images):
                            image_path = os.path.join(images_dir, filename)
                            
                            if not os.path.exists(image_path):
                                self.stdout.write(self.style.WARNING(f'  ⚠ Image not found: {filename}'))
                                continue
                            
                            if use_cloudinary:
                                # Upload to Cloudinary
                                result = cloudinary.uploader.upload(
                                    image_path,
                                    folder=f'nexadevices/products/{product.sku}',
                                    public_id=os.path.splitext(filename)[0]
                                )
                                
                                ProductImage.objects.create(
                                    product=product,
                                    image=result['secure_url'],
                                    is_primary=(idx == 0),
                                    order=idx,
                                    alt_text=product.name
                                )
                                self.stdout.write(self.style.SUCCESS(f'  ✓ Uploaded to Cloudinary: {filename}'))
                            else:
                                # Local storage
                                with open(image_path, 'rb') as img_file:
                                    product_image = ProductImage(
                                        product=product,
                                        is_primary=(idx == 0),
                                        order=idx,
                                        alt_text=product.name
                                    )
                                    product_image.image.save(filename, File(img_file), save=True)
                                self.stdout.write(self.style.SUCCESS(f'  ✓ Added: {filename}'))
                        
                        self.stdout.write(self.style.SUCCESS(f'✓ Completed: {product.name}'))
                        
                    except Product.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f'✗ Product not found: {sku}'))
                
                self.stdout.write(self.style.SUCCESS('\n✅ Image import complete!'))
                
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'✗ File not found: {file_path}'))
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR('✗ Invalid JSON format'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error: {str(e)}'))
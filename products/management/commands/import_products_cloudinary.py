# products/management/commands/import_products_cloudinary.py
from django.core.management.base import BaseCommand
from products.models import Category, Product, ProductImage
import json
import csv
from decimal import Decimal
import os
from pathlib import Path
from PIL import Image
import io
import cloudinary
import cloudinary.uploader
from django.conf import settings

class Command(BaseCommand):
    help = 'Import products with optimized images to Cloudinary'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to CSV or JSON file')
        parser.add_argument(
            '--images-dir',
            type=str,
            default='product_images',
            help='Directory containing product images'
        )
        parser.add_argument(
            '--format',
            type=str,
            default='json',
            choices=['json', 'csv'],
            help='File format (json or csv)'
        )
        parser.add_argument(
            '--max-size',
            type=int,
            default=1024,
            help='Maximum file size in KB (default: 1024KB = 1MB)'
        )
        parser.add_argument(
            '--max-dimension',
            type=int,
            default=2000,
            help='Maximum width/height in pixels (default: 2000px)'
        )

    def handle(self, *args, **options):
        file_path = options['file_path']
        images_dir = options['images_dir']
        file_format = options['format']
        self.max_size_kb = options['max_size']
        self.max_dimension = options['max_dimension']

        # Configure Cloudinary
        cloudinary_config = settings.CLOUDINARY_STORAGE
        cloudinary.config(
            cloud_name=cloudinary_config['CLOUD_NAME'],
            api_key=cloudinary_config['API_KEY'],
            api_secret=cloudinary_config['API_SECRET'],
            secure=True
        )
        
        self.stdout.write(self.style.SUCCESS(f'✓ Cloudinary configured: {cloudinary_config["CLOUD_NAME"]}'))

        # Verify images directory exists
        if not os.path.exists(images_dir):
            self.stdout.write(self.style.ERROR(f'✗ Images directory not found: {images_dir}'))
            return

        if file_format == 'json':
            self.import_from_json(file_path, images_dir)
        else:
            self.import_from_csv(file_path, images_dir)

    def optimize_image(self, image_path):
        """
        Optimize image: resize, compress, convert to best format
        Returns: optimized image bytes and format
        """
        try:
            # Open image
            img = Image.open(image_path)
            
            # Convert RGBA to RGB if needed (for JPEG)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Get original dimensions
            width, height = img.size
            original_size = os.path.getsize(image_path) / 1024  # KB

            # Resize if too large
            if width > self.max_dimension or height > self.max_dimension:
                img.thumbnail((self.max_dimension, self.max_dimension), Image.Resampling.LANCZOS)
                self.stdout.write(f'  ↓ Resized from {width}x{height} to {img.size[0]}x{img.size[1]}')

            # Try different quality settings to get under size limit
            quality = 95
            output_format = 'JPEG'  # JPEG is best for photos
            
            while quality > 20:
                output = io.BytesIO()
                img.save(output, format=output_format, quality=quality, optimize=True)
                size_kb = output.tell() / 1024
                
                if size_kb <= self.max_size_kb:
                    self.stdout.write(self.style.SUCCESS(
                        f'  ✓ Optimized: {original_size:.1f}KB → {size_kb:.1f}KB (quality: {quality})'
                    ))
                    output.seek(0)
                    return output, output_format.lower()
                
                quality -= 5
                output.close()

            # If still too large, try WebP format (better compression)
            output_format = 'WEBP'
            quality = 85
            
            while quality > 20:
                output = io.BytesIO()
                img.save(output, format=output_format, quality=quality, optimize=True)
                size_kb = output.tell() / 1024
                
                if size_kb <= self.max_size_kb:
                    self.stdout.write(self.style.SUCCESS(
                        f'  ✓ Optimized: {original_size:.1f}KB → {size_kb:.1f}KB (WebP, quality: {quality})'
                    ))
                    output.seek(0)
                    return output, output_format.lower()
                
                quality -= 5
                output.close()

            # Last resort: aggressive compression
            output = io.BytesIO()
            img.save(output, format='WEBP', quality=20, optimize=True)
            size_kb = output.tell() / 1024
            self.stdout.write(self.style.WARNING(
                f'  ⚠ Optimized: {original_size:.1f}KB → {size_kb:.1f}KB (WebP, quality: 20)'
            ))
            output.seek(0)
            return output, 'webp'

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Error optimizing image: {str(e)}'))
            return None, None

    def upload_to_cloudinary(self, image_data, filename, product_sku):
        """Upload optimized image to Cloudinary"""
        try:
            # Create folder structure in Cloudinary
            folder = f'nexadevices/products/{product_sku}'
            
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                image_data,
                folder=folder,
                public_id=Path(filename).stem,
                resource_type='image',
                format='auto',  # Let Cloudinary choose best format
                quality='auto:best',  # Cloudinary can further optimize if needed
                fetch_format='auto'
            )
            
            url = result['secure_url']
            self.stdout.write(self.style.SUCCESS(f'  ✓ Uploaded to Cloudinary: {url}'))
            return url
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Cloudinary upload failed: {str(e)}'))
            return None

    def process_product_images(self, product, image_filenames, images_dir):
        """Process and upload images for a product"""
        if not image_filenames:
            return
        
        # Handle both list and comma-separated string
        if isinstance(image_filenames, str):
            image_filenames = [f.strip() for f in image_filenames.split(',')]
        
        for idx, filename in enumerate(image_filenames):
            if not filename:
                continue
                
            image_path = os.path.join(images_dir, filename)
            
            if not os.path.exists(image_path):
                self.stdout.write(self.style.WARNING(f'  ⚠ Image not found: {image_path}'))
                continue
            
            self.stdout.write(f'  Processing: {filename}')
            
            # Optimize image
            optimized_image, image_format = self.optimize_image(image_path)
            
            if not optimized_image:
                continue
            
            # Upload to Cloudinary
            cloudinary_url = self.upload_to_cloudinary(
                optimized_image,
                filename,
                product.sku
            )
            
            if cloudinary_url:
                # Create ProductImage record with Cloudinary URL
                ProductImage.objects.create(
                    product=product,
                    image=cloudinary_url,  # Store Cloudinary URL
                    is_primary=(idx == 0),
                    order=idx,
                    alt_text=product.name
                )

    def import_from_json(self, file_path, images_dir):
        """Import products from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
                total = len(data)
                created = 0
                updated = 0
                errors = 0

                self.stdout.write(self.style.SUCCESS(f'\n{"="*60}'))
                self.stdout.write(self.style.SUCCESS(f'Starting import of {total} products...'))
                self.stdout.write(self.style.SUCCESS(f'{"="*60}\n'))

                for idx, item in enumerate(data, 1):
                    try:
                        self.stdout.write(f'\n[{idx}/{total}] Processing: {item.get("name", "Unknown")}')
                        
                        # Get or create category
                        category_name = item.get('category')
                        category, _ = Category.objects.get_or_create(
                            name=category_name,
                            defaults={'description': f'{category_name} products'}
                        )

                        # Create or update product
                        product, is_created = Product.objects.update_or_create(
                            sku=item['sku'],
                            defaults={
                                'category': category,
                                'name': item['name'],
                                'description': item.get('description', ''),
                                'specifications': item.get('specifications', {}),
                                'price': Decimal(str(item['price'])),
                                'compare_price': Decimal(str(item['compare_price'])) if item.get('compare_price') else None,
                                'stock': int(item.get('stock', 0)),
                                'featured': item.get('featured', False),
                                'is_active': item.get('is_active', True),
                                'shipping_weight': Decimal(str(item.get('shipping_weight', 1.0))),
                                'estimated_delivery_days': int(item.get('estimated_delivery_days', 3)),
                            }
                        )

                        # Delete old images if updating
                        if not is_created:
                            product.images.all().delete()

                        # Process and upload images
                        if 'images' in item:
                            self.process_product_images(product, item['images'], images_dir)

                        if is_created:
                            created += 1
                            self.stdout.write(self.style.SUCCESS(f'✓ Created: {product.name}'))
                        else:
                            updated += 1
                            self.stdout.write(self.style.WARNING(f'↻ Updated: {product.name}'))

                    except Exception as e:
                        errors += 1
                        self.stdout.write(self.style.ERROR(f'✗ Error: {str(e)}'))

                self.stdout.write(self.style.SUCCESS(
                    f'\n{"="*60}\n'
                    f'Import Complete!\n'
                    f'{"="*60}\n'
                    f'Total: {total} | Created: {created} | Updated: {updated} | Errors: {errors}\n'
                    f'{"="*60}'
                ))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'✗ File not found: {file_path}'))
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR('✗ Invalid JSON format'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error: {str(e)}'))

    def import_from_csv(self, file_path, images_dir):
        """Import products from CSV file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                created = 0
                updated = 0
                errors = 0
                total = 0

                for row in reader:
                    total += 1
                    try:
                        self.stdout.write(f'\n[{total}] Processing: {row.get("name", "Unknown")}')
                        
                        # Get or create category
                        category_name = row.get('category')
                        category, _ = Category.objects.get_or_create(
                            name=category_name,
                            defaults={'description': f'{category_name} products'}
                        )

                        # Parse specifications
                        specs = {}
                        if row.get('specifications'):
                            try:
                                specs = json.loads(row['specifications'])
                            except:
                                pass

                        # Create or update product
                        product, is_created = Product.objects.update_or_create(
                            sku=row['sku'],
                            defaults={
                                'category': category,
                                'name': row['name'],
                                'description': row.get('description', ''),
                                'specifications': specs,
                                'price': Decimal(str(row['price'])),
                                'compare_price': Decimal(str(row['compare_price'])) if row.get('compare_price') else None,
                                'stock': int(row.get('stock', 0)),
                                'featured': row.get('featured', 'false').lower() == 'true',
                                'is_active': row.get('is_active', 'true').lower() == 'true',
                                'shipping_weight': Decimal(str(row.get('shipping_weight', 1.0))),
                                'estimated_delivery_days': int(row.get('estimated_delivery_days', 3)),
                            }
                        )

                        # Delete old images if updating
                        if not is_created:
                            product.images.all().delete()

                        # Process and upload images
                        if row.get('images'):
                            self.process_product_images(product, row['images'], images_dir)

                        if is_created:
                            created += 1
                            self.stdout.write(self.style.SUCCESS(f'✓ Created: {product.name}'))
                        else:
                            updated += 1
                            self.stdout.write(self.style.WARNING(f'↻ Updated: {product.name}'))

                    except Exception as e:
                        errors += 1
                        self.stdout.write(self.style.ERROR(f'✗ Error: {str(e)}'))

                self.stdout.write(self.style.SUCCESS(
                    f'\n{"="*60}\n'
                    f'Import Complete!\n'
                    f'{"="*60}\n'
                    f'Total: {total} | Created: {created} | Updated: {updated} | Errors: {errors}\n'
                    f'{"="*60}'
                ))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'✗ File not found: {file_path}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error: {str(e)}'))
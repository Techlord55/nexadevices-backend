# products/management/commands/import_products_with_images.py
from django.core.management.base import BaseCommand
from django.core.files import File
from products.models import Category, Product, ProductImage
import json
import csv
from decimal import Decimal
import os
from pathlib import Path

class Command(BaseCommand):
    help = 'Import products with local images from CSV or JSON file'

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

    def handle(self, *args, **options):
        file_path = options['file_path']
        images_dir = options['images_dir']
        file_format = options['format']

        # Verify images directory exists
        if not os.path.exists(images_dir):
            self.stdout.write(self.style.ERROR(f'Images directory not found: {images_dir}'))
            return

        if file_format == 'json':
            self.import_from_json(file_path, images_dir)
        else:
            self.import_from_csv(file_path, images_dir)

    def add_product_images(self, product, image_filenames, images_dir):
        """Add images to product from local files"""
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
                self.stdout.write(self.style.WARNING(f'Image not found: {image_path}'))
                continue
            
            try:
                with open(image_path, 'rb') as img_file:
                    # Create ProductImage
                    product_image = ProductImage(
                        product=product,
                        is_primary=(idx == 0),
                        order=idx,
                        alt_text=product.name
                    )
                    # Save the image file
                    product_image.image.save(
                        filename,
                        File(img_file),
                        save=True
                    )
                    self.stdout.write(self.style.SUCCESS(f'  Added image: {filename}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error adding image {filename}: {str(e)}'))

    def import_from_json(self, file_path, images_dir):
        """Import products from JSON file with local images"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
                total = len(data)
                created = 0
                updated = 0
                errors = 0

                for item in data:
                    try:
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

                        # Add product images from local files
                        if 'images' in item:
                            self.add_product_images(product, item['images'], images_dir)

                        if is_created:
                            created += 1
                            self.stdout.write(self.style.SUCCESS(f'✓ Created: {product.name}'))
                        else:
                            updated += 1
                            self.stdout.write(self.style.WARNING(f'↻ Updated: {product.name}'))

                    except Exception as e:
                        errors += 1
                        self.stdout.write(self.style.ERROR(f'✗ Error processing {item.get("name", "unknown")}: {str(e)}'))

                self.stdout.write(self.style.SUCCESS(
                    f'\n{"="*50}\nImport Summary:\n{"="*50}\n'
                    f'Total: {total} | Created: {created} | Updated: {updated} | Errors: {errors}'
                ))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR('Invalid JSON format'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))

    def import_from_csv(self, file_path, images_dir):
        """Import products from CSV file with local images"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                created = 0
                updated = 0
                errors = 0

                for row in reader:
                    try:
                        # Get or create category
                        category_name = row.get('category')
                        category, _ = Category.objects.get_or_create(
                            name=category_name,
                            defaults={'description': f'{category_name} products'}
                        )

                        # Parse specifications from JSON string if provided
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

                        # Add product images from local files
                        if row.get('images'):
                            self.add_product_images(product, row['images'], images_dir)

                        if is_created:
                            created += 1
                            self.stdout.write(self.style.SUCCESS(f'✓ Created: {product.name}'))
                        else:
                            updated += 1
                            self.stdout.write(self.style.WARNING(f'↻ Updated: {product.name}'))

                    except Exception as e:
                        errors += 1
                        self.stdout.write(self.style.ERROR(f'✗ Error processing {row.get("name", "unknown")}: {str(e)}'))

                self.stdout.write(self.style.SUCCESS(
                    f'\n{"="*50}\nImport Summary:\n{"="*50}\n'
                    f'Created: {created} | Updated: {updated} | Errors: {errors}'
                ))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
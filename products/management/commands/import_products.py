# products/management/commands/import_products.py
# Create directory structure: products/management/commands/
# Don't forget to add __init__.py in both management/ and commands/ folders

from django.core.management.base import BaseCommand
from products.models import Category, Product, ProductImage
import json
import csv
from decimal import Decimal

class Command(BaseCommand):
    help = 'Import products from CSV or JSON file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to CSV or JSON file')
        parser.add_argument(
            '--format',
            type=str,
            default='json',
            choices=['json', 'csv'],
            help='File format (json or csv)'
        )

    def handle(self, *args, **options):
        file_path = options['file_path']
        file_format = options['format']

        if file_format == 'json':
            self.import_from_json(file_path)
        else:
            self.import_from_csv(file_path)

    def import_from_json(self, file_path):
        """Import products from JSON file"""
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

                        # Add product images if provided
                        if 'images' in item:
                            for idx, image_url in enumerate(item['images']):
                                ProductImage.objects.get_or_create(
                                    product=product,
                                    image=image_url,
                                    defaults={
                                        'is_primary': idx == 0,
                                        'order': idx,
                                        'alt_text': product.name
                                    }
                                )

                        if is_created:
                            created += 1
                            self.stdout.write(self.style.SUCCESS(f'Created: {product.name}'))
                        else:
                            updated += 1
                            self.stdout.write(self.style.WARNING(f'Updated: {product.name}'))

                    except Exception as e:
                        errors += 1
                        self.stdout.write(self.style.ERROR(f'Error processing {item.get("name", "unknown")}: {str(e)}'))

                self.stdout.write(self.style.SUCCESS(
                    f'\nImport complete!\nTotal: {total} | Created: {created} | Updated: {updated} | Errors: {errors}'
                ))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR('Invalid JSON format'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))

    def import_from_csv(self, file_path):
        """Import products from CSV file"""
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

                        if is_created:
                            created += 1
                            self.stdout.write(self.style.SUCCESS(f'Created: {product.name}'))
                        else:
                            updated += 1
                            self.stdout.write(self.style.WARNING(f'Updated: {product.name}'))

                    except Exception as e:
                        errors += 1
                        self.stdout.write(self.style.ERROR(f'Error processing {row.get("name", "unknown")}: {str(e)}'))

                self.stdout.write(self.style.SUCCESS(
                    f'\nImport complete!\nCreated: {created} | Updated: {updated} | Errors: {errors}'
                ))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
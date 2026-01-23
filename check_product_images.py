"""
Check all products and their image status for NexaDevices
"""
from dotenv import load_dotenv
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

import django
import sys
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from products.models import Product, ProductImage

print("=" * 80)
print("NEXADEVICES - PRODUCT IMAGE STATUS")
print("=" * 80)

products = Product.objects.all().order_by('name')

print(f"\nTotal Products: {products.count()}\n")

products_without_images = []
products_needing_more = []

for i, product in enumerate(products, 1):
    print(f"{i}. {product.name}")
    print(f"   Category: {product.category.name if product.category else 'No category'}")
    print(f"   Slug: {product.slug}")
    
    # Check product images
    image_count = product.images.count()
    primary_images = product.images.filter(is_primary=True).count()
    
    if image_count == 0:
        print(f"   ❌ No images at all")
        products_without_images.append(product)
    elif image_count < 2:
        print(f"   ⚠️  Only {image_count} image(s) - needs more")
        products_needing_more.append(product)
    else:
        print(f"   ✅ Has {image_count} images")
    
    if primary_images == 0 and image_count > 0:
        print(f"   ⚠️  No primary image set")
    elif primary_images > 1:
        print(f"   ⚠️  Multiple primary images ({primary_images})")
    
    print()

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"\nProducts with NO images: {len(products_without_images)}")
print(f"Products needing MORE images: {len(products_needing_more)}")
print(f"Total products needing attention: {len(products_without_images) + len(products_needing_more)}")

if products_without_images:
    print("\n❌ Products with NO images:")
    for p in products_without_images:
        print(f"   - {p.name}")

if products_needing_more:
    print("\n⚠️  Products needing MORE images:")
    for p in products_needing_more:
        print(f"   - {p.name} (current: {p.images.count()})")

print("\n" + "=" * 80)

"""
Add product images automatically from Unsplash
Downloads high-quality images and uploads to Cloudinary
Adds 3 images per product (1 primary + 2 additional)
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
import requests
import time
import cloudinary.uploader
from io import BytesIO

# Product-specific images organized by category and product type
PRODUCT_IMAGE_SETS = {
    # Drones
    'dji': [
        'https://images.unsplash.com/photo-1473968512647-3e447244af8f?w=800&q=80',
        'https://images.unsplash.com/photo-1508444845599-5c89863b1c44?w=800&q=80',
        'https://images.unsplash.com/photo-1507582020474-9a35b7d455d9?w=800&q=80',
    ],
    
    # Smartphones
    'iphone': [
        'https://images.unsplash.com/photo-1510557880182-3d4d3cba35a5?w=800&q=80',
        'https://images.unsplash.com/photo-1512054502232-10a0a035d672?w=800&q=80',
        'https://images.unsplash.com/photo-1592286927505-c9d0e9687d84?w=800&q=80',
    ],
    'samsung': [
        'https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=800&q=80',
        'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=800&q=80',
        'https://images.unsplash.com/photo-1585060544812-6b45742d762f?w=800&q=80',
    ],
    'oneplus': [
        'https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=800&q=80',
        'https://images.unsplash.com/photo-1574944985070-8f3ebc6b79d2?w=800&q=80',
        'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=800&q=80',
    ],
    'pixel': [
        'https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=800&q=80',
        'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=800&q=80',
        'https://images.unsplash.com/photo-1574944985070-8f3ebc6b79d2?w=800&q=80',
    ],
    
    # Laptops
    'macbook': [
        'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=800&q=80',
        'https://images.unsplash.com/photo-1611186871348-b1ce696e52c9?w=800&q=80',
        'https://images.unsplash.com/photo-1484788984921-03950022c9ef?w=800&q=80',
    ],
    'dell': [
        'https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=800&q=80',
        'https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=800&q=80',
        'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=800&q=80',
    ],
    'lenovo': [
        'https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?w=800&q=80',
        'https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=800&q=80',
        'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=800&q=80',
    ],
    'hp': [
        'https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?w=800&q=80',
        'https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=800&q=80',
        'https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=800&q=80',
    ],
    'asus': [
        'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=800&q=80',
        'https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?w=800&q=80',
        'https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=800&q=80',
    ],
    'acer': [
        'https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=800&q=80',
        'https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?w=800&q=80',
        'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=800&q=80',
    ],
    'razer': [
        'https://images.unsplash.com/photo-1603481588273-2f908a9a7a1b?w=800&q=80',
        'https://images.unsplash.com/photo-1625948515291-69613efd103f?w=800&q=80',
        'https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=800&q=80',
    ],
}

# Category fallbacks
CATEGORY_FALLBACKS = {
    'smartphones': [
        'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=800&q=80',
        'https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=800&q=80',
        'https://images.unsplash.com/photo-1574944985070-8f3ebc6b79d2?w=800&q=80',
    ],
    'laptops': [
        'https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?w=800&q=80',
        'https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=800&q=80',
        'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=800&q=80',
    ],
}

# Generic tech device images as last resort
DEFAULT_IMAGES = [
    'https://images.unsplash.com/photo-1498049794561-7780e7231661?w=800&q=80',
    'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&q=80',
    'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=800&q=80',
]

def find_best_images(product):
    """Find the best matching images for a product"""
    slug = product.slug.lower()
    name = product.name.lower()
    category = product.category.name.lower() if product.category else ''
    
    # Try to match by slug keywords
    for keyword, images in PRODUCT_IMAGE_SETS.items():
        if keyword in slug or keyword in name:
            return images
    
    # Try to match by category
    for cat_keyword, images in CATEGORY_FALLBACKS.items():
        if cat_keyword in category:
            return images
    
    # Return default
    return DEFAULT_IMAGES

print("=" * 80)
print("ADD PRODUCT IMAGES TO NEXADEVICES")
print("=" * 80)

# Find products needing images
products_needing_images = []
for product in Product.objects.all():
    image_count = product.images.count()
    if image_count < 2:  # Need at least 2 images per product
        products_needing_images.append(product)

if not products_needing_images:
    print("\n✅ All products already have sufficient images!")
    sys.exit(0)

print(f"\nFound {len(products_needing_images)} products needing images\n")

for p in products_needing_images:
    current = p.images.count()
    needed = 3 - current
    print(f"   - {p.name} (has {current}, needs {needed} more)")

proceed = input(f"\nAdd images to these {len(products_needing_images)} products? (yes/no): ")
if proceed.lower() != 'yes':
    print("Cancelled.")
    sys.exit(0)

print("\n" + "-" * 80)
print("Processing...")
print("-" * 80)

total_added = 0
failed_count = 0

for product in products_needing_images:
    print(f"\n📦 {product.name}")
    
    current_images = product.images.count()
    images_to_add = 3 - current_images
    
    # Get appropriate images
    image_urls = find_best_images(product)
    
    # Determine starting order
    max_order = 0
    if current_images > 0:
        max_order = product.images.order_by('-order').first().order
    
    has_primary = product.images.filter(is_primary=True).exists()
    
    for i in range(images_to_add):
        image_url = image_urls[i % len(image_urls)]
        order = max_order + i + 1
        is_primary = not has_primary and i == 0 and current_images == 0
        
        try:
            # Step 1: Download image from Unsplash to memory
            print(f"   📥 Downloading image {order} from Unsplash...")
            response = requests.get(image_url, timeout=15, stream=True)
            response.raise_for_status()
            
            # Ensure we got content
            if not response.content:
                raise ValueError("Empty response content")
            
            # Create a BytesIO object from the downloaded content
            image_bytes = BytesIO(response.content)
            
            # Step 2: Upload the downloaded image to Cloudinary
            print(f"   ☁️  Uploading image {order} to Cloudinary...")
            upload_result = cloudinary.uploader.upload(
                image_bytes,
                folder="nexadevices/products",
                public_id=f"{product.slug}-{order}",
                overwrite=True,
                resource_type="image"
            )
            
            # Step 3: Create ProductImage instance and save to database
            product_image = ProductImage(
                product=product,
                image=upload_result['public_id'],  # Store the Cloudinary public_id
                alt_text=f"{product.name} - View {order}",
                is_primary=is_primary,
                order=order
            )
            
            # Save to database
            product_image.save()
            
            primary_text = " (PRIMARY)" if is_primary else ""
            print(f"   ✅ Successfully added image {order}{primary_text}")
            total_added += 1
            
            # Rate limiting
            time.sleep(0.5)
            
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Network error downloading image {order}: {e}")
            failed_count += 1
        except Exception as e:
            print(f"   ❌ Failed to add image {order}: {e}")
            failed_count += 1

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"\n✅ Successfully added: {total_added} images")
if failed_count > 0:
    print(f"❌ Failed: {failed_count} images")

print("\n🎉 Done! All products now have multiple images.")
print("   Images are stored on Cloudinary and ready to use.")
print("\n" + "=" * 80)

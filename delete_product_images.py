"""
Delete all product images from database and Cloudinary
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

from products.models import ProductImage
import cloudinary.uploader

print("=" * 80)
print("DELETE ALL PRODUCT IMAGES")
print("=" * 80)

# Count existing images
total_images = ProductImage.objects.count()

if total_images == 0:
    print("\n✅ No images found in database!")
    sys.exit(0)

print(f"\nFound {total_images} product images in database")
print("\n⚠️  WARNING: This will:")
print("   - Delete all ProductImage records from database")
print("   - Delete all images from Cloudinary")
print("   - This action CANNOT be undone!")

proceed = input(f"\nDelete all {total_images} images? (yes/no): ")
if proceed.lower() != 'yes':
    print("Cancelled.")
    sys.exit(0)

print("\n" + "-" * 80)
print("Deleting...")
print("-" * 80)

deleted_count = 0
failed_count = 0

for image in ProductImage.objects.all():
    try:
        # Delete from Cloudinary if image exists
        if image.image:
            try:
                cloudinary.uploader.destroy(image.image.public_id)
                print(f"   ☁️  Deleted from Cloudinary: {image.product.name} - Image {image.order}")
            except Exception as e:
                print(f"   ⚠️  Cloudinary delete failed (might not exist): {image.product.name}")
        
        # Delete from database
        image.delete()
        deleted_count += 1
        
    except Exception as e:
        print(f"   ❌ Failed to delete: {e}")
        failed_count += 1

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"\n✅ Successfully deleted: {deleted_count} images")
if failed_count > 0:
    print(f"❌ Failed: {failed_count} images")

print("\n🎉 Done! All product images have been removed.")
print("\n" + "=" * 80)

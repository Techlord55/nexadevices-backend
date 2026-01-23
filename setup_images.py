"""
NEXADEVICES - COMPLETE IMAGE SETUP GUIDE
==========================================

This script will:
1. Check current image status
2. Add missing images to all products
3. Optimize performance
4. Update views for better caching

Run this after adding your products to set everything up automatically.
"""

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║              NEXADEVICES - PRODUCT IMAGE SETUP                               ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

This wizard will:
  ✅ Check all products for images
  ✅ Download and add 3 high-quality images per product
  ✅ Upload all images to Cloudinary automatically
  ✅ Set primary images
  ✅ Optimize database queries

""")

import subprocess
import sys
from pathlib import Path

# Get the backend directory
BASE_DIR = Path(__file__).resolve().parent

print("Step 1: Checking current product image status...")
print("=" * 80)
subprocess.run([sys.executable, str(BASE_DIR / "check_product_images.py")])

print("\n" * 2)
proceed = input("Do you want to add missing images? (yes/no): ")

if proceed.lower() == 'yes':
    print("\nStep 2: Adding product images...")
    print("=" * 80)
    subprocess.run([sys.executable, str(BASE_DIR / "add_product_images.py")])
    
    print("\n" * 2)
    print("✅ SETUP COMPLETE!")
    print("\nNext steps:")
    print("1. Replace products/views.py with products/views_optimized.py for better performance")
    print("2. Add Cloudinary environment variables to your production server (Render)")
    print("3. Deploy your backend")
    print("\nCloudinary Variables needed:")
    print("  - CLOUDINARY_CLOUD_NAME")
    print("  - CLOUDINARY_API_KEY")
    print("  - CLOUDINARY_API_SECRET")
else:
    print("\nCancelled. You can run this script again anytime.")

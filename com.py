# # Local storage
# python manage.py add_images_to_existing_products add_images.json --images-dir=product_images

# # Or with Cloudinary
# python manage.py add_images_to_existing_products add_images.json --images-dir=product_images --cloudinary


# # Without images (fastest)
# python manage.py import_products products.json

# # With local images
# python manage.py import_products_with_images products.json --images-dir=product_images

# # With Cloudinary optimization (best for production)
# python manage.py import_products_cloudinary products.json --images-dir=
# python manage.py import_products_cloudinary products.json --images-dir=product_images







# Run this in Django shell: python manage.py shell
# Copy and paste this entire script

from products.models import ProductImage, Product
import cloudinary
from django.conf import settings

print("="*80)
print("🔍 CLOUDINARY DIAGNOSTIC REPORT")
print("="*80)

# Check Cloudinary configuration
print("\n1️⃣ CLOUDINARY CONFIG:")
print(f"   Cloud Name: {cloudinary.config().cloud_name}")
print(f"   API Key: {'*' * 20 if cloudinary.config().api_key else 'NOT SET'}")
print(f"   Secure: {cloudinary.config().secure}")

# Check settings
print("\n2️⃣ DJANGO SETTINGS:")
print(f"   CLOUDINARY_CLOUD_NAME: {getattr(settings, 'CLOUDINARY_CLOUD_NAME', 'NOT SET')}")

# Check database images
print("\n3️⃣ DATABASE IMAGE SAMPLES:")
images = ProductImage.objects.all()[:5]

if not images:
    print("   ⚠️ No images found in database!")
else:
    for img in images:
        print(f"\n   Image ID: {img.id}")
        print(f"   Product: {img.product.name}")
        print(f"   Raw value: {img.image}")
        print(f"   Type: {type(img.image)}")
        
        # Try to get URL
        if hasattr(img.image, 'url'):
            print(f"   .url: {img.image.url}")
        
        # Construct expected URL
        cloud_name = cloudinary.config().cloud_name
        raw_path = str(img.image)
        
        if not raw_path.startswith('http'):
            if not raw_path.startswith('image/upload'):
                expected_url = f'https://res.cloudinary.com/{cloud_name}/image/upload/{raw_path}'
            else:
                expected_url = f'https://res.cloudinary.com/{cloud_name}/{raw_path}'
            print(f"   ✅ Expected URL: {expected_url}")

# Test serializer
print("\n4️⃣ SERIALIZER TEST:")
from products.serializers import ProductImageSerializer

if images:
    test_image = images[0]
    serializer = ProductImageSerializer(test_image)
    print(f"   Serialized image URL: {serializer.data.get('image')}")

# Test Product List
print("\n5️⃣ PRODUCT LIST SERIALIZER TEST:")
from products.serializers import ProductListSerializer

products = Product.objects.all()[:3]
for product in products:
    serializer = ProductListSerializer(product)
    print(f"\n   Product: {product.name}")
    print(f"   Primary Image: {serializer.data.get('primary_image')}")

print("\n" + "="*80)
print("✅ DIAGNOSTIC COMPLETE")
print("="*80)

# Recommended fixes
print("\n📋 RECOMMENDATIONS:")
print("1. Ensure CLOUDINARY_CLOUD_NAME is set in environment variables")
print("2. Update next.config.mjs to allow res.cloudinary.com")
print("3. Verify URLs start with https://res.cloudinary.com/")
print("4. Redeploy both Django and Next.js after changes")
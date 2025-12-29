# # test_rls.py
# import os
# import django

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
# django.setup()

# from products.models import Product, Category

# # This should work (service_role has full access)
# print("Testing database access...")

# # Count categories
# categories = Category.objects.all()
# print(f"✅ Found {categories.count()} categories")

# # Count products
# products = Product.objects.all()
# print(f"✅ Found {products.count()} products")

# print("\n✅ RLS is working! Django backend has full access.")


# test_env.py
from decouple import config

print("DB_PASSWORD:", config('DB_PASSWORD')[:50] + "...")
print("Length:", len(config('DB_PASSWORD')))
print("Starts with 'eyJ':", config('DB_PASSWORD').startswith('eyJ'))
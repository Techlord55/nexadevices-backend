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
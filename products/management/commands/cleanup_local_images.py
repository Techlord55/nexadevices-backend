# products/management/commands/cleanup_local_images.py
from django.core.management.base import BaseCommand
from products.models import ProductImage, Category

class Command(BaseCommand):
    help = 'Delete all local image references (non-Cloudinary URLs)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Actually delete the images (default is dry-run)',
        )

    def handle(self, *args, **options):
        do_delete = options['delete']
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write("🧹 Cleaning Up Local Image References")
        self.stdout.write("="*60)
        
        if not do_delete:
            self.stdout.write(self.style.WARNING(
                "\n⚠️  DRY RUN MODE - No changes will be made"
            ))
            self.stdout.write("Run with --delete flag to actually remove images\n")
        
        # Find all local images (not Cloudinary URLs)
        product_images = ProductImage.objects.all()
        local_images = [
            img for img in product_images 
            if not str(img.image).startswith('http')
        ]
        
        category_images = Category.objects.exclude(image='')
        local_category_images = [
            cat for cat in category_images 
            if cat.image and not str(cat.image).startswith('http')
        ]
        
        self.stdout.write(f"\n📊 Found:")
        self.stdout.write(f"   - {len(local_images)} product images with local paths")
        self.stdout.write(f"   - {len(local_category_images)} category images with local paths")
        
        if not local_images and not local_category_images:
            self.stdout.write(self.style.SUCCESS(
                "\n✅ No local images found! All images are on Cloudinary."
            ))
            return
        
        # Show examples
        self.stdout.write(f"\n📋 Examples of local paths found:")
        for img in local_images[:5]:
            self.stdout.write(f"   - {img.product.name}: {img.image}")
        
        if do_delete:
            self.stdout.write(self.style.WARNING(
                f"\n🗑️  Deleting {len(local_images)} product image records..."
            ))
            deleted_count = 0
            for img in local_images:
                img.delete()
                deleted_count += 1
            
            self.stdout.write(self.style.WARNING(
                f"\n🗑️  Clearing {len(local_category_images)} category images..."
            ))
            for cat in local_category_images:
                cat.image = ''
                cat.save()
            
            self.stdout.write(self.style.SUCCESS(
                f"\n✅ Deleted {deleted_count} local image references!"
            ))
            self.stdout.write(self.style.SUCCESS(
                "✅ Now re-upload images through Django admin or import command."
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f"\n💡 Run 'python manage.py cleanup_local_images --delete' to remove these"
            ))
        
        self.stdout.write("\n" + "="*60 + "\n")
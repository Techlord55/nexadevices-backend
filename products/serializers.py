# products/serializers.py
from rest_framework import serializers
from .models import Category, Product, ProductImage
from django.db.models import Avg
import cloudinary
from django.conf import settings

class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_primary', 'order']
    
    def get_image(self, obj):
        """
        ✅ CRITICAL: Construct full Cloudinary URL from relative path
        """
        if not obj.image:
            return None
            
        try:
            image_str = str(obj.image)
            
            # If already a full URL, return it
            if image_str.startswith(('http://', 'https://')):
                return image_str
            
            # If it has a .url attribute (CloudinaryField)
            if hasattr(obj.image, 'url'):
                url = str(obj.image.url)
                # Ensure it's absolute
                if url.startswith('//'):
                    return f'https:{url}'
                elif url.startswith('http'):
                    return url
            
            # ✅ CONSTRUCT FULL CLOUDINARY URL from relative path
            # Your DB shows: "image/upload/v176753331/nexadevices/..."
            # We need: "https://res.cloudinary.com/YOUR_CLOUD/image/upload/v176753331/nexadevices/..."
            
            # Get cloud name from settings or cloudinary config
            cloud_name = getattr(settings, 'CLOUDINARY_CLOUD_NAME', None) or \
                        cloudinary.config().cloud_name
            
            if cloud_name and not image_str.startswith('http'):
                # If path doesn't start with "image/upload", add it
                if not image_str.startswith('image/upload'):
                    full_url = f'https://res.cloudinary.com/{cloud_name}/image/upload/{image_str}'
                else:
                    full_url = f'https://res.cloudinary.com/{cloud_name}/{image_str}'
                
                print(f'✅ Constructed Cloudinary URL: {full_url}')
                return full_url
            
            # Fallback
            print(f'⚠️ Could not construct URL for: {image_str}')
            return image_str
            
        except Exception as e:
            print(f"❌ Error processing image: {e}")
            import traceback
            traceback.print_exc()
            return None


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'image', 'product_count']
    
    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()
    
    def get_image(self, obj):
        if not obj.image:
            return None
            
        try:
            image_str = str(obj.image)
            
            if image_str.startswith(('http://', 'https://')):
                return image_str
            
            if hasattr(obj.image, 'url'):
                url = str(obj.image.url)
                if url.startswith('//'):
                    return f'https:{url}'
                elif url.startswith('http'):
                    return url
            
            # Construct full URL
            cloud_name = getattr(settings, 'CLOUDINARY_CLOUD_NAME', None) or \
                        cloudinary.config().cloud_name
            
            if cloud_name and not image_str.startswith('http'):
                if not image_str.startswith('image/upload'):
                    return f'https://res.cloudinary.com/{cloud_name}/image/upload/{image_str}'
                else:
                    return f'https://res.cloudinary.com/{cloud_name}/{image_str}'
            
            return image_str
            
        except Exception as e:
            print(f"❌ Error processing category image: {e}")
            return None


class ProductListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    primary_image = serializers.SerializerMethodField()
    in_stock = serializers.BooleanField(read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'category', 'price', 'compare_price',
            'primary_image', 'in_stock', 'discount_percentage', 'featured'
        ]
    
    def get_primary_image(self, obj):
        """
        Get primary image with full Cloudinary URL
        """
        try:
            # Get primary or first image
            primary = obj.images.filter(is_primary=True).first()
            if not primary:
                primary = obj.images.order_by('order', 'id').first()
            
            if not primary or not primary.image:
                return None
            
            # Use ProductImageSerializer to get the URL
            serializer = ProductImageSerializer(primary, context=self.context)
            return serializer.data.get('image')
            
        except Exception as e:
            print(f"❌ Error getting primary image for {obj.name}: {e}")
            return None


class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    images = serializers.SerializerMethodField()
    in_stock = serializers.BooleanField(read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)
    related_products = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    total_reviews = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = '__all__'
    
    def get_images(self, obj):
        """Return ordered images with full URLs"""
        try:
            images_queryset = obj.images.all().order_by('order', 'id')
            serializer = ProductImageSerializer(
                images_queryset,
                many=True,
                context=self.context
            )
            return serializer.data
        except Exception as e:
            print(f"❌ Error serializing images for {obj.name}: {e}")
            return []
    
    def get_related_products(self, obj):
        related = Product.objects.filter(
            category=obj.category,
            is_active=True
        ).exclude(id=obj.id)[:4]
        return ProductListSerializer(related, many=True, context=self.context).data
    
    def get_average_rating(self, obj):
        avg = obj.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0
    
    def get_total_reviews(self, obj):
        return obj.reviews.count()
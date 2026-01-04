# products/serializers.py
from rest_framework import serializers
from .models import Category, Product, ProductImage
from django.db.models import Avg

class ProductImageSerializer(serializers.ModelSerializer):
    # Fix: CloudinaryField returns the URL directly as a string
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_primary', 'order']
    
    def get_image(self, obj):
        if obj.image:
            # CloudinaryField stores the full URL directly
            # Check if it's already a full URL
            image_str = str(obj.image)
            if image_str.startswith('http'):
                return image_str
            # If it's a CloudinaryResource object, get its URL
            elif hasattr(obj.image, 'url'):
                return obj.image.url
            else:
                return image_str
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
        if obj.image:
            image_str = str(obj.image)
            if image_str.startswith('http'):
                return image_str
            elif hasattr(obj.image, 'url'):
                return obj.image.url
            else:
                return image_str
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
        # Get the primary image or first image by order
        primary = obj.images.filter(is_primary=True).first()
        if not primary:
            primary = obj.images.order_by('order', 'id').first()
        
        if primary and primary.image:
            image_str = str(primary.image)
            # Return the Cloudinary URL
            if image_str.startswith('http'):
                return image_str
            elif hasattr(primary.image, 'url'):
                return primary.image.url
            else:
                return image_str
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    images = serializers.SerializerMethodField()  # ✅ CHANGED: Use SerializerMethodField
    in_stock = serializers.BooleanField(read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)
    related_products = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    total_reviews = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = '__all__'
    
    def get_images(self, obj):
        """
        ✅ KEY FIX: Explicitly order images and serialize them
        This ensures images are always returned in correct order
        """
        # Get all images, ordered by 'order' field first, then by id
        images_queryset = obj.images.all().order_by('order', 'id')
        
        # Serialize with context to pass request for URL building
        serializer = ProductImageSerializer(
            images_queryset,
            many=True,
            context=self.context
        )
        
        return serializer.data
    
    def get_related_products(self, obj):
        related = Product.objects.filter(
            category=obj.category,
            is_active=True
        ).exclude(id=obj.id)[:4]
        return ProductListSerializer(related, many=True, context=self.context).data
    
    def get_average_rating(self, obj):
        """Calculate average rating from reviews"""
        avg = obj.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0
    
    def get_total_reviews(self, obj):
        """Get total number of reviews"""
        return obj.reviews.count()
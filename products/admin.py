# products/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Avg
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Category, Product, ProductImage, Review
import json


# ============================================================================
# CATEGORY ADMIN
# ============================================================================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'image_preview', 'product_count', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['image_preview_large', 'created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Image', {
            'fields': ('image', 'image_preview_large'),
            'description': 'Upload a category image (recommended: 800x600px)'
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def product_count(self, obj):
        count = obj.products.count()
        url = reverse('admin:products_product_changelist') + f'?category__id__exact={obj.id}'
        return format_html('<a href="{}">{} products</a>', url, count)
    product_count.short_description = 'Products'
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />', obj.image.url)
        return "No image"
    image_preview.short_description = 'Preview'
    
    def image_preview_large(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-width: 400px; max-height: 400px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />', obj.image.url)
        return "No image uploaded"
    image_preview_large.short_description = 'Current Image'


# ============================================================================
# PRODUCT IMAGE INLINE
# ============================================================================
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image_preview', 'image', 'alt_text', 'is_primary', 'order']
    readonly_fields = ['image_preview']
    ordering = ['order']
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
        js = ('admin/js/image_preview.js',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Preview'


# ============================================================================
# REVIEW INLINE
# ============================================================================
class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    readonly_fields = ['user', 'rating', 'rating_stars', 'comment', 'created_at']
    fields = ['user', 'rating_stars', 'comment', 'created_at']
    can_delete = True
    
    def rating_stars(self, obj):
        stars = '⭐' * obj.rating
        empty = '☆' * (5 - obj.rating)
        return format_html('<span style="font-size: 16px;">{}{}</span>', stars, empty)
    rating_stars.short_description = 'Rating'
    
    def has_add_permission(self, request, obj=None):
        return False


# ============================================================================
# PRODUCT ADMIN
# ============================================================================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'primary_image_preview',
        'name',
        'category',
        'price_display',
        'stock_status',
        'featured_badge',
        'is_active',
        'created_at'
    ]
    list_filter = ['category', 'featured', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'sku']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ReviewInline]
    readonly_fields = [
        'in_stock',
        'discount_percentage',
        'primary_image_large',
        'specifications_display',
        'average_rating',
        'total_reviews',
        'created_at',
        'updated_at'
    ]
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('📦 Product Information', {
            'fields': ('name', 'slug', 'category', 'sku'),
            'description': 'Basic product identification'
        }),
        ('📝 Description', {
            'fields': ('description',),
            'description': 'Detailed product description'
        }),
        ('💰 Pricing', {
            'fields': ('price', 'compare_price', 'discount_percentage'),
            'description': 'Product pricing and discounts'
        }),
        ('📊 Inventory', {
            'fields': ('stock', 'in_stock'),
            'description': 'Stock management'
        }),
        ('🔧 Specifications', {
            'fields': ('specifications', 'specifications_display'),
            'classes': ('collapse',),
            'description': 'Technical specifications (JSON format)'
        }),
        ('📦 Shipping', {
            'fields': ('shipping_weight', 'estimated_delivery_days'),
            'classes': ('collapse',),
        }),
        ('⭐ Reviews & Rating', {
            'fields': ('average_rating', 'total_reviews'),
            'classes': ('collapse',),
        }),
        ('🎯 Display Settings', {
            'fields': ('featured', 'is_active', 'primary_image_large'),
            'description': 'Control product visibility and featured status'
        }),
        ('📅 Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    actions = ['make_featured', 'remove_featured', 'mark_active', 'mark_inactive']
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
    
    # ========== List Display Methods ==========
    
    def primary_image_preview(self, obj):
        primary = obj.images.filter(is_primary=True).first()
        if not primary:
            primary = obj.images.first()
        if primary:
            return format_html(
                '<img src="{}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" />',
                primary.image.url
            )
        return mark_safe('<div style="width: 60px; height: 60px; background: #f0f0f0; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 24px;">📷</div>')
    primary_image_preview.short_description = 'Image'
    
    def price_display(self, obj):
        if obj.compare_price and obj.compare_price > obj.price:
            return format_html(
                '<div style="line-height: 1.4;">'
                '<strong style="color: #e74c3c; font-size: 16px;">${}</strong><br>'
                '<span style="text-decoration: line-through; color: #999; font-size: 12px;">${}</span> '
                '<span style="background: #e74c3c; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px; font-weight: bold;">-{}%</span>'
                '</div>',
                obj.price, obj.compare_price, obj.discount_percentage
            )
        return format_html('<strong style="font-size: 16px;">${}</strong>', obj.price)
    price_display.short_description = 'Price'
    
    def stock_status(self, obj):
        if obj.stock == 0:
            return mark_safe(
                '<span style="background: #e74c3c; color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: bold;">OUT OF STOCK</span>'
            )
        elif obj.stock < 5:
            return format_html(
                '<span style="background: #f39c12; color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: bold;">LOW: {}</span>',
                obj.stock
            )
        return format_html(
            '<span style="background: #27ae60; color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: bold;">IN STOCK: {}</span>',
            obj.stock
        )
    stock_status.short_description = 'Stock'
    
    def featured_badge(self, obj):
        if obj.featured:
            return mark_safe(
                '<span style="background: #3498db; color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: bold;">⭐ FEATURED</span>'
            )
        return mark_safe('<span style="color: #999;">—</span>')
    featured_badge.short_description = 'Featured'
    
    # ========== Readonly Field Methods ==========
    
    def primary_image_large(self, obj):
        primary = obj.images.filter(is_primary=True).first()
        if not primary:
            primary = obj.images.first()
        if primary:
            return format_html(
                '<div style="text-align: center;">'
                '<img src="{}" style="max-width: 400px; max-height: 400px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);" />'
                '<p style="margin-top: 10px; color: #666; font-size: 12px;">Primary product image</p>'
                '</div>',
                primary.image.url
            )
        return mark_safe(
            '<div style="padding: 40px; text-align: center; background: #f9f9f9; border-radius: 8px; color: #999;">'
            '<div style="font-size: 48px; margin-bottom: 10px;">📷</div>'
            '<p>No images uploaded yet</p>'
            '<p style="font-size: 12px;">Add images using the "Product Images" section below</p>'
            '</div>'
        )
    primary_image_large.short_description = 'Product Image'
    
    def specifications_display(self, obj):
        if obj.specifications:
            json_str = json.dumps(obj.specifications, indent=2)
            return format_html(
                '<div style="background: #f9f9f9; padding: 15px; border-radius: 8px; font-family: monospace; font-size: 12px;">'
                '<pre style="margin: 0;">{}</pre>'
                '</div>',
                json_str
            )
        return "No specifications"
    specifications_display.short_description = 'Specifications Preview'
    
    def average_rating(self, obj):
        avg = obj.reviews.aggregate(Avg('rating'))['rating__avg']
        if avg:
            stars = '⭐' * int(round(avg))
            return format_html(
                '<span style="font-size: 16px;">{}</span> <span style="color: #666;">({:.1f}/5)</span>',
                stars, avg
            )
        return "No reviews yet"
    average_rating.short_description = 'Average Rating'
    
    def total_reviews(self, obj):
        count = obj.reviews.count()
        if count > 0:
            return format_html(
                '<strong style="color: #3498db; font-size: 14px;">{}</strong> reviews',
                count
            )
        return "No reviews"
    total_reviews.short_description = 'Total Reviews'
    
    # ========== Custom Actions ==========
    
    def make_featured(self, request, queryset):
        updated = queryset.update(featured=True)
        self.message_user(request, f'{updated} products marked as featured.')
    make_featured.short_description = '⭐ Mark as Featured'
    
    def remove_featured(self, request, queryset):
        updated = queryset.update(featured=False)
        self.message_user(request, f'{updated} products removed from featured.')
    remove_featured.short_description = '⭐ Remove Featured'
    
    def mark_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} products marked as active.')
    mark_active.short_description = '✅ Mark as Active'
    
    def mark_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} products marked as inactive.')
    mark_inactive.short_description = '❌ Mark as Inactive'


# ============================================================================
# REVIEW ADMIN
# ============================================================================
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating_stars', 'created_at', 'comment_preview']
    list_filter = ['rating', 'created_at']
    search_fields = ['product__name', 'user__username', 'comment']
    readonly_fields = ['created_at', 'updated_at', 'rating_stars']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Review Details', {
            'fields': ('product', 'user', 'rating', 'rating_stars')
        }),
        ('Comment', {
            'fields': ('comment',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def rating_stars(self, obj):
        stars = '⭐' * obj.rating
        empty = '☆' * (5 - obj.rating)
        return format_html('<span style="font-size: 18px;">{}{}</span>', stars, empty)
    rating_stars.short_description = 'Rating'
    
    def comment_preview(self, obj):
        if len(obj.comment) > 100:
            return obj.comment[:100] + '...'
        return obj.comment
    comment_preview.short_description = 'Comment'
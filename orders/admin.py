from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['subtotal']
    fields = ['product', 'product_name', 'product_sku', 'quantity', 'price', 'subtotal']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'status', 'total', 'created_at']
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['order_number', 'user__email', 'user__username', 'tracking_number']
    inlines = [OrderItemInline]
    readonly_fields = ['order_number', 'subtotal', 'tax', 'total', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status')
        }),
        ('Shipping', {
            'fields': ('shipping_address', 'shipping_method', 'shipping_cost', 'tracking_number', 'estimated_delivery')
        }),
        ('Payment', {
            'fields': ('payment_method', 'payment_status', 'stripe_payment_intent')
        }),
        ('Totals', {
            'fields': ('subtotal', 'tax', 'total')
        }),
        ('Additional', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product_name', 'quantity', 'price', 'subtotal']
    search_fields = ['order__order_number', 'product__name', 'product_name']
    readonly_fields = ['subtotal']
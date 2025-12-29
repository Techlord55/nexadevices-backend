# backend/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter
from products.views import CategoryViewSet, ProductViewSet
from users.views import UserViewSet, AddressViewSet
from orders.views import OrderViewSet
from payments.views import stripe_webhook
from users.webhooks import clerk_webhook

# API Router
router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'users', UserViewSet, basename='user')
router.register(r'addresses', AddressViewSet, basename='address')
router.register(r'orders', OrderViewSet, basename='order')

# URL Patterns
urlpatterns = [
    # Admin - Use custom URL for security
    path(settings.ADMIN_URL, admin.site.urls),
    
    # API endpoints
    path('api/', include(router.urls)),
    
    # Webhooks
    path('api/webhooks/stripe/', stripe_webhook, name='stripe-webhook'),
    path('api/webhooks/clerk/', clerk_webhook, name='clerk-webhook'),
    path('api/contact/', include('contact.urls')),
    # Health check endpoint
    path('health/', include('health.urls')),
    
    # Redirect root to API
    path('', RedirectView.as_view(url='/api/', permanent=False)),
]

# Serve media files in development only
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Add debug toolbar if installed
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

# Custom admin site configuration
admin.site.site_header = "NexaDevices Admin"
admin.site.site_title = "NexaDevices Admin Portal"
admin.site.index_title = "Welcome to NexaDevices Administration"

# Custom error handlers
handler400 = 'users.views.custom_bad_request'
handler403 = 'users.views.custom_permission_denied'
handler404 = 'users.views.custom_page_not_found'
handler500 = 'users.views.custom_server_error'
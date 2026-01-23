# products/views.py - OPTIMIZED VERSION
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db.models import Q, Prefetch
from django.core.cache import cache
from .models import Category, Product, ProductImage
from .serializers import CategorySerializer, ProductListSerializer, ProductDetailSerializer

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    authentication_classes = []  # Disable authentication for categories

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    # ✅ OPTIMIZATION 1: Use select_related and prefetch_related to reduce queries
    queryset = Product.objects.filter(is_active=True).select_related('category').prefetch_related(
        Prefetch('images', queryset=ProductImage.objects.order_by('order', 'id'))
    )
    permission_classes = [AllowAny]
    authentication_classes = []  # Disable authentication for products
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'specifications']
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductListSerializer
    
    # ✅ OPTIMIZATION 2: Cache product detail for 5 minutes
    def retrieve(self, request, *args, **kwargs):
        slug = kwargs.get('slug')
        cache_key = f'product_detail_{slug}'
        
        # Try to get from cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)
        
        # If not in cache, fetch from database
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        
        # Cache for 5 minutes (300 seconds)
        cache.set(cache_key, data, 300)
        
        return Response(data)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by category
        category_slug = self.request.query_params.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Filter by stock
        in_stock = self.request.query_params.get('in_stock')
        if in_stock == 'true':
            queryset = queryset.filter(stock__gt=0)
        
        # Featured products
        featured = self.request.query_params.get('featured')
        if featured == 'true':
            queryset = queryset.filter(featured=True)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        # ✅ OPTIMIZATION 3: Cache featured products
        cache_key = 'featured_products'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        products = self.get_queryset().filter(featured=True)[:8]
        serializer = self.get_serializer(products, many=True)
        data = serializer.data
        
        # Cache for 10 minutes
        cache.set(cache_key, data, 600)
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')
        if query:
            products = self.get_queryset().filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(category__name__icontains=query)
            )[:20]
            serializer = self.get_serializer(products, many=True)
            return Response(serializer.data)
        return Response([])

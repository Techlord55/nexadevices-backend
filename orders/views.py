# orders/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils.crypto import get_random_string
from datetime import datetime, timedelta
from .models import Order, OrderItem
from .serializers import OrderSerializer, CreateOrderSerializer
from products.models import Product
from users.models import Address
import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items')
    
    @transaction.atomic
    def create(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        items_data = serializer.validated_data['items']
        address = Address.objects.get(id=serializer.validated_data['shipping_address_id'])
        
        # Calculate totals
        subtotal = 0
        order_items = []
        
        for item_data in items_data:
            product = Product.objects.get(id=item_data['product_id'])
            quantity = item_data['quantity']
            
            if product.stock < quantity:
                return Response(
                    {'error': f'{product.name} is out of stock'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            subtotal += product.price * quantity
            order_items.append({
                'product': product,
                'quantity': quantity,
                'price': product.price
            })
        
        shipping_cost = 10.00  # Calculate based on method
        tax = subtotal * 0.08  # 8% tax
        total = subtotal + shipping_cost + tax
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            order_number=f"ORD-{get_random_string(8).upper()}",
            shipping_address=address,
            shipping_method=serializer.validated_data['shipping_method'],
            shipping_cost=shipping_cost,
            subtotal=subtotal,
            tax=tax,
            total=total,
            payment_method='card',
            estimated_delivery=datetime.now().date() + timedelta(days=3)
        )
        
        # Create order items
        for item in order_items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                product_name=item['product'].name,
                product_sku=item['product'].sku,
                price=item['price'],
                quantity=item['quantity']
            )
            
            # Update stock
            item['product'].stock -= item['quantity']
            item['product'].save()
        
        # Create Stripe payment intent
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(total * 100),  # Amount in cents
                currency='usd',
                metadata={
                    'order_id': order.id,
                    'order_number': order.order_number
                }
            )
            
            order.stripe_payment_intent = intent.id
            order.save()
            
            return Response({
                'order': OrderSerializer(order).data,
                'client_secret': intent.client_secret
            }, status=status.HTTP_201_CREATED)
            
        except stripe.error.StripeError as e:
            order.delete()
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

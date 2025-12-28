# payments/views.py
import logging
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
import stripe
from orders.models import Order

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Handle Stripe webhook events
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    if not sig_header:
        logger.warning('Missing Stripe signature header')
        return JsonResponse({'error': 'Missing signature'}, status=400)
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f'Invalid Stripe webhook payload: {str(e)}')
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f'Invalid Stripe webhook signature: {str(e)}')
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    
    # Handle the event
    event_type = event.get('type')
    logger.info(f'Received Stripe webhook event: {event_type}')
    
    try:
        if event_type == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            order_id = payment_intent.get('metadata', {}).get('order_id')
            
            if order_id:
                try:
                    order = Order.objects.get(id=order_id)
                    order.payment_status = 'paid'
                    order.status = 'processing'
                    order.save()
                    
                    logger.info(f'Payment succeeded for order {order.order_number}')
                except Order.DoesNotExist:
                    logger.error(f'Order {order_id} not found for payment_intent.succeeded')
            else:
                logger.warning('No order_id in payment_intent metadata')
        
        elif event_type == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            order_id = payment_intent.get('metadata', {}).get('order_id')
            
            if order_id:
                try:
                    order = Order.objects.get(id=order_id)
                    order.payment_status = 'failed'
                    order.save()
                    
                    logger.warning(f'Payment failed for order {order.order_number}')
                except Order.DoesNotExist:
                    logger.error(f'Order {order_id} not found for payment_intent.payment_failed')
        
        elif event_type == 'charge.refunded':
            charge = event['data']['object']
            payment_intent_id = charge.get('payment_intent')
            
            if payment_intent_id:
                try:
                    order = Order.objects.get(stripe_payment_intent=payment_intent_id)
                    order.payment_status = 'refunded'
                    order.status = 'cancelled'
                    order.save()
                    
                    logger.info(f'Refund processed for order {order.order_number}')
                except Order.DoesNotExist:
                    logger.error(f'Order not found for refunded charge')
        
        else:
            logger.info(f'Unhandled Stripe event type: {event_type}')
    
    except Exception as e:
        logger.error(f'Error processing Stripe webhook: {str(e)}', exc_info=True)
        return JsonResponse({'error': 'Processing failed'}, status=500)
    
    return HttpResponse(status=200)


@csrf_exempt
@require_POST
def create_payment_intent(request):
    """
    Create a Stripe payment intent for an order
    """
    try:
        import json
        data = json.loads(request.body)
        
        amount = data.get('amount')
        currency = data.get('currency', 'usd')
        order_id = data.get('order_id')
        
        if not amount or not order_id:
            return JsonResponse({
                'error': 'Amount and order_id are required'
            }, status=400)
        
        # Create payment intent
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Convert to cents
            currency=currency,
            metadata={'order_id': order_id},
            automatic_payment_methods={'enabled': True},
        )
        
        logger.info(f'Payment intent created: {intent.id} for order {order_id}')
        
        return JsonResponse({
            'client_secret': intent.client_secret,
            'payment_intent_id': intent.id
        })
        
    except Exception as e:
        logger.error(f'Error creating payment intent: {str(e)}', exc_info=True)
        return JsonResponse({
            'error': str(e)
        }, status=500)
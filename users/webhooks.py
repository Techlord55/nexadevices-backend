# users/webhooks.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import logging
from .models import User

logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def clerk_webhook(request):
    try:
        # Log the raw payload for debugging
        raw_body = request.body.decode('utf-8')
        logger.info(f"Received webhook payload: {raw_body}")
        
        payload = json.loads(raw_body)
        event_type = payload.get('type')
        data = payload.get('data')
        
        logger.info(f"Event type: {event_type}")
        logger.info(f"Data: {data}")
        
        if not event_type:
            logger.error("No event type found in payload")
            return JsonResponse({'error': 'No event type found'}, status=400)
        
        if not data:
            logger.error("No data found in payload")
            return JsonResponse({'error': 'No data found'}, status=400)
        
        if event_type == 'user.created':
            # Create new user
            clerk_id = data.get('id')
            
            if not clerk_id:
                logger.error("No clerk_id found in user.created event")
                return JsonResponse({'error': 'No user id found'}, status=400)
            
            # Check if user already exists
            if User.objects.filter(clerk_id=clerk_id).exists():
                logger.info(f"User with clerk_id {clerk_id} already exists, skipping creation")
                return JsonResponse({'status': 'success', 'message': 'User already exists'})
            
            email_addresses = data.get('email_addresses', [])
            email = email_addresses[0].get('email_address') if email_addresses else ''
            
            # Generate unique username
            base_username = data.get('username')
            if not base_username:
                base_username = email.split('@')[0] if email else f"user_{clerk_id[:8]}"
            
            # Ensure username is unique
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            try:
                user = User.objects.create(
                    clerk_id=clerk_id,
                    username=username,
                    email=email,
                    first_name=data.get('first_name', ''),
                    last_name=data.get('last_name', ''),
                    avatar=data.get('image_url', ''),
                )
                logger.info(f"User created: {user.username} (clerk_id: {clerk_id})")
            except Exception as e:
                logger.error(f"Error creating user: {str(e)}")
                return JsonResponse({'error': f'Failed to create user: {str(e)}'}, status=400)
            
        elif event_type == 'user.updated':
            # Update existing user
            clerk_id = data.get('id')
            
            if not clerk_id:
                logger.error("No clerk_id found in user.updated event")
                return JsonResponse({'error': 'No user id found'}, status=400)
            
            try:
                user = User.objects.get(clerk_id=clerk_id)
                email_addresses = data.get('email_addresses', [])
                
                if data.get('username'):
                    user.username = data.get('username')
                if email_addresses:
                    user.email = email_addresses[0].get('email_address', user.email)
                if data.get('first_name'):
                    user.first_name = data.get('first_name')
                if data.get('last_name'):
                    user.last_name = data.get('last_name')
                if data.get('image_url'):
                    user.avatar = data.get('image_url')
                
                user.save()
                logger.info(f"User updated: {user.username}")
            except User.DoesNotExist:
                logger.warning(f"User with clerk_id {clerk_id} not found for update")
                
        elif event_type == 'user.deleted':
            # Handle user deletion
            clerk_id = data.get('id')
            
            if not clerk_id:
                logger.error("No clerk_id found in user.deleted event")
                return JsonResponse({'error': 'No user id found'}, status=400)
            
            try:
                user = User.objects.get(clerk_id=clerk_id)
                user.is_active = False
                user.save()
                logger.info(f"User deactivated: {user.username}")
            except User.DoesNotExist:
                logger.warning(f"User with clerk_id {clerk_id} not found for deletion")
        
        else:
            logger.warning(f"Unhandled event type: {event_type}")
        
        return JsonResponse({'status': 'success'})
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=400)
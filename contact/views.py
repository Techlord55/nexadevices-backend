# backend/contact/views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from .models import ContactMessage
from .serializers import ContactMessageSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def contact_submit(request):
    serializer = ContactMessageSerializer(data=request.data)
    
    if serializer.is_valid():
        # Save to database
        contact_message = serializer.save()
        
        # Send email notification
        try:
            send_mail(
                subject=f'New Contact Form: {contact_message.subject}',
                message=f'''
New contact form submission:

From: {contact_message.name}
Email: {contact_message.email}
Subject: {contact_message.subject}

Message:
{contact_message.message}

---
Submitted at: {contact_message.created_at.strftime('%Y-%m-%d %H:%M:%S')}
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_EMAIL],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Email sending failed: {e}")
            # Still return success since message was saved
        
        return Response(
            {'message': 'Message sent successfully!'},
            status=status.HTTP_201_CREATED
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

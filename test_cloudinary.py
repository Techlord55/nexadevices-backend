#!/usr/bin/env python
"""
Test Cloudinary configuration and upload
Run: python test_cloudinary.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

import cloudinary
import cloudinary.uploader
from django.conf import settings

def test_cloudinary():
    print("\n" + "="*60)
    print("🧪 Testing Cloudinary Configuration")
    print("="*60)
    
    # Check configuration
    print(f"\n✓ Cloud Name: {settings.CLOUDINARY_STORAGE['CLOUD_NAME']}")
    print(f"✓ API Key: {settings.CLOUDINARY_STORAGE['API_KEY'][:10]}...")
    print(f"✓ Storage Backend: {settings.DEFAULT_FILE_STORAGE}")
    
    # Test upload with a simple text file
    print("\n📤 Testing upload to Cloudinary...")
    try:
        # Create a temporary test file
        test_content = b"Cloudinary Test - If you see this in your Cloudinary dashboard, it works!"
        
        result = cloudinary.uploader.upload(
            test_content,
            folder='nexadevices/test',
            resource_type='raw',
            public_id='connection_test'
        )
        
        print(f"\n✅ SUCCESS! Upload completed!")
        print(f"📎 URL: {result['secure_url']}")
        print(f"📁 Public ID: {result['public_id']}")
        print(f"📦 Resource Type: {result['resource_type']}")
        
        # Try to delete the test file
        cloudinary.uploader.destroy(result['public_id'], resource_type='raw')
        print("\n🗑️  Test file cleaned up from Cloudinary")
        
        print("\n" + "="*60)
        print("✨ Cloudinary is working perfectly!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\nCheck your Cloudinary credentials in .env file:")
        print("  - CLOUDINARY_CLOUD_NAME")
        print("  - CLOUDINARY_API_KEY")
        print("  - CLOUDINARY_API_SECRET")

if __name__ == '__main__':
    test_cloudinary()
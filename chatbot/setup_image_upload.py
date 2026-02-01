#!/usr/bin/env python
"""
Setup script for image upload feature
Run this after installing dependencies
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatbot.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.core.management import call_command

print("=" * 60)
print("IMAGE UPLOAD FEATURE SETUP")
print("=" * 60)

print("\n1. Creating migrations for Message.image field...")
try:
    call_command('makemigrations', 'chats')
    print("   ✓ Migrations created")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n2. Applying migrations to database...")
try:
    call_command('migrate')
    print("   ✓ Migrations applied")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n3. Creating media directory for temporary images...")
try:
    media_root = os.path.join(os.path.dirname(__file__), 'media')
    os.makedirs(media_root, exist_ok=True)
    os.makedirs(os.path.join(media_root, 'temp_images'), exist_ok=True)
    print(f"   ✓ Created {media_root}")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "=" * 60)
print("SETUP COMPLETE!")
print("=" * 60)
print("\nNext steps:")
print("1. Install Pillow: pip install Pillow")
print("2. Restart your Django development server")
print("3. Test by uploading an image in the chat interface")

"""
Simple script to create media directories
Run with: python setup_media.py
"""
import os
from pathlib import Path

# Get the base directory
BASE_DIR = Path(__file__).resolve().parent

# Create media directory
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_ROOT.mkdir(exist_ok=True)
print(f"✓ Created/verified: {MEDIA_ROOT}")

# Create products subdirectory
PRODUCTS_DIR = MEDIA_ROOT / 'products'
PRODUCTS_DIR.mkdir(exist_ok=True)
print(f"✓ Created/verified: {PRODUCTS_DIR}")

# Create profile_images subdirectory
PROFILE_DIR = MEDIA_ROOT / 'profile_images'
PROFILE_DIR.mkdir(exist_ok=True)
print(f"✓ Created/verified: {PROFILE_DIR}")

print("\n✅ Media directory structure created successfully!")
print(f"\nYour media files will be stored in: {MEDIA_ROOT}")

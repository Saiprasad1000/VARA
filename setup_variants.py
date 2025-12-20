"""
Setup script to create Gold and Black frame variants
Run this with: python setup_variants.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Vara.settings')
django.setup()

from Admin.models import Variant

def create_variants():
    """Create Gold and Black frame variants"""
    
    # Create Gold frame variant
    gold_variant, gold_created = Variant.objects.get_or_create(
        variant_type='gold',
        defaults={
            'price': 1000.00,
            'stock': 100,
            'isListed': True
        }
    )
    
    if gold_created:
        print("✅ Created Gold frame variant")
        print(f"   - Price: ₹{gold_variant.price}")
        print(f"   - Stock: {gold_variant.stock}")
    else:
        print("ℹ️  Gold frame variant already exists")
        print(f"   - ID: {gold_variant.id}")
        print(f"   - Price: ₹{gold_variant.price}")
        print(f"   - Stock: {gold_variant.stock}")
    
    # Create Black frame variant
    black_variant, black_created = Variant.objects.get_or_create(
        variant_type='black',
        defaults={
            'price': 800.00,
            'stock': 100,
            'isListed': True
        }
    )
    
    if black_created:
        print("✅ Created Black frame variant")
        print(f"   - Price: ₹{black_variant.price}")
        print(f"   - Stock: {black_variant.stock}")
    else:
        print("ℹ️  Black frame variant already exists")
        print(f"   - ID: {black_variant.id}")
        print(f"   - Price: ₹{black_variant.price}")
        print(f"   - Stock: {black_variant.stock}")
    
    print("\n" + "="*50)
    print("🎉 Variants Setup Complete!")
    print("="*50)
    
    # Show all active variants
    all_variants = Variant.objects.filter(isListed=True)
    print(f"\nTotal Active Variants: {all_variants.count()}")
    for variant in all_variants:
        print(f"  - {variant.variant_type}: ₹{variant.price} (Stock: {variant.stock})")
    
    print("\n✨ Gold and Black frames are now available for all products!")
    print("   They will appear on the product detail page automatically.")

if __name__ == '__main__':
    try:
        create_variants()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

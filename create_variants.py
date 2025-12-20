# Run this inside Django shell: python manage.py shell
# Then paste this code

from Admin.models import Variant

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
    print("✅ Created Gold frame variant (Price: ₹1000, Stock: 100)")
else:
    print(f"ℹ️  Gold frame already exists (ID: {gold_variant.id}, Price: ₹{gold_variant.price})")

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
    print("✅ Created Black frame variant (Price: ₹800, Stock: 100)")
else:
    print(f"ℹ️  Black frame already exists (ID: {black_variant.id}, Price: ₹{black_variant.price})")

print("\n🎉 Setup Complete!")
print(f"Total active variants: {Variant.objects.filter(isListed=True).count()}")
for v in Variant.objects.filter(isListed=True):
    print(f"  - {v.variant_type}: ₹{v.price} (Stock: {v.stock})")

"""
Script to create Gold and Black frame variants for all products
Run this in Django shell: python manage.py shell
Then: exec(open('create_product_variants.py').read())
"""

from Admin.models import Product, Variant

def create_variants_for_all_products():
    """Create Gold and Black variants for each product"""
    
    products = Product.objects.filter(is_deleted=False)
    total_products = products.count()
    
    print(f"Found {total_products} active products")
    print("="*50)
    
    created_count = 0
    
    for product in products:
        print(f"\nProduct: {product.title} (ID: {product.id})")
        
        # Create Gold variant for this product
        gold_variant, gold_created = Variant.objects.get_or_create(
            product=product,
            variant_type='gold',
            defaults={
                'price': product.price + 200,  # Gold frame adds ₹200
                'stock': 50,
                'isListed': True
            }
        )
        
        if gold_created:
            print(f"  ✅ Created Gold variant (₹{gold_variant.price})")
            created_count += 1
        else:
            print(f"  ℹ️  Gold variant exists (₹{gold_variant.price})")
        
        # Create Black variant for this product
        black_variant, black_created = Variant.objects.get_or_create(
            product=product,
            variant_type='black',
            defaults={
                'price': product.price,  # Black frame same as product price
                'stock': 50,
                'isListed': True
            }
        )
        
        if black_created:
            print(f"  ✅ Created Black variant (₹{black_variant.price})")
            created_count += 1
        else:
            print(f"  ℹ️  Black variant exists (₹{black_variant.price})")
    
    print("\n" + "="*50)
    print(f"🎉 Complete! Created {created_count} new variants")
    print(f"Total variants in database: {Variant.objects.count()}")
    print("\n✨ All products now have Gold and Black frame options!")

# Run the function
create_variants_for_all_products()

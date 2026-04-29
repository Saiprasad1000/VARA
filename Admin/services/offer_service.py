from django.utils import timezone
from Admin.models import Offer
from decimal import Decimal

def get_best_offer(product, variant=None):
    """
    Calculates the best possible discount from all active offers 
    applicable to a product, its category, or its variant.
    
    Returns a dict containing:
        - best_offer: The Offer model instance (or None)
        - discount_amount: Decimal amount of the highest discount
        - final_price: Decimal price after applying the discount
    """
    price = variant.price if variant else product.price
    price = Decimal(str(price))
    
    now = timezone.now()
    
    # Base query for active offers within validity dates
    active_offers = Offer.objects.filter(
        is_active=True,
        start_date__lte=now,
        end_date__gte=now,
    ).prefetch_related('products', 'categories', 'variants')
    
    # We will accumulate all offers that apply
    applicable_offers = set()
    
    # Evaluate which offers apply based on relations
    for offer in active_offers:
        # Category match
        if offer.categories.filter(id=product.category.id).exists():
            applicable_offers.add(offer)
        # Product match
        elif offer.products.filter(id=product.id).exists():
            applicable_offers.add(offer)
        # Variant match
        elif variant and offer.variants.filter(id=variant.id).exists():
            applicable_offers.add(offer)
            
    best_offer = None
    max_discount_amount = Decimal('0.00')
    
    for offer in applicable_offers:
        discount = Decimal('0.00')
        if offer.offer_type == 'Percentage':
            discount = (Decimal(str(offer.value)) / Decimal('100.0')) * price
        elif offer.offer_type == 'Flat':
            discount = Decimal(str(offer.value))
            
        # Cap the discount strictly at the base price
        if discount > price:
            discount = price
            
        # Select the offer giving the highest benefit
        if discount > max_discount_amount:
            max_discount_amount = discount
            best_offer = offer
            
    final_price = price - max_discount_amount
    
    return {
        'best_offer': best_offer,
        'discount_amount': round(max_discount_amount, 2),
        'final_price': round(final_price, 2),
        'original_price': round(price, 2)
    }

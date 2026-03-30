from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from Admin.models import Product, Variant

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email must be provided")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=15, unique=True,blank=True, null=True)
    referral_code = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    pro_image = models.ImageField(upload_to='profile_images/', blank=True, null=True,max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'mobile']

    def __str__(self):
        return self.email



class Cart(models.Model):
    user = models.OneToOneField(CustomUser,on_delete=models.CASCADE,related_name='cart',null=True,blank=True)
    session_key = models.CharField(max_length=40,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
     
    class Meta:
        db_table = 'cart' 
    
    def __str__(self):
        if self.user:
            return f'Cart for {self.user.email}'
        else:
            return f'Cart for session {self.session_key}'
    

    def get_total(self):
        return sum(item.get_subtotal() for item in self.items.all())
    
    def get_item_count(self):
        return sum(item.quantity for item in self.items.all())


class CartItems(models.Model):
    cart = models.ForeignKey(Cart,on_delete=models.CASCADE,related_name='items')
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    varient=models.ForeignKey(Variant,on_delete=models.CASCADE,null=True,blank=True)
    quantity=models.IntegerField(default=1)
    added_at=models.DateTimeField(auto_now_add=True)


    class Meta:
        db_table = 'cart_items'
        unique_together = ('cart', 'product', 'varient')
    
    
    def __str__(self):
        return f"{self.quantity} x {self.product.title}"

    def get_subtotal(self):
        if self.varient:
            return self.varient.price * self.quantity
        else:
            return self.product.price * self.quantity
    def get_price(self):
        if self.varient:
            return self.varient.price
        else:
            return self.product.price   

class Wishlist(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='wishlist', null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
     
    class Meta:
        db_table = 'wishlist' 
    
    def __str__(self):
        if self.user:
            return f'Wishlist for {self.user.email}'
        else:
            return f'Wishlist for session {self.session_key}'
    
    def get_item_count(self):
        """Get total number of items in wishlist"""
        return self.items.count()


class WishlistItems(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    varient = models.ForeignKey(Variant, on_delete=models.CASCADE, null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wishlist_items'
        unique_together = ('wishlist', 'product', 'varient')
    
    def __str__(self):
        return f"{self.product.title}"


class Address(models.Model):
    ADDRESS_TYPE_CHOICES = (
        ('Home', 'Home'),
        ('Work', 'Work'),
    )
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='addresses')
    name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15)
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPE_CHOICES, default='Home')
    is_default = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.name} - {self.city}"
    
    def save(self, *args, **kwargs):
        # If set as default, unset other default addresses for this user
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancel Requested', 'Cancel Requested'),
        ('Cancelled', 'Cancelled'),
        ('Return Requested', 'Return Requested'),
        ('Returned', 'Returned'),
    )
    
    # Status progression priority (lower = earlier in pipeline)
    STATUS_PRIORITY = {
        'Pending': 1,
        'Confirmed': 2,
        'Shipped': 3,
        'Delivered': 4,
        'Cancel Requested': 5,
        'Cancelled': 6,
        'Return Requested': 7,
        'Returned': 8,
    }
    
    # Strict status transition map for state machine
    VALID_TRANSITIONS = {
        'Pending': ['Confirmed', 'Cancel Requested', 'Cancelled'],
        'Confirmed': ['Shipped', 'Cancel Requested', 'Cancelled'],
        'Shipped': ['Delivered'],
        'Delivered': ['Return Requested', 'Returned'],
        'Cancel Requested': ['Cancelled', 'Pending', 'Confirmed'], # Can approve (Cancelled) or reject (Pending/Confirmed)
        'Cancelled': [],
        'Return Requested': ['Returned', 'Delivered'], # Can approve (Returned) or reject (Delivered)
        'Returned': [],
    }
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='orders')
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, default='COD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    
    # Razorpay fields
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    
    PAYMENT_STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Failed', 'Failed'),
        ('Payment Pending', 'Payment Pending'),
    )
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order #{self.id} by {self.user.email}"
    
    @classmethod
    def is_valid_transition(cls, from_status, to_status):
        """Check if a status transition is allowed."""
        return to_status in cls.VALID_TRANSITIONS.get(from_status, [])
    
    def sync_status_from_items(self):
        """Recalculate order status based on aggregated item statuses."""
        items = self.items.all()
        if not items.exists():
            return
        
        active_items = items.exclude(status__in=['Cancelled', 'Returned'])
        
        if not active_items.exists():
            # All items are in terminal states
            all_returned = not items.exclude(status='Returned').exists()
            self.status = 'Returned' if all_returned else 'Cancelled'
            self.save(update_fields=['status'])
            return
        
        # Order status = lowest-progress active item
        active_statuses = list(active_items.values_list('status', flat=True))
        lowest_status = min(
            active_statuses,
            key=lambda s: self.STATUS_PRIORITY.get(s, 0)
        )
        self.status = lowest_status
        self.save(update_fields=['status'])


class OrderItem(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancel Requested', 'Cancel Requested'),
        ('Cancelled', 'Cancelled'),
        ('Return Requested', 'Return Requested'),
        ('Returned', 'Returned'),
    )
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(Variant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    return_reason = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.quantity} x {self.product.title}"
    
    def get_subtotal(self):
        return self.price * self.quantity

class Wallet(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wallet for {self.user.email} - Balance: ₹{self.balance}"

    def credit(self, amount, description, order=None):
        from decimal import Decimal
        amount = Decimal(str(amount))
        self.balance += amount
        self.save(update_fields=['balance', 'updated_at'])
        WalletTransaction.objects.create(
            wallet=self,
            transaction_type='Credit',
            amount=amount,
            description=description,
            order=order
        )

    def debit(self, amount, description, order=None):
        from decimal import Decimal
        amount = Decimal(str(amount))
        if self.balance >= amount:
            self.balance -= amount
            self.save(update_fields=['balance', 'updated_at'])
            WalletTransaction.objects.create(
                wallet=self,
                transaction_type='Debit',
                amount=amount,
                description=description,
                order=order
            )
            return True
        return False

class WalletTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('Credit', 'Credit'),
        ('Debit', 'Debit'),
    )
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} of ₹{self.amount} - {self.description}"
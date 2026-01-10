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
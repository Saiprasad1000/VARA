from django.db import models

# Create your models here.
from django.utils import timezone



class Category(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    isListed = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'category'
        ordering = ['name']

    def __str__(self):
        return self.name



class Variant(models.Model):
    id = models.AutoField(primary_key=True)
    variant_type = models.CharField(max_length=150)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    isListed = models.BooleanField(default=True)

    class Meta:
        db_table = 'variant'
        ordering = ['variant_type']

    def __str__(self):
        return f"{self.variant_type}"



class Product(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products'
    )
    variant = models.ForeignKey(
        Variant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )

    artist_name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available_quantity = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    publishing_date = models.DateField()
    product_imgs = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'product'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.category.name})"


class Offer(models.Model):
    product_name = models.CharField(max_length=255)
    category_name = models.CharField(max_length=255)
    discount = models.IntegerField()
    is_listed = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'offer'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product_name} - {self.discount}%"





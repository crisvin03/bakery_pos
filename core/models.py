from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date

class Product(models.Model):
    name = models.CharField(max_length=160)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    ingredients = models.TextField(blank=True)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False, help_text="Archived products are hidden from normal view but can be restored")
    expiration_date = models.DateField(blank=True, null=True, help_text="Product expiration date")

    # Product image (stored under MEDIA_ROOT/products/)
    image = models.ImageField(upload_to="products/", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def get_expiration_status(self):
        """Returns expiration status: 'expired', 'today', 'future', or None"""
        if not self.expiration_date:
            return None
        today = date.today()
        if self.expiration_date < today:
            return 'expired'
        elif self.expiration_date == today:
            return 'today'
        else:
            return 'future'
    
    def is_expired(self):
        """Returns True if product is expired"""
        if not self.expiration_date:
            return False
        return self.expiration_date < date.today()
    
    def is_available_for_sale(self):
        """Returns True if product can be sold (active, in stock, not expired, and not archived)"""
        return self.is_active and self.stock > 0 and not self.is_expired() and not self.is_archived()


class SalesTransaction(models.Model):
    PAYMENT_METHODS = (
        ('CASH', 'Cash'),
    )
    cashier = models.ForeignKey(User, on_delete=models.PROTECT, related_name='sales')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='CASH')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sale #{self.pk} - {self.created_at:%Y-%m-%d %H:%M}"


class SalesItem(models.Model):
    sale = models.ForeignKey(SalesTransaction, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    qty = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product} x {self.qty}"


class LoginHistory(models.Model):
    """Track login history for cashiers and admins"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_history')
    login_time = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-login_time']
        verbose_name_plural = 'Login Histories'
    
    def __str__(self):
        return f"{self.user.username} - {self.login_time.strftime('%Y-%m-%d %H:%M:%S')}"


class UserProfile(models.Model):
    """Extended user profile with profile picture"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    @property
    def get_profile_picture_url(self):
        """Returns the profile picture URL or None"""
        if self.profile_picture:
            return self.profile_picture.url
        return None

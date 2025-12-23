from django.contrib import admin
from .models import Product, SalesTransaction, SalesItem, LoginHistory, UserProfile

class SalesItemInline(admin.TabularInline):
    model = SalesItem
    extra = 0

@admin.register(SalesTransaction)
class SalesTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'cashier', 'total_amount', 'discount', 'payment_method', 'created_at')
    inlines = [SalesItemInline]

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name',)

@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'login_time', 'ip_address', 'logout_time']
    list_filter = ['login_time', 'user']
    search_fields = ['user__username', 'ip_address']
    readonly_fields = ['login_time', 'ip_address', 'user_agent']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'updated_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']

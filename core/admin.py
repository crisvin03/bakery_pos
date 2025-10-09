from django.contrib import admin
from .models import Product, SalesTransaction, SalesItem

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

from django.contrib import admin
from .models import Category, Product, ProductImage, ProductVariant, Reviews, Order, OrderItem

# Register your models here.

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'base_price', 'is_activate', 'created_at')
    list_filter = ('category', 'is_activate', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'is_feature')
    list_filter = ('is_feature', 'product')

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'color', 'size', 'stock')
    list_filter = ('product', 'color', 'size')
    search_fields = ('product__name',)

@admin.register(Reviews)
class ReviewsAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at', 'product')
    search_fields = ('product__name', 'user__username', 'comment')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'full_name', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('full_name', 'address', 'user__username')
    readonly_fields = ('created_at',)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'variant', 'quantity', 'price')
    list_filter = ('order', 'variant__product')
    search_fields = ('order__full_name', 'variant__product__name')
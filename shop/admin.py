from django.contrib import admin
from .models import (
    Product, ProductVariant, CartItem, Comment, Order, OrderItem, Feedback,
    ProductColor, CarouselImage, Coupon
)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_featured', 'is_flash_sale', 'flash_percent', 'flash_from', 'flash_to')
    list_filter = ('category', 'is_featured', 'is_flash_sale')
    search_fields = ('name',)
    fieldsets = (
        (None, {"fields": ("name", "description", "category", "image", "is_featured", "stock")}),
        ("Flash Sale", {"fields": ("is_flash_sale", "flash_percent", "flash_from", "flash_to")}),
    )

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'storage', 'price', 'stock', 'flash_badge', 'price_after_flash')
    list_filter = ('storage', 'product__category')
    search_fields = ('product__name',)

    def flash_badge(self, obj):
        return "✅" if obj.is_flash_sale else "—"
    flash_badge.short_description = "Flash Sale"

    def price_after_flash(self, obj):
        return obj.discounted_price()
    price_after_flash.short_description = "Giá sau giảm"

admin.site.register(CartItem)
admin.site.register(Comment)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Feedback)

@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ['product', 'name']
    list_filter = ['product']

@admin.register(CarouselImage)
class CarouselImageAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("title", "caption")

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount', 'valid_from', 'valid_to', 'active')
    search_fields = ('code',)
    list_filter = ('active', 'valid_from', 'valid_to')

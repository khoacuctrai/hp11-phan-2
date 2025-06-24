from django.contrib import admin
from .models import Product, ProductVariant, CartItem, Comment, Order, OrderItem, Feedback,ProductColor

# Quản lý sản phẩm chính
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_featured')
    list_filter = ('category', 'is_featured')
    search_fields = ('name',)

# Quản lý cấu hình dung lượng (chỉ iPhone và MacBook)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'storage', 'price')
    list_filter = ('storage',)
    search_fields = ('product__name',)

# Đăng ký các model với admin
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductVariant, ProductVariantAdmin)
admin.site.register(CartItem)
admin.site.register(Comment)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Feedback)

@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ['product', 'name']
    list_filter = ['product']
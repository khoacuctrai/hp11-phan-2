from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

#định nghĩa cấu trúc dữ liệu
# Loại sản phẩm
CATEGORY_CHOICES = [
    ('iphone', 'iPhone'),
    ('macbook', 'MacBook'),
    ('ipad', 'iPad'),
    ('watch', 'Watch'),
    ('audio', 'Tai nghe, loa'),
    ('accessory', 'Phụ kiện'),
]

# ------------------------------
# 🟩 Sản phẩm
# ------------------------------
class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    stock = models.PositiveIntegerField(default=0)
    def __str__(self):
        return self.name

    def has_variants(self):
        return self.category in dict(CATEGORY_CHOICES)

    def display_price(self):
        first_variant = self.variants.first()
        return first_variant.price if first_variant else 0


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    storage = models.CharField(max_length=200)
    price = models.IntegerField()    # Sửa từ FloatField thành IntegerField
    color = models.ForeignKey('ProductColor', on_delete=models.CASCADE, related_name='variants', null=True, blank=True)

    def __str__(self):
        return f"{self.product.name} - {self.storage} - {self.color.name if self.color else 'No color'}"


class ProductColor(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='colors')
    name = models.CharField(max_length=50)  # ví dụ: "Đen", "Trắng", "Xanh"
    image = models.ImageField(upload_to='product_colors/')  # ảnh ứng với màu

    def __str__(self):
        return f"{self.product.name} - {self.name}"


# ------------------------------
# 🟩 Giỏ hàng
# ------------------------------
class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    def get_price(self):
        return self.variant.price if self.variant else 0

    def get_total(self):
        return self.get_price() * self.quantity

    def __str__(self):
        variant_info = f" ({self.variant.storage})" if self.variant else ""
        return f"{self.product.name}{variant_info} x {self.quantity} ({self.user.username})"


# ------------------------------
# 🟩 Bình luận và phản hồi
# ------------------------------
class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    content = models.TextField()
    likes = models.IntegerField(default=0)
    dislikes = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)  # ✅ thêm dòng này
    @property
    def total_likes(self):
        return self.likes

    @property
    def total_dislikes(self):
        return self.dislikes



class CommentReaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='reactions')
    REACTION_CHOICES = [('like', 'Like'), ('dislike', 'Dislike')]
    reaction = models.CharField(max_length=10, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'comment')  # Một người chỉ được phản ứng 1 lần

    def __str__(self):
        return f"{self.user.username} {self.reaction} on comment {self.comment.id}"


# ------------------------------
# 🟩 Đơn hàng
# ------------------------------
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)

    # Thông tin người nhận
    full_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def total_price(self):
        return sum(item.total() for item in self.items.all())

    def __str__(self):
        return f"Đơn hàng #{self.id} của {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    def total(self):
        return (self.variant.price if self.variant else 0) * self.quantity

    def __str__(self):
        variant_info = f" ({self.variant.storage})" if self.variant else ""
        return f"{self.product.name}{variant_info} x {self.quantity}"






# ------------------------------
# 🟩 Góp ý / Khiếu nại
# ------------------------------
class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks')
    message = models.TextField()
    is_complaint = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        label = "Khiếu nại" if self.is_complaint else "Góp ý"
        return f"{label} từ {self.user.username}"




class CarouselImage(models.Model):
    title = models.CharField("Tiêu đề", max_length=100, blank=True)
    image = models.ImageField("Ảnh", upload_to='carousel/')
    caption = models.CharField("Chú thích", max_length=255, blank=True)
    is_active = models.BooleanField("Hiển thị", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title or f"Ảnh #{self.id}"

from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

# Create your models here.
class ShippingProvince(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Tên tỉnh/thành")
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=0, default=30000)

    def __str__(self):
        return f"{self.name} - {self.shipping_fee}đ"
class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)


    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_activate = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Giá khuyến mãi")

    @property
    def current_price(self):
        """Trả về giá thực tế khách phải trả"""
        if self.sale_price and self.sale_price > 0:
            return self.sale_price
        return self.base_price

    @property
    def discount_percent(self):
        """Tính % giảm giá"""
        if self.sale_price and self.base_price > 0:
            discount = ((self.base_price - self.sale_price) / self.base_price) * 100
            return int(discount)
        return 0
    def __str__(self):
        return self.name
    def get_feature_image(self):
        return self.images.filter(is_feature=True).first()

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to='products/')
    is_feature = models.BooleanField(default=False)  # check coi có phải ảnh đại diện hông nếu đúng thì tích


# 4. Biến thể sản phẩm (Giải quyết yêu cầu: Nhiều Size, Nhiều Màu)
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    color = models.CharField(max_length=50)  # VD: Đỏ
    size = models.CharField(max_length=20)  # VD: XL
    stock = models.PositiveIntegerField(default=0)  # Số lượng tồn kho cho size/màu này

    def __str__(self):
        return f"{self.product.name} - {self.color} - {self.size}"



class Order(models.Model):
    PAYMENT_METHODS = (
        ('cod', 'Thanh toán khi nhận hàng'),
        ('qr', 'Chuyển khoản qua mã QR'),
    )
    STATUS_CHOICES = (
        ('pending', 'Chờ xác nhận'),
        ('confirmed', 'Đã xác nhận'),
        ('shipping', 'Đang giao hàng'),
        ('delivered', 'Đã giao thành công'),
        ('cancelled', 'Đã hủy'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, default='cod')
    # Tiền hàng (chưa ship)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, db_column='total_amount')

    # Phí vận chuyển theo tỉnh thành
    province = models.ForeignKey(ShippingProvince, on_delete=models.SET_NULL, null=True, blank=True)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    voucher = models.ForeignKey('Voucher', on_delete=models.SET_NULL, null=True, blank=True)
    voucher_discount = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    order_code = models.CharField(max_length=10, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    items_json = models.TextField()
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, db_column='phone')
    address = models.TextField()
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Order {self.order_code} - {self.user.username}"

    # Hàm tính tổng cuối cùng để quét mã QR và hiển thị
    @property
    def final_total(self):
        return self.total_price + self.shipping_fee


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    # Giải quyết lỗi "Thành tiền" trong bảng sản phẩm
    @property
    def total_item_price(self):
        return self.price * self.quantity
class Reviews(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    rating = models.IntegerField(default=5)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.name} - {self.rating}⭐"
from django.utils import timezone

class Voucher(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=0) # Số tiền giảm (ví dụ: 50000)
    min_order_value = models.DecimalField(max_digits=10, decimal_places=0, default=0) # Đơn tối thiểu
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField()
    active = models.BooleanField(default=True)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return self.code

from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout  # Import thêm cái này để đăng nhập luôn
from .forms import CustomerSignupForm  # Import cái Form bạn vừa tạo
from .models import Product, ProductImage, Reviews
from django.db.models import Q
#phân trang
from django.core.paginator import Paginator

import os
import gdown
import pickle
import pandas as pd
from django.conf import settings
from django.contrib.auth.decorators import login_required


def signup_view(request):
    if request.method == 'POST':
        form = CustomerSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            # Tạo riêng một mã giảm giá cho khách mới này (ví dụ giảm 10%)
            Voucher.objects.create(
                code=f"WELCOME_{user.username.upper()}",
                discount_amount=30000,
                min_order_value=0,
                valid_to=timezone.now() + timezone.timedelta(days=30),
                is_used=False,
                active=True
            )

            messages.success(request, "Đăng ký thành công! Bạn nhận được mã giảm giá WELCOME dành riêng cho bạn.")
            return redirect('home')
    else:
        # 5. Khi khách mới vào trang, hiện form trống
        form = CustomerSignupForm()

    return render(request, 'app/signup.html', {'form': form})
def logout_view(request):
    logout(request) # Xóa sạch session và user đang đăng nhập
    return redirect('home')
def home(request):
    products_news = Product.objects.all().order_by('-id')[:4]
    sale_products = Product.objects.filter(sale_price__gt=0, is_activate=True).order_by('-created_at')[:4]
    products = Product.objects.filter(is_activate=True).prefetch_related('images').order_by('?')[:4]
    return render(request, 'app/home.html', {
        'products': products,
        'products_news': products_news,
        'sale_products' : sale_products
    })
def search(request):
    query = request.GET.get('q', '')
    result = Product.objects.none()
    if query:
        result = Product.objects.filter(name__icontains=query).distinct()
    return render(request, 'app/search.html', {
        'result': result
    })
def category(request):
    query = request.GET.get('c', '')

    if query == 'all' or not query:
        result_list = Product.objects.filter(is_activate=True)
    else:
        result_list = Product.objects.filter(
            category__name__icontains=query,
            is_activate=True
        ).distinct()
    # Sắp xếp và tối ưu query ảnh
    result_list = result_list.prefetch_related('images').order_by('-id')
    paginator = Paginator(result_list, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'app/search.html', {
        'result': page_obj,
        'query': query  # Gửi biến này để template dùng trong link phân trang
    })
def product_view(request):
    return render(request, 'app/productview.html',{})


# def product_detail(request, pk):
#     product = get_object_or_404(Product, pk=pk)
#     return render(request, 'app/product_detail.html', {
#         'product': product
#     })
#thêm tại đây
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)

    # 🔥 LẤY TÊN GỢI Ý TỪ MODEL
    rec_names = get_recommend_products(product.name, top_k=10)

    # 🔥 CHỈ LẤY NHỮNG SẢN PHẨM CÓ TRONG DB
    recommend_products = Product.objects.filter(name__in=rec_names)
    can_review = False
    if request.user.is_authenticated:
        # Kiểm tra xem user đã nhận hàng thành công sản phẩm này chưa
        has_purchased = OrderItem.objects.filter(
            order__user=request.user,
            order__status='delivered',
            variant__product=product
        ).exists()

        # 2. Kiểm tra xem đã đánh giá sản phẩm này TRƯỚC ĐÓ chưa
        already_reviewed = Reviews.objects.filter(
            user=request.user,
            product=product
        ).exists()

        # ĐIỀU KIỆN: Đã mua + Chưa đánh giá
        if has_purchased and not already_reviewed:
            can_review = True

    return render(request, 'app/product_detail.html', {
        'product': product,
        'recommend_products': recommend_products,
        'can_review': can_review,
    })


def cart(request):
    cart_session = request.session.get('cart', {})
    cart_items = []
    order_history = []
    if request.user.is_authenticated:
        order_history = Order.objects.filter(user=request.user).order_by('-created_at')

    total_price = 0
    for key, item in cart_session.items():
        try:
            product = Product.objects.get(id=item['product_id'])
            unit_price = float(product.current_price)
            total_item_price = unit_price * item['quantity']
            total_price += total_item_price

            variant = ProductVariant.objects.filter(product=product, color=item['color'], size=item['size']).first()
            cart_items.append({
                'key': key,
                'product': product,
                'quantity': item['quantity'],
                'color': item['color'],
                'size': item['size'],
                'unit_price': unit_price,
                'total_item_price': total_item_price,
                'variant_stock': variant.stock if variant else 0,
            })
        except (Product.DoesNotExist, ValueError):
            continue

    # --- LOGIC VOUCHER TẠI GIỎ HÀNG ---
    voucher_discount = request.session.get('voucher_discount', 0)
    voucher_code = request.session.get('voucher_code')

    # Kiểm tra lại điều kiện đơn hàng tối thiểu nếu đang có voucher
    if voucher_code:
        try:
            v = Voucher.objects.get(code=voucher_code, active=True)
            if total_price < float(v.min_order_value):
                # Nếu tổng tiền sau khi xóa/giảm sp không đủ đk voucher
                voucher_discount = 0
                del request.session['voucher_discount']
                del request.session['voucher_code']
                messages.warning(request, f"Mã {voucher_code} đã bị gỡ do đơn hàng chưa đạt {v.min_order_value:,.0f}đ")
        except Voucher.DoesNotExist:
            pass

    total_after_discount = max(0, total_price - voucher_discount)

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'voucher_discount': voucher_discount,
        'total_after_discount': total_after_discount,
        'order_history': order_history
    }
    return render(request, 'app/cart.html', context)

@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.status == 'pending':
        # TRUY VẤN TRỰC TIẾP ORDERITEM ĐỂ ĐẢM BẢO CHÍNH XÁC
        items = OrderItem.objects.filter(order=order)

        for item in items:
            variant = item.variant
            if variant:
                # Cộng lại số lượng vào kho
                variant.stock += item.quantity
                variant.save()

        # Cập nhật trạng thái đơn hàng
        order.status = 'cancelled'
        order.save()
        messages.success(request,
                         f"Đã hủy thành công đơn hàng #{order.order_code} và hoàn trả {items.count()} mặt hàng vào kho.")
    else:
        messages.error(request, "Không thể hủy đơn hàng này.")

    return redirect('cart')
def remove_cart(request, key):
    cart = request.session.get('cart', {})
    if key in cart:
        del cart[key]
        request.session['cart'] = cart
        request.session.modified = True
    return redirect('cart')


def update_cart(request, key, action):
    cart = request.session.get('cart', {})
    if key in cart:
        product_id = cart[key]['product_id']
        variant_id = cart[key]['variant_id']
        variant = get_object_or_404(ProductVariant, id=variant_id)

        if action == 'increase':
            # Check kho trước khi cho tăng
            if variant.stock > cart[key]['quantity']:
                cart[key]['quantity'] += 1
            else:
                messages.warning(request, "Số lượng trong kho đã đạt giới hạn tối đa.")
        elif action == 'decrease':
            if cart[key]['quantity'] > 1:
                cart[key]['quantity'] -= 1
            else:
                del cart[key]

        request.session['cart'] = cart
        request.session.modified = True
    return redirect('cart')

# ===== LOAD TF-IDF MODEL (LOAD 1 LẦN) =====
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#
# with open(os.path.join(BASE_DIR, "app/ml/tfidf_model_1.pkl"), "rb") as f:
#     tfidf_data = pickle.load(f)
#
# df_tfidf = tfidf_data["df"]
# cosine_sim = tfidf_data["cosine_sim"]
# #thêm vào
# def normalize(text):
#     return (
#         text.lower()
#         .replace("-", " ")
#         .replace("_", " ")
#         .strip()
#     )
#
#
# def get_recommend_products(product_name, top_k=4):
#     product_name = normalize(product_name)
#
#     matches = df_tfidf[df_tfidf["norm_name"] == product_name]
#     if matches.empty:
#         return []
#
#     idx = matches.index[0]
#
#     scores = list(enumerate(cosine_sim[idx]))
#     scores = sorted(scores, key=lambda x: x[1], reverse=True)
#
#     rec_names = [
#         df_tfidf.iloc[i]["productDisplayName"]
#         for i, _ in scores[1:top_k+1]
#     ]
#
#     return rec_names

# 1. Cấu hình đường dẫn và ID file từ link bạn vừa gửi
MODEL_DIR = os.path.join(settings.BASE_DIR, 'app', 'ml')
MODEL_PATH = os.path.join(MODEL_DIR, 'tfidf_model_1.pkl')
GOOGLE_DRIVE_ID = '11JynkiR6GoEutGR_IIg7OUAgdW4f81zk'  # ID từ link của bạn


def ensure_model_exists():
    """Kiểm tra file cục bộ, nếu thiếu thì tự động tải từ Drive"""
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)

    if not os.path.exists(MODEL_PATH):
        print("--- Đang tải model từ Google Drive (Vui lòng đợi giây lát)... ---")
        url = f'https://drive.google.com/uc?id={GOOGLE_DRIVE_ID}'
        try:
            # Tải file về máy
            gdown.download(url, MODEL_PATH, quiet=False)
            print("--- Tải model thành công! ---")
        except Exception as e:
            print(f"Lỗi khi tải file từ Drive: {e}")
            return None
    # Load model sau khi đã có file
    try:
        with open(MODEL_PATH, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        print(f"Lỗi khi đọc file pkl: {e}")
        return None


# 2. Khởi tạo dữ liệu gợi ý (Chạy 1 lần duy nhất khi khởi động server)
tfidf_data = ensure_model_exists()

if tfidf_data:
    df_tfidf = tfidf_data["df"]
    cosine_sim = tfidf_data["cosine_sim"]
else:
    # Tránh lỗi sập web nếu không load được model
    df_tfidf = pd.DataFrame()
    cosine_sim = None


# --- Giữ nguyên các hàm normalize và get_recommend_products phía dưới của bạn ---
def normalize(text):
    if not text: return ""
    return text.lower().replace("-", " ").replace("_", " ").strip()


def get_recommend_products(product_name, top_k=10):
    if df_tfidf.empty or cosine_sim is None:
        return []

    product_name_norm = normalize(product_name)
    matches = df_tfidf[df_tfidf["norm_name"] == product_name_norm]

    if matches.empty:
        return []

    idx = matches.index[0]
    scores = list(enumerate(cosine_sim[idx]))
    scores = sorted(scores, key=lambda x: x[1], reverse=True)

    rec_names = [
        df_tfidf.iloc[i]["productDisplayName"]
        for i, _ in scores[1:top_k + 1]
    ]
    return rec_names


import uuid
from .models import Order, OrderItem, ProductVariant


def add_cart(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        color = request.POST.get('color')
        size = request.POST.get('size')
        quantity = int(request.POST.get('quantity', 1))

        product = get_object_or_404(Product, id=product_id)
        variant = ProductVariant.objects.filter(product=product, color=color, size=size).first()

        if not variant:
            messages.error(request, "Lỗi: Không tìm thấy biến thể sản phẩm này!")
            return redirect(request.META.get('HTTP_REFERER'))

        key = f"{product_id}_{color}_{size}"
        cart = request.session.get('cart', {})

        # Lấy số lượng hiện tại đang có trong giỏ hàng (nếu có)
        quantity_in_cart = cart.get(key, {}).get('quantity', 0)
        # Tính tổng số lượng khách muốn mua
        total_requested_quantity = quantity_in_cart + quantity

        # KIỂM TRA TỔNG SỐ LƯỢNG VỚI KHO
        if variant.stock < total_requested_quantity:
            messages.error(request,
                           f"Bạn đã có {quantity_in_cart} trong giỏ. Kho chỉ còn lại {variant.stock} sản phẩm.")
            return redirect(request.META.get('HTTP_REFERER'))

        current_unit_price = float(product.current_price)

        if key in cart:
            cart[key]['quantity'] = total_requested_quantity  # Cập nhật tổng số lượng
            cart[key]['price'] = current_unit_price
        else:
            cart[key] = {
                'product_id': product_id,
                'variant_id': variant.id,
                'color': color,
                'size': size,
                'quantity': quantity,
                'price': current_unit_price,
                # 'variant_stock': variant.stock if variant else 0,
            }

        request.session['cart'] = cart
        request.session.modified = True
        messages.success(request, f"Đã thêm {product.name} vào giỏ hàng.")

    return redirect('cart')


@login_required(login_url='login')
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, "Giỏ hàng của bạn đang trống!")
        return redirect('cart')

    provinces = ShippingProvince.objects.all().order_by('name')
    total_product_price = 0
    display_items = []

    for key, item in cart.items():
        product = get_object_or_404(Product, id=item['product_id'])
        unit_price = product.current_price
        item_total = unit_price * item['quantity']
        total_product_price += item_total

        display_items.append({
            'product': product,
            'quantity': item['quantity'],
            'color': item['color'],
            'size': item['size'],
            'unit_price': unit_price,
            'item_total': item_total
        })

    # --- LẤY THÔNG TIN VOUCHER TỪ SESSION ---
    voucher_id = request.session.get('voucher_id')
    voucher_discount = request.session.get('voucher_discount', 0)

    # Kiểm tra điều kiện đơn hàng tối thiểu cho Voucher (Double Check)
    if voucher_id:
        try:
            v = Voucher.objects.get(id=voucher_id, active=True)
            if total_product_price < v.min_order_value:
                voucher_discount = 0
                voucher_id = None
                messages.warning(request, "Đơn hàng không đủ điều kiện áp dụng mã giảm giá.")
        except Voucher.DoesNotExist:
            voucher_discount = 0
            voucher_id = None

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        full_name = request.POST.get('full_name')
        phone_number = request.POST.get('phone')
        address = request.POST.get('address')
        note = request.POST.get('note')
        province_id = request.POST.get('province')

        province = get_object_or_404(ShippingProvince, id=province_id)
        shipping_fee = province.shipping_fee
        order_code = "ORD-" + str(uuid.uuid4().hex[:6].upper())

        # 1. Tạo Order (Đã bao gồm Voucher và Voucher Discount)
        order = Order.objects.create(
            user=request.user,
            total_price=total_product_price,
            province=province,
            shipping_fee=shipping_fee,
            order_code=order_code,
            full_name=full_name,
            phone_number=phone_number,
            address=address,
            note=note,
            payment_method=payment_method,
            items_json=str(cart),
            status='pending',
            # Gán thêm thông tin voucher vào đây
            voucher_id=voucher_id,
            voucher_discount=voucher_discount
        )

        # 2. Lưu OrderItem và GIẢM TỒN KHO
        for key, item in cart.items():
            product = Product.objects.get(id=item['product_id'])
            variant = ProductVariant.objects.filter(
                product=product,
                color=item['color'],
                size=item['size']
            ).first()

            if variant:
                if variant.stock >= item['quantity']:
                    variant.stock -= item['quantity']
                    variant.save()

                    OrderItem.objects.create(
                        order=order,
                        variant=variant,
                        quantity=item['quantity'],
                        price=product.current_price
                    )
                else:
                    # Hoàn tác: Nếu 1 món hết hàng, nên hủy cả đơn này
                    order.delete()
                    messages.error(request, f"Sản phẩm {product.name} đã hết hàng!")
                    return redirect('cart')
        if voucher_id:
            try:
                v = Voucher.objects.get(id=voucher_id)
                v.is_used = True  # Đánh dấu đã dùng (phải chạy dbshell trước đó)
                v.active = False  # Tắt luôn mã này để không ai dùng được nữa
                v.save()
            except Voucher.DoesNotExist:
                pass
        request.session['cart'] = {}
        # Xóa từng key voucher
        keys_to_remove = ['voucher_id', 'voucher_code', 'voucher_discount']
        for k in keys_to_remove:
            if k in request.session:
                del request.session[k]
        request.session.modified = True

        if payment_method == 'qr':
            return render(request, 'app/payment_qr.html', {
                'order': order,
                'final_amount': order.final_total,  # final_total đã trừ voucher trong Model
                'momo_phone': '0367225716',
                'account_name': 'NGUYEN VAN NGOAN'
            })
        else:
            messages.success(request, f"Đặt hàng thành công! Đơn hàng #{order_code} đang được chờ xác nhận.")
            return redirect('cart')

    return render(request, 'app/checkout.html', {
        'cart_items': display_items,
        'total_product_price': total_product_price,
        'provinces': provinces,
        'voucher_discount': voucher_discount,
        # Tính tổng nháp để hiển thị ở trang checkout
        'temp_final_total': (total_product_price - voucher_discount)
    })

@login_required
def order_detail(request, order_id):
    # Lấy đơn hàng, đảm bảo đơn hàng đó phải thuộc về người đang đăng nhập
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Lấy danh sách các sản phẩm trong đơn hàng này
    items = order.items.all()
    for item in items:
        item.total_price = item.price * item.quantity

    return render(request, 'app/order_detail.html', {
        'order': order,
        'items': items
    })
# views.py
from django.http import JsonResponse
from .models import ShippingProvince

def get_shipping_fee(request):
    province_id = request.GET.get('province_id')
    try:
        province = ShippingProvince.objects.get(id=province_id)
        return JsonResponse({'shipping_fee': float(province.shipping_fee)})
    except ShippingProvince.DoesNotExist:
        return JsonResponse({'shipping_fee': 0})


from django.contrib.admin.views.decorators import staff_member_required


@staff_member_required # Chỉ nhân viên (is_staff=True) mới vào được trang này
def shipper_dashboard(request):
    # Lấy các đơn hàng cần giao (đã xác nhận hoặc đang giao)
    orders = Order.objects.filter(status__in=['confirmed', 'shipping']).order_by('-created_at')
    return render(request, 'app/shipper_dashboard.html', {'orders': orders})

@staff_member_required
def update_delivery_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['shipping', 'delivered']:
            order.status = new_status
            order.save()
    return redirect('shipper_dashboard')


from django.contrib import messages


def submit_review(request, product_id):
    if request.method == "POST":
        product = get_object_or_404(Product, id=product_id)

        # Kiểm tra xem User đã có đơn hàng nào 'delivered' chứa sản phẩm này chưa
        can_review = OrderItem.objects.filter(
            order__user=request.user,
            order__status='delivered',
            variant__product=product
        ).exists()

        if not can_review:
            messages.error(request, "Bạn chỉ có thể đánh giá sản phẩm sau khi đơn hàng đã được giao thành công!")
            # SỬA CHỖ NÀY: Thay slug bằng pk
            return redirect('product_detail', pk=product.id)

        # Lấy dữ liệu từ form
        rating = request.POST.get('rating', 5)
        comment = request.POST.get('comment', '')

        # Tạo đánh giá
        Reviews.objects.create(
            product=product,
            user=request.user,
            rating=rating,
            comment=comment
        )

        messages.success(request, "Cảm ơn bạn đã gửi đánh giá!")
        # CHỖ NÀY BẠN ĐÃ SỬA ĐÚNG:
        return redirect('product_detail', pk=product.id)


from .models import Voucher
from django.utils import timezone


def apply_voucher(request):
    if request.method == "POST":
        code = request.POST.get('voucher_code')
        now = timezone.now()
        try:
            # Kiểm tra mã có tồn tại, còn hạn và đang kích hoạt không
            voucher = Voucher.objects.get(code__iexact=code,
                                          valid_from__lte=now,
                                          valid_to__gte=now,
                                          active=True)

            # Lưu mã và số tiền giảm vào Session
            request.session['voucher_id'] = voucher.id
            request.session['voucher_code'] = voucher.code
            request.session['voucher_discount'] = int(voucher.discount_amount)

            messages.success(request, f"Đã áp dụng mã {code} thành công!")
        except Voucher.DoesNotExist:
            messages.error(request, "Mã giảm giá không hợp lệ hoặc đã hết hạn.")

    return redirect('cart')  # Hoặc tên name của trang giỏ hàng bạn đặt


def remove_voucher(request):
    # Xóa toàn bộ các key liên quan đến voucher trong session
    keys_to_delete = ['voucher_id', 'voucher_code', 'voucher_discount']
    for key in keys_to_delete:
        if key in request.session:
            del request.session[key]

    messages.info(request, "Đã gỡ bỏ mã giảm giá.")
    return redirect('cart')
from django.utils import timezone

def my_vouchers(request):
    now = timezone.now()
    # Chỉ lấy mã Active, còn hạn VÀ chưa bị dùng (is_used=False)
    all_vouchers = Voucher.objects.filter(
        active=True,
        valid_to__gte=now,
        is_used=False  # Thêm điều kiện này
    ).order_by('-discount_amount')

    return render(request, 'app/my_vouchers.html', {
        'my_vouchers': all_vouchers
    })

def return_policy(request):
    return render(request, 'app/return-policy.html')
def size_guide(request):
    return render(request, 'app/size-guide.html')
def recruitment(request):
    return render(request, 'app/recruitment.html')
def store_system(request):
    return render(request, 'app/store-system.html')
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout  # Import thêm cái này để đăng nhập luôn
from .forms import CustomerSignupForm  # Import cái Form bạn vừa tạo
from .models import Product, ProductImage
from django.db.models import Q
import pickle
import os

import os
import gdown
import pickle
import pandas as pd
from django.conf import settings

def signup_view(request):
    if request.method == 'POST':
        # 1. Thay UserCreationForm bằng form tùy chỉnh của bạn
        form = CustomerSignupForm(request.POST)

        if form.is_valid():
            # 2. Lưu user vào database
            user = form.save()

            # 3. (Tùy chọn) Đăng nhập luôn cho khách sau khi đăng ký thành công
            login(request, user)

            # 4. Chuyển hướng về trang chủ
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
    products = Product.objects.filter(is_activate=True).prefetch_related('images').order_by('-id')
    return render(request, 'app/home.html', {
        'products': products,
        'products_news': products_news
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
    result = Product.objects.none()
    if query == 'all':
        result = Product.objects.all()
    elif (query):
        result = Product.objects.filter(category__name__icontains=query).distinct()
    return render(request, 'app/search.html', {
        'result': result
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

    return render(request, 'app/product_detail.html', {
        'product': product,
        'recommend_products': recommend_products
    })

def add_cart(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        color = request.POST.get('color')
        size = request.POST.get('size')
        quantity = int(request.POST.get('quantity', 1))

        # --- DÒNG KIỂM TRA (DEBUG) ---
        print(f"Dữ liệu nhận được: ID={product_id}, Màu={color}, Size={size}")

        if not product_id:
            return HttpResponse("Lỗi: Không nhận được product_id từ Form!")

        key = f"{product_id}_{color}_{size}"
        cart = request.session.get('cart', {})

        if key in cart:
            cart[key]['quantity'] += quantity
        else:
            cart[key] = {
                'product_id': product_id,
                'color': color,
                'quantity': quantity,
                'size': size,
            }

        request.session['cart'] = cart
        request.session.modified = True

        print("Giỏ hàng sau khi lưu:", request.session['cart'])  # Xem nó đã lưu chưa

    return redirect('cart')
def cart(request):
    cart_session = request.session.get('cart', {})
    cart_items = []
    total_price = 0

    for key, item in cart_session.items():
        try:
            product = Product.objects.get(id=item['product_id'])
            total_item_price = product.base_price * item['quantity']
            total_price += total_item_price

            cart_items.append({
                'key': key,
                'product': product,
                'quantity': item['quantity'],
                'color': item['color'],
                'size': item['size'],
                'total_item_price': total_item_price,
            })
        except (Product.DoesNotExist, ValueError):
            continue

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }
    return render(request, 'app/cart.html', context)


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
        if action == 'increase':
            cart[key]['quantity'] += 1
        elif action == 'decrease':
            cart[key]['quantity'] -= 1
            # Nếu giảm xuống 0 thì xóa luôn
            if cart[key]['quantity'] < 1:
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
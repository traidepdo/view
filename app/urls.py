from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Sử dụng LoginView có sẵn của Django
    path('login/', auth_views.LoginView.as_view(template_name='app/login.html'), name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.home, name = 'home'),
    path('product/', views.product_view, name = 'product'),
    path('search/', views.search, name='product_search'),
    path('category/', views.category, name='product_category'),
    # urls.py
    path('add-cart/', views.add_cart, name='add_cart'),
    path('cart/', views.cart, name='cart'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('remove-cart/<str:key>/', views.remove_cart, name='remove_cart'),
    path('update-cart/<str:key>/<str:action>/', views.update_cart, name='update_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order-detail/<int:order_id>/', views.order_detail, name='order_detail'),
    path('shipper/', views.shipper_dashboard, name='shipper_dashboard'),
    path('shipper/update/<int:order_id>/', views.update_delivery_status, name='update_delivery_status'),
    path('product/review/<int:product_id>/', views.submit_review, name='submit_review'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('apply-voucher/', views.apply_voucher, name='apply_voucher'),
    path('my-vouchers/', views.my_vouchers, name='my_vouchers'),
    path('remove-voucher/', views.remove_voucher, name='remove_voucher'),
    path('chinh-sach-doi-tra/', views.return_policy, name='return_policy'),
    path('huong-dan-size/', views.size_guide, name='size_guide'),
    path('tuyen-dung/', views.recruitment, name='recruitment'),
    path('he-thong-cua-hang/', views.store_system, name='store_system'),
]
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

]
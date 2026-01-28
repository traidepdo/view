from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
urlpatterns = [
    # Sử dụng LoginView có sẵn của Django
    path('login/', auth_views.LoginView.as_view(template_name='app/login.html'), name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', views.home, name = 'home')
]
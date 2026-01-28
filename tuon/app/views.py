from django.shortcuts import render, redirect
from django.contrib.auth import login  # Import thêm cái này để đăng nhập luôn
from .forms import CustomerSignupForm  # Import cái Form bạn vừa tạo


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
def home(request):
    return render(request, 'app/home.html', {})
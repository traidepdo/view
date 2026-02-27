def cart_count(request):
    count = 0
    # Lấy giỏ hàng từ session
    cart = request.session.get('cart', {})

    # Kiểm tra xem cart có thực sự là một dictionary và không trống không
    if isinstance(cart, dict) and cart:
        for item in cart.values():
            # Lấy quantity, nếu không thấy thì mặc định là 0
            count += int(item.get('quantity', 0))

    # Trả về kết quả
    return {'cart_total_quantity': count}
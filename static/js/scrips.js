// 1. Hiệu ứng đổi màu Navbar khi cuộn
window.addEventListener('scroll', function() {
    const header = document.querySelector('header');
    header.classList.toggle('sticky', window.scrollY > 0);
});
const observerOptions = {
    threshold: 0.2 // Hiện ra khi thấy được 20% phần tử
};


// cuộn
document.addEventListener("DOMContentLoaded", function() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const card = entry.target;

                // 1. Tìm xem card này là con thứ mấy trong cái lưới (grid)
                const allCards = Array.from(card.parentNode.children);
                const index = allCards.indexOf(card);

                // 2. Tính toán vị trí của nó trong hàng (mỗi hàng có 4 cái)
                // Phép chia lấy dư (%) giúp mình biết nó là cột 1, 2, 3 hay 4
                const column = index % 4;

                // 3. Tự động gắn độ trễ dựa trên cột
                // Cột càng cao thì chờ càng lâu (0.1s, 0.2s...)
                card.style.transitionDelay = `${column * 0.1}s`;

                // 4. Kích hoạt hiệu ứng hiện lên
                card.classList.add('active');

                // Xong rồi thì không cần theo dõi card này nữa
                observer.unobserve(card);
            }
        });
    }, { threshold: 0.1 });

    // Bảo máy tính đi tìm tất cả các card có class 'reveal' để quan sát
    document.querySelectorAll('.card.reveal').forEach(card => observer.observe(card));
});


//cuộn của category
document.addEventListener("DOMContentLoaded", function() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Khi phần tử lọt vào tầm mắt -> Thêm class active để hiện ra
                entry.target.classList.add('active');
            } else {
                // Khi phần tử khuất khỏi tầm mắt -> Xóa class active để chuẩn bị cho lần lướt sau
                entry.target.classList.remove('active');
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: "0px 0px -50px 0px" // Kích hoạt sớm hơn một chút để mượt hơn
    });

    document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
});
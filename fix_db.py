import sqlite3

try:
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    # Danh sách các cột cần kiểm tra và thêm nếu thiếu
    fields = [
        ('total_price', 'decimal(12, 2) NOT NULL DEFAULT 0'),
        ('full_name', 'varchar(255) DEFAULT ""'),
        ('phone_number', 'varchar(20) DEFAULT ""'),
        ('address', 'text DEFAULT ""'),
        ('order_code', 'varchar(10) DEFAULT ""'),
        ('items_json', 'text DEFAULT ""'),
        ('note', 'text DEFAULT ""'),
    ]

    for field_name, field_type in fields:
        try:
            cursor.execute(f"ALTER TABLE app_order ADD COLUMN {field_name} {field_type}")
            print(f"--- Đã thêm cột: {field_name}")
        except sqlite3.OperationalError:
            print(f"--- Cột {field_name} đã tồn tại, bỏ qua.")

    conn.commit()
    conn.close()
    print("\n>>> XỬ LÝ DATABASE HOÀN TẤT! BẠN CÓ THỂ XÓA FILE NÀY.")
except Exception as e:
    print(f"Lỗi: {e}")
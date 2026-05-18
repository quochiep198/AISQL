# Kế hoạch triển khai — {{TICKET}} ({{FEATURE_NAME}})

> Tạo ngày: [YYYY-MM-DD]
> Được suy ra từ: `docs/changes/{{TICKET}}/spec-pack.md`  
> Nhánh: `{{BRANCH_NAME}}`

---

## 1. Cách tiếp cận

<!-- Cách tiếp cận triển khai được chọn và lý do. So sánh với các phương án thay thế nếu phù hợp. -->

## 2. Phạm vi ảnh hưởng

### Các tệp / mô-đun cần thay đổi

| #   | Tệp | Loại thay đổi | Ghi chú |
| --- | --- | ------------- | ------- |
| 1   |     | Thêm/Sửa/Xóa  |         |

### Các khu vực ảnh hưởng khác

| #   | Hạng mục      | Mức ảnh hưởng | Ghi chú |
| --- | ------------- | ------------- | ------- |
| 1   | Lược đồ DB    |               |         |
| 2   | Hợp đồng API  |               |         |
| 3   | Cấu hình      |               |         |
| 4   | Nhật ký       |               |         |
| 5   | Quyền/Vai trò |               |         |
| 6   | Thành phần FE |               |         |

## 3. Mã hiện có cần đọc trước

<!-- Liệt kê các tệp bạn cần hiểu trước khi chỉnh sửa. -->

- [ ]
- [ ]

## 4. Các bước triển khai

<!-- Mỗi bước phải đủ nhỏ để có thể được rà soát độc lập. -->

| #   | Bước | Tệp được chỉnh sửa | Cách xác minh |
| --- | ---- | ------------------ | ------------- |
| 1   |      |                    |               |
| 2   |      |                    |               |

## 5. Rủi ro & Biện pháp giảm thiểu

| #   | Rủi ro | Biện pháp giảm thiểu |
| --- | ------ | -------------------- |
| 1   |        |                      |

## 6. Quy trình hoàn tác

<!-- Cách hoàn tác thay đổi này nếu nó gây ra sự cố trên môi trường production. -->

1.

## 7. Các bước xác minh

<!-- Các lệnh cần chạy để xác nhận thay đổi hoạt động đúng. -->

```bash
# Backend
cd demo && ./gradlew test

# Frontend
cd my-react-app && npm run lint && npm run build
```

---

## Bảng ánh xạ AC

| #   | AC                | (Các) bước đáp ứng | Cách xác minh |
| --- | ----------------- | ------------------ | ------------- |
| 1   | AC-[feature]-1/v1 | Bước X             |               |

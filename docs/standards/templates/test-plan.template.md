# Kế hoạch kiểm thử — {{TICKET}} ({{FEATURE_NAME}})

> Tạo: [YYYY-MM-DD]
> Mỗi AC phải được bao phủ bởi ít nhất một loại kiểm thử.

---

## 1. Ma trận bao phủ

| #   | AC                | FE UT | BE UT | API IT | E2E | Black-box |
| --- | ----------------- | ----- | ----- | ------ | --- | --------- |
| 1   | AC-[feature]-1/v1 |       |       |        |     |           |

## 2. Unit test FE

| #   | Tệp kiểm thử | Nội dung kiểm thử | AC  |
| --- | ------------ | ----------------- | --- |
| 1   |              |                   |     |

**Các trọng tâm:** validation của form, chuyển trạng thái, hiển thị lỗi, render có điều kiện.

## 3. Unit test BE

| #   | Lớp kiểm thử | Nội dung kiểm thử | AC  |
| --- | ------------ | ----------------- | --- |
| 1   |              |                   |     |

**Các trọng tâm:** giá trị biên, luồng exception, logic phân quyền trong use case/domain.

## 4. Integration test API

| #   | Endpoint | Kịch bản                                       | AC  |
| --- | -------- | ---------------------------------------------- | --- |
| 1   |          | luồng thành công, lỗi xác thực, lỗi validation |     |

## 5. Kiểm thử E2E (Playwright)

| #   | Kịch bản                  | Các bước | Kết quả mong đợi | AC  |
| --- | ------------------------- | -------- | ---------------- | --- |
| 1   | Luồng chính (bình thường) |          |                  |     |
| 2   | Luồng lỗi chính           |          |                  |     |

## 6. Các lệnh chạy kiểm thử

```bash
# FE unit tests
cd my-react-app && npm test

# BE unit tests
cd demo && ./gradlew test

# E2E
cd my-react-app && npx playwright test
```

## 7. Ghi chú / Ràng buộc

<!-- Chính sách mock, yêu cầu dữ liệu kiểm thử, các khu vực đã biết là dễ flaky -->

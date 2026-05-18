# Danh sách kiểm tra review — {{TICKET}} ({{FEATURE_NAME}})

> Ngày: [YYYY-MM-DD]
> Mức độ nghiêm trọng: **Blocker** = bắt buộc phải sửa trước khi merge | **Major** = phải sửa trong PR này | **Minor** = sửa hoặc ghi nhận là nợ kỹ thuật

---

## 1. Spec / AC

| #     | Hạng mục                                                                                  | Mức độ  | Trạng thái |
| ----- | ----------------------------------------------------------------------------------------- | ------- | ---------- |
| RC-01 | Tất cả AC đã được triển khai và có thể chứng minh là đã đáp ứng                           | Blocker | [ ]        |
| RC-02 | Không thêm hành vi nào nằm ngoài phạm vi của spec-pack                                    | Blocker | [ ]        |
| RC-03 | Các Open Issues vẫn còn được liệt kê; không mục nào được triển khai khi chưa có phê duyệt | Blocker | [ ]        |

## 2. Thiết kế / Phụ thuộc

| #     | Hạng mục                                                                                | Mức độ  | Trạng thái |
| ----- | --------------------------------------------------------------------------------------- | ------- | ---------- |
| RC-04 | Ranh giới giữa các layer được tôn trọng (không đặt domain logic trong controller, v.v.) | Major   | [ ]        |
| RC-05 | Không phát sinh phụ thuộc vòng tròn                                                     | Major   | [ ]        |
| RC-06 | API / contract công khai khớp với spec                                                  | Blocker | [ ]        |

## 3. Bảo mật

| #     | Hạng mục                                                           | Mức độ  | Trạng thái |
| ----- | ------------------------------------------------------------------ | ------- | ---------- |
| RC-07 | Tất cả dữ liệu đầu vào từ người dùng đều được kiểm tra và làm sạch | Blocker | [ ]        |
| RC-08 | Việc phân quyền được kiểm tra ở mọi endpoint/hành động             | Blocker | [ ]        |
| RC-09 | Không có secret, key hoặc PII trong log, diff hoặc response        | Blocker | [ ]        |
| RC-10 | Không có rủi ro SQL injection / XSS / command injection            | Blocker | [ ]        |

## 4. Hiệu năng

| #     | Hạng mục                                                                      | Mức độ | Trạng thái |
| ----- | ----------------------------------------------------------------------------- | ------ | ---------- |
| RC-11 | Không tạo ra truy vấn N+1                                                     | Major  | [ ]        |
| RC-12 | Không có payload lớn không cần thiết hoặc blocking I/O trên luồng xử lý chính | Major  | [ ]        |

## 5. Tương thích

| #     | Hạng mục                                  | Mức độ  | Trạng thái |
| ----- | ----------------------------------------- | ------- | ---------- |
| RC-13 | Các API hiện có vẫn giữ tương thích ngược | Blocker | [ ]        |
| RC-14 | Migration DB có thể hoàn tác              | Major   | [ ]        |

## 6. Logging / Audit

| #     | Hạng mục                                                   | Mức độ  | Trạng thái |
| ----- | ---------------------------------------------------------- | ------- | ---------- |
| RC-15 | Các thao tác chính (create/update/delete) đều được ghi log | Major   | [ ]        |
| RC-16 | Thông điệp log không chứa PII                              | Blocker | [ ]        |

## 7. Xử lý lỗi

| #     | Hạng mục                                                        | Mức độ | Trạng thái |
| ----- | --------------------------------------------------------------- | ------ | ---------- |
| RC-17 | Tất cả exception đều được bắt và trả về phản hồi lỗi có ý nghĩa | Major  | [ ]        |
| RC-18 | Client không nhận được stack trace nội bộ                       | Major  | [ ]        |

## 8. Kiểm thử

| #     | Hạng mục                                                               | Mức độ | Trạng thái |
| ----- | ---------------------------------------------------------------------- | ------ | ---------- |
| RC-19 | Unit test FE bao phủ validation của form và các chuyển trạng thái      | Major  | [ ]        |
| RC-20 | Unit test BE bao phủ các giá trị biên và exception                     | Major  | [ ]        |
| RC-21 | Integration test API bao phủ auth + luồng thành công + luồng lỗi       | Major  | [ ]        |
| RC-22 | Test E2E bao phủ user story chính (luồng bình thường + lỗi quan trọng) | Major  | [ ]        |

## 9. Vận hành

| #     | Hạng mục                                                       | Mức độ | Trạng thái |
| ----- | -------------------------------------------------------------- | ------ | ---------- |
| RC-23 | Quy trình hoàn tác đã được tài liệu hóa                        | Major  | [ ]        |
| RC-24 | Có dùng feature flag hoặc config switch nếu rollout rủi ro cao | Minor  | [ ]        |

---

## Bảng ánh xạ AC

| #   | AC                | Các hạng mục checklist dùng để xác nhận |
| --- | ----------------- | --------------------------------------- |
| 1   | AC-[feature]-1/v1 | RC-01, RC-06, RC-19                     |

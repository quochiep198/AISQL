# Báo cáo thay đổi — {{TICKET}} ({{FEATURE_NAME}})

> Tạo: [YYYY-MM-DD]
> Đối tượng đọc: kỹ sư tiếp theo, người review, người trực on-call.  
> Phải có thể hiểu được chỉ từ nội dung chính. Bao gồm đường dẫn tới bằng chứng.

---

## 1. Tóm tắt thay đổi

<!-- Tổng quan trong 1 trang: đã thay đổi gì, vì sao thay đổi, và ảnh hưởng đến những gì. -->

**Ticket:** {{TICKET}}  
**Nhánh:** {{BRANCH_NAME}}  
**Ngày:** YYYY-MM-DD  
**Tác giả:** (có hỗ trợ từ Claude)

### Đã thay đổi gì

-

### Lý do

- ***

## 2. Phạm vi ảnh hưởng

| #   | Khu vực             | Chi tiết |
| --- | ------------------- | -------- |
| 1   | Các tệp đã thay đổi |          |
| 2   | Lược đồ DB          |          |
| 3   | Hợp đồng API        |          |
| 4   | Cấu hình            |          |
| 5   | Nhật ký             |          |
| 6   | Quyền/Vai trò       |          |

---

## 3. Kết quả review

### Tự kiểm tra của Claude (`docs/changes/{{TICKET}}/self-review.md`)

- Blocker phát hiện:
- Vấn đề mức nghiêm trọng cao phát hiện:
- Tất cả AC đã được đáp ứng: Có / Không / Một phần

### Review bởi Codex (nếu có chạy)

- Kết luận tổng thể: Phê duyệt / Yêu cầu chỉnh sửa
- ## Các phát hiện chính:

### Các phát hiện từ review thủ công

| #   | Phát hiện | Mức độ nghiêm trọng | Hành động đã thực hiện |
| --- | --------- | ------------------- | ---------------------- |
| 1   |           |                     |                        |

---

## 4. Kết quả kiểm thử

| Loại kiểm thử | Lệnh                  | Kết quả     | Ghi chú |
| ------------- | --------------------- | ----------- | ------- |
| FE UT         | `npm test`            | PASS / FAIL |         |
| BE UT         | `./gradlew test`      | PASS / FAIL |         |
| API IT        |                       |             |         |
| E2E           | `npx playwright test` | PASS / FAIL |         |
| Black-box     | thủ công              | PASS / FAIL |         |

Chi tiết đầy đủ: `docs/changes/{{TICKET}}/test-results.md`

---

## 5. Công việc còn lại / Hành động tiếp theo

| #   | Công việc | Người phụ trách | Hạn chót |
| --- | --------- | --------------- | -------- |
| 1   |           |                 |          |

---

## 6. Quy trình hoàn tác

<!-- Các bước để hoàn tác thay đổi này nếu nó gây ra sự cố trên production. -->

1.

---

## 7. Danh mục đầu ra

| #   | Tệp                                             | Mục đích                                      |
| --- | ----------------------------------------------- | --------------------------------------------- |
| 1   | `docs/changes/{{TICKET}}/spec-pack.md`          | Nguồn tham chiếu duy nhất cho spec & AC       |
| 2   | `docs/changes/{{TICKET}}/impl-plan.md`          | Cách tiếp cận triển khai & các bước thực hiện |
| 3   | `docs/changes/{{TICKET}}/review-checklist.md`   | Các góc nhìn review                           |
| 4   | `docs/changes/{{TICKET}}/self-review.md`        | Kết quả tự kiểm tra của Claude                |
| 5   | `docs/changes/{{TICKET}}/test-plan.md`          | Kế hoạch bao phủ kiểm thử                     |
| 6   | `docs/changes/{{TICKET}}/test-results.md`       | Kết quả thực thi kiểm thử                     |
| 7   | `docs/changes/{{TICKET}}/blackbox-testcases.md` | Các test case black-box                       |

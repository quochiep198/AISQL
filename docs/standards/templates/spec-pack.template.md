# Gói đặc tả — #22394 (FHVW0020NM — ロケ在庫照会)

> Tạo: 2026-04-03 · Giai đoạn: 1  
> **Nguồn tham chiếu duy nhất cho thay đổi này.**  
> Không triển khai bất kỳ nội dung nào không được viết ở đây. Các điểm chưa rõ → Open Issues.

---

## 1. Bối cảnh / Mục đích
Hiện tại mong muốn triển khai màn hình FHVW0020NM có thể tra cứu tồn kho của từng itemcd dựa vào mã location đã nhập

---

## 2. Phạm vi

### Trong phạm vi
- Màn hình tra cứu tồn kho theo ロケーションコード (Location → Item search direction)
- 3 sub-screens: SHVW0021NM (nhập ロケコード), SHVW0022NM (danh sách 商品, 4 item/page), SHVW0023NM (chi tiết tồn kho)
- Hiển thị chi tiết tồn kho: phân tách theo GROUP BY lcncd, QltyCd, StckMngKey1
- Phân trang item list: 4 items/page
- Hỗ trợ SysKbn8 = 1/2 (chế độ NM switch F2/F3)

### Ngoài phạm vi
- Không hỗ trợ SysFlg13 (Lot branch)
- Không sửa stored procedures — chỉ inline SQL trong DataAccess

---

## 3. Thuật ngữ

| #  | Thuật ngữ | Định nghĩa |
|----|-----------|------------|
| 1  | ロケ在庫照会 | Tra cứu tồn kho theo ロケーション (location inventory inquiry) |
| 2  | ロケーションコード (LctnCd) | Mã vị trí kho — key input tại màn hình SHVW0021NM |
| 3  | 品質区分 (QltyCd) | Mã phân loại chất lượng hàng tồn |
| 4  | 在庫区分 (StckMngKey1) | Mã phân loại quản lý tồn kho |
| 5  | NM variant | Phiên bản màn hình tối ưu cho handy terminal NM (3 sub-screens liên tiếp) |
| 6  | 物流コード (ExStr14) | Mã logistics — từ `TMT091_ITEMEXP.EXSTR14`|
| 7  | メーカー品番 (ExStr2) | Mã logistics — từ `TMT091_ITEMEXP.EXSTR2`|
| 8  | 商品名1 | chính là clsE.FHVW0010NMItemEntity(i).ItemNm1 được lấy từ method FHCommon_SetBnktName(clsE.FHVW0010NMItemEntity(i).ItemNm, clsE.FHVW0010NMItemEntity(i).ItemNm1, clsE.FHVW0010NMItemEntity(i).ItemNm2)|
| 9  | 商品名2 |  chính là clsE.FHVW0010NMItemEntity(i).ItemNm2 được lấy từ method FHCommon_SetBnktName(clsE.FHVW0010NMItemEntity(i).ItemNm, clsE.FHVW0010NMItemEntity(i).ItemNm1, clsE.FHVW0010NMItemEntity(i).ItemNm2)|
| 10  | 商品名2 |  chính là clsE.FHVW0010NMItemEntity(i).ItemNm2 được lấy từ method FHCommon_SetBnktName(clsE.FHVW0010NMItemEntity(i).ItemNm, clsE.FHVW0010NMItemEntity(i).ItemNm1, clsE.FHVW0010NMItemEntity(i).ItemNm2)|


---
## 4. Hiện trạng / Trạng thái mục tiêu

| #  | Khía cạnh | Hiện trạng | Trạng thái mục tiêu |
|----|-----------|------------|---------------------|
| 1  | Tra cứu tồn kho theo ロケ trên NM | Chưa có  | FHVW0020NM: 3 sub-screens chạy trên handy terminal NM |

---

## 5. Chi tiết đặc tả
### 5.1 SHVW0021NM — Nhập ロケーション & khởi động tìm kiếm

**Pre-conditions:**
- Người dùng đã đăng nhập và có quyền truy cập màn hình này.

**Luồng chính:**
1. Người dùng nhập ロケーション vào ô tìm kiếm.
2. Người dùng nhấn [Enter/Scan] để khởi động tìm kiếm.
3. Hệ thống validate mã (xem BR-1).
4. Nhấn F3 chuyển sang màn SHVW0022NM với kết quả theo ロケーション tương ứng.
5. Nhấn F2 để trở về màn submenu

**Business rules:**
- BR-1: [Nếu người dùng không nhập gì -> hiển thị mã lỗi ME000004]
- BR-2: [Nếu không tìm thấy ロケ trong bảng master kho→ hiển thị mã lỗi ME000014]
- BR-3: [Nếu không tìm thấy ロケ trong bảng tồn kho → hiển thị mã lỗi ME000014]


**Post-conditions:** Chuyển sang SHVW0022NM với ロケ đã chọn.

---

### 5.2 SHVW0022NM — Danh sách 商品 tại ロケ (phân trang 4/page)

**Pre-conditions:**
- SHVW0021NM đã truyền ロケーションコード hợp lệ.

**Luồng chính:**
1. Hệ thống truy vấn danh sách 商品 theo ロケーションコード.
2. Hiển thị tối đa **4 dòng/trang**, có điều hướng trang, hiển thị theo quy luật index + itemnname
3. Validate nếu người dùng nhập index của location không hợp lệ xem mã BR-5,BR-6
4. Nếu người dùng chọn một index 商品 hợp lệ nhấn F3→ chuyển sang SHVW0023NM.
5. Nhấn F2 chuyển sang SHVW0022NM.
6. Nhấn F1/F4 để chuyển qua trang tiếp theo

**Business rules:**
- BR-4: [Sắp xếp danh sách theo tiêu chí là group by theo itemcd]
- BR-5: [Nếu người dùng không nhập gì -> hiển thị mã lỗi ME000004]
- BR-6: [Nếu người dùng nhập không phải số -> hiển thị mã lỗi ME000007]

**Post-conditions:** Chuyển sang SHVW0023NM với 商品 đã chọn.

---

### 5.3 SHVW0023NM — Chi tiết tồn kho của 商品 được chọn

**Pre-conditions:**
- SHVW0022NM đã truyền mã 商品 hợp lệ.

**Luồng chính:**
1. Hệ thống truy vấn chi tiết tồn kho của 商品
2. Nhấn F1/F4 để chuyển qua trang tiếp
2. Nhấn F2 để chuyển về SHVW0022NM


**Business rules:**
- BR-8: [Sắp xếp danh sách theo tiêu chí là group by theo LCTNCD,QLTYCD,STRINGKEY1]
---

## 6. Yêu cầu phi chức năng

| #  | Danh mục | Yêu cầu |
|----|----------|---------|
| 1  | Hiệu năng | Truy vấn phải trả kết quả trong thời gian phản hồi bình thường của handy terminal NM (không có yêu cầu cụ thể về ms) |
| 2  | Bảo mật | Không lưu credentials. Không log dữ liệu tồn kho ra file ngoài FHCommon_UpdLog chuẩn |
| 3  | Tính sẵn sàng | Theo yêu cầu chung của WMS — không có SLA riêng cho màn hình này |
| 4  | Khả năng quan sát | Ghi log FHCommon_UpdLog tại CNST_Operation_SHVW0021NM, 0022NM, 0023NM theo chuẩn NM screens hiện có |

---

## 7. Tiêu chí chấp nhận

| #  | ID | Mô tả | Loại kiểm thử |
|----|----|-------|---------------|
| 1  | AC-VW0020NM-1/v1 | Nhập ロケーションコード hợp lệ tại SHVW0021NM → chuyển sang SHVW0022NM hiển thị danh sách 商品 (≤4 item/page) | E2E |
| 2  | AC-VW0020NM-2/v1 | ロケーションコード không tồn tại trong TST010_STCK → hiển thị thông báo lỗi, không chuyển màn hình | E2E |
| 3  | AC-VW0020NM-3/v1 | Tại SHVW0022NM có >4 item → phân trang đúng (F1: trang trước, F4: trang sau) | E2E |
| 4  | AC-VW0020NM-4/v1 | Chọn item tại SHVW0022NM → chuyển SHVW0023NM hiển thị đúng QltyNm, StckNm, StckQty, AllwQty, ItemNm1/2, ExStr14 | E2E |
| 5  | AC-VW0020NM-5/v1 | F2/F3 tại SHVW0021NM → quay về submenu (SysKbn8=1: F2; SysKbn8=2: F3) | E2E |
| 6  | AC-VW0020NM-6/v1 | SysFlg13 không ảnh hưởng đến luồng — không có nhánh Lot | IT |
| 7  | AC-VW0020NM-7/v1 | Build thành công không có lỗi biên dịch | IT |

---

## 8. Ví dụ

### Các luồng bình thường

1. **Tra cứu thành công 1 page:** Nhập LctnCd="A-01-01" → SHVW0022NM hiển thị 3 item → chọn item 2 → SHVW0023NM hiển thị tồn kho chi tiết theo LctnCd và itemcd đã chọn.
2. **Tra cứu nhiều page:** LctnCd="B-02-03" có 7 items → SHVW0022NM page 1 (4 items) → nhấn F4 → page 2 (3 items) → chọn item → SHVW0023NM.
3. **Quay về:** Từ SHVW0023NM nhấn F2 → quay về SHVW0022NM → F2 tiếp → quay về SHVW0021NM → F2 → về submenu.

### Các luồng lỗi

1. **ロケ không tồn tại:** Nhập LctnCd không có trong TST010_STCK → hiển thị error message ME000014, ở lại SHVW0021NM.
2. **Nhập trống:** Nhấn Enter khi LctnCd rỗng → hiển thị ME000004 (必須チェック), ở lại SHVW0021NM.
3. **ロケ không tồn tại trong master kho:** Nhập LctnCd không có trong tmt130_lctn → hiển thị error message ME000014, ở lại SHVW0021NM.
### Các trường hợp biên
1. **StckQty = 0:** Hiển thị "0" tại SHVW0023NM, không lọc bỏ.

---

## 9. Wireframe ASCII

### SHVW0021NM — ロケ在庫照会 (ロケ入力)

```text
+------------------------------------------+
|         ロケ在庫照会                      |
|------------------------------------------|
| ロケーション  [ A-01-01______________]   |
|              [                       ]   |
|------------------------------------------|
| F2戻             F3確認                  |
+------------------------------------------+
```

### SHVW0022NM — 商品一覧

```text
+------------------------------------------+
|         ロケ在庫照会                      |
|------------------------------------------|
| ロケーションコード: A-01-01               |
|                                          |
| SKUコード  商品1  [________________]     |
| 商品2      [________________]            |
| 商品3      [________________]            |
| 商品4      [________________]            |
|------------------------------------------|
| F2戻 F1◁ F4▷ F3詳細                     |
+------------------------------------------+
```

### SHVW0023NM — 在庫詳細

```text
+------------------------------------------+
|         ロケ在庫照会                      |
|------------------------------------------|
| ロケコード:  A-01-01                     |
| 商品コード:  ITEM001                     |
| 物流コード:  LOGIS01                     |
| 品名1:       商品名称行1                 |
| 品名2:       商品名称行2                 |
| 品質:        良品                        |
| 在庫区分:    通常                        |
| 在庫数:      100                         |
| 品質表示:    95                          |
|------------------------------------------|
| F2戻 F1◁ F4▷                            |
+------------------------------------------+
```

### Ghi chú

- Các trạng thái chính: SHVW0021NM (nhập) → SHVW0022NM (list) → SHVW0023NM (detail); F2 luôn quay về màn hình trước
- Thông điệp xác thực / lỗi: ME000004 (必須), ME000007 (数値チェック), chuẩn FHCommon_DispMsg1
- Lưu ý về responsive: Thiết kế cho màn hình handy terminal NM — không cần responsive web

---

## 10. Các vấn đề mở

| #    | Câu hỏi | Người phụ trách | Hạn chót |
|------|---------|-----------------|----------|

---

## 11. Rủi ro

| #  | Rủi ro | Khả năng xảy ra | Mức độ ảnh hưởng | Biện pháp giảm thiểu |
|----|--------|-----------------|------------------|----------------------|
| 1  | WinNo 344/345/346 xung đột với screen khác | Thấp (đã verify free) | Cao — build lỗi | Đã kiểm tra trong spec-pack gốc |
| 2  | Field name trong HtSetHandyInData không khớp INI label SHVW0021NM | Trung bình | Trung bình — cursor không đúng vị trí | Xác nhận bằng test thực tế trên thiết bị NM |
| 3  | Entity chưa khởi tạo gây NullReferenceException khi navigate | Thấp (đã init trong SHVW0021NM handler) | Cao — crash | Review lại FHVW0020NMMain.vb line 19-27 |
| 4  | SQL GetZikDetail trả empty khi StckMngKey1=NULL | Trung bình | Trung bình — SHVW0023NM hiển thị trống | LEFT JOIN đã xử lý IFNULL; cần test case cụ thể |

---

## Bảng truy vết

| #  | AC | Màn hình/API | DB | Logs | Quyền | Loại kiểm thử | 
|----|----|--------------|----|------|-------|---------------|
| 1  | AC-VW0020NM-8/v1 | SHVW0021NM | TST010_STCK, tmt130_lctn | - | Đăng nhập | E2E |
| 2  | AC-VW0020NM-9/v1 | TST010_STCK, tmt090_item | - | Gía trị location hợp lệ từ màn SHVW0021NM | E2E |
| 3  | AC-VW0020NM-10/v1 | TST010_STCK,tmt091_itemexp,tmt050_name,TMT090_ITEM | - | Gía trị index itemcd hợp lệ từ màn SHVW0022NM | E2E |


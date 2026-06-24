# Báo Cáo Kỹ Thuật: Cơ Sở Dữ Liệu (Database)
**Dự án:** Nhận diện Biển Số Xe (License Plate Recognition)  
**Tác giả:** Database & Platform Engineering Team  
**Ngày lập:** 24/06/2026  
**Trạng thái:** Tài liệu Đặc tả Thiết kế & Bản ghi Hiện trạng Hệ thống  

---

## 📌 Mục lục
1. [Thiết kế Lược đồ Cấu trúc (Schema Design)](#1-thiết-kế-lược-đồ-cấu-trúc-schema-design)
2. [Quản lý Phiên bản & Di cư Lược đồ (Migrations with Alembic)](#2-quản-lý-phiên-bản--di-cư-lược-đồ-migrations-with-alembic)
3. [Quản lý Kết nối và Vòng đời Phiên (Connection Pooling & Sessions)](#3-quản-lý-kết-nối-và-vòng-đời-phiên-connection-pooling--sessions)
4. [Chiến lược Tối ưu hóa Hiệu năng (Performance Optimization)](#4-chiến-lược-tối-ưu-hóa-hiệu-năng-performance-optimization)
5. [Chính sách Bảo mật Dữ liệu (Security Best Practices)](#5-chính-sách-bảo-mật-dữ-liệu-security-best-practices)
6. [Sao lưu & Phục hồi Thảm họa (Backup & Disaster Recovery)](#6-sao-lưu--phục-hồi-thảm-họa-backup--disaster-recovery)
7. [Bản đồ liên kết File & Ký hiệu Code](#7-bản-đồ-liên-kết-file--ký-hiệu-code)

---

## 1. Thiết kế Lược đồ Cấu trúc (Schema Design)

Hệ thống sử dụng cơ sở dữ liệu quan hệ **PostgreSQL 16** để lưu trữ thông tin nhận diện biển số xe và siêu dữ liệu (metadata) đi kèm. Bảng trung tâm điều phối dữ liệu là `recognition_requests`, được ánh xạ bằng SQLAlchemy ORM thông qua lớp [RecognitionRequest](file:///home/leduc1009/BTL_AIT2004-2/apps/api/app/models/recognition.py#L20) trong [recognition.py](file:///home/leduc1009/BTL_AIT2004-2/apps/api/app/models/recognition.py).

### Chi tiết các cột trong bảng `recognition_requests`:

| Tên cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---------|--------------|-----------|-------|
| `id` | UUID | Primary Key | Khóa chính tự sinh ngẫu nhiên dạng UUIDv4. |
| `image_url` | VARCHAR(512) | NOT NULL | Đường dẫn tuyệt đối hoặc URL ký trước dẫn tới ảnh/video lưu trữ. |
| `plate_number` | VARCHAR(32) | Nullable | Chuỗi ký tự biển số xe sau nhận diện và định dạng lại. |
| `status` | ENUM | NOT NULL | Trạng thái: `NOT_STARTED`, `PENDING`, `COMPLETED`, `NEEDS_REVIEW`, `FAILED`. |
| `error_message` | TEXT | Nullable | Chi tiết lỗi nếu trạng thái là `FAILED`. |
| `confidence_score`| FLOAT | Nullable | Điểm tin cậy tổng hợp cuối cùng sau xác thực (tỷ lệ $0-100\%$). |
| `detection_confidence`| FLOAT| Nullable | Điểm tin cậy của thuật toán phát hiện vùng biển số xe. |
| `ocr_confidence` | FLOAT | Nullable | Điểm tin cậy trung bình của các ký tự nhận dạng được từ OCR. |
| `needs_review` | BOOLEAN | NOT NULL | Cờ đánh dấu nếu điểm tin cậy tổng hợp dưới ngưỡng an toàn, cần duyệt lại. |
| `bounding_box` | JSON | Nullable | Tọa độ dạng hình học `{x, y, width, height}` (theo % vùng ảnh phương tiện). |
| `plate_region` | VARCHAR(8) | Nullable | Mã quốc gia áp dụng luật xác thực (ví dụ: `BR` - Brazil, `GB` - Vương quốc Anh). |
| `metadata_json` | JSON | Nullable | Dữ liệu mở rộng dạng key-value (ví dụ: mã camera, hướng di chuyển, parent ID). |
| `created_at` | TIMESTAMP | NOT NULL, Default: NOW() | Thời điểm bản ghi được khởi tạo. |
| `updated_at` | TIMESTAMP | NOT NULL, Default: NOW() | Thời điểm bản ghi cập nhật trạng thái gần nhất. |

---

## 2. Quản lý Phiên bản & Di cư Lược đồ (Migrations with Alembic)

Việc nâng cấp lược đồ cơ sở dữ liệu trên các môi trường được tự động hóa hoàn toàn bằng công cụ **Alembic**, cấu hình tại tệp tin [alembic.ini](file:///home/leduc1009/BTL_AIT2004-2/apps/api/alembic.ini).

Lịch sử các phiên bản migration nằm trong thư mục [migrations/versions](file:///home/leduc1009/BTL_AIT2004-2/apps/api/migrations/versions):
1. **`001_create_recognition_requests.py`:** Khởi tạo cấu trúc bảng `recognition_requests` sơ khai kèm theo kiểu dữ liệu ENUM trạng thái.
2. **`002_add_confidence_and_detection_fields.py`:** Mở rộng thêm các trường lưu trữ điểm tin cậy riêng biệt (`detection_confidence`, `ocr_confidence`) để phục vụ thuật toán đánh giá đa tầng.
3. **`003_add_not_started_status.py`:** Cập nhật bổ sung trạng thái `NOT_STARTED` vào danh sách trạng thái của kiểu dữ liệu ENUM để quản lý các tác vụ vừa tạo chưa chạy.

*Quy trình áp dụng migration:* Chạy lệnh `alembic upgrade head` để đồng bộ CSDL lên phiên bản mới nhất, hoặc `alembic downgrade -1` để khôi phục (rollback) về phiên bản trước đó khi có sự cố lược đồ xảy ra.

---

## 3. Quản lý Kết nối và Vòng đời Phiên (Connection Pooling & Sessions)

Để tối ưu hóa số lượng kết nối đồng thời và giảm chi phí bắt tay TCP thiết lập kết nối đến Postgres, hệ thống cấu hình bộ động cơ SQLAlchemy bất đồng bộ (`create_async_engine`) tại [database.py](file:///home/leduc1009/BTL_AIT2004-2/apps/api/app/shared/database.py):

- **Connection Pool:** Cấu hình hồ chứa gồm `pool_size=5` kết nối mặc định, cho phép mở rộng tạm thời `max_overflow=10` kết nối phụ khi hệ thống chịu tải cao đột biến.
- **Pre-Ping:** Bật `pool_pre_ping=True` để thực thi câu lệnh SQL nhẹ (`SELECT 1`) kiểm tra tính hoạt động của kết nối trước khi bàn giao cho ứng dụng, giúp ngăn chặn lỗi mất kết nối đột ngột (stale connection errors).
- **Session Generator ([get_db](file:///home/leduc1009/BTL_AIT2004-2/apps/api/app/shared/database.py#L32)):** Cung cấp cơ chế yield Session bất đồng bộ cho mỗi request. Nếu có bất kỳ lỗi logic hoặc lỗi cơ sở dữ liệu phát sinh trong luồng xử lý API, khối lệnh `try...except` sẽ tự động thực hiện `session.rollback()` trước khi đóng kết nối để giữ an toàn tuyệt đối cho dữ liệu.

---

## 4. Chiến lược Tối ưu hóa Hiệu năng (Performance Optimization)

Nhận diện biển số là hệ thống lưu trữ lịch sử liên tục, số lượng bản ghi trong sản xuất có thể tăng lên hàng triệu dòng. Hệ thống áp dụng các giải pháp tối ưu sau:

### 4.1. Thiết lập Index thông minh
- **Index Thời gian Giảm dần:** Bảng `recognition_requests` định nghĩa chỉ mục B-Tree `ix_recognition_requests_created_at_desc` trên cột `created_at` sắp xếp giảm dần tại [recognition.py](file:///home/leduc1009/BTL_AIT2004-2/apps/api/app/models/recognition.py#L22). Điều này giúp các truy vấn GET danh sách phân trang (sắp xếp theo thời gian mới nhất) đạt độ trễ cực thấp $O(\log N)$ thay vì quét toàn bộ bảng (Full Table Scan).
- **Kế hoạch tương lai:** Bổ sung chỉ mục GIN (Generalized Inverted Index) trên cột `plate_number` kết hợp tiện ích mở rộng `pg_trgm` để hỗ trợ tìm kiếm mờ (fuzzy search) biển số xe theo mảnh ký tự với tốc độ cao.

### 4.2. Phân vùng Dữ liệu (Time-Series Partitioning)
- Khi kích thước CSDL vượt quá $10M$ dòng, Platform Team lên kế hoạch phân vùng (Partitioning) bảng `recognition_requests` theo tháng dựa trên cột `created_at`.
- Việc phân vùng giúp cô lập hoạt động ghi và tối ưu hóa bộ nhớ đệm vì Postgres chỉ cần giữ chỉ mục của phân vùng tháng hiện tại trong RAM.

---

## 5. Chính sách Bảo mật Dữ liệu (Security Best Practices)

- **SQL Injection Prevention:** Tránh tuyệt đối việc cộng chuỗi SQL thô. Hệ thống sử dụng trình biên dịch câu lệnh tham số hóa (Parameterized Queries) của SQLAlchemy để loại bỏ nguy cơ chèn mã độc thông qua các chuỗi tìm kiếm biển số do người dùng nhập.
- **Cô lập Môi trường mạng:** Cơ sở dữ liệu Postgres chạy trong mạng nội bộ Docker Compose, chỉ mở cổng `5432` cho API backend kết nối trực tiếp. Cổng `5433` ánh xạ ra ngoài máy chủ cục bộ chỉ sử dụng cho mục đích gỡ lỗi (debug) tại môi trường phát triển cục bộ và được khóa chặt trên môi trường production.
- **Quản lý Secrets:** Mọi thông tin nhạy cảm như `POSTGRES_PASSWORD`, `DATABASE_URL` được cấu hình ngoài mã nguồn thông qua tệp `.env` không được commit lên Git.

---

## 6. Sao lưu & Phục hồi Thảm họa (Backup & Disaster Recovery)

Hệ thống thiết lập quy trình sao lưu nghiêm ngặt nhằm đáp ứng mục tiêu phục hồi sau thảm họa (Disaster Recovery):

- **Mục tiêu RTO (Recovery Time Objective):** $< 1$ giờ (thời gian tối đa để khôi phục toàn bộ dịch vụ cơ sở dữ liệu về trạng thái hoạt động bình thường).
- **Mục tiêu RPO (Recovery Point Objective):** $< 15$ phút (giới hạn tối đa dữ liệu bị mất mát khi xảy ra sự cố phần cứng).
- **Kịch bản Backup:**
  - Sao lưu toàn phần (Full Backup) hàng ngày bằng công cụ `pg_dump` nén gzip và tự động đẩy lên kho lưu trữ đối tượng MinIO/S3 riêng biệt.
  - Tích hợp ghi nhật ký trước khi ghi (Write-Ahead Logging - WAL) để hỗ trợ phục hồi dữ liệu về bất kỳ thời điểm nào trong quá khứ (Point-in-Time Recovery - PITR).

---

## 7. Bản đồ liên kết File & Ký hiệu Code

Dưới đây là các tệp tin quan trọng nhất liên quan tới cơ sở dữ liệu:

* **Đặc tả bảng dữ liệu:** [recognition.py](file:///home/leduc1009/BTL_AIT2004-2/apps/api/app/models/recognition.py) -> Lớp định nghĩa bảng [RecognitionRequest](file:///home/leduc1009/BTL_AIT2004-2/apps/api/app/models/recognition.py#L20).
* **Khởi tạo kết nối & Generator:** [database.py](file:///home/leduc1009/BTL_AIT2004-2/apps/api/app/shared/database.py) -> Quản lý Pool và hàm phụ thuộc [get_db](file:///home/leduc1009/BTL_AIT2004-2/apps/api/app/shared/database.py#L32).
* **Cấu hình Alembic:** [alembic.ini](file:///home/leduc1009/BTL_AIT2004-2/apps/api/alembic.ini) -> Tệp cấu hình đường dẫn di cư.
* **Thư mục chứa script migration:** [versions/](file:///home/leduc1009/BTL_AIT2004-2/apps/api/migrations/versions) -> Các file chứa mã nâng cấp/hạ cấp CSDL.
* **Cấu hình dịch vụ Docker CSDL:** [docker-compose.yml](file:///home/leduc1009/BTL_AIT2004-2/docker-compose.yml#L2) -> Cấu hình container hình ảnh `postgres:16-alpine`.

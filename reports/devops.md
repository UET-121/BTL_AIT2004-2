# Báo Cáo Kỹ Thuật: DevOps & Hạ Tầng (Infrastructure)
**Dự án:** Nhận diện Biển Số Xe (License Plate Recognition)  
**Tác giả:** DevOps & Infrastructure Team  
**Ngày lập:** 24/06/2026  
**Trạng thái:** Tài liệu Đặc tả Hạ tầng & Bản ghi Hiện trạng Triển khai  

---

## 📌 Mục lục
1. [Kiến trúc Điều phối Monorepo (Docker Compose Orchestration)](#1-kiến-trúc-điều-phối-monorepo-docker-compose-orchestration)
2. [Chi tiết Cấu hình Container (Dockerfiles)](#2-chi-tiết-cấu-hình-container-dockerfiles)
3. [Tối ưu hóa Tài nguyên CPU trên Môi trường Docker](#3-tối-ưu-hóa-tài-nguyên-cpu-trên-môi-trường-docker)
4. [Kiểm tra Trạng thái Khỏe mạnh (Health Checks & Dependencies)](#4-kiểm-tra-trạng-thái-khỏe-mạnh-health-checks--dependencies)
5. [Quy trình Phát triển Cục bộ (Local Developer Workflow)](#5-quy-trình-phát-triển-cục-bộ-local-developer-workflow)
6. [Cổng kiểm soát chất lượng & Quy trình phát hành (CI/CD Quality Gates & Release)](#6-cổng-kiểm-soát-chất-lượng--quy-trình-phát-hành-cicd-quality-gates--release)
7. [Bản đồ liên kết File & Ký hiệu Code](#7-bản-đồ-liên-kết-file--ký-hiệu-code)

---

## 1. Kiến trúc Điều phối Monorepo (Docker Compose Orchestration)

Hệ thống sử dụng **Docker Compose** làm công cụ chính để điều phối và quản lý toàn bộ các thành phần hạ tầng dưới dạng Monorepo. Toàn bộ cấu trúc orchestration được định nghĩa tại tệp [docker-compose.yml](file:///home/leduc1009/BTL_AIT2004-2/docker-compose.yml).

Hệ thống bao gồm 4 dịch vụ (services) cốt lõi hoạt động chung trong một mạng nội bộ:
- **`db` (PostgreSQL 16):** Cơ sở dữ liệu quan hệ, sử dụng image `postgres:16-alpine` để giảm dung lượng đĩa, ánh xạ dữ liệu ra volume ngoài `pgdata` để tránh mất dữ liệu khi tái khởi động container.
- **`minio` (MinIO Object Storage):** Kho lưu trữ đối tượng chứa tệp hình ảnh/video, chạy image `minio/minio:latest` với cổng API `9000` và cổng Console quản trị `9001`, lưu dữ liệu đệm tại volume `miniodata`.
- **`api` (FastAPI backend):** Dịch vụ API xử lý nghiệp vụ và chạy luồng ML, build trực tiếp từ mã nguồn thư mục `apps/api`, mount thư mục ảnh tạm `uploads/` với máy chủ vật lý.
- **`frontend` (React + Vite SPA):** Giao diện quản trị viên và live stream camera, build từ thư mục nguồn `frontend/`, chạy Vite dev server ánh xạ cổng `5173`.

---

## 2. Chi tiết Cấu hình Container (Dockerfiles)

### 2.1. Container API Backend ([Dockerfile của API](file:///home/leduc1009/BTL_AIT2004-2/apps/api/Dockerfile))
- **Base image:** Sử dụng `python:3.11-slim` để giảm dung lượng container và tăng tính bảo mật.
- **Thư viện hệ thống:** Cài đặt các gói phụ thuộc hệ điều hành cần thiết cho OpenCV và ONNX Runtime hoạt động như `libgl1` (OpenGL), `libglib2.0-0` (Glib) và `ffmpeg`.
- **Cài đặt Python packages:** 
  - Thực hiện cài đặt trước `torch` và `torchvision` để lưu bộ nhớ đệm (build cache).
  - Cài đặt danh sách thư viện trong `requirements.txt` bằng công cụ `pip` với cờ `--no-cache-dir` để giữ container gọn nhẹ nhất có thể.
- **Lưu trữ:** Tạo thư mục nội bộ `/app/uploads` để làm điểm mount cho dữ liệu ảnh tải lên.

### 2.2. Container Frontend ([Dockerfile của Frontend](file:///home/leduc1009/BTL_AIT2004-2/frontend/Dockerfile))
- **Base image:** Sử dụng `node:20-alpine` siêu nhẹ phục vụ môi trường chạy Node.js.
- **Quy trình cài đặt:** Sao chép các tệp cấu hình package, mã nguồn và tệp CSS chủ đề [default_shadcn_theme.css](file:///home/leduc1009/BTL_AIT2004-2/frontend/default_shadcn_theme.css), sau đó chạy `npm install` cấu hình cờ tự động thử lại 5 lần khi gặp lỗi mạng.
- **Khởi chạy:** Mở cổng `5173` và khởi chạy Vite dev server ở chế độ lắng nghe mọi địa chỉ IP mạng (`--host 0.0.0.0`) để container bên ngoài có thể truy cập.

---

## 3. Tối ưu hóa Tài nguyên CPU trên Môi trường Docker

Khi triển khai các mô hình Deep Learning nặng (như YOLO và OCR dựa trên PyTorch/ONNX Runtime) bên trong container Docker chạy trên môi trường CPU (không có GPU tăng tốc), một vấn đề lớn thường gặp là **CPU Thrashing**:
- Mặc định, thư viện toán học MKL (Math Kernel Library) và OpenMP bên trong PyTorch/ONNX sẽ tự động tạo ra số lượng luồng tính toán song song bằng số nhân logic của CPU máy chủ.
- Khi có nhiều đối tượng được theo vết hoặc nhiều luồng video chạy đồng thời, việc tạo quá nhiều luồng tính toán song song này sẽ tạo ra overhead cực kỳ lớn do hiện tượng tranh chấp CPU và chuyển đổi ngữ cảnh liên tục (context-switching overhead).
- **Giải pháp DevOps:** Cấu hình triệt tiêu overhead này bằng cách thiết lập các biến môi trường giới hạn luồng toán học về giá trị tĩnh `1` cho dịch vụ `api` trong file [docker-compose.yml](file:///home/leduc1009/BTL_AIT2004-2/docker-compose.yml#L47):
  - `OMP_NUM_THREADS: 1` (Giới hạn luồng OpenMP)
  - `MKL_NUM_THREADS: 1` (Giới hạn luồng Intel MKL)
  - `OPENBLAS_NUM_THREADS: 1` (Giới hạn luồng OpenBLAS)
  - `VECLIB_MAXIMUM_THREADS: 1` (Giới hạn luồng VecLib)
  - `NUMEXPR_NUM_THREADS: 1` (Giới hạn luồng NumExpr)
- **Kết quả:** Việc chuyển về tính toán đơn luồng cho mỗi tác vụ con giúp hệ thống chạy ổn định hơn, giảm độ trễ xử lý frame hình trung bình xuống mức thấp nhất và ngăn ngừa lỗi sập ứng dụng do tràn bộ nhớ (Out-Of-Memory).

---

## 4. Kiểm tra Trạng thái Khỏe mạnh (Health Checks & Dependencies)

Để đảm bảo toàn bộ hệ thống khởi động theo đúng trình tự và không gặp lỗi mất kết nối dịch vụ khi khởi chạy đồng thời, DevOps triển khai cơ chế kiểm tra sức khỏe tự động:

1. **PostgreSQL Healthcheck ([docker-compose.yml](file:///home/leduc1009/BTL_AIT2004-2/docker-compose.yml#L12)):** Dùng lệnh nội bộ `pg_isready` để kiểm tra cổng kết nối và database đã sẵn sàng nhận truy vấn chưa. Thăm dò mỗi 5 giây, thử lại tối đa 10 lần.
2. **MinIO Healthcheck ([docker-compose.yml](file:///home/leduc1009/BTL_AIT2004-2/docker-compose.yml#L63)):** Chạy lệnh `curl` gửi yêu cầu HTTP đến endpoint `/minio/health/live` để xác nhận MinIO đã khởi động hoàn toàn.
3. **API Dependency Control ([docker-compose.yml](file:///home/leduc1009/BTL_AIT2004-2/docker-compose.yml#L22)):** API chỉ được khởi động khi container cơ sở dữ liệu đạt trạng thái `service_healthy`. Điều này ngăn chặn lỗi sập kết nối cơ sở dữ liệu khi chạy các đoạn code tự động đồng bộ lược đồ DB lúc khởi chạy.

---

## 5. Quy trình Phát triển Cục bộ (Local Developer Workflow)

DevOps cung cấp một hệ thống lệnh bọc (Wrapper Commands) qua công cụ `make` để nhà phát triển thao tác nhanh với hệ thống:

```bash
# 1. Khởi động hạ tầng nền (Postgres và MinIO) để phát triển code cục bộ bên ngoài container
docker compose up -d db minio

# 2. Đồng bộ các bản di cư cơ sở dữ liệu lên head
cd apps/api && alembic upgrade head

# 3. Chạy toàn bộ stack hệ thống (db, minio, api, frontend) ở chế độ chạy nền
docker compose up -d

# 4. Kiểm tra trạng thái hoạt động của các container
docker compose ps

# 5. Xem log ghi nhận thời gian thực của container API
docker compose logs -f api
```

---

## 6. Kiểm soát Chất lượng & Quy trình Phát hành (CI/CD Quality Gates & Release)

Tiến trình Agile của nhánh DevOps trải qua 7 Sprint (12 tuần):

- **Sprint 0 (Foundation - Hiện tại):** Thiết lập cấu trúc monorepo, docker-compose ban đầu cho DB & MinIO, viết Makefile bọc lệnh root, cấu hình env variables reference.
- **Sprint 1 (Local Stack):** Hoàn thiện bộ Dockerfile cho cả API và Frontend, tích hợp đầy đủ 4 service chạy liên kết trong Docker Compose.
- **Sprint 2 (Observability):** Thiết lập hệ thống ghi log tập trung, cấu hình healthcheck cho container và xây dựng script kiểm tra khói (smoke test) hạ tầng.
- **Sprint 3 (Model Artifacts):** Tích hợp công cụ quản lý phiên bản dữ liệu DVC, thiết lập volume mount riêng biệt cho thư mục trọng số mô hình `models/onnx`.
- **Sprint 4 (Quality Gates):** Triển khai pre-commit hooks (tự động chạy linter, formatter) và viết kịch bản `ci.sh` tự động hóa việc chạy unit test khi push code.
- **Sprint 5 (Hardening):** Cấu hình giới hạn cứng về tài nguyên (Resource limits: CPU/Memory limits) cho từng container trong Compose, thiết lập cronjob sao lưu cơ sở dữ liệu tự động.
- **Sprint 6 (Release v1.0):** Đóng gói bộ cài đặt, thực hiện kiểm thử khói đầy đủ, tạo nhãn Git (git tag v1.0.0) và xuất bản giao thức chuyển giao dự án.

### Tiêu chí Đóng gói Phát hành v1.0 (Release Criteria)
- Lệnh `docker compose up -d` khởi động toàn bộ 4 dịch vụ và đạt trạng thái `healthy` trong thời gian $< 3$ phút.
- Khớp nối toàn bộ các bước kiểm tra chất lượng của kịch bản `ci.sh` (Pre-commit hook pass, linting pass, unit test đạt độ phủ $\ge 70\%$).
- Toàn bộ kịch bản kiểm thử E2E bằng Playwright trên trình duyệt phải vượt qua thành công.

---

## 7. Bản đồ liên kết File & Ký hiệu Code

Dưới đây là các tệp tin quan trọng nhất liên quan tới hạ tầng & DevOps:

* **Tập tin orchestration chính:** [docker-compose.yml](file:///home/leduc1009/BTL_AIT2004-2/docker-compose.yml).
* **Dockerfile của backend API:** [Dockerfile (API)](file:///home/leduc1009/BTL_AIT2004-2/apps/api/Dockerfile).
* **Dockerfile của frontend web:** [Dockerfile (Frontend)](file:///home/leduc1009/BTL_AIT2004-2/frontend/Dockerfile).
* **Cấu hình biến môi trường mẫu:** [.env.example](file:///home/leduc1009/BTL_AIT2004-2/.env.example).
* **Tài liệu hướng dẫn biến môi trường:** [06-env-variables.md](file:///home/leduc1009/BTL_AIT2004-2/plan/_shared/06-env-variables.md).
* **Bảng theo dõi rủi ro hạ tầng:** [07-risk-register.md](file:///home/leduc1009/BTL_AIT2004-2/plan/_shared/07-risk-register.md).

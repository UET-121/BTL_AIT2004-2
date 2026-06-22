# 💻 Frontend - Real-Time Lpr Recognition System

Đây là ứng dụng giao diện người dùng (Frontend) của hệ thống Nhận diện Biển số Thời gian thực. Ứng dụng được xây dựng theo kiến trúc SPA (Single Page Application) tập trung vào tốc độ, trải nghiệm người dùng và thiết kế hiện đại.

## 🚀 Công Nghệ Sử Dụng

- **Core**: [React 18](https://reactjs.org/) + [Vite](https://vitejs.dev/) (Build tool siêu tốc)
- **Routing**: [React Router v7](https://reactrouter.com/)
- **Charts/Monitoring**: [Recharts](https://recharts.org/) (Vẽ biểu đồ dữ liệu Prometheus)
- **HTTP Client**: [Axios](https://axios-http.com/)
- **Icons**: [Lucide React](https://lucide.dev/)
- **Styling**: Vanilla CSS (Thiết kế Dark Theme, Glassmorphism)
- **Real-time**: WebSocket (Nhận cảnh báo nhận diện biển số tức thời)

## 🌟 Tính Năng Chính

- **Dashboard (Detections)**: Xem lịch sử nhận diện biển số, trích xuất báo cáo Excel, nhận cảnh báo thời gian thực qua Toast (WebSocket).
- **Profiles Management**: Quản lý danh sách nhân viên/biển số (Thêm, Sửa, Xóa).
- **Vision (Camera Management)**: Thêm/Sửa/Xóa camera RTSP/HTTP, xem trực tiếp luồng Live Stream, tắt/bật AI cho từng camera.
- **Monitoring**: Theo dõi sức khỏe hệ thống (Traffic API, CPU, RAM) được lấy trực tiếp từ Prometheus API thông qua biểu đồ diện tích trực quan.
- **Webhooks**: Cấu hình các điểm cuối Webhook để đẩy dữ liệu nhận diện ra hệ thống bên ngoài.
- **Role-Based Access Control (RBAC)**: Phân quyền chi tiết cho `admin` (Toàn quyền), `manager` (Quản lý dữ liệu, không sửa hệ thống) và `viewer` (Chỉ xem).

## 📂 Cấu Trúc Thư Mục

```text
frontend/
├── index.html            # Entry point HTML
├── package.json          # Quản lý dependencies và scripts
├── vite.config.js        # Cấu hình Vite
└── src/
    ├── main.jsx          # File boot ứng dụng React
    ├── App.jsx           # Định tuyến (Routes) & cấu hình WebSocket tổng
    ├── components/       # Các component dùng chung
    │   └── ProtectedRoute.jsx  # Component bảo vệ các trang yêu cầu quyền
    ├── pages/            # Chứa các màn hình chính
    │   ├── Login.jsx     # Trang đăng nhập
    │   ├── Dashboard.jsx # Lịch sử Detections
    │   ├── Profiles.jsx  # Quản lý hồ sơ
    │   ├── Vision.jsx    # Quản lý Camera
    │   ├── Webhooks.jsx  # Cấu hình Webhook
    │   └── Monitoring.jsx# Dashboard Monitor (Recharts)
    ├── services/         # Chứa logic kết nối Backend
    │   └── api.js        # Khởi tạo Axios & các hàm gọi API
    └── assets/           # Hình ảnh, font chữ tĩnh
```
## 📦 Build & Triển Khai (Production)

Để tối ưu hóa mã nguồn cho môi trường thực tế, chạy lệnh:
```bash
npm run build
```
Lệnh này sẽ nén toàn bộ code và sinh ra thư mục `dist/`. Thư mục này sau đó được mount vào container của Nginx (port 80) để phục vụ cho người dùng (Xem thêm cấu hình trong `docker-compose.yml`).

## 🎨 Lưu ý Thiết Kế
- Toàn bộ ứng dụng sử dụng bảng màu **Dark Mode** mặc định kết hợp hiệu ứng kính (Glassmorphism) qua class `.glass-panel`.
- Hạn chế inline-styles, mọi tuỳ chỉnh CSS nên được định nghĩa trong file CSS riêng của từng Page (ví dụ: `Dashboard.css`, `Profiles.css`) để dễ dàng bảo trì.

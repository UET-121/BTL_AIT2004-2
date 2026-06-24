# Báo Cáo Kỹ Thuật: Nhánh Frontend
**Dự án:** Nhận diện Biển Số Xe (License Plate Recognition)  
**Tác giả:** Frontend Engineering Team  
**Ngày lập:** 24/06/2026  
**Trạng thái:** Bản phác thảo Thiết kế & Hiện trạng Sprint 0  

---

## 📌 Mục lục
1. [Tổng quan về React/Vite SPA](#1-tổng-quan-về-reactvite-spa)
2. [Chi tiết Luồng Giao diện & Thành phần chính](#2-chi-tiết-luồng-giao-diện--thành-phần-chính)
3. [Xử lý Dữ liệu Real-time qua WebSockets](#3-xử-lý-dữ-liệu-real-time-qua-websockets)
4. [Tích hợp API và Quản lý Trạng thái](#4-tích-hợp-api-và-quản-lý-trạng-thái)
5. [Cơ chế Crop Biển số phía Client (Client-Side Cropping)](#5-cơ-chế-crop-biển-số-phía-client-client-side-cropping)
6. [Kế hoạch Sprint & Chỉ số Chất lượng (Frontend Track)](#6-kế-hoạch-sprint--chỉ-số-chất-lượng-frontend-track)
7. [Bản đồ liên kết File & Ký hiệu Code](#7-bản-đồ-liên-kết-file--ký-hiệu-code)

---

## 1. Tổng quan về React/Vite SPA

Ứng dụng Frontend được thiết kế dưới dạng Single Page Application (SPA) hiện đại sử dụng **React 19**, **Vite 6** và viết hoàn toàn bằng **TypeScript**. 

### Các tính năng cốt lõi:
- **Upload video nhận diện:** Hỗ trợ kéo thả video tải lên, giới hạn kích thước tối đa 250MB.
- **Giám sát thời gian thực (Real-time Live Feed):** Nhận hình ảnh video truyền phát trực tiếp (MJPEG nén) và thông tin bounding box chồng đè lên canvas từ WebSocket.
- **Quản lý lịch sử và Chi tiết (CRUD History & Details):** Xem danh sách phân trang các lượt nhận diện, xóa lịch sử, phóng to hình ảnh/video kết quả, hiển thị biểu đồ độ tin cậy (Confidence).
- **Giao diện Responsive & Dark Mode:** Tương thích tốt trên cả máy tính và thiết bị di động, tự động chuyển đổi theme màu hài hòa dựa trên Tailwind CSS và CSS variables định nghĩa trong [default_shadcn_theme.css](file:///d:/MySC/Python/BTL_AIT2004-2/frontend/default_shadcn_theme.css).

---

## 2. Chi tiết Luồng Giao diện & Thành phần chính

Cấu trúc thư mục nguồn của Frontend nằm trong [frontend/src](file:///d:/MySC/Python/BTL_AIT2004-2/frontend/src).

### 2.1. Quản trị Trung tâm (App Shell)
Tệp [App.tsx](file:///d:/MySC/Python/BTL_AIT2004-2/frontend/src/app/App.tsx) đóng vai trò điều hướng tuyến đường cục bộ (Router) và bao bọc trạng thái toàn cục:
- **Trình điều hướng (Simple Router):** Phân tích `window.location.pathname` qua hàm `currentRoute` để hiển thị trang chủ (`home`), chi tiết (`detail`), hoặc trang giám sát trực tiếp (`live`).
- **UploadPanel ([UploadPanel](file:///d:/MySC/Python/BTL_AIT2004-2/frontend/src/app/App.tsx#L216)):** Hộp kéo thả file video. Khi chọn file, nó kiểm tra hợp lệ về định dạng và kích thước trước khi gọi hàm tải lên backend. Sau khi tải lên thành công, giao diện tự động điều hướng người dùng sang trang chi tiết để theo dõi tiến độ xử lý.
- **DetailView ([DetailView](file:///d:/MySC/Python/BTL_AIT2004-2/frontend/src/app/App.tsx#L603)):** 
  - Trình chiếu Video hoặc ảnh biển số xe.
  - Vẽ Bounding Box chứa biển số xe đè lên khung hình dựa trên tỷ lệ kích thước tự nhiên (`naturalWidth`/`naturalHeight`) của phương tiện được tải về qua component [BboxOverlay](file:///d:/MySC/Python/BTL_AIT2004-2/frontend/src/app/App.tsx#L586).
  - Bảng thống kê độ tin cậy [ConfidenceCard](file:///d:/MySC/Python/BTL_AIT2004-2/frontend/src/app/App.tsx#L557) hiển thị chi tiết điểm số của ba yếu tố: Độ tin cậy phát hiện xe (Detection), độ tin cậy OCR và điểm số tổng hợp. Nếu điểm số thấp, banner màu cam cảnh báo `NEEDS_REVIEW` sẽ xuất hiện.

### 2.2. Trang Giám sát Realtime (Live Page)
Trang [LivePage.tsx](file:///d:/MySC/Python/BTL_AIT2004-2/frontend/src/app/live/LivePage.tsx) là bảng điều khiển camera giám sát trực tuyến thời gian thực, tích hợp ba thành phần chuyên biệt nằm trong thư mục [frontend/src/app/live/components](file:///d:/MySC/Python/BTL_AIT2004-2/frontend/src/app/live/components):
1. **VideoCanvas ([VideoCanvas.tsx](file:///d:/MySC/Python/BTL_AIT2004-2/frontend/src/app/live/components/VideoCanvas.tsx)):** Nhận dữ liệu ảnh Base64 từ WebSocket vẽ trực tiếp lên thẻ canvas, đồng thời tự động vẽ các khung hình bao (Bounding Box) màu sắc khác nhau bao quanh xe và biển số xe tương ứng dựa trên trạng thái của đối tượng (Xác nhận: xanh lá; Đang chờ: vàng; Từ chối: đỏ).
2. **StreamControls ([StreamControls.tsx](file:///d:/MySC/Python/BTL_AIT2004-2/frontend/src/app/live/components/StreamControls.tsx)):** Cho phép nhập nguồn video (RTSP url hoặc đường dẫn file cục bộ) và điều khiển bật/tắt luồng stream lên backend.
3. **ResultPanel ([ResultPanel.tsx](file:///d:/MySC/Python/BTL_AIT2004-2/frontend/src/app/live/components/ResultPanel.tsx)):** Chia làm hai nửa: bên trái hiển thị danh sách các xe đang được theo vết trong khung hình hiện tại (Active Tracks); bên phải hiển thị lịch sử 10 biển số xe đã được xác nhận thành công gần nhất (đọc từ sự kiện `plate.confirmed`).

---

## 3. Xử lý Dữ liệu Real-time qua WebSockets

Cơ chế kết nối và xử lý thông điệp từ WebSocket của [LivePage.tsx](file:///d:/MySC/Python/BTL_AIT2004-2/frontend/src/app/live/LivePage.tsx#L86) diễn ra như sau:

- **Khởi tạo Kết nối:** Khi trạng thái luồng chuyển sang `running` hoặc `starting`, hook `useEffect` sẽ khởi tạo kết nối WebSocket đến địa chỉ `ws://localhost:8000/ws/live` qua hàm `getWsUrl`.
- **Lắng nghe Sự kiện (`onmessage`):**
  - **`frame.processed`:** Cập nhật ảnh Base64 lên canvas, lấy các chỉ số FPS và số lượng xe hiện thời trong khung hình để đưa vào dashboard. Đồng thời, giải nén danh sách phát hiện (`detections`) để vẽ khung bao.
  - **`plate.confirmed`:** Đẩy biển số xe vừa được nhận dạng thành công vào danh sách lịch sử xác nhận của Panel dưới dạng thẻ ghi nhận kèm mức độ tự tin.
  - **`plate.rejected`:** Đẩy biển số xe không thống nhất được ký tự vào danh sách lịch sử dưới nhãn màu đỏ cảnh báo.
  - **`stream.stopped`:** Ngắt kết nối WebSocket cục bộ, reset lại các chỉ số giám sát về $0$ và tự động điều hướng người dùng về lại trang chủ.
  - **`stream.error`:** Hiển thị thông báo lỗi hệ thống lên bảng điều khiển stream.
- **Dọn dẹp (Cleanup):** Khi thoát trang hoặc dừng stream, kết nối WebSocket tự động được đóng nhằm tránh rò rỉ bộ nhớ (memory leak).

---

## 4. Tích hợp API và Quản lý Trạng thái

Toàn bộ các yêu cầu HTTP giao tiếp với Backend được đóng gói trong tệp tin [api.ts](file:///d:/MySC/Python/BTL_AIT2004-2/frontend/src/app/api.ts).

### Các hàm gọi API chính:
- `listRecognitions(page, pageSize)`: Lấy danh sách yêu cầu nhận dạng (phân trang).
- `getRecognition(id)`: Lấy chi tiết một yêu cầu nhận diện.
- `uploadRecognition(file)`: Đóng gói file video vào đối tượng `FormData` và gửi yêu cầu `POST` dạng upload đa phần (multipart upload) đến backend.
- `startStream(source)`: Yêu cầu Backend bắt đầu luồng bắt hình video từ `source`.
- `stopStream()`: Yêu cầu Backend ngắt luồng.
- `getStreamStatus()`: Kiểm tra trạng thái luồng hiện tại từ máy chủ.
- `deleteRecognition(id)`: Xóa yêu cầu nhận diện.

---

## 5. Cơ chế Crop Biển số Phía Client (Client-Side Cropping)

Theo thiết kế hệ thống, ứng dụng hỗ trợ cơ chế cắt ảnh biển số xe trực tiếp tại trình duyệt (Client-side plate cropping) bằng thư viện `react-easy-crop` (sẽ được hoàn thiện tối ưu trong Sprint 1):
- Khi người dùng tải lên một hình ảnh tĩnh thay vì video, giao diện cung cấp khung cắt (Cropper) cho phép người dùng tự khoanh vùng biển số xe trước khi gửi đi.
- **Lợi ích:** Việc khoanh vùng thủ công giúp loại bỏ hoàn toàn các yếu tố nhiễu ngoại cảnh (như cây cối, xe cộ xung quanh), giúp nâng cao độ chính xác của bộ phân tích ML (YOLO & OCR) lên mức tối đa khi xử lý ảnh tĩnh.

---

## 6. Kế hoạch Sprint & Chỉ số Chất lượng (Frontend Track)

Kế hoạch phát triển Agile của Frontend:

- **Sprint 0 (Vite Scaffold - Hiện tại):** Khởi tạo ứng dụng React bằng Vite, cài đặt cấu hình router TanStack, Tailwind CSS, cài đặt Dark mode và khai báo kiểu dữ liệu chung.
- **Sprint 1 (Upload Flow):** Thiết kế giao diện upload tệp video/ảnh tĩnh, tích hợp khung Cropper phía client.
- **Sprint 2 (Request Management):** Triển khai giao diện bảng danh sách yêu cầu nhận diện, trạng thái xử lý và cơ chế tự động thăm dò (polling) trạng thái cho các bản ghi đang xử lý.
- **Sprint 3 (Detail & Confidence):** Thiết kế trang chi tiết yêu cầu, vẽ khung bao biển số đè lên xe và hiển thị biểu đồ phân tích độ tin cậy chi tiết.
- **Sprint 4 (Review Workflow):** Xây dựng giao diện duyệt thủ công biển số (NEEDS_REVIEW) và nút yêu cầu xử lý lại (reprocess) biển số.
- **Sprint 5 (UX Polish):** Tối ưu hóa trải nghiệm responsive trên thiết bị di động, cải thiện tốc độ render canvas thời gian thực và khả năng tiếp cận (a11y).
- **Sprint 6 (Release & QA):** Viết các kịch bản kiểm thử tự động E2E bằng Playwright để đảm bảo toàn bộ luồng hoạt động ổn định trước khi phát hành v1.0.

---

## 7. Bản đồ liên kết File & Ký hiệu Code

Dưới đây là các tệp tin quan trọng nhất thuộc nhánh Frontend:

* **Trang chủ & Tuyến đường:** [App.tsx](file:///d:/MySC/Python/BTL_AIT2004-2/frontend/src/app/App.tsx) -> Router cục bộ, upload panel và detail panel.
* **Trang giám sát camera:** [LivePage.tsx](file:///d:/MySC/Python/BTL_AIT2004-2/frontend/src/app/live/LivePage.tsx) -> Quản lý kết nối WebSocket và cập nhật dashboard.
* **Vẽ canvas camera:** [VideoCanvas.tsx](file:///d:/MySC/Python/BTL_AIT2004-2/frontend/src/app/live/components/VideoCanvas.tsx).
* **Điều khiển luồng:** [StreamControls.tsx](file:///d:/MySC/Python/BTL_AIT2004-2/frontend/src/app/live/components/StreamControls.tsx).
* **Kết quả theo vết & Lịch sử:** [ResultPanel.tsx](file:///d:/MySC/Python/BTL_AIT2004-2/frontend/src/app/live/components/ResultPanel.tsx).
* **Cổng gọi API:** [api.ts](file:///d:/MySC/Python/BTL_AIT2004-2/frontend/src/app/api.ts).
* **Khai báo kiểu TypeScript:** [types.ts](file:///d:/MySC/Python/BTL_AIT2004-2/frontend/src/app/types.ts).

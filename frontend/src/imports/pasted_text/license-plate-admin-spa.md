Thiết kế một SPA quản trị cho hệ thống nhận diện biển số xe, phong cách utilitarian, rõ ràng, gọn, thiên về thao tác và đọc dữ liệu hơn là trang trí. Đây không phải landing page marketing. Giao diện phải phục vụ 4 luồng chính: upload ảnh biển số, xem danh sách request, xem chi tiết kết quả với confidence/bounding box, và reprocess các request cần xử lý lại.
Hệ thống có các endpoint và dữ liệu sau:
POST /api/v1/recognitionUpload ảnh image/jpeg hoặc image/png
Max 10MB
Trả về request_id, status, created_at

GET /api/v1/recognitionDanh sách paginated
Query: page, page_size
Trả về items, total, page, page_size, total_pages

GET /api/v1/recognition/{request_id}Chi tiết một request
Trả về: id, image_url, plate_number, status, error_message, created_at, updated_at, confidence_score, detection_confidence, ocr_confidence, needs_review, bounding_box, plate_region

POST /api/v1/recognition/{request_id}/reprocessChỉ dùng cho FAILED hoặc NEEDS_REVIEW
Sau khi bấm, trạng thái về NOT_STARTED và hệ thống xử lý lại

Static image:image_url và /uploads/... phải hiển thị ảnh trực tiếp

Health endpoint:GET /health chỉ để phục vụ trạng thái hệ thống, không cần là màn hình chính

Mục tiêu trải nghiệm
Người dùng có thể upload ảnh biển số trong vài giây, thấy preview, crop trước khi gửi, rồi tự động được chuyển sang màn hình chi tiết.
Người dùng có thể xem toàn bộ lịch sử request trong một bảng/list có thumbnail, trạng thái và biển số đã đọc được.
Người dùng có thể theo dõi tiến trình xử lý gần như realtime bằng polling.
Người dùng có thể nhìn rõ mức tin cậy của kết quả, xem vùng phát hiện biển số trên ảnh, và biết khi nào cần manual review.
Khi request thất bại hoặc cần duyệt, người dùng phải thấy lý do và có hành động reprocess rõ ràng.
Cấu trúc màn hình
Home pageThanh tiêu đề tối giản, tên app rõ ràng.
Khu vực upload nằm ở đầu trang, nổi bật nhưng không “hero” phô trương.
Bên dưới là danh sách request gần đây.
Có trạng thái empty nếu chưa có dữ liệu: hướng dẫn upload ảnh để bắt đầu.
Có trạng thái loading skeleton khi list đang tải.
Có phân trang: Prev/Next, page indicator, page size selector.
Có auto-refresh nếu còn item NOT_STARTED hoặc PENDING.
Có nút refresh thủ công dạng icon button.

Upload flowDrop zone kéo-thả, click để chọn file.
Chỉ chấp nhận JPG/PNG.
Báo lỗi ngay nếu file > 10MB hoặc không phải image.
Sau khi chọn ảnh, hiển thị preview.
Có modal crop ảnh, crop ratio gợi ý 3:1 như biển số xe.
Có slider zoom, nút Confirm/Cancel.
Trong lúc upload phải disable control và hiển thị loading state.
Sau khi upload thành công, tự động điều hướng sang trang detail của request mới.

Request listDesktop: table gọn, dễ scan.
Mobile: chuyển sang card list hoặc stacked list.
Mỗi item hiển thị:thumbnail ảnh
status badge
plate_number nếu có
created_at

Row/card có thể click để đi tới detail.
Nếu thumbnail lỗi, thay bằng placeholder icon.
Badge trạng thái phải rất rõ:NOT_STARTED gray
PENDING yellow
COMPLETED green
NEEDS_REVIEW orange
FAILED red

Nên có subtle pulse cho PENDING.

Detail pageDesktop: layout 2 cột.Cột trái: ảnh lớn với bounding box overlay
Cột phải: thông tin, trạng thái, confidence, metadata, hành động

Mobile: xếp dọc, ảnh lên trên, info dưới
Hiển thị:request ID rút gọn
created_at và updated_at
status badge
plate_number thật nổi bật nếu có
image viewer với zoom/reset
bounding box overlay nếu có
plate_region
error_message nếu FAILED

Khi đang xử lý:hiển thị spinner + “Processing...”
polling tự động mỗi 2s cho chi tiết, dừng khi terminal

Khi kết quả xấu:NEEDS_REVIEW phải có banner/cảnh báo màu cam
giải thích đây là kết quả dưới ngưỡng tin cậy

Có nút reprocess chỉ hiện khi status là FAILED hoặc NEEDS_REVIEW
Reprocess phải có confirmation dialog
Sau khi reprocess thành công:cache update ngay
status quay về NOT_STARTED
polling tiếp tục
thông báo “Reprocessing started”


Confidence UI
Thiết kế một khối confidence rõ ràng, không mơ hồ:
Overall confidence: progress bar 0-100%
Màu theo ngưỡng:= 85: xanh


= 60 và < 85: cam


< 60: đỏ

Breakdown:detection_confidence
ocr_confidence
confidence_score

Nếu toàn bộ confidence còn null, ẩn section này để tránh hiển thị dữ liệu chưa có.
Có tooltip ngắn giải thích từng loại confidence.
Có badge/flag nếu needs_review = true.
Bounding box overlay
Hiển thị rectangle từ bounding_box trên ảnh.
Coordinates theo pixel: x, y, width, height.
Overlay phải scale đúng khi resize ảnh.
Nếu không có bbox thì chỉ hiển thị ảnh thường.
Label nhỏ “Plate” trên box là đủ, không cần trang trí thêm.
Trạng thái cần thiết kế rõ
NOT_STARTED: đã tạo nhưng chưa vào worker
PENDING: worker đang xử lý
COMPLETED: nhận diện thành công
NEEDS_REVIEW: có kết quả nhưng cần kiểm tra thủ công
FAILED: xử lý lỗi hoặc không ra kết quả sau retry
Map nhãn tiếng Việt có thể dùng:
Chưa bắt đầu
Đang xử lý
Hoàn tất
Cần duyệt
Thất bại
Tông visual
Gọn, hiện đại, mang cảm giác công cụ nội bộ chuyên nghiệp.
Dùng khoảng trắng vừa phải, typography rõ, hierarchy mạnh.
Dark mode phải là chế độ đầu tiên được hỗ trợ thật sự, không chỉ đổi màu bề mặt.
Không dùng hero lớn, gradient trang trí, blur orb, hay card marketing.
Các section chính nên là khối thẳng, dễ scan, ưu tiên chiều sâu thông tin.
Nút hành động dùng icon rõ ràng, ngắn gọn.
Mọi text phải fit tốt trên mobile và desktop.
Layout phải giữ nhịp ổn định, tránh nhảy khi loading hay khi status đổi.
Accessibility
Drop zone có aria-label rõ.
Badge trạng thái có nhãn cho screen reader.
Progress bar có role="progressbar" và aria-valuenow.
Modal crop và confirm dialog phải có focus trap, đóng bằng Escape.
Tab order phải logic.
Contrast đạt chuẩn AA.
Các state quan trọng phải có
Empty state home
Loading state list
Loading state detail
Upload error state
404 request not found
Failed result state
Needs review state
Reprocess confirmation state
Optimistic update state khi reprocess
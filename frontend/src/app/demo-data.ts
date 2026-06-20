import type { UiRequest } from './types'

const svgDataUrl = (label: string, accent: string) =>
  `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(`
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 675">
      <defs>
        <linearGradient id="g" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%" stop-color="#0f172a" />
          <stop offset="100%" stop-color="#1f2937" />
        </linearGradient>
      </defs>
      <rect width="1200" height="675" fill="url(#g)" />
      <rect x="60" y="70" width="1080" height="535" rx="28" fill="none" stroke="${accent}" stroke-width="8" opacity="0.7" />
      <rect x="360" y="250" width="480" height="140" rx="20" fill="white" opacity="0.95" />
      <rect x="390" y="285" width="420" height="70" rx="14" fill="${accent}" opacity="0.18" />
      <text x="600" y="323" font-size="64" fill="#0f172a" font-family="Arial, Helvetica, sans-serif" text-anchor="middle" font-weight="700">${label}</text>
    </svg>
  `)}`

const now = Date.now()

export const demoRequests: UiRequest[] = [
  {
    id: 'demo_01',
    image_url: svgDataUrl('51F-928.44', '#f59e0b'),
    media_url: svgDataUrl('51F-928.44', '#f59e0b'),
    media_type: 'image',
    thumbnail_url: svgDataUrl('51F-928.44', '#f59e0b'),
    plate_number: '51F-928.44',
    status: 'COMPLETED',
    error_message: null,
    created_at: new Date(now - 1000 * 60 * 8).toISOString(),
    updated_at: new Date(now - 1000 * 60 * 6).toISOString(),
    confidence_score: 93,
    detection_confidence: 96,
    ocr_confidence: 91,
    needs_review: false,
    bounding_box: { x: 392, y: 246, width: 416, height: 148 },
    plate_region: 'BR',
    gate: 'Cổng Chính',
    direction: 'IN',
    camera_id: 'CAM-01',
    display_name: 'Camera cổng chính',
  },
  {
    id: 'demo_02',
    image_url: svgDataUrl('30H-772.18', '#fb923c'),
    media_url: svgDataUrl('30H-772.18', '#fb923c'),
    media_type: 'image',
    thumbnail_url: svgDataUrl('30H-772.18', '#fb923c'),
    plate_number: '30H-772.18',
    status: 'NEEDS_REVIEW',
    error_message: null,
    created_at: new Date(now - 1000 * 60 * 24).toISOString(),
    updated_at: new Date(now - 1000 * 60 * 21).toISOString(),
    confidence_score: 68,
    detection_confidence: 82,
    ocr_confidence: 61,
    needs_review: true,
    bounding_box: { x: 402, y: 262, width: 394, height: 122 },
    plate_region: 'BR',
    gate: 'Cổng Phụ 1',
    direction: 'OUT',
    camera_id: 'CAM-03',
    display_name: 'Ảnh cần duyệt',
  },
  {
    id: 'demo_03',
    image_url: svgDataUrl('Đang xử lý', '#fde047'),
    media_url: svgDataUrl('Đang xử lý', '#fde047'),
    media_type: 'image',
    thumbnail_url: svgDataUrl('Đang xử lý', '#fde047'),
    plate_number: null,
    status: 'PENDING',
    error_message: null,
    created_at: new Date(now - 1000 * 45).toISOString(),
    updated_at: new Date(now - 1000 * 20).toISOString(),
    confidence_score: null,
    detection_confidence: null,
    ocr_confidence: null,
    needs_review: false,
    bounding_box: null,
    plate_region: null,
    gate: 'Cổng Cấp Cứu',
    direction: 'IN',
    camera_id: 'CAM-05',
    display_name: 'Request đang chạy',
  },
  {
    id: 'demo_04',
    image_url: svgDataUrl('FAILED', '#ef4444'),
    media_url: svgDataUrl('FAILED', '#ef4444'),
    media_type: 'image',
    thumbnail_url: svgDataUrl('FAILED', '#ef4444'),
    plate_number: null,
    status: 'FAILED',
    error_message: 'Ảnh quá tối, worker không xác định được vùng biển số sau 3 lần thử.',
    created_at: new Date(now - 1000 * 60 * 95).toISOString(),
    updated_at: new Date(now - 1000 * 60 * 92).toISOString(),
    confidence_score: 24,
    detection_confidence: 31,
    ocr_confidence: 18,
    needs_review: false,
    bounding_box: null,
    plate_region: null,
    gate: 'Cổng Chính',
    direction: 'IN',
    camera_id: 'CAM-01',
    display_name: 'Request lỗi',
  },
]

export type RecognitionStatus =
  | 'NOT_STARTED'
  | 'PENDING'
  | 'COMPLETED'
  | 'NEEDS_REVIEW'
  | 'FAILED'

export interface BoundingBox {
  x: number
  y: number
  width: number
  height: number
}

export interface RecognitionRequest {
  id: string
  image_url: string
  plate_number: string | null
  status: RecognitionStatus
  error_message: string | null
  created_at: string
  updated_at: string
  confidence_score: number | null
  detection_confidence: number | null
  ocr_confidence: number | null
  needs_review: boolean
  bounding_box: BoundingBox | null
  plate_region: string | null
}

export interface RecognitionSubmitResponse {
  request_id: string
  status: RecognitionStatus
  created_at: string
  image_url: string
}

export interface RecognitionListResponse {
  items: RecognitionRequest[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface ApiErrorShape {
  detail: string
}

export interface ApiError extends Error {
  status: number
  detail: string
}

export interface RequestMeta {
  gate?: string
  direction?: 'IN' | 'OUT'
  camera_id?: string
}

export type UiRequest = RecognitionRequest &
  RequestMeta & {
    media_type: 'image' | 'video'
    media_url: string
    thumbnail_url?: string
    display_name?: string
  }

export const terminalStatuses: RecognitionStatus[] = ['COMPLETED', 'FAILED', 'NEEDS_REVIEW']

export const isTerminalStatus = (status: RecognitionStatus) => terminalStatuses.includes(status)

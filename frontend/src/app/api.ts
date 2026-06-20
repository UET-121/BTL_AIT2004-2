import type {
  ApiError,
  RecognitionListResponse,
  RecognitionRequest,
  RecognitionSubmitResponse,
} from './types'

const baseUrl = (import.meta.env.VITE_API_URL ?? '').trim().replace(/\/$/, '')

async function readError(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown }
    if (typeof payload.detail === 'string') return payload.detail
    if (Array.isArray(payload.detail)) return payload.detail.map(String).join(', ')
  } catch {
    // fall through
  }
  return response.statusText || 'Request failed'
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: init?.headers,
  })

  if (!response.ok) {
    const error = new Error(await readError(response)) as ApiError
    error.status = response.status
    error.detail = error.message
    throw error
  }

  return (await response.json()) as T
}

export function getApiBaseUrl() {
  return baseUrl || 'same-origin proxy'
}

export async function listRecognitions(page: number, pageSize: number) {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
  return requestJson<RecognitionListResponse>(`/api/v1/recognition?${params.toString()}`)
}

export async function getRecognition(requestId: string) {
  return requestJson<RecognitionRequest>(`/api/v1/recognition/${requestId}`)
}

export async function uploadRecognition(file: File) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${baseUrl}/api/v1/recognition`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const error = new Error(await readError(response)) as ApiError
    error.status = response.status
    error.detail = error.message
    throw error
  }

  return (await response.json()) as RecognitionSubmitResponse
}

export async function reprocessRecognition(requestId: string) {
  return requestJson<RecognitionSubmitResponse>(`/api/v1/recognition/${requestId}/reprocess`, {
    method: 'POST',
  })
}

import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import {
  Activity,
  AlertTriangle,
  ArrowDownLeft,
  ArrowUpRight,
  Camera,
  Check,
  ChevronLeft,
  ChevronRight,
  Eye,
  FileImage,
  Loader2,
  RefreshCcw,
  RotateCcw,
  Search,
  UploadCloud,
  Trash2,
  X,
  ZoomIn,
} from 'lucide-react'
import { deleteRecognition, getApiBaseUrl, getRecognition, listRecognitions, reprocessRecognition, uploadRecognition } from './api'
import type { BoundingBox, RecognitionRequest, RecognitionStatus, RecognitionSubmitResponse, UiRequest } from './types'
import { isTerminalStatus } from './types'

type RouteState =
  | { view: 'home' }
  | { view: 'detail'; id: string }
  | { view: 'not-found' }

type LoadMode = 'api' | 'demo'
type ToastState = { message: string; kind: 'success' | 'warning' | 'error' } | null

const PAGE_SIZES = [5, 10, 20]
const POLL_MS = 2000
const MAX_MEDIA_SIZE = 50 * 1024 * 1024
const ALLOWED_TYPES = new Set(['image/jpeg', 'image/png', 'video/mp4', 'video/mpeg', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska'])
const MEDIA_VIDEO_RE = /\.(mp4|avi|mov|mpeg|mkv)(?:$|\?)/i

function resolveMediaUrl(url: string) {
  if (!url) return url
  if (/^(https?:|data:|blob:|\/\/)/i.test(url)) return url
  if (url.startsWith('/')) {
    const apiBase = getApiBaseUrl()
    if (apiBase && apiBase !== 'same-origin proxy') {
      return new URL(url, apiBase).toString()
    }
  }
  return url
}

function isVideoMedia(url: string) {
  return MEDIA_VIDEO_RE.test(url)
}


const statusLabel: Record<RecognitionStatus, string> = {
  NOT_STARTED: 'Chưa bắt đầu',
  PENDING: 'Đang xử lý',
  COMPLETED: 'Hoàn tất',
  NEEDS_REVIEW: 'Cần duyệt',
  FAILED: 'Thất bại',
}

const statusClass: Record<RecognitionStatus, string> = {
  NOT_STARTED: 'bg-slate-500/15 text-slate-300 ring-slate-400/25',
  PENDING: 'bg-yellow-500/15 text-yellow-200 ring-yellow-400/30 animate-pulse',
  COMPLETED: 'bg-emerald-500/15 text-emerald-200 ring-emerald-400/30',
  NEEDS_REVIEW: 'bg-orange-500/15 text-orange-200 ring-orange-400/35',
  FAILED: 'bg-red-500/15 text-red-200 ring-red-400/35',
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('vi-VN', {
    hour: '2-digit',
    minute: '2-digit',
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(new Date(value))
}

function formatTimeSpan(seconds: number) {
  const minutes = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return minutes > 0 ? `${minutes}:${secs.toString().padStart(2, '0')}` : `${secs}s`
}

function formatShortId(id: string) {
  return `#${id.slice(0, 8)}`
}

function isAllowedMedia(file: File) {
  return ALLOWED_TYPES.has(file.type) || file.name.match(/\.(mp4|avi|mov|mpeg|mkv)/i)
}

function makeObjectUrl(file: Blob) {
  return URL.createObjectURL(file)
}

function normalizeRequest(item: RecognitionRequest): UiRequest {
  const mediaUrl = resolveMediaUrl(item.image_url)
  const isVideo = isVideoMedia(mediaUrl)
  return {
    ...item,
    media_type: isVideo ? 'video' : 'image',
    media_url: mediaUrl,
    thumbnail_url: mediaUrl,
  }
}


function statusBadge(status: RecognitionStatus) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${statusClass[status]}`}>
      {statusLabel[status]}
    </span>
  )
}

function confidenceColor(value: number) {
  if (value >= 85) return 'text-emerald-300'
  if (value >= 60) return 'text-orange-300'
  return 'text-red-300'
}

function confidenceBar(value: number) {
  if (value >= 85) return 'bg-emerald-500'
  if (value >= 60) return 'bg-orange-400'
  return 'bg-red-500'
}

function terminal(status: RecognitionStatus) {
  return isTerminalStatus(status)
}

function currentRoute(): RouteState {
  const path = window.location.pathname
  if (path === '/' || path === '') return { view: 'home' }
  const match = path.match(/^\/requests\/([^/]+)$/)
  if (match) return { view: 'detail', id: decodeURIComponent(match[1]) }
  return { view: 'not-found' }
}

function navigate(route: RouteState) {
  const path = route.view === 'home' ? '/' : route.view === 'detail' ? `/requests/${encodeURIComponent(route.id)}` : '/404'
  window.history.pushState({}, '', path)
  window.dispatchEvent(new PopStateEvent('popstate'))
}

function loadImage(src: string) {
  return new Promise<HTMLImageElement>((resolve, reject) => {
    const image = new Image()
    image.onload = () => resolve(image)
    image.onerror = () => reject(new Error('Không tải được ảnh crop'))
    image.src = src
  })
}

async function createCroppedImage(file: File, zoom: number) {
  const objectUrl = makeObjectUrl(file)
  try {
    const image = await loadImage(objectUrl)
    const ratio = 3 / 1
    const sourceRatio = image.width / image.height

    let cropWidth = image.width / zoom
    let cropHeight = image.height / zoom

    if (sourceRatio > ratio) {
      cropHeight = image.height / zoom
      cropWidth = cropHeight * ratio
    } else {
      cropWidth = image.width / zoom
      cropHeight = cropWidth / ratio
    }

    cropWidth = Math.min(cropWidth, image.width)
    cropHeight = Math.min(cropHeight, image.height)

    const sx = Math.max(0, (image.width - cropWidth) / 2)
    const sy = Math.max(0, (image.height - cropHeight) / 2)

    const canvas = document.createElement('canvas')
    canvas.width = Math.max(1, Math.round(cropWidth))
    canvas.height = Math.max(1, Math.round(cropHeight))

    const ctx = canvas.getContext('2d')
    if (!ctx) throw new Error('Trình duyệt không hỗ trợ canvas')

    ctx.drawImage(image, sx, sy, cropWidth, cropHeight, 0, 0, canvas.width, canvas.height)

    const blob = await new Promise<Blob>((resolve, reject) => {
      canvas.toBlob((value) => {
        if (value) resolve(value)
        else reject(new Error('Không thể tạo file crop'))
      }, 'image/jpeg', 0.92)
    })

    const previewUrl = makeObjectUrl(blob)
    const output = new File([blob], `${file.name.replace(/\.[^.]+$/, '') || 'upload'}.jpg`, {
      type: 'image/jpeg',
    })

    return { file: output, previewUrl }
  } finally {
    URL.revokeObjectURL(objectUrl)
  }
}

function AppShell({ children }: { children: ReactNode }) {
  return <div className="min-h-screen bg-background text-foreground">{children}</div>
}

function Header({
  onRefresh,
  onToggleTheme,
  processingCount,
  refreshing,
}: {
  onRefresh: () => void | Promise<void>
  onToggleTheme: () => void
  processingCount: number
  refreshing: boolean
}) {
  return (
    <header className="sticky top-0 z-30 border-b border-border/80 bg-background/95 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-3 px-4 py-3 sm:px-6">
        <button
          type="button"
          onClick={() => navigate({ view: 'home' })}
          className="flex items-center gap-3 text-left"
        >
          <div className="grid size-10 place-items-center border border-border bg-card font-mono text-xs font-semibold tracking-wider">
            ALPR
          </div>
          <div>
            <p className="text-sm font-semibold leading-tight">License Plate Admin</p>
            <p className="font-mono text-[11px] text-muted-foreground">HyperCan Team</p>
          </div>
        </button>

        <div className="flex items-center gap-2 sm:gap-3">
          <div className="hidden items-center gap-2 rounded-full border border-border bg-card px-3 py-1.5 text-xs text-muted-foreground sm:flex">
            <div className={`size-2 rounded-full ${processingCount > 0 ? 'bg-yellow-400 animate-pulse' : 'bg-emerald-400'}`} />
            <span>{processingCount > 0 ? `${processingCount} job đang xử lý` : 'Hệ thống ổn định'}</span>
          </div>
          <button
            type="button"
            onClick={onRefresh}
            disabled={refreshing}
            className="inline-flex size-10 items-center justify-center border border-border bg-card transition hover:bg-secondary disabled:cursor-not-allowed disabled:opacity-60"
            aria-label="Refresh"
            title="Refresh"
          >
            <RefreshCcw size={16} className={refreshing ? 'animate-spin' : ''} />
          </button>
          <button
            type="button"
            onClick={onToggleTheme}
            className="inline-flex items-center justify-center border border-border bg-card px-3 py-2 text-sm transition hover:bg-secondary"
          >
            Theme
          </button>
        </div>
      </div>
    </header>
  )
}

function UploadPanel({
  onSubmit,
  busy,
}: {
  onSubmit: (payload: { file: File; previewUrl: string }) => Promise<void>
  busy: boolean
}) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState('')
  const [previewUrl, setPreviewUrl] = useState('')
  const [cropOpen, setCropOpen] = useState(false)
  const [zoom, setZoom] = useState(1)
  const [busyLocal, setBusyLocal] = useState(false)

  useEffect(() => {
    return () => {
      if (previewUrl.startsWith('blob:')) URL.revokeObjectURL(previewUrl)
    }
  }, [previewUrl])

  const reset = () => {
    setFile(null)
    setError('')
    setCropOpen(false)
    setZoom(1)
  }

  const pick = (picked?: File) => {
    setError('')
    setFile(null)
    setCropOpen(false)
    if (previewUrl.startsWith('blob:')) URL.revokeObjectURL(previewUrl)
    setPreviewUrl('')
    if (!picked) return
    if (!isAllowedMedia(picked)) {
      setError('Chỉ chấp nhận ảnh JPG/PNG hoặc video MP4/AVI/MOV/MKV.')
      return
    }
    if (picked.size > MAX_MEDIA_SIZE) {
      setError('File vượt quá 50MB.')
      return
    }
    if (previewUrl.startsWith('blob:')) URL.revokeObjectURL(previewUrl)
    const nextPreview = makeObjectUrl(picked)
    setFile(picked)
    setPreviewUrl(nextPreview)
    
    const isVid = picked.type.startsWith('video/') || picked.name.match(/\.(mp4|avi|mov|mpeg|mkv)/i)
    if (isVid) {
      setCropOpen(false)
    } else {
      setCropOpen(true)
    }
  }

  const confirm = async () => {
    if (!file) return
    setBusyLocal(true)
    try {
      const cropped = await createCroppedImage(file, zoom)
      await onSubmit(cropped)
      reset()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload thất bại')
    } finally {
      setBusyLocal(false)
    }
  }

  return (
    <section className="border-b border-border bg-card/40">
      <div className="mx-auto max-w-7xl px-4 py-5 sm:px-6">
        <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
          <button
            type="button"
            aria-label="Kéo thả hoặc chọn ảnh biển số"
            disabled={busy || busyLocal}
            onClick={() => inputRef.current?.click()}
            onDrop={(event) => {
              event.preventDefault()
              pick(event.dataTransfer.files[0])
            }}
            onDragOver={(event) => event.preventDefault()}
            className="group flex min-h-40 items-center justify-center border border-dashed border-border bg-background/80 p-5 text-left transition hover:border-accent disabled:opacity-60"
          >
            <input
              ref={inputRef}
              type="file"
              accept="image/jpeg,image/png,video/mp4,video/quicktime,video/x-msvideo,video/x-matroska"
              className="hidden"
              onChange={(event) => pick(event.target.files?.[0])}
            />
            <div className="flex w-full flex-col gap-3 sm:flex-row sm:items-center">
              <div className="grid size-12 shrink-0 place-items-center rounded bg-secondary text-foreground">
                <UploadCloud size={22} />
              </div>
              <div className="space-y-1">
                <h2 className="text-lg font-semibold">Upload ảnh/video biển số</h2>
                <p className="text-sm text-muted-foreground">JPG/PNG/MP4/AVI/MOV tối đa 50MB. Ảnh sẽ được crop 3:1.</p>
                {file && (
                  <p className="inline-flex items-center gap-1.5 text-sm text-accent">
                    <FileImage size={13} />
                    {file.name} · {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                )}
                {error && <p className="text-sm font-medium text-red-300">{error}</p>}
              </div>
            </div>
          </button>

          <div className="space-y-4 border border-border bg-background p-4">
            <div className="space-y-2">
              <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">Trạng thái</p>
              <p className="text-sm text-muted-foreground">Upload xong sẽ tự động điều hướng sang detail và polling.</p>
            </div>
            <button
              type="button"
              disabled={!file || busy || busyLocal}
              onClick={async () => {
                if (file) {
                  const isVid = file.type.startsWith('video/') || file.name.match(/\.(mp4|avi|mov|mpeg|mkv)/i)
                  if (isVid) {
                    setBusyLocal(true)
                    try {
                      await onSubmit({ file, previewUrl })
                      reset()
                    } catch (err) {
                      setError(err instanceof Error ? err.message : 'Upload thất bại')
                    } finally {
                      setBusyLocal(false)
                    }
                  } else {
                    setCropOpen(true)
                  }
                }
              }}
              className="inline-flex w-full items-center justify-center gap-2 bg-accent px-4 py-2.5 font-semibold text-accent-foreground transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {busy || busyLocal ? <Loader2 size={16} className="animate-spin" /> : <Check size={16} />}
              {busy || busyLocal ? 'Đang upload...' : (file && (file.type.startsWith('video/') || file.name.match(/\.(mp4|avi|mov|mpeg|mkv)/i)) ? 'Upload Video' : 'Crop & Upload')}
            </button>
          </div>
        </div>
      </div>

      {cropOpen && file && (
        <div
          role="dialog"
          aria-modal="true"
          onKeyDown={(event) => {
            if (event.key === 'Escape') setCropOpen(false)
          }}
          className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-4"
        >
          <div className="w-full max-w-2xl border border-border bg-card p-4 shadow-2xl">
            <div className="mb-3 flex items-center justify-between gap-3">
              <div>
                <h3 className="font-semibold">Crop ảnh 3:1</h3>
                <p className="text-sm text-muted-foreground">Phóng to/thu nhỏ trước khi gửi lên backend.</p>
              </div>
              <button type="button" onClick={() => setCropOpen(false)} className="p-2 hover:bg-secondary" aria-label="Đóng">
                <X size={18} />
              </button>
            </div>

            <div className="relative mx-auto aspect-[3/1] max-h-80 overflow-hidden border border-accent bg-black">
              {previewUrl && <img src={previewUrl} alt="Preview" className="h-full w-full object-cover" style={{ transform: `scale(${zoom})` }} />}
              <div className="absolute inset-4 border-2 border-accent">
                <span className="bg-accent px-2 py-0.5 font-mono text-xs text-accent-foreground">3:1</span>
              </div>
            </div>

            <label className="mt-4 block text-sm">
              Zoom
              <input
                type="range"
                min="1"
                max="2"
                step="0.05"
                value={zoom}
                onChange={(event) => setZoom(Number(event.target.value))}
                className="mt-2 w-full"
              />
            </label>

            <div className="mt-4 flex justify-end gap-2">
              <button type="button" className="border border-border px-4 py-2 hover:bg-secondary" onClick={() => setCropOpen(false)}>
                Cancel
              </button>
              <button
                type="button"
                disabled={busy || busyLocal}
                onClick={confirm}
                className="inline-flex items-center gap-2 bg-primary px-4 py-2 text-primary-foreground disabled:opacity-60"
              >
                {busy || busyLocal ? <Loader2 size={16} className="animate-spin" /> : <Check size={16} />}
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  )
}

function ListSkeleton() {
  return (
    <div className="space-y-2">
      {Array.from({ length: 5 }).map((_, index) => (
        <div key={index} className="h-16 animate-pulse border border-border bg-card" />
      ))}
    </div>
  )
}

function EmptyState() {
  return (
    <div className="border border-border bg-card p-10 text-center">
      <FileImage className="mx-auto text-muted-foreground" />
      <h3 className="mt-3 font-semibold">Chưa có dữ liệu nhận diện</h3>
      <p className="text-sm text-muted-foreground">Upload một ảnh biển số để bắt đầu luồng kiểm thử.</p>
    </div>
  )
}

function NetworkBanner({ message }: { message: string }) {
  return (
    <div className="border border-orange-400/30 bg-orange-500/10 px-4 py-3 text-sm text-orange-100">
      <AlertTriangle className="mr-2 inline" size={16} />
      {message}
    </div>
  )
}

function DeleteConfirmDialog({
  item,
  onCancel,
  onConfirm,
  busy,
}: {
  item: UiRequest
  onCancel: () => void
  onConfirm: () => void
  busy: boolean
}) {
  return (
    <div role="dialog" aria-modal="true" className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-4">
      <div className="w-full max-w-md border border-border bg-card p-5 shadow-2xl">
        <h3 className="font-semibold">Xóa mẫu này?</h3>
        <p className="mt-2 text-sm text-muted-foreground">
          Mẫu <span className="font-mono">{formatShortId(item.id)}</span> sẽ bị xóa khỏi database và storage, bất kể đang ở trạng thái nào.
        </p>
        <div className="mt-4 rounded border border-border bg-background px-3 py-2 text-sm">
          <div className="flex items-center justify-between gap-4">
            <span className="text-muted-foreground">Trạng thái</span>
            <span className="font-mono">{item.status}</span>
          </div>
          <div className="mt-1 flex items-center justify-between gap-4">
            <span className="text-muted-foreground">Biển số</span>
            <span className="font-mono">{item.plate_number || '—'}</span>
          </div>
        </div>
        <div className="mt-5 flex justify-end gap-2">
          <button type="button" className="border border-border px-4 py-2 hover:bg-secondary" onClick={onCancel} disabled={busy}>
            Cancel
          </button>
          <button
            type="button"
            className="inline-flex items-center gap-2 border border-red-400/20 bg-red-500/10 px-4 py-2 text-red-100 hover:bg-red-500/20 disabled:opacity-60"
            onClick={onConfirm}
            disabled={busy}
          >
            <Trash2 size={16} /> {busy ? 'Deleting...' : 'Delete'}
          </button>
        </div>
      </div>
    </div>
  )
}

function RequestThumb({ item }: { item: UiRequest }) {
  const [broken, setBroken] = useState(false)
  const [hovered, setHovered] = useState(false)
  const src = resolveMediaUrl(item.thumbnail_url || item.media_url)
  const isVideo = isVideoMedia(src)

  return (
    <div
      className="relative h-full w-full overflow-hidden bg-secondary transition-colors duration-200"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {broken ? (
        <div className="grid h-full w-full place-items-center text-muted-foreground">
          <FileImage size={22} />
        </div>
      ) : isVideo ? (
        hovered ? (
          <video
            src={src}
            className="h-full w-full object-cover"
            muted
            playsInline
            autoPlay
            loop
            preload="metadata"
            onError={() => setBroken(true)}
          />
        ) : (
          <div className="flex h-full w-full flex-col items-center justify-center gap-1 bg-slate-800 text-slate-400">
            <Camera size={18} />
            <span className="font-mono text-[9px] uppercase tracking-wider bg-slate-900/60 px-1 py-0.5 rounded text-slate-300">
              Video
            </span>
          </div>
        )
      ) : (
        <img src={src} onError={() => setBroken(true)} alt="Thumbnail" className="h-full w-full object-cover" />
      )}
      {item.status === 'PENDING' && <div className="absolute inset-0 bg-black/10" />}
    </div>
  )
}

function RequestList({
  loading,
  items,
  onOpen,
  onDelete,
}: {
  loading: boolean
  items: UiRequest[]
  onOpen: (id: string) => void
  onDelete: (item: UiRequest) => void
}) {
  if (loading) return <ListSkeleton />
  if (!items.length) return <EmptyState />

  return (
    <div className="overflow-hidden border border-border bg-card">
      <table className="hidden w-full text-sm md:table">
        <thead className="bg-secondary text-left text-xs uppercase tracking-wider text-muted-foreground">
          <tr>
            <th className="p-3">Phương tiện</th>
            <th className="px-3">Trạng thái</th>
            <th className="px-3">Biển số</th>
            <th className="px-3">Thời gian</th>
            <th className="pr-3 text-right">Mở</th>
            <th className="pr-3 text-right">Xóa</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id} onClick={() => onOpen(item.id)} className="cursor-pointer border-t border-border hover:bg-secondary/60">
              <td className="p-3">
                <div className="h-14 w-24 overflow-hidden border border-border">
                  <RequestThumb item={item} />
                </div>
              </td>
              <td className="px-3">{statusBadge(item.status)}</td>
              <td className="px-3 font-mono text-base font-semibold">{item.plate_number || '—'}</td>
              <td className="px-3 font-mono text-xs text-muted-foreground">{formatDate(item.created_at)}</td>
              <td className="pr-3 text-right">
                <Eye className="inline" size={17} />
              </td>
              <td className="pr-3 text-right">
                <button
                  type="button"
                  onClick={(event) => {
                    event.stopPropagation()
                    onDelete(item)
                  }}
                  className="inline-flex items-center gap-1 rounded border border-red-400/20 bg-red-500/10 px-2 py-1 text-xs text-red-100 hover:bg-red-500/20"
                  aria-label={`Delete ${item.id}`}
                  title="Delete"
                >
                  <Trash2 size={14} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="divide-y divide-border md:hidden">
        {items.map((item) => (
          <div
            key={item.id}
            role="button"
            tabIndex={0}
            onClick={() => onOpen(item.id)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault()
                onOpen(item.id)
              }
            }}
            className="flex w-full gap-3 p-3 text-left"
          >
            <div className="h-16 w-24 shrink-0 overflow-hidden border border-border">
              <RequestThumb item={item} />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap gap-1">
                {statusBadge(item.status)}
              </div>
              <p className="mt-1.5 truncate font-mono font-semibold">{item.plate_number || formatShortId(item.id)}</p>
              <p className="text-xs text-muted-foreground">{formatDate(item.created_at)}</p>
            </div>
            <button
              type="button"
              onClick={(event) => {
                event.stopPropagation()
                onDelete(item)
              }}
              className="ml-auto inline-flex h-9 shrink-0 items-center justify-center rounded border border-red-400/20 bg-red-500/10 px-2 text-red-100 hover:bg-red-500/20"
              aria-label={`Delete ${item.id}`}
              title="Delete"
            >
              <Trash2 size={14} />
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}

function ConfidenceCard({ item }: { item: UiRequest }) {
  const values = [item.confidence_score, item.detection_confidence, item.ocr_confidence]
  if (values.every((value) => value == null)) return null
  const overall = item.confidence_score ?? 0

  return (
    <div className="border border-border bg-background p-4">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="font-semibold">Confidence</h3>
        {item.needs_review && <span className="bg-orange-500/15 px-2 py-1 text-xs text-orange-200">needs_review</span>}
      </div>
      <div role="progressbar" aria-valuenow={overall} aria-valuemin={0} aria-valuemax={100} className="h-2 bg-secondary">
        <div className={`h-full ${confidenceBar(overall)}`} style={{ width: `${overall}%` }} />
      </div>
      <p className="mt-2 font-mono text-2xl font-semibold">{overall}%</p>
      {[
        ['Detection', item.detection_confidence, 'Độ tin cậy vùng biển số'],
        ['OCR', item.ocr_confidence, 'Độ tin cậy ký tự'],
        ['Overall', item.confidence_score, 'Điểm tổng hợp'],
      ].map(([label, value, tip]) => (
        <div key={label as string} title={tip as string} className="mt-3 flex items-center justify-between text-sm">
          <span className="text-muted-foreground">{label}</span>
          <span className={`font-mono ${confidenceColor((value as number) ?? 0)}`}>{value ?? '—'}%</span>
        </div>
      ))}
    </div>
  )
}

function BboxOverlay({ boundingBox }: { boundingBox: BoundingBox | null }) {
  if (!boundingBox) return null
  return (
    <div
      className="absolute border-2 border-accent"
      style={{
        left: `${boundingBox.x}%`,
        top: `${boundingBox.y}%`,
        width: `${boundingBox.width}%`,
        height: `${boundingBox.height}%`,
      }}
    >
      <span className="absolute -top-6 left-0 bg-accent px-2 py-0.5 font-mono text-xs text-accent-foreground">Plate</span>
    </div>
  )
}

function DetailView({
  item,
  loading,
  onBack,
  onReprocess,
  onDelete,
}: {
  item: UiRequest | null
  loading: boolean
  onBack: () => void
  onReprocess: (id: string) => void
  onDelete: (item: UiRequest) => void
}) {
  const [zoom, setZoom] = useState(1)
  const [confirm, setConfirm] = useState(false)
  const [natural, setNatural] = useState<{ width: number; height: number } | null>(null)

  useEffect(() => {
    setNatural(null)
    setZoom(1)
  }, [item?.id])

  if (loading) {
    return (
      <main className="mx-auto max-w-7xl px-4 py-5 sm:px-6">
        <div className="h-10 w-28 animate-pulse bg-secondary" />
        <div className="mt-4 grid gap-5 lg:grid-cols-[minmax(0,1.35fr)_420px]">
          <div className="h-96 animate-pulse border border-border bg-card" />
          <div className="space-y-4">
            <div className="h-56 animate-pulse border border-border bg-card" />
            <div className="h-44 animate-pulse border border-border bg-card" />
          </div>
        </div>
      </main>
    )
  }

  if (!item) {
    return (
      <main className="mx-auto max-w-5xl p-6">
        <button type="button" onClick={onBack} className="mb-4 text-sm text-muted-foreground">
          ← Back
        </button>
        <div className="border border-border bg-card p-8">
          <h2>404 request not found</h2>
          <p className="text-muted-foreground">Không tìm thấy request trong dữ liệu hiện tại.</p>
        </div>
      </main>
    )
  }

  const bboxStyle = natural && item.bounding_box
    ? {
        left: `${(item.bounding_box.x / natural.width) * 100}%`,
        top: `${(item.bounding_box.y / natural.height) * 100}%`,
        width: `${(item.bounding_box.width / natural.width) * 100}%`,
        height: `${(item.bounding_box.height / natural.height) * 100}%`,
      }
    : null

  return (
    <main className="mx-auto max-w-7xl px-4 py-5 sm:px-6">
      <button type="button" onClick={onBack} className="mb-4 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
        <ChevronLeft size={16} /> Danh sách
      </button>

      {item.status === 'NEEDS_REVIEW' && (
        <NetworkBanner message="Kết quả dưới ngưỡng tin cậy, cần kiểm tra thủ công trước khi sử dụng." />
      )}
      {item.status === 'PENDING' && (
        <div className="mb-4 border border-yellow-400/25 bg-yellow-500/10 p-3 text-sm text-yellow-100">
          <Loader2 className="mr-2 inline animate-spin" size={16} />
          Processing...
        </div>
      )}

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1.35fr)_420px]">
        <section className="border border-border bg-card p-3">
          <div className="mb-3 flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs text-muted-foreground">MEDIA VIEWER</span>
              <span className="inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs font-semibold ring-1 bg-slate-500/10 text-slate-300 ring-slate-400/20">
                <FileImage size={11} />
                {item.media_type === 'video' ? 'Video' : 'Phương tiện'}
              </span>
            </div>
            <div className="flex gap-2">
              <button type="button" aria-label="Zoom in" onClick={() => setZoom((value) => Math.min(2, value + 0.15))} className="border border-border p-2 hover:bg-secondary">
                <ZoomIn size={16} />
              </button>
              <button type="button" onClick={() => setZoom(1)} className="border border-border px-3 py-2 text-sm">
                Reset
              </button>
            </div>
          </div>

          <div className="relative overflow-hidden bg-black">
            <div style={{ transform: `scale(${zoom})`, transformOrigin: 'center' }} className="relative">
              {item.media_type === 'video' ? (
                <video
                  src={item.media_url}
                  className="aspect-[16/10] w-full object-cover"
                  controls
                  muted
                  playsInline
                  preload="metadata"
                  onLoadedMetadata={(event) => {
                    const video = event.currentTarget
                    setNatural({
                      width: video.videoWidth || 1,
                      height: video.videoHeight || 1,
                    })
                  }}
                />
              ) : (
                <img
                  src={item.media_url}
                  className="aspect-[16/10] w-full object-cover"
                  alt="Phương tiện biển số"
                  onLoad={(event) => {
                    const image = event.currentTarget
                    setNatural({
                      width: image.naturalWidth || 1,
                      height: image.naturalHeight || 1,
                    })
                  }}
                />
              )}
              {bboxStyle && (
                <div className="absolute border-2 border-accent" style={bboxStyle}>
                  <span className="absolute -top-6 left-0 bg-accent px-2 py-0.5 font-mono text-xs text-accent-foreground">Plate</span>
                </div>
              )}
            </div>
          </div>
        </section>

        <aside className="space-y-4">
          <div className="border border-border bg-card p-4">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div>
                <p className="font-mono text-xs text-muted-foreground">{formatShortId(item.id)}</p>
                <p className="mt-2 font-mono text-4xl font-bold">{item.plate_number || '—'}</p>
              </div>
              {statusBadge(item.status)}
            </div>

            <div className="mt-4 flex flex-wrap gap-2">
              {item.gate && (
                <span className="inline-flex items-center gap-1 rounded bg-secondary px-2 py-1 text-xs text-muted-foreground">
                  <Camera size={10} /> {item.gate}
                </span>
              )}
              {item.direction && (
                <span className={`inline-flex items-center gap-1 rounded px-2 py-1 text-xs font-semibold ring-1 ${
                  item.direction === 'IN'
                    ? 'bg-blue-500/15 text-blue-200 ring-blue-400/25'
                    : 'bg-purple-500/15 text-purple-200 ring-purple-400/25'
                }`}>
                  {item.direction === 'IN' ? <ArrowDownLeft size={11} /> : <ArrowUpRight size={11} />}
                  {item.direction === 'IN' ? 'Vào' : 'Ra'}
                </span>
              )}
              {item.camera_id && (
                <span className="inline-flex items-center gap-1 rounded bg-secondary px-2 py-1 text-xs text-muted-foreground">
                  {item.camera_id}
                </span>
              )}
            </div>

            <dl className="mt-5 grid grid-cols-2 gap-3 text-sm">
              <dt className="text-muted-foreground">Created</dt>
              <dd className="text-right font-mono">{formatDate(item.created_at)}</dd>
              <dt className="text-muted-foreground">Updated</dt>
              <dd className="text-right font-mono">{formatDate(item.updated_at)}</dd>
              <dt className="text-muted-foreground">Plate region</dt>
              <dd className="text-right font-mono">{item.plate_region || '—'}</dd>
              <dt className="text-muted-foreground">Request ID</dt>
              <dd className="text-right font-mono">{formatShortId(item.id)}</dd>
            </dl>

            {item.error_message && (
              <p className="mt-4 border border-red-400/25 bg-red-500/10 p-3 text-sm text-red-100">{item.error_message}</p>
            )}

            <div className="mt-4 grid gap-2">
              {['FAILED', 'NEEDS_REVIEW'].includes(item.status) && (
                <button
                  type="button"
                  onClick={() => setConfirm(true)}
                  className="inline-flex w-full items-center justify-center gap-2 bg-accent px-4 py-2.5 text-accent-foreground transition hover:opacity-90"
                >
                  <RotateCcw size={16} /> Reprocess
                </button>
              )}
              <button
                type="button"
                onClick={() => onDelete(item)}
                className="inline-flex w-full items-center justify-center gap-2 border border-red-400/20 bg-red-500/10 px-4 py-2.5 text-red-100 transition hover:bg-red-500/20"
              >
                <Trash2 size={16} /> Delete
              </button>
            </div>
          </div>

          <ConfidenceCard item={item} />
        </aside>
      </div>

      {confirm && (
        <div role="dialog" aria-modal="true" className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-4">
          <div className="max-w-md border border-border bg-card p-5">
            <h3 className="font-semibold">Xác nhận reprocess?</h3>
            <p className="mt-2 text-sm text-muted-foreground">Trạng thái sẽ quay về NOT_STARTED và worker sẽ chạy lại request này.</p>
            <div className="mt-5 flex justify-end gap-2">
              <button type="button" className="border border-border px-4 py-2 hover:bg-secondary" onClick={() => setConfirm(false)}>
                Cancel
              </button>
              <button
                type="button"
                className="bg-accent px-4 py-2 text-accent-foreground"
                onClick={() => {
                  onReprocess(item.id)
                  setConfirm(false)
                }}
              >
                Reprocess
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  )
}

export default function App() {
  const [theme, setTheme] = useState<'dark' | 'light'>('dark')
  const [route, setRoute] = useState<RouteState>(() => currentRoute())
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(5)
  const [listItems, setListItems] = useState<UiRequest[]>([])
  const [listTotal, setListTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(1)
  const [listLoading, setListLoading] = useState(true)
  const [detailItem, setDetailItem] = useState<UiRequest | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [uploadBusy, setUploadBusy] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<UiRequest | null>(null)
  const [deleteBusy, setDeleteBusy] = useState(false)
  const [toast, setToast] = useState<ToastState>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [refreshToken, setRefreshToken] = useState(0)
  const [refreshing, setRefreshing] = useState(false)
  const toastTimerRef = useRef<number | null>(null)

  useEffect(() => {
    const storedTheme = window.localStorage.getItem('theme') as 'dark' | 'light' | null
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    const nextTheme = storedTheme ?? (prefersDark ? 'dark' : 'light')
    setTheme(nextTheme)
    document.documentElement.classList.toggle('dark', nextTheme === 'dark')
  }, [])

  useEffect(() => {
    window.localStorage.setItem('theme', theme)
    document.documentElement.classList.toggle('dark', theme === 'dark')
  }, [theme])

  useEffect(() => {
    const handlePopState = () => setRoute(currentRoute())
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  useEffect(() => {
    return () => {
      if (toastTimerRef.current) window.clearTimeout(toastTimerRef.current)
    }
  }, [])

  const applyToast = (message: string, kind: 'success' | 'warning' | 'error' = 'success') => {
    setToast({ message, kind })
    if (toastTimerRef.current) window.clearTimeout(toastTimerRef.current)
    toastTimerRef.current = window.setTimeout(() => setToast(null), 2400)
  }

  const apiBase = getApiBaseUrl()

  const loadList = async (pageToLoad = page, sizeToLoad = pageSize, options?: { silent?: boolean }) => {
    if (!options?.silent) {
      setListLoading(true)
    }
    try {
      const response = await listRecognitions(pageToLoad, sizeToLoad)
      setListItems(response.items.map(normalizeRequest))
      setListTotal(response.total)
      setTotalPages(Math.max(1, response.total_pages || 1))
      setNotice(null)
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'Không tải được danh sách')
    } finally {
      if (!options?.silent) {
        setListLoading(false)
      }
    }
  }

  const loadDetail = async (requestId: string, options?: { silent?: boolean }) => {
    if (!options?.silent) {
      setDetailLoading(true)
    }
    try {
      const item = normalizeRequest(await getRecognition(requestId))
      setDetailItem(item)
      setListItems((current) => current.map((row) => (row.id === item.id ? item : row)))
      setNotice(null)
    } catch (error) {
      if (error && typeof error === 'object' && 'status' in error && (error as { status?: number }).status === 404) {
        setDetailItem(null)
      } else {
        setNotice(error instanceof Error ? error.message : 'Không tải được chi tiết')
      }
    } finally {
      if (!options?.silent) {
        setDetailLoading(false)
      }
    }
  }

  const refreshCurrentView = async (options?: { silent?: boolean }) => {
    if (route.view === 'detail') {
      await loadDetail(route.id, options)
      return
    }

    await loadList(page, pageSize, options)
  }

  useEffect(() => {
    void loadList(page, pageSize)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, pageSize])

  useEffect(() => {
    if (route.view !== 'detail') {
      setDetailItem(null)
      return
    }
    void loadDetail(route.id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [route.view, route.view === 'detail' ? route.id : ''])

  useEffect(() => {
    const shouldPollList = listItems.some((item) => !terminal(item.status))
    const shouldPollDetail = route.view === 'detail' && detailItem != null && !terminal(detailItem.status)
    if (!shouldPollList && !shouldPollDetail) return

    const timer = window.setInterval(() => {
      setRefreshToken((value) => value + 1)
    }, POLL_MS)

    return () => window.clearInterval(timer)
  }, [listItems, detailItem, route.view])

  useEffect(() => {
    if (refreshToken === 0) return
    void loadList(page, pageSize, { silent: true })
    if (route.view === 'detail' && detailItem && !terminal(detailItem.status)) {
      void loadDetail(route.id, { silent: true })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshToken])

  const processingCount = useMemo(() => listItems.filter((item) => !terminal(item.status)).length, [listItems])

  const handleRefresh = async () => {
    if (refreshing) return
    setRefreshing(true)
    try {
      await refreshCurrentView()
    } finally {
      setRefreshing(false)
    }
  }

  const handleThemeToggle = () => setTheme((value) => (value === 'dark' ? 'light' : 'dark'))

  const handleUpload = async (payload: { file: File; previewUrl: string }) => {
    setUploadBusy(true)
    try {
      await uploadRecognition(payload.file)
      navigate({ view: 'home' })
      setRefreshToken((value) => value + 1)
      applyToast('Upload thành công')
    } catch (error) {
      applyToast(error instanceof Error ? error.message : 'Upload thất bại', 'error')
      throw error
    } finally {
      setUploadBusy(false)
    }
  }

  const handleReprocess = async (requestId: string) => {
    try {
      await reprocessRecognition(requestId)
      applyToast('Reprocessing started')
      setRefreshToken((value) => value + 1)
    } catch (error) {
      applyToast(error instanceof Error ? error.message : 'Reprocess thất bại', 'error')
    }
  }

  const handleDeleteRequest = (item: UiRequest) => {
    setDeleteTarget(item)
  }

  const confirmDelete = async () => {
    if (!deleteTarget) return
    setDeleteBusy(true)
    try {
      await deleteRecognition(deleteTarget.id)
      applyToast('Xóa thành công')
      if (route.view === 'detail' && route.id === deleteTarget.id) {
        navigate({ view: 'home' })
      }
      setDeleteTarget(null)
      setRefreshToken((value) => value + 1)
    } catch (error) {
      applyToast(error instanceof Error ? error.message : 'Xóa thất bại', 'error')
    } finally {
      setDeleteBusy(false)
    }
  }

  const selectedItem = route.view === 'detail' ? detailItem : null

  return (
    <AppShell>
      <Header
        onRefresh={handleRefresh}
        onToggleTheme={handleThemeToggle}
        processingCount={processingCount}
        refreshing={refreshing}
      />

      {notice && <NetworkBanner message={notice} />}

      {route.view === 'detail' ? (
        <DetailView
          loading={detailLoading}
          item={selectedItem}
          onBack={() => navigate({ view: 'home' })}
          onReprocess={handleReprocess}
          onDelete={handleDeleteRequest}
        />
      ) : route.view === 'not-found' ? (
        <main className="mx-auto max-w-5xl p-6">
          <div className="border border-border bg-card p-8">
            <h2 className="text-xl font-semibold">404</h2>
            <p className="mt-2 text-muted-foreground">Route không hợp lệ.</p>
            <button type="button" onClick={() => navigate({ view: 'home' })} className="mt-4 border border-border px-4 py-2 hover:bg-secondary">
              Về trang chính
            </button>
          </div>
        </main>
      ) : (
        <>
          <UploadPanel onSubmit={handleUpload} busy={uploadBusy} />

          <main className="mx-auto max-w-7xl px-4 py-5 sm:px-6">
            <div className="mb-3 flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
              <div>
                <h1 className="text-2xl font-semibold">Lịch sử nhận diện</h1>
              </div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Activity size={14} />
                <span>{processingCount > 0 ? 'Auto-refresh đang chạy' : 'Không có job đang xử lý'}</span>
              </div>
            </div>

            <RequestList
              loading={listLoading}
              items={listItems}
              onOpen={(id) => navigate({ view: 'detail', id })}
              onDelete={handleDeleteRequest}
            />

            <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-sm">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  disabled={page <= 1}
                  onClick={() => setPage((value) => Math.max(1, value - 1))}
                  className="border border-border px-3 py-2 disabled:opacity-40"
                >
                  <ChevronLeft className="inline" size={16} /> Prev
                </button>
                <button
                  type="button"
                  disabled={page >= totalPages}
                  onClick={() => setPage((value) => Math.min(totalPages, value + 1))}
                  className="border border-border px-3 py-2 disabled:opacity-40"
                >
                  Next <ChevronRight className="inline" size={16} />
                </button>
                <span className="font-mono text-muted-foreground">
                  Page {page}/{totalPages} · {listTotal} items
                </span>
              </div>

              <label className="text-muted-foreground">
                Page size{' '}
                <select
                  value={pageSize}
                  onChange={(event) => {
                    setPageSize(Number(event.target.value))
                    setPage(1)
                  }}
                  className="ml-2 border border-border bg-input px-2 py-2 text-foreground"
                >
                  {PAGE_SIZES.map((size) => (
                    <option key={size} value={size}>
                      {size}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </main>
        </>
      )}

      {deleteTarget && (
        <DeleteConfirmDialog
          item={deleteTarget}
          onCancel={() => !deleteBusy && setDeleteTarget(null)}
          onConfirm={confirmDelete}
          busy={deleteBusy}
        />
      )}

      {toast && (
        <div
          className={`fixed bottom-4 right-4 border px-4 py-3 text-sm shadow-xl ${
            toast.kind === 'error'
              ? 'border-red-400/30 bg-red-500/15 text-red-100'
              : toast.kind === 'warning'
                ? 'border-orange-400/30 bg-orange-500/15 text-orange-100'
                : 'border-emerald-400/30 bg-emerald-500/15 text-emerald-100'
          }`}
        >
          {toast.message}
        </div>
      )}
    </AppShell>
  )
}

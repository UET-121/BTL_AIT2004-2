import { useEffect, useRef } from 'react'
import { Camera } from 'lucide-react'

interface Detection {
  track_id: number
  vehicle_bbox?: {
    x: number
    y: number
    width: number
    height: number
  }
  plate_bbox?: {
    x: number
    y: number
    width: number
    height: number
  }
  bbox?: {
    x: number
    y: number
    width: number
    height: number
  }
  status: 'pending' | 'confirmed' | 'rejected'
  text: string
  confidence: number
  vehicle_confidence?: number
  plate_confidence?: number
  ocr_confidence?: number
}

interface VideoCanvasProps {
  imageBase64: string | null
  detections: Detection[]
  status: string
}

export function VideoCanvas({ imageBase64, detections, status }: VideoCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    if (!imageBase64 || !canvasRef.current) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const img = new Image()
    img.src = `data:image/jpeg;base64,${imageBase64}`
    img.onload = () => {
      // Set canvas size to display image dimension
      canvas.width = img.width
      canvas.height = img.height

      // Clear and draw image
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      ctx.drawImage(img, 0, 0)

      // Draw bounding boxes
      detections.forEach((det) => {
        // 1. Draw vehicle bounding box if available
        if (det.vehicle_bbox) {
          const vx = (det.vehicle_bbox.x / 100) * canvas.width
          const vy = (det.vehicle_bbox.y / 100) * canvas.height
          const vw = (det.vehicle_bbox.width / 100) * canvas.width
          const vh = (det.vehicle_bbox.height / 100) * canvas.height

          ctx.strokeStyle = '#3b82f6' // Blue for vehicle outline
          ctx.lineWidth = Math.max(1, Math.round(canvas.width * 0.0015))
          ctx.strokeRect(vx, vy, vw, vh)

          // Vehicle label (Xe #ID)
          const fontSize = Math.max(10, Math.round(canvas.height * 0.02))
          ctx.font = `${fontSize}px sans-serif`
          ctx.fillStyle = '#3b82f6'
          ctx.fillText(`Xe #${det.track_id}`, vx + 5, vy + fontSize + 5)
        }

        // 2. Draw plate bounding box (fallback to det.bbox if plate_bbox is not sent)
        const pBbox = det.plate_bbox || det.bbox
        if (pBbox) {
          const px = (pBbox.x / 100) * canvas.width
          const py = (pBbox.y / 100) * canvas.height
          const pw = (pBbox.width / 100) * canvas.width
          const ph = (pBbox.height / 100) * canvas.height

          // Determine border and fill colors based on status
          let strokeColor = '#f59e0b' // yellow for pending
          let fillColor = 'rgba(245, 158, 11, 0.15)'
          if (det.status === 'confirmed') {
            strokeColor = '#10b981' // emerald for confirmed
            fillColor = 'rgba(16, 185, 129, 0.15)'
          } else if (det.status === 'rejected') {
            strokeColor = '#ef4444' // red for rejected
            fillColor = 'rgba(239, 68, 68, 0.15)'
          }

          // Draw bbox rectangle
          ctx.strokeStyle = strokeColor
          ctx.lineWidth = Math.max(2, Math.round(canvas.width * 0.003))
          ctx.fillStyle = fillColor
          ctx.fillRect(px, py, pw, ph)
          ctx.strokeRect(px, py, pw, ph)

          // Draw tag text label
          const fontSize = Math.max(11, Math.round(canvas.height * 0.028))
          ctx.font = `bold ${fontSize}px monospace`
          const textLabel = det.text || '...'
          const textWidth = ctx.measureText(textLabel).width

          // Draw background tag header
          ctx.fillStyle = strokeColor
          const tagHeight = fontSize + 6
          ctx.fillRect(px, py - tagHeight > 0 ? py - tagHeight : py, textWidth + 10, tagHeight)

          // Draw text
          ctx.fillStyle = '#000000'
          ctx.fillText(
            textLabel,
            px + 5,
            py - tagHeight > 0 ? py - tagHeight + fontSize - 1 : py + fontSize - 1
          )
        }
      })
    }
  }, [imageBase64, detections])


  const isStreamActive = status === 'running' && imageBase64

  return (
    <div className="relative border border-border bg-black aspect-video flex items-center justify-center overflow-hidden w-full">
      {isStreamActive ? (
        <canvas ref={canvasRef} className="max-w-full max-h-full object-contain w-full h-full" />
      ) : (
        <div className="text-center text-muted-foreground flex flex-col items-center gap-3 p-8">
          <div className={`p-4 rounded-full bg-secondary/50 border border-border/80 ${status === 'starting' ? 'animate-pulse' : ''}`}>
            <Camera size={36} className="text-muted-foreground" />
          </div>
          <div>
            <h4 className="font-semibold text-foreground">
              {status === 'starting' ? 'Đang kết nối camera...' : status === 'running' ? 'Đang đợi dữ liệu hình ảnh...' : 'Luồng stream ngoại tuyến'}
            </h4>
            <p className="text-xs max-w-sm mt-1">
              {status === 'running'
                ? 'Đang lắng nghe frame nhận diện từ backend...'
                : 'Nhấn Bắt đầu Stream ở bảng điều khiển để kích hoạt luồng camera nhận dạng biển số.'}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

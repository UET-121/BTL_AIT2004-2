import { useEffect, useState, useRef } from 'react'
import { getApiBaseUrl, getStreamStatus, startStream, stopStream } from '../api'
import { StreamControls } from './components/StreamControls'
import { VideoCanvas } from './components/VideoCanvas'
import { ResultPanel } from './components/ResultPanel'

interface Detection {
  track_id: number
  bbox: {
    x: number
    y: number
    width: number
    height: number
  }
  status: 'pending' | 'confirmed' | 'rejected'
  text: string
  confidence: number
}

interface ConfirmedPlate {
  track_id: number
  plate_text: string
  confidence: number
  timestamp: string
  status: 'confirmed' | 'rejected'
}

interface ActiveTrack {
  track_id: number
  text: string
  confidence: number
  status: 'pending' | 'confirmed' | 'rejected'
}

const getWsUrl = () => {
  const apiBase = getApiBaseUrl()
  if (apiBase && apiBase !== 'same-origin proxy') {
    try {
      const url = new URL(apiBase)
      const protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
      return `${protocol}//${url.host}/ws/live`
    } catch {
      // fallback
    }
  }
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/ws/live`
}

export default function LivePage() {
  const [status, setStatus] = useState<string>('stopped')
  const [source, setSource] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  
  const [imageBase64, setImageBase64] = useState<string | null>(null)
  const [activeTracks, setActiveTracks] = useState<ActiveTrack[]>([])
  const [detections, setDetections] = useState<Detection[]>([])
  const [confirmedHistory, setConfirmedHistory] = useState<ConfirmedPlate[]>([])

  // Live metrics
  const [fps, setFps] = useState<number>(0)
  const [vehicleAcc, setVehicleAcc] = useState<number>(0)
  const [plateAcc, setPlateAcc] = useState<number>(0)

  const [loading, setLoading] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  // Fetch status on mount
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await getStreamStatus()
        setStatus(res.status)
        setSource(res.source)
        setErrorMessage(res.error_message)
      } catch (err) {
        console.error('Failed to get stream status:', err)
      }
    }
    fetchStatus()
  }, [])

  // Manage WebSocket connection based on stream status
  useEffect(() => {
    if (status === 'running' || status === 'starting') {
      if (!wsRef.current) {
        const wsUrl = getWsUrl()
        console.log('Connecting to WebSocket:', wsUrl)
        const ws = new WebSocket(wsUrl)
        
        ws.onopen = () => {
          console.log('WebSocket connection opened')
        }

        ws.onmessage = (e) => {
          try {
            const event = JSON.parse(e.data)
            
            if (event.type === 'frame.processed') {
              setImageBase64(event.image_base64)
              if (event.fps !== undefined) {
                setFps(event.fps)
              }
              if (event.data?.detections) {
                setDetections(event.data.detections)
                
                // Map detections to active tracks
                const tracks: ActiveTrack[] = event.data.detections.map((d: any) => ({
                  track_id: d.track_id,
                  text: d.text,
                  confidence: d.confidence,
                  status: d.status,
                }))
                setActiveTracks(tracks)

                // Add newly confirmed plates to history without duplicates
                const confirmedDetections = event.data.detections.filter(
                  (d: any) => d.status === 'confirmed' && d.text && d.text.trim() !== ''
                )
                if (confirmedDetections.length > 0) {
                  setConfirmedHistory((prev) => {
                    let updated = [...prev]
                    confirmedDetections.forEach((d: any) => {
                      const newConfirmed: ConfirmedPlate = {
                        track_id: d.track_id,
                        plate_text: d.text,
                        confidence: d.confidence || 100,
                        timestamp: new Date().toISOString(),
                        status: 'confirmed',
                      }
                      // Remove any existing entry with the same track_id or plate_text to prevent duplicates
                      updated = [
                        newConfirmed,
                        ...updated.filter(
                          (item) => item.track_id !== d.track_id && item.plate_text !== d.text
                        ),
                      ]
                    })
                    return updated.slice(0, 10)
                  })
                }

                // Update vehicle and plate accuracies using latest frame values
                if (event.data.detections.length > 0) {
                  const avgVeh = event.data.detections.reduce((sumAcc: number, d: any) => sumAcc + (d.vehicle_confidence || 0), 0) / event.data.detections.length;
                  const avgPlt = event.data.detections.reduce((sumAcc: number, d: any) => sumAcc + (d.plate_confidence || 0), 0) / event.data.detections.length;
                  setVehicleAcc(Math.round(avgVeh))
                  setPlateAcc(Math.round(avgPlt))
                }
              }
            } else if (event.type === 'plate.confirmed') {
              const newConfirmed: ConfirmedPlate = {
                track_id: event.track_id,
                plate_text: event.plate_text,
                confidence: event.confidence,
                timestamp: event.timestamp || new Date().toISOString(),
                status: 'confirmed',
              }
              setConfirmedHistory((prev) => {
                const filtered = prev.filter(
                  (item) => item.track_id !== event.track_id && item.plate_text !== event.plate_text
                )
                return [newConfirmed, ...filtered].slice(0, 10) // Display maximum 10 cars
              })
            } else if (event.type === 'plate.rejected') {
              const newRejected: ConfirmedPlate = {
                track_id: event.track_id,
                plate_text: event.plate_text,
                confidence: event.confidence,
                timestamp: event.timestamp || new Date().toISOString(),
                status: 'rejected',
              }
              setConfirmedHistory((prev) => {
                const filtered = prev.filter(
                  (item) => item.track_id !== event.track_id && item.plate_text !== event.plate_text
                )
                return [newRejected, ...filtered].slice(0, 10) // Display maximum 10 cars
              })
            } else if (event.type === 'stream.stopped') {
              setStatus('stopped')
              const src = event.data?.source
              if (src && (src.includes('uploads/') || src.includes('uploads\\') || /\.(mp4|avi|mov|mpeg|mkv)/i.test(src))) {
                window.history.pushState({}, '', '/')
                window.dispatchEvent(new PopStateEvent('popstate'))
              }
            } else if (event.type === 'stream.error') {
              setErrorMessage(event.data?.message || 'Lỗi không xác định từ luồng stream')
              setStatus('error')
            }
          } catch (err) {
            console.error('Failed to parse WebSocket message:', err)
          }
        }

        ws.onclose = () => {
          console.log('WebSocket connection closed')
          wsRef.current = null
          setFps(0)
          setVehicleAcc(0)
          setPlateAcc(0)
        }

        ws.onerror = (err) => {
          console.error('WebSocket error:', err)
        }

        wsRef.current = ws
      }
    } else {
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
      setImageBase64(null)
      setActiveTracks([])
      setDetections([])
      setFps(0)
      setVehicleAcc(0)
      setPlateAcc(0)
    }

    return () => {
      if (wsRef.current && (status === 'stopped' || status === 'error')) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [status])

  const handleStart = async (streamSource: string) => {
    setLoading(true)
    setErrorMessage(null)
    try {
      const res = await startStream(streamSource)
      setStatus(res.status)
      setSource(res.source)
      setErrorMessage(res.error_message)
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Khởi động stream thất bại')
      setStatus('error')
    } finally {
      setLoading(false)
    }
  }

  const handleStop = async () => {
    setLoading(true)
    try {
      const res = await stopStream()
      setStatus(res.status)
      setSource(res.source)
      setErrorMessage(res.error_message)
      setImageBase64(null)
      setActiveTracks([])
      setDetections([])
      setFps(0)
      setVehicleAcc(0)
      setPlateAcc(0)
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Dừng stream thất bại')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-1 border-b border-border/80 pb-4">
        <h2 className="text-2xl font-bold tracking-tight">Giám sát Camera Real-Time</h2>
        <p className="text-sm text-muted-foreground">
          Đọc luồng video RTSP/Camera trực tiếp, phát hiện xe, biển số, theo dõi chuyển động và chạy nhận diện song song.
        </p>
      </div>

      {/* Real-time stats dashboard */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="border border-border bg-card p-4 rounded-lg flex flex-col justify-center">
          <span className="text-[10px] text-muted-foreground uppercase tracking-wider font-mono">Trạng thái</span>
          <span className={`text-base font-bold mt-1 ${status === 'running' ? 'text-emerald-400' : 'text-slate-400'}`}>
            {status === 'running' ? '● Đang phát' : status === 'starting' ? 'Đang khởi động...' : 'Ngoại tuyến'}
          </span>
        </div>
        <div className="border border-border bg-card p-4 rounded-lg flex flex-col justify-center">
          <span className="text-[10px] text-muted-foreground uppercase tracking-wider font-mono">FPS</span>
          <span className="text-xl font-bold mt-1 text-sky-400 font-mono">{status === 'running' ? fps : '0.0'}</span>
        </div>
        <div className="border border-border bg-card p-4 rounded-lg flex flex-col justify-center font-mono">
          <span className="text-[10px] text-muted-foreground uppercase tracking-wider font-sans">Độ chính xác xe</span>
          <span className="text-xl font-bold mt-1 text-emerald-400">
            {status === 'running' && vehicleAcc > 0 ? `${vehicleAcc}%` : '—'}
          </span>
        </div>
        <div className="border border-border bg-card p-4 rounded-lg flex flex-col justify-center font-mono">
          <span className="text-[10px] text-muted-foreground uppercase tracking-wider font-sans">Độ chính xác biển</span>
          <span className="text-xl font-bold mt-1 text-yellow-400 font-mono">
            {status === 'running' && plateAcc > 0 ? `${plateAcc}%` : '—'}
          </span>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        {/* Left Column: Video Monitoring Canvas */}
        <div className="space-y-6 flex flex-col justify-between">
          <VideoCanvas imageBase64={imageBase64} detections={detections} status={status} />
        </div>

        {/* Right Column: Stream Controls panel */}
        <div className="space-y-6">
          <StreamControls
            status={status}
            source={source}
            errorMessage={errorMessage}
            onStart={handleStart}
            onStop={handleStop}
            loading={loading}
          />
        </div>
      </div>

      {/* Real-time Tracking and Confirmed History Logs */}
      <ResultPanel activeTracks={activeTracks} confirmedHistory={confirmedHistory} />
    </div>
  )
}


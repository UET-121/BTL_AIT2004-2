import React, { useState } from 'react'
import { Play, Square, Settings, AlertCircle } from 'lucide-react'

interface StreamControlsProps {
  status: string
  source: string | null
  errorMessage: string | null
  onStart: (source: string) => Promise<void>
  onStop: () => Promise<void>
  loading: boolean
}

export function StreamControls({
  status,
  source,
  errorMessage,
  onStart,
  onStop,
  loading,
}: StreamControlsProps) {
  const [customSource, setCustomSource] = useState('0')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (customSource.trim()) {
      onStart(customSource.trim())
    }
  }

  const getStatusColor = () => {
    switch (status) {
      case 'running':
        return 'bg-emerald-500 text-emerald-100 ring-emerald-400/30'
      case 'starting':
        return 'bg-yellow-500 text-yellow-100 ring-yellow-400/30 animate-pulse'
      case 'error':
        return 'bg-red-500 text-red-100 ring-red-400/35'
      default:
        return 'bg-slate-500 text-slate-100 ring-slate-400/25'
    }
  }

  const getStatusLabel = () => {
    switch (status) {
      case 'running':
        return 'Đang chạy'
      case 'starting':
        return 'Đang khởi động'
      case 'error':
        return 'Lỗi luồng'
      default:
        return 'Đã dừng'
    }
  }

  return (
    <div className="border border-border bg-card p-5">
      <div className="flex items-center justify-between mb-4 border-b border-border/50 pb-3">
        <h3 className="font-semibold flex items-center gap-2">
          <Settings size={18} className="text-muted-foreground" />
          Điều khiển Luồng Stream
        </h3>
        <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ${getStatusColor()}`}>
          {getStatusLabel()}
        </span>
      </div>

      {status === 'error' && errorMessage && (
        <div className="mb-4 flex items-start gap-2 border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-100">
          <AlertCircle size={16} className="shrink-0 mt-0.5" />
          <div>
            <p className="font-medium">Lỗi kết nối:</p>
            <p className="text-xs opacity-90">{errorMessage}</p>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="streamSource" className="block text-xs font-mono uppercase tracking-wider text-muted-foreground mb-1">
            Nguồn Stream (RTSP URL / Index Camera / Đường dẫn video)
          </label>
          <div className="flex gap-2">
            <input
              id="streamSource"
              type="text"
              value={customSource}
              onChange={(e) => setCustomSource(e.target.value)}
              disabled={status === 'running' || status === 'starting' || loading}
              placeholder="e.g. 0 hoặc rtsp://username:password@ip:port/h264"
              className="flex-1 bg-background border border-border px-3 py-2 text-sm focus:outline-none focus:border-accent disabled:opacity-50"
            />
          </div>
        </div>

        <div className="flex gap-2">
          {status === 'running' || status === 'starting' ? (
            <button
              type="button"
              onClick={onStop}
              disabled={loading}
              className="flex-1 inline-flex items-center justify-center gap-2 bg-red-600 hover:bg-red-500 text-white font-semibold py-2 px-4 transition disabled:opacity-50"
            >
              <Square size={16} /> Dừng Stream
            </button>
          ) : (
            <button
              type="submit"
              disabled={loading || !customSource.trim()}
              className="flex-1 inline-flex items-center justify-center gap-2 bg-accent hover:opacity-90 text-accent-foreground font-semibold py-2 px-4 transition disabled:opacity-50"
            >
              <Play size={16} /> Bắt đầu Stream
            </button>
          )}
        </div>
      </form>

      {status === 'running' && source && (
        <div className="mt-4 pt-3 border-t border-border/50 text-xs font-mono text-muted-foreground space-y-1">
          <p>Nguồn đang phát: <span className="text-foreground break-all">{source}</span></p>
          <p>Trạng thái camera: Live (10 FPS preview)</p>
        </div>
      )}
    </div>
  )
}

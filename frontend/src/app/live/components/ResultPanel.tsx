import { Activity, Check, X, AlertTriangle } from 'lucide-react'

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

interface ResultPanelProps {
  activeTracks: ActiveTrack[]
  confirmedHistory: ConfirmedPlate[]
}

export function ResultPanel({ activeTracks, confirmedHistory }: ResultPanelProps) {
  const formatTime = (isoString: string) => {
    try {
      const d = new Date(isoString)
      return d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    } catch {
      return ''
    }
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 h-full">
      {/* Active Tracks Section */}
      <div className="border border-border bg-card p-4 flex flex-col h-[350px]">
        <div className="flex items-center gap-2 mb-3 border-b border-border/50 pb-2">
          <Activity size={18} className="text-yellow-400 animate-pulse" />
          <h4 className="font-semibold text-sm">Các đối tượng đã theo dõi</h4>
        </div>
        <div className="flex-1 overflow-y-auto space-y-2 pr-1">
          {activeTracks.length === 0 ? (
            <div className="h-full flex items-center justify-center text-xs text-muted-foreground italic">
              Không có xe/biển số nào trong khung hình
            </div>
          ) : (
            activeTracks.map((track) => (
              <div
                key={track.track_id}
                className="flex items-center justify-between border border-border bg-background px-3 py-2 text-sm"
              >
                <div className="flex items-center gap-2.5">
                  <div className="h-2 w-2 rounded-full bg-yellow-400 animate-ping" />
                  <span className="font-mono text-xs text-muted-foreground">ID: {track.track_id}</span>
                  <span className="font-mono font-bold text-base tracking-wide">
                    {track.text || 'Đang nhận diện...'}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">{track.confidence}%</span>
                  <span className="inline-flex items-center rounded-full bg-yellow-500/10 px-2 py-0.5 text-[10px] font-semibold text-yellow-300 ring-1 ring-yellow-400/20">
                    {track.status === 'confirmed' ? 'Hoàn tất' : 'Pending'}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Confirmed History Log Section */}
      <div className="border border-border bg-card p-4 flex flex-col h-[350px]">
        <div className="flex items-center gap-2 mb-3 border-b border-border/50 pb-2">
          <Check size={18} className="text-emerald-400" />
          <h4 className="font-semibold text-sm">Nhật ký Biển số đã xác nhận</h4>
        </div>
        <div className="flex-1 overflow-y-auto space-y-2 pr-1">
          {confirmedHistory.length === 0 ? (
            <div className="h-full flex items-center justify-center text-xs text-muted-foreground italic">
              Chưa có biển số nào được xác nhận
            </div>
          ) : (
            confirmedHistory.map((item, index) => (
              <div
                key={`${item.track_id}-${index}`}
                className={`flex items-center justify-between border px-3 py-2 text-sm ${
                  item.status === 'confirmed'
                    ? 'border-emerald-500/20 bg-emerald-500/5'
                    : 'border-red-500/20 bg-red-500/5'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  {item.status === 'confirmed' ? (
                    <div className="p-1 rounded-full bg-emerald-500/25 text-emerald-300">
                      <Check size={12} />
                    </div>
                  ) : (
                    <div className="p-1 rounded-full bg-red-500/25 text-red-300">
                      <X size={12} />
                    </div>
                  )}
                  <div className="flex flex-col">
                    <span className="font-mono font-bold text-base tracking-wide text-foreground">
                      {item.plate_text}
                    </span>
                    <span className="text-[10px] text-muted-foreground font-mono">
                      Track: #{item.track_id} · {formatTime(item.timestamp)}
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-mono font-semibold text-xs text-foreground">
                    {item.confidence}% Conf.
                  </div>
                  <span
                    className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold ring-1 ${
                      item.status === 'confirmed'
                        ? 'bg-emerald-500/10 text-emerald-400 ring-emerald-400/20'
                        : 'bg-red-500/10 text-red-400 ring-red-400/20'
                    }`}
                  >
                    {item.status === 'confirmed' ? 'Đã duyệt' : 'Từ chối'}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

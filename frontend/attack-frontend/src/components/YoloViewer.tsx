import { useEffect, useState } from 'react'
import { Camera, AlertCircle } from 'lucide-react'

const API_BASE = 'http://127.0.0.1:8000'

type StartYoloResponse = {
  status: 'success' | 'error'
  message: string
  task_id?: string
  active_task_id?: string
  source?: string
  started_by?: string
}

type YoloViewerProps = {
  isMonitoring: boolean
  source: string
}

const glassPanel =
  'rounded-[14px] 2xl:rounded-[16px] bg-white/10 shadow-[inset_0_1px_0_rgba(255,255,255,0.14),0_8px_24px_rgba(0,0,0,0.18)] backdrop-blur-xl'

const glassSection =
  'rounded-[12px] bg-black/20 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]'

export default function YoloViewer({ isMonitoring, source }: YoloViewerProps) {
  const [taskId, setTaskId] = useState('')
  const [imageUrl, setImageUrl] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [stopping, setStopping] = useState(false)

  const token = localStorage.getItem('token') || ''

  const startYolo = async () => {
    try {
      setLoading(true)
      setError('')

      const res = await fetch(`${API_BASE}/yolo/start?source=${source}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        credentials: 'include',
      })

      const data: StartYoloResponse = await res.json()

      if (data.status === 'success' && data.task_id) {
        setTaskId(data.task_id)
      } else if (data.active_task_id) {
        setTaskId(data.active_task_id)
        setError(data.message)
      } else {
        setError(data.message || '啟動失敗')
      }
    } catch {
      setError('無法連線到後端')
    } finally {
      setLoading(false)
    }
  }

  const stopYolo = async () => {
    if (!taskId) return

    try {
      setStopping(true)
      await fetch(`${API_BASE}/yolo/stop/${taskId}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        credentials: 'include',
      })
    } catch {
      setError('停止失敗')
    } finally {
      setTaskId('')
      setImageUrl('')
      setStopping(false)
    }
  }

  useEffect(() => {
    if (isMonitoring && !taskId && !loading) {
      startYolo()
    }

    if (!isMonitoring && taskId) {
      stopYolo()
    }
  }, [isMonitoring, source])

  useEffect(() => {
    if (!taskId) return

    const timer = setInterval(() => {
      setImageUrl(`${API_BASE}/yolo/stream/${taskId}/cam0?t=${Date.now()}`)
    }, 200)

    return () => clearInterval(timer)
  }, [taskId])

  return (
    <div className="h-full">
      {error && (
        <div className="mb-3 rounded-xl bg-red-500/10 px-4 py-3 text-sm text-red-200">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4" />
            <span>{error}</span>
          </div>
        </div>
      )}

      <div className={`${glassPanel} overflow-hidden`}>
        <div className="flex flex-col gap-3 px-4 py-4 lg:flex-row lg:items-center lg:justify-between 2xl:px-5">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-400/15 text-emerald-400">
                <Camera className="h-4 w-4" />
              </div>
              <div>
                <h3 className="text-sm font-black text-white 2xl:text-base">單鏡頭即時監控</h3>
                <p className="text-[11px] text-white/45 2xl:text-xs">來源鏡頭 Source {source}</p>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <div className="rounded-full bg-white/5 px-3 py-1 text-[11px] font-bold text-white/70">
              {taskId ? `Task ${taskId}` : '尚未啟動'}
            </div>
            <div
              className={`rounded-full px-3 py-1 text-[11px] font-black ${
                taskId
                  ? 'bg-emerald-400 text-emerald-950'
                  : 'bg-white/10 text-white/70'
              }`}
            >
              {loading ? 'STARTING' : stopping ? 'STOPPING' : taskId ? 'RUNNING' : 'IDLE'}
            </div>
          </div>
        </div>

        <div className="p-3 2xl:p-4">
          <div className={`${glassSection} p-3`}>
            <div className="relative flex min-h-[320px] items-center justify-center overflow-hidden rounded-2xl bg-slate-950/85 ring-1 ring-white/5 sm:min-h-[420px]">
              {taskId ? (
                <img
                  src={imageUrl}
                  alt="YOLO stream cam0"
                  className="h-full w-full object-contain"
                />
              ) : (
                <div className="flex flex-col items-center justify-center px-6 text-center">
                  <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-white/10 text-white/70">
                    <Camera className="h-6 w-6" />
                  </div>
                  <h4 className="text-sm font-bold text-white 2xl:text-base">尚未啟動監測</h4>
                  <p className="mt-2 text-xs leading-6 text-white/45 2xl:text-sm">
                    請於上方 Dashboard 點擊開始監測。
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
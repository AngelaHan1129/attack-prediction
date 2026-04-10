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
  'rounded-[14px] 2xl:rounded-[16px] border border-white/15 bg-white/10 shadow-[inset_0_1px_0_rgba(255,255,255,0.14),0_8px_24px_rgba(0,0,0,0.18)] backdrop-blur-xl'

const glassSection =
  'rounded-[12px] border border-white/10 bg-black/20 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]'

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
      setImageUrl(`${API_BASE}/yolo/stream/${taskId}?t=${Date.now()}`)
    }, 200)

    return () => clearInterval(timer)
  }, [taskId])

  return (
    <div className="h-full">
      {error && (
        <div className="mb-3 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-200">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4" />
            <span>{error}</span>
          </div>
        </div>
      )}

      <div className={` overflow-hidden`}>
        <div className="p-3 2xl:p-4">
            <div className="relative flex min-h-[320px] items-center justify-center overflow-hidden rounded-2xl border border-white/10 bg-slate-950/80 sm:min-h-[420px]">
              {taskId ? (
                <img
                  src={imageUrl}
                  alt="YOLO stream"
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
  )
}
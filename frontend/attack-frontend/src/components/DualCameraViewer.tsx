import { useEffect, useState } from 'react'
import { Camera, AlertCircle } from 'lucide-react'

const API_BASE = 'http://127.0.0.1:8000'

type DualCameraViewerProps = {
  isMonitoring: boolean
  source0: string
  source1: string
}

const glassSection =
  'rounded-[12px] border border-white/10 bg-white/60 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]'

const DualCameraViewer = ({ isMonitoring, source0, source1 }: DualCameraViewerProps) => {
  const [taskId, setTaskId] = useState('')
  const [error, setError] = useState('')
  const [isStarting, setIsStarting] = useState(false)
  const [isStopping, setIsStopping] = useState(false)
  const [cam0Url, setCam0Url] = useState('')
  const [cam1Url, setCam1Url] = useState('')

  const token = localStorage.getItem('token') || ''

  const clearStreams = () => {
    setCam0Url('')
    setCam1Url('')
  }

  const startDual = async () => {
    try {
      setIsStarting(true)
      setError('')
      clearStreams()

      const res = await fetch(
        `${API_BASE}/yolo/start/dual?source0=${source0}&source1=${source1}`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
          },
          credentials: 'include',
        }
      )

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.detail || data.message || '啟動失敗')
      }

      if (data.task_id) {
        setTaskId(data.task_id)
      } else {
        throw new Error(data.message || '未取得 task_id')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '發生未知錯誤')
    } finally {
      setIsStarting(false)
    }
  }

  const stopDual = async () => {
    if (!taskId) return

    try {
      setIsStopping(true)
      setError('')

      const res = await fetch(`${API_BASE}/yolo/stop/${taskId}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        credentials: 'include',
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.detail || data.message || '停止失敗')
      }

      setTaskId('')
      clearStreams()
    } catch (err) {
      setError(err instanceof Error ? err.message : '停止任務失敗')
    } finally {
      setIsStopping(false)
    }
  }

  useEffect(() => {
    if (isMonitoring && !taskId && !isStarting) {
      startDual()
    }

    if (!isMonitoring && taskId) {
      stopDual()
    }
  }, [isMonitoring, source0, source1])

  useEffect(() => {
    if (!taskId) return

    const timer = setInterval(() => {
      const t = Date.now()
      setCam0Url(`${API_BASE}/yolo/stream/${taskId}/cam0?t=${t}`)
      setCam1Url(`${API_BASE}/yolo/stream/${taskId}/cam1?t=${t}`)
    }, 200)

    return () => clearInterval(timer)
  }, [taskId])

  return (
    <div className="h-full space-y-3">
      {error && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-200">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4" />
            <span>{error}</span>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-3 p-3 xl:grid-cols-2 2xl:p-4">
        {[{ label: source0, url: cam0Url }, { label: source1, url: cam1Url }].map((camera) => (
          <div key={camera.label} className={`${glassSection} p-3`}>
            <div className="mb-3 flex items-center justify-between">
              <div>
                <h4 className="text-sm font-black text-black">Camera {camera.label}</h4>
                <p className="text-[11px] text-gray-500">即時偵測畫面</p>
              </div>
              <div className="rounded-full border border-white/10 bg-green-400 px-2.5 py-1 text-[10px] font-bold text-white/70">
                {taskId ? 'LIVE' : 'IDLE'}
              </div>
            </div>

            <div className="relative flex min-h-[320px] items-center justify-center overflow-hidden rounded-2xl border border-white/10 bg-slate-950/80">
              {camera.url ? (
                <img
                  src={camera.url}
                  alt={`cam-${camera.label}`}
                  className="h-full w-full object-contain"
                />
              ) : (
                <div className="flex flex-col items-center justify-center px-6 text-center">
                  <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-white/10 text-white/70">
                    <Camera className="h-6 w-6" />
                  </div>
                  <h4 className="text-sm font-bold text-white">Camera {camera.label} 未啟動</h4>
                  <p className="mt-2 text-xs leading-6 text-white/45">請於上方 Dashboard 點擊開始監測。</p>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default DualCameraViewer
import { useEffect, useMemo, useState } from 'react'
import { Camera, AlertCircle } from 'lucide-react'

const API_BASE = 'http://127.0.0.1:8000'

type MultiCameraViewerProps = {
  isMonitoring: boolean
  sources: string[]
}

const glassPanel =
  'rounded-[14px] 2xl:rounded-[16px] bg-white/10 shadow-[inset_0_1px_0_rgba(255,255,255,0.14),0_8px_24px_rgba(0,0,0,0.18)] backdrop-blur-xl'

const glassSection =
  'rounded-[12px] bg-black/20 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]'

export default function MultiCameraViewer({ isMonitoring, sources }: MultiCameraViewerProps) {
  const [taskId, setTaskId] = useState('')
  const [error, setError] = useState('')
  const [isStarting, setIsStarting] = useState(false)
  const [isStopping, setIsStopping] = useState(false)
  const [streamUrls, setStreamUrls] = useState<Record<string, string>>({})

  const token = localStorage.getItem('token') || ''
  const sourcesKey = useMemo(() => sources.join(','), [sources])

  const startMulti = async () => {
    try {
      setIsStarting(true)
      setError('')
      setStreamUrls({})

      const res = await fetch(`${API_BASE}/yolo/start/multi?sources=${encodeURIComponent(sourcesKey)}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        credentials: 'include',
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.detail || data.message || '啟動失敗')
      }

      if (data.task_id) {
        setTaskId(data.task_id)
      } else if (data.active_task_id) {
        setTaskId(data.active_task_id)
        setError(data.message || '已有執行中的任務')
      } else {
        throw new Error(data.message || '未取得 task_id')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '多鏡頭啟動失敗')
    } finally {
      setIsStarting(false)
    }
  }

  const stopMulti = async () => {
    if (!taskId) return

    try {
      setIsStopping(true)
      setError('')

      await fetch(`${API_BASE}/yolo/stop/${taskId}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        credentials: 'include',
      })

      setTaskId('')
      setStreamUrls({})
    } catch (err) {
      setError(err instanceof Error ? err.message : '停止任務失敗')
    } finally {
      setIsStopping(false)
    }
  }

  useEffect(() => {
    if (isMonitoring && !taskId && !isStarting) {
      startMulti()
    }

    if (!isMonitoring && taskId) {
      stopMulti()
    }
  }, [isMonitoring, sourcesKey])

  useEffect(() => {
    if (!taskId) return

    const timer = setInterval(() => {
      const t = Date.now()
      const nextUrls: Record<string, string> = {}

      sources.forEach((source, index) => {
        nextUrls[`cam${index}`] = `${API_BASE}/yolo/stream/${taskId}/cam${index}?t=${t}`
      })

      setStreamUrls(nextUrls)
    }, 200)

    return () => clearInterval(timer)
  }, [taskId, sourcesKey])

  return (
    <div className="h-full space-y-3">
      {error && (
        <div className="rounded-xl bg-red-500/10 px-4 py-3 text-sm text-red-200">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4" />
            <span>{error}</span>
          </div>
        </div>
      )}

      <div className={`${glassPanel} overflow-hidden`}>
        <div className="flex flex-col gap-3 px-4 py-4 lg:flex-row lg:items-center lg:justify-between 2xl:px-5">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-400/15 text-emerald-400">
              <Camera className="h-4 w-4" />
            </div>
            <div>
              <h3 className="text-sm font-black text-white 2xl:text-base">多鏡頭即時監控</h3>
              <p className="text-[11px] text-white/45 2xl:text-xs">
                共 {sources.length} 路來源，統一 ReID / Pose 偵測
              </p>
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
              {isStarting ? 'STARTING' : isStopping ? 'STOPPING' : taskId ? 'RUNNING' : 'IDLE'}
            </div>
          </div>
        </div>

        <div className="p-3 2xl:p-4">
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-3 2xl:grid-cols-4">
            {sources.map((source, index) => {
              const camKey = `cam${index}`
              const url = streamUrls[camKey] || ''

              return (
                <div key={camKey} className={`${glassSection} p-3`}>
                  <div className="mb-3 flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-black text-white">Camera {source}</h4>
                      <p className="text-[11px] text-white/45">映射 {camKey}</p>
                    </div>
                    <div className="rounded-full bg-white/5 px-2.5 py-1 text-[10px] font-bold text-white/70">
                      {taskId ? 'LIVE' : 'IDLE'}
                    </div>
                  </div>

                  <div className="relative flex aspect-[16/9] items-center justify-center overflow-hidden rounded-2xl bg-slate-950/85 ring-1 ring-white/5">
                    {url ? (
                      <img
                        src={url}
                        alt={camKey}
                        className="h-full w-full object-contain"
                      />
                    ) : (
                      <div className="flex flex-col items-center justify-center px-4 text-center">
                        <div className="mb-2 flex h-12 w-12 items-center justify-center rounded-2xl bg-white/10 text-white/70">
                          <Camera className="h-5 w-5" />
                        </div>
                        <h4 className="text-xs font-bold text-white lg:text-sm">
                          Camera {source} 未啟動
                        </h4>
                        <p className="mt-1 text-[10px] text-white/45 lg:text-xs">
                          等待多鏡頭任務開始
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
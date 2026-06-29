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
  <div className="flex flex-col h-full space-y-3 min-h-0">
    {/* 錯誤提示 */}
    {error && (
      <div className="shrink-0 rounded-xl bg-red-500/10 px-4 py-3 text-sm text-red-200">
        <div className="flex items-center gap-2">
          <AlertCircle className="h-4 w-4" />
          <span>{error}</span>
        </div>
      </div>
    )}

    {/* 主面板容器 - 設定 flex-1 填滿剩餘空間，min-h-0 觸發滾動 */}
    <div className={`${glassPanel} flex flex-1 flex-col overflow-hidden min-h-0`}>
      

      {/* 鏡頭畫面滾動區塊 - 這裡是最關鍵的滾動處 */}
      <div className="custom-scrollbar flex-1 overflow-y-auto p-3 2xl:p-4 bg-black/20">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4">
          {sources.map((source, index) => {
            const camKey = `cam${index}`
            const url = streamUrls[camKey] || ''

            return (
              <div key={camKey} className={`${glassSection} p-3 flex flex-col`}>
                <div className="mb-3 flex items-center justify-between shrink-0">
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
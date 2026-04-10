import { useEffect, useState } from 'react'

const API_BASE = 'http://127.0.0.1:8000'

const DualCameraViewer = () => {
  const [taskId, setTaskId] = useState('')
  const [error, setError] = useState('')
  const [isStarting, setIsStarting] = useState(false)
  const [isStopping, setIsStopping] = useState(false)
  const [cam0Url, setCam0Url] = useState('')
  const [cam1Url, setCam1Url] = useState('')
  const [cam0Error, setCam0Error] = useState(false)
  const [cam1Error, setCam1Error] = useState(false)

  const token = localStorage.getItem('token') || ''

  const clearStreams = () => {
    setCam0Url('')
    setCam1Url('')
    setCam0Error(false)
    setCam1Error(false)
  }

  const startDual = async () => {
    try {
      setIsStarting(true)
      setError('')
      clearStreams()

      const res = await fetch(
        `${API_BASE}/yolo/start/dual?source0=0&source1=1`,
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

      const currentTaskId = taskId

      const res = await fetch(`${API_BASE}/yolo/stop/${currentTaskId}`, {
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
    if (!taskId) return

    const timer = setInterval(() => {
      const t = Date.now()
      setCam0Url(`${API_BASE}/yolo/stream/${taskId}/cam0?t=${t}`)
      setCam1Url(`${API_BASE}/yolo/stream/${taskId}/cam1?t=${t}`)
    }, 200)

    return () => clearInterval(timer)
  }, [taskId])

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <div className="mb-6 rounded-3xl border border-white/60 bg-white/70 p-6 shadow-xl shadow-slate-200/60 backdrop-blur-xl">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              雙鏡頭 YOLO 即時畫面
            </h1>
            <p className="mt-2 text-sm text-slate-600">
              可同步鏡頭 cam0 與 cam1，並持續更新後端偵測結果。
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={startDual}
              disabled={isStarting || isStopping}
              className="inline-flex items-center justify-center rounded-xl bg-lime-400 px-5 py-3 text-sm font-semibold text-black shadow-md shadow-lime-400/30 transition hover:bg-lime-300 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isStarting ? '啟動中...' : '啟動雙鏡頭偵測'}
            </button>

            <button
              onClick={stopDual}
              disabled={!taskId || isStarting || isStopping}
              className="inline-flex items-center justify-center rounded-xl bg-red-500 px-5 py-3 text-sm font-semibold text-white shadow-md shadow-red-500/20 transition hover:bg-red-400 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isStopping ? '停止中...' : '停止任務'}
            </button>
          </div>
        </div>

        <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
          <div className="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-sm text-slate-700">
            <span className="mr-2 h-2.5 w-2.5 rounded-full bg-emerald-500" />
            {taskId ? `Task ID: ${taskId}` : '尚未啟動任務'}
          </div>

          <div className="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-sm text-slate-700">
            Source: cam0 + cam1
          </div>
        </div>

        {error && (
          <div className="mt-5 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
            {error}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <div className="overflow-hidden rounded-3xl border border-slate-200/80 bg-white/80 shadow-2xl shadow-slate-200/70 backdrop-blur-xl">
          <div className="flex items-center justify-between border-b border-slate-200/80 px-5 py-4">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Camera 0</h2>
              <p className="mt-1 text-sm text-slate-500">即時偵測畫面</p>
            </div>
            <div className="rounded-full bg-slate-900 px-3 py-1 text-xs font-medium text-white">
              {taskId ? 'RUNNING' : 'IDLE'}
            </div>
          </div>

          <div className="p-4 sm:p-6">
            <div className="relative flex min-h-[320px] items-center justify-center overflow-hidden rounded-2xl border border-slate-200 bg-slate-950 sm:min-h-[420px]">
              {cam0Url ? (
                <img
                  src={cam0Url}
                  alt="cam0"
                  className="h-full w-full object-contain"
                  onError={() => setCam0Error(true)}
                  onLoad={() => setCam0Error(false)}
                />
              ) : (
                <div className="flex flex-col items-center justify-center px-6 text-center">
                  <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-white/10 text-2xl text-white">
                    📷
                  </div>
                  <h3 className="text-lg font-semibold text-white">Camera 0 尚未啟動</h3>
                  <p className="mt-2 max-w-md text-sm leading-6 text-slate-300">
                    啟動雙鏡頭任務後，這裡會顯示 cam0 的即時畫面。
                  </p>
                </div>
              )}
            </div>

            {cam0Error && (
              <p className="mt-3 text-sm font-medium text-red-600">
                cam0 畫面載入失敗
              </p>
            )}
          </div>
        </div>

        <div className="overflow-hidden rounded-3xl border border-slate-200/80 bg-white/80 shadow-2xl shadow-slate-200/70 backdrop-blur-xl">
          <div className="flex items-center justify-between border-b border-slate-200/80 px-5 py-4">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Camera 1</h2>
              <p className="mt-1 text-sm text-slate-500">即時偵測畫面</p>
            </div>
            <div className="rounded-full bg-slate-900 px-3 py-1 text-xs font-medium text-white">
              {taskId ? 'RUNNING' : 'IDLE'}
            </div>
          </div>

          <div className="p-4 sm:p-6">
            <div className="relative flex min-h-[320px] items-center justify-center overflow-hidden rounded-2xl border border-slate-200 bg-slate-950 sm:min-h-[420px]">
              {cam1Url ? (
                <img
                  src={cam1Url}
                  alt="cam1"
                  className="h-full w-full object-contain"
                  onError={() => setCam1Error(true)}
                  onLoad={() => setCam1Error(false)}
                />
              ) : (
                <div className="flex flex-col items-center justify-center px-6 text-center">
                  <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-white/10 text-2xl text-white">
                    📷
                  </div>
                  <h3 className="text-lg font-semibold text-white">Camera 1 尚未啟動</h3>
                  <p className="mt-2 max-w-md text-sm leading-6 text-slate-300">
                    啟動雙鏡頭任務後，這裡會顯示 cam1 的即時畫面。
                  </p>
                </div>
              )}
            </div>

            {cam1Error && (
              <p className="mt-3 text-sm font-medium text-red-600">
                cam1 畫面載入失敗
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default DualCameraViewer
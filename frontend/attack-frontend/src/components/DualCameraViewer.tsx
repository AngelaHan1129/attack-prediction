import { useEffect, useState } from 'react'

import dashboardBg from '../assets/hlogo_al.png'
import workspaceOverlay from '../assets/work-space.svg'

const API_BASE = 'http://localhost:8000'

const DualCameraViewer = () => {
  const [taskId, setTaskId] = useState('')
  const [error, setError] = useState('')
  const [isStarting, setIsStarting] = useState(false)
  const [isStopping, setIsStopping] = useState(false)
  const token = localStorage.getItem('token') || ''

  const startDual = async () => {
    try {
      setIsStarting(true)
      setError('')

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
      const cam0 = document.getElementById('cam0') as HTMLImageElement | null
      const cam1 = document.getElementById('cam1') as HTMLImageElement | null

      if (cam0) {
        cam0.src = `${API_BASE}/yolo/stream/${taskId}/cam0?t=${t}`
      }

      if (cam1) {
        cam1.src = `${API_BASE}/yolo/stream/${taskId}/cam1?t=${t}`
      }
    }, 200)

    return () => clearInterval(timer)
  }, [taskId])

  return (
  <div className="relative min-h-screen overflow-hidden">
    <div className="absolute inset-0 z-0 overflow-hidden">
      <img
        src={workspaceOverlay}
        alt="workspace overlay"
        className="pointer-events-none absolute inset-0 z-[1] h-full w-full select-none object-cover"
      />
      <img
        src={dashboardBg}
        alt="dashboard background"
        className="pointer-events-none absolute inset-0 z-[2] h-full w-full select-none object-cover object-center"
      />
      <div className="absolute inset-0 z-[3] bg-white/40 backdrop-blur-[1px]" />
    </div>

    <div className="relative z-10 mx-auto max-w-7xl p-6">
      <div className="mb-6 flex items-center gap-4">
        <button
          onClick={startDual}
          disabled={isStarting || isStopping}
          className="rounded-xl bg-lime-400 px-5 py-3 font-semibold text-black transition hover:bg-lime-300 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isStarting ? '啟動中...' : '啟動雙鏡頭偵測'}
        </button>

        <button
          onClick={stopDual}
          disabled={!taskId || isStarting || isStopping}
          className="rounded-xl bg-red-500 px-5 py-3 font-semibold text-white transition hover:bg-red-400 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isStopping ? '停止中...' : '停止任務'}
        </button>

        {taskId && (
          <span className="rounded-lg bg-white/70 px-3 py-2 text-sm text-slate-700 shadow">
            Task ID: {taskId}
          </span>
        )}
      </div>

      {error && (
        <div className="mb-4 rounded-xl border border-red-300 bg-red-50 px-4 py-3 text-red-700">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <div className="rounded-2xl bg-white/70 p-4 shadow backdrop-blur">
          <h2 className="mb-3 text-lg font-bold text-slate-800">Camera 0</h2>
          <img
            id="cam0"
            alt="cam0"
            className="w-full rounded-xl border border-slate-200 bg-slate-100"
          />
        </div>

        <div className="rounded-2xl bg-white/70 p-4 shadow backdrop-blur">
          <h2 className="mb-3 text-lg font-bold text-slate-800">Camera 1</h2>
          <img
            id="cam1"
            alt="cam1"
            className="w-full rounded-xl border border-slate-200 bg-slate-100"
          />
        </div>
      </div>
    </div>
  </div>
)
}

export default DualCameraViewer
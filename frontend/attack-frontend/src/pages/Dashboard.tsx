import React, { useEffect, useMemo, useState } from 'react'
import { Clock, Bell, X, Camera, LogOut, RefreshCw } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import YoloViewer from '../components/YoloViewer'
import MultiCameraViewer from '../components/MultiCameraViewer'

import dashboardBg from '../assets/hlogo_al.png'
import workspaceOverlay from '../assets/work-space.svg'

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000'

type RiskLevel = 'L0' | 'L1' | 'L2' | 'L3' | 'L4'
type ViewMode = 'single' | 'multi'

type Alert = {
  id: string
  camera: string
  level: RiskLevel
  time: string
  description: string
}

type CameraItem = {
  id: string
  name: string
  source: string
  streamUrl?: string
}

type CameraListResponse = {
  count: number
  cameras: CameraItem[]
}

const glassCard =
  'relative rounded-[16px] 2xl:rounded-[18px] border border-white/50 bg-white/45 backdrop-blur-2xl backdrop-saturate-150 shadow-[0_10px_30px_rgba(15,23,42,0.08)] ring-1 ring-white/60'

const controlButton =
  'rounded-lg px-2 py-1.5 md:px-3 md:py-2 text-[10px] md:text-xs font-bold transition disabled:cursor-not-allowed disabled:opacity-50 whitespace-nowrap'

const riskBadgeStyles: Record<RiskLevel, string> = {
  L0: 'bg-emerald-400 text-emerald-950',
  L1: 'bg-yellow-400 text-yellow-950',
  L2: 'bg-orange-400 text-orange-950',
  L3: 'bg-red-500 text-white',
  L4: 'bg-fuchsia-500 text-white',
}

const venues: string[] = ['車站A', '車站B', '車站C', '商圈']

const Dashboard: React.FC = () => {
  const navigate = useNavigate()

  const [currentVenue, setCurrentVenue] = useState<string>(venues[0])
  const [viewMode, setViewMode] = useState<ViewMode>('multi')
  const [isMonitoring, setIsMonitoring] = useState<boolean>(false)
  const [selectedCamera, setSelectedCamera] = useState<string>('0')
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [currentTime, setCurrentTime] = useState<Date>(new Date())

  const [cameras, setCameras] = useState<CameraItem[]>([])
  const [cameraLoading, setCameraLoading] = useState<boolean>(true)
  const [cameraError, setCameraError] = useState<string>('')

  const handleLogout = (): void => {
    localStorage.removeItem('token')
    navigate('/login')
  }

  const stats = useMemo(() => {
    const l3Events = alerts.filter((a) => a.level === 'L3').length
    const l4Events = alerts.filter((a) => a.level === 'L4').length
    const handledRate = alerts.length === 0 ? 100 : 85
    return { l3Events, l4Events, handledRate }
  }, [alerts])

  const cameraOptions = useMemo(
    () => cameras.map((camera) => camera.source),
    [cameras]
  )

  const multiSources = useMemo(
    () => cameras.map((camera) => camera.source),
    [cameras]
  )

  const fetchCameras = async () => {
    try {
      setCameraLoading(true)
      setCameraError('')

      const res = await fetch(`${BASE_URL}/yolo/cameras`)
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`)
      }

      const data: CameraListResponse = await res.json()
      const nextCameras = Array.isArray(data.cameras) ? data.cameras : []

      setCameras(nextCameras)

      if (nextCameras.length > 0) {
        const hasSelected = nextCameras.some((camera) => camera.source === selectedCamera)
        if (!hasSelected) {
          setSelectedCamera(nextCameras[0].source)
        }
      }
    } catch (err) {
      console.error(err)
      setCameraError('無法取得鏡頭資料，請確認 FastAPI /cameras 是否正常')
      setCameras([])
    } finally {
      setCameraLoading(false)
    }
  }

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    fetchCameras()
  }, [])

  useEffect(() => {
    const demoAlerts: Alert[] = [
      {
        id: 'a1',
        camera: 'Cam 02',
        level: 'L3',
        time: '20:01:14',
        description: '高風險肢體衝突疑似發生',
      },
      {
        id: 'a2',
        camera: 'Cam 07',
        level: 'L2',
        time: '20:02:48',
        description: '人群聚集異常',
      },
      {
        id: 'a3',
        camera: 'Cam 01',
        level: 'L4',
        time: '20:03:09',
        description: '危急事件，建議立即查看',
      },
    ]
    setAlerts(demoAlerts)
  }, [])

  const clearAlert = (id: string) => {
    setAlerts((prev) => prev.filter((a) => a.id !== id))
  }

  const clearAllAlerts = () => setAlerts([])

  const modeButton = (active: boolean) =>
    `${controlButton} ${
      active
        ? 'bg-emerald-400 text-emerald-950 shadow-sm'
        : 'bg-slate-900/8 text-slate-700 hover:bg-slate-900/12'
    }`

  return (
    <div className="relative min-h-screen lg:h-[100dvh] w-full overflow-x-hidden bg-white text-slate-900">
      <div className="fixed inset-0 z-0 pointer-events-none">
        <img
          src={workspaceOverlay}
          alt=""
          className="absolute inset-0 h-full w-full object-cover opacity-25"
        />
        <img
          src={dashboardBg}
          alt=""
          className="absolute inset-0 h-full w-full object-cover opacity-18"
        />
        <div className="absolute inset-0 bg-white/78" />
      </div>

      <div className="relative z-10 flex min-h-screen flex-col gap-3 p-3 md:p-4 lg:h-[100dvh] lg:overflow-hidden lg:p-5">
        <header className={`${glassCard} shrink-0 p-3`}>
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="flex min-w-0 items-center gap-3">
              <Clock className="h-5 w-5 shrink-0 text-emerald-500" />
              <div className="min-w-0">
                <p className="truncate text-sm font-black tabular-nums md:text-lg text-slate-900">
                  {currentTime.toLocaleString('zh-TW', { hour12: false })}
                </p>
                <p className="text-[11px] text-slate-500">
                  AI 風險監視儀表板・{currentVenue}
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <select
                value={currentVenue}
                onChange={(e) => setCurrentVenue(e.target.value)}
                className="rounded-lg border border-slate-200/80 bg-white/70 px-2 py-1 text-xs text-slate-700 outline-none backdrop-blur"
              >
                {venues.map((v) => (
                  <option key={v} value={v}>
                    {v}
                  </option>
                ))}
              </select>

              <div className="flex gap-1 rounded-xl bg-slate-900/5 p-1">
                {(['single', 'multi'] as ViewMode[]).map((m) => (
                  <button
                    key={m}
                    onClick={() => setViewMode(m)}
                    className={modeButton(viewMode === m)}
                  >
                    {m === 'single' ? '單鏡頭' : `多鏡頭(${cameras.length})`}
                  </button>
                ))}
              </div>

              {viewMode === 'single' && (
                <div className="flex items-center gap-1 rounded-xl bg-slate-900/5 p-1">
                  <Camera className="h-4 w-4 text-slate-500" />
                  <select
                    value={selectedCamera}
                    onChange={(e) => setSelectedCamera(e.target.value)}
                    className="rounded-md bg-transparent px-1 py-1 text-xs text-slate-700 outline-none"
                    disabled={cameras.length === 0}
                  >
                    {cameraOptions.length === 0 ? (
                      <option value="">無鏡頭</option>
                    ) : (
                      cameraOptions.map((cam) => (
                        <option key={cam} value={cam} className="bg-white text-slate-800">
                          Cam {cam}
                        </option>
                      ))
                    )}
                  </select>
                </div>
              )}

              <button
                onClick={fetchCameras}
                className={`${controlButton} flex items-center gap-1.5 bg-slate-200 text-slate-800 hover:bg-slate-300`}
              >
                <RefreshCw className="h-3.5 w-3.5" />
                <span>刷新鏡頭</span>
              </button>

              <button
                onClick={() => setIsMonitoring((prev) => !prev)}
                className={`${controlButton} ${
                  isMonitoring
                    ? 'bg-red-500 text-white hover:bg-red-600'
                    : 'bg-lime-400 text-lime-950 hover:bg-lime-500'
                }`}
              >
                {isMonitoring ? '停止監測' : '開始監測'}
              </button>

              <button
                onClick={handleLogout}
                className={`${controlButton} flex items-center gap-1.5 bg-red-800 text-white hover:bg-red-600`}
                aria-label="登出系統"
              >
                <LogOut className="h-3.5 w-3.5" />
                <span>登出</span>
              </button>
            </div>
          </div>
        </header>

        <main className="grid flex-1 grid-cols-1 gap-4 lg:min-h-0 lg:grid-cols-4 xl:grid-cols-5">
          <section
            className={`${glassCard} flex min-h-[500px] flex-col p-3 lg:col-span-3 lg:min-h-0 xl:col-span-4`}
          >
            <div className="flex-1 min-h-0 overflow-y-auto overscroll-contain custom-scrollbar rounded-lg bg-white/25">
              {cameraLoading ? (
                <div className="flex h-full min-h-[300px] items-center justify-center text-sm text-slate-500">
                  讀取鏡頭中...
                </div>
              ) : cameraError ? (
                <div className="flex h-full min-h-[300px] items-center justify-center text-sm text-red-500">
                  {cameraError}
                </div>
              ) : cameras.length === 0 ? (
                <div className="flex h-full min-h-[300px] items-center justify-center text-sm text-slate-500">
                  目前沒有可用鏡頭
                </div>
              ) : viewMode === 'single' ? (
                <YoloViewer isMonitoring={isMonitoring} source={selectedCamera} />
              ) : (
                <MultiCameraViewer
                  isMonitoring={isMonitoring}
                  sources={multiSources}
                />
              )}
            </div>
          </section>

          <aside className="flex min-h-0 flex-col gap-4 lg:col-span-1">
            <div
              className={`${glassCard} flex min-h-[300px] flex-1 flex-col overflow-hidden p-4 lg:min-h-0`}
            >
              <div className="mb-3 flex items-center justify-between">
                <h3 className="flex items-center gap-2 text-xs font-black text-slate-500">
                  <Bell className="h-4 w-4 text-red-500" />
                  即時告警
                </h3>

                {alerts.length > 0 && (
                  <button
                    onClick={clearAllAlerts}
                    className="text-[10px] text-slate-500 transition hover:text-slate-800"
                  >
                    清空
                  </button>
                )}
              </div>

              <div className="flex-1 overflow-y-auto overscroll-contain custom-scrollbar pr-1">
                {alerts.length === 0 ? (
                  <div className="flex h-full min-h-[180px] items-center justify-center rounded-xl border border-dashed border-slate-200 bg-white/40 text-center">
                    <div>
                      <Bell className="mx-auto mb-2 h-5 w-5 text-slate-300" />
                      <p className="text-xs font-semibold text-slate-700">目前沒有告警</p>
                      <p className="mt-1 text-[11px] text-slate-500">
                        系統將在偵測到高風險事件時顯示
                      </p>
                    </div>
                  </div>
                ) : (
                  alerts.map((alert) => (
                    <div
                      key={alert.id}
                      className="relative mb-2 rounded-lg border border-white/70 bg-white/55 p-3 shadow-sm"
                    >
                      <button
                        onClick={() => clearAlert(alert.id)}
                        className="absolute right-2 top-2 text-slate-400 opacity-70 transition hover:text-slate-700 hover:opacity-100"
                        aria-label={`關閉告警 ${alert.id}`}
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>

                      <div className="mb-2 flex items-center gap-2">
                        <span
                          className={`rounded px-1.5 py-0.5 text-[10px] font-black ${riskBadgeStyles[alert.level]}`}
                        >
                          {alert.level}
                        </span>
                        <span className="text-[11px] text-slate-500">{alert.time}</span>
                      </div>

                      <div className="text-xs font-bold text-slate-900">{alert.camera}</div>
                      <p className="mt-1 pr-5 text-[11px] leading-5 text-slate-600">
                        {alert.description}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </div>
          </aside>
        </main>
      </div>

      <style>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; height: 4px; }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(100, 116, 139, 0.35);
          border-radius: 999px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
      `}</style>
    </div>
  )
}

export default Dashboard
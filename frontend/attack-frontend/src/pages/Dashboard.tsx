import React, { useEffect, useRef, useState } from 'react'
import { Video, Clock, Bell, X } from 'lucide-react'
import YoloViewer from '../components/YoloViewer'
import DualCameraViewer from '../components/DualCameraViewer'
import MultiCameraViewer from '../components/MultiCameraViewer'

import dashboardBg from '../assets/hlogo_al.png'
import workspaceOverlay from '../assets/work-space.svg'

type RiskLevel = 'L0' | 'L1' | 'L2' | 'L3' | 'L4'
type ViewMode = 'single' | 'dual' | 'twelve'

const riskColors: Record<RiskLevel, string> = {
  L0: 'bg-emerald-400',
  L1: 'bg-yellow-400',
  L2: 'bg-orange-400',
  L3: 'bg-red-500',
  L4: 'bg-fuchsia-500',
}

type Camera = {
  id: string
  name: string
  risk: RiskLevel
  streamUrl: string
}

type Alert = {
  id: string
  camera: string
  level: RiskLevel
  time: string
  description: string
}

const venues: string[] = ['車站A', '車站B', '車站C', '商圈']

const glassCard =
  'relative rounded-[16px] 2xl:rounded-[18px] border border-white/20 bg-black/20 backdrop-blur-2xl backdrop-saturate-140 backdrop-brightness-110 shadow-[0_12px_28px_rgba(0,0,0,0.16),inset_0_1px_0_rgba(255,255,255,0.22),inset_0_-10px_16px_rgba(255,255,255,0.04)] ring-1 ring-white/10'

const controlButton =
  'rounded-lg px-3 py-2 text-xs font-bold transition disabled:cursor-not-allowed disabled:opacity-50'

const Dashboard: React.FC = () => {
  const [currentVenue, setCurrentVenue] = useState<string>(venues[0])
  const [viewMode, setViewMode] = useState<ViewMode>('twelve')
  const [isMonitoring, setIsMonitoring] = useState<boolean>(false)
  const [selectedCamera, setSelectedCamera] = useState<string>('0')

  const [cameras] = useState<Camera[]>(() =>
    Array.from({ length: 12 }, (_, i) => ({
      id: `cam-${i + 1}`,
      name: `鏡頭 ${i + 1}`,
      risk: (
        ['L0', 'L1', 'L0', 'L2', 'L0', 'L3', 'L1', 'L0', 'L4', 'L0', 'L2', 'L0'] as RiskLevel[]
      )[i],
      streamUrl: `cam${i}`,
    }))
  )

  const [alerts, setAlerts] = useState<Alert[]>([])
  const [stats] = useState({
    l3Events: 5,
    l4Events: 2,
    handledRate: 85,
  })
  const [currentTime, setCurrentTime] = useState<Date>(new Date())
  const [systemStatus] = useState<'正常' | '警告' | '故障'>('正常')
  const audioRef = useRef<HTMLAudioElement>(null)

  const twelveSources = Array.from({ length: 12 }, (_, i) => String(i))

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    const interval = setInterval(() => {
      if (!isMonitoring) return

      const now = new Date()
      const newAlert: Alert = {
        id: `alert-${Date.now()}`,
        camera: `鏡頭 ${Math.floor(Math.random() * 12) + 1}`,
        level: (['L3', 'L4'] as RiskLevel[])[Math.floor(Math.random() * 2)],
        time: now.toLocaleTimeString('zh-TW', { hour12: false }),
        description: '偵測異常行為',
      }

      setAlerts((prev) => [newAlert, ...prev.slice(0, 9)])

      if (audioRef.current) {
        audioRef.current.play().catch(() => {})
      }
    }, 30000)

    return () => clearInterval(interval)
  }, [isMonitoring])

  const clearAlert = (id: string): void => {
    setAlerts((prev) => prev.filter((a) => a.id !== id))
  }

  const handleVenueChange = (venue: string): void => {
    setCurrentVenue(venue)
  }

  const handleStartMonitoring = (): void => {
    setIsMonitoring(true)
  }

  const handleStopMonitoring = (): void => {
    setIsMonitoring(false)
  }

  const modeButton = (active: boolean) =>
    `${controlButton} ${
      active
        ? 'bg-emerald-400 text-emerald-950'
        : 'bg-white/10 text-white hover:bg-white/20'
    }`

  return (
    <div className="relative h-[100dvh] w-full overflow-hidden bg-slate-950 text-black">
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
      </div>

      <div className="relative z-10 grid h-full min-h-0 grid-rows-[auto,minmax(0,1fr)] gap-2 p-2 pb-24 lg:gap-2.5 lg:p-2.5 lg:pb-24 2xl:gap-4 2xl:p-4 2xl:pb-4">
        <div className={`${glassCard} min-h-0 px-2.5 py-1.5 2xl:px-4 2xl:py-2.5`}>
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex min-w-0 items-center gap-2.5">
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border border-white/20 bg-white/10 shadow-lg backdrop-blur-md lg:h-8 lg:w-8 2xl:h-9 2xl:w-9">
                <Clock className="h-3.5 w-3.5 text-white/80 2xl:h-4.5 2xl:w-4.5" />
              </div>

              <div className="min-w-0">
                <p className="text-[7px] font-semibold uppercase tracking-[0.18em] text-white/38 lg:text-[8px] lg:tracking-[0.22em]">
                  Surveillance Security Platform
                </p>
                <p className="truncate text-xs font-extrabold tracking-normal text-white tabular-nums lg:text-sm xl:text-base 2xl:text-lg">
                  {currentTime.toLocaleString('zh-TW', { hour12: false })}
                </p>
              </div>

              <div
                className={`shrink-0 rounded-full px-2.5 py-1 text-[9px] font-black shadow-lg 2xl:px-3 2xl:text-[10px] ${
                  systemStatus === '正常'
                    ? 'bg-emerald-400 text-emerald-950'
                    : 'bg-red-500 text-white'
                }`}
              >
                系統{systemStatus}
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <select
                value={currentVenue}
                onChange={(e) => handleVenueChange(e.target.value)}
                className="rounded-lg border border-white/10 bg-white/5 px-2.5 py-1.5 text-[11px] font-bold text-white outline-none backdrop-blur-xl transition-all hover:bg-white/10 focus:ring-2 focus:ring-emerald-400/50 lg:px-3 lg:py-2 lg:text-xs"
              >
                {venues.map((v) => (
                  <option key={v} value={v} className="bg-slate-900">
                    {v}
                  </option>
                ))}
              </select>

              {viewMode === 'single' && (
                <select
                  value={selectedCamera}
                  onChange={(e) => setSelectedCamera(e.target.value)}
                  className="rounded-lg border border-white/10 bg-white/5 px-2.5 py-1.5 text-[11px] font-bold text-white outline-none backdrop-blur-xl transition-all hover:bg-white/10 focus:ring-2 focus:ring-emerald-400/50 lg:px-3 lg:py-2 lg:text-xs"
                >
                  {cameras.map((camera, index) => (
                    <option key={camera.id} value={String(index)} className="bg-slate-900">
                      {camera.name}
                    </option>
                  ))}
                </select>
              )}

              <button onClick={() => setViewMode('single')} className={modeButton(viewMode === 'single')}>
                單鏡頭
              </button>

              <button onClick={() => setViewMode('dual')} className={modeButton(viewMode === 'dual')}>
                雙鏡頭
              </button>

              <button onClick={() => setViewMode('twelve')} className={modeButton(viewMode === 'twelve')}>
                12鏡頭
              </button>

              <button
                onClick={handleStartMonitoring}
                disabled={isMonitoring}
                className={`${controlButton} bg-lime-400 text-black hover:bg-lime-300`}
              >
                開始監測
              </button>

              <button
                onClick={handleStopMonitoring}
                disabled={!isMonitoring}
                className={`${controlButton} bg-red-500 text-white hover:bg-red-400`}
              >
                停止監測
              </button>
            </div>
          </div>
        </div>

        <div className="grid min-h-0 grid-cols-1 gap-2 lg:grid-cols-[minmax(0,3.7fr)_220px] 2xl:grid-cols-[minmax(0,3.35fr)_minmax(260px,0.95fr)] 2xl:gap-4">
          <div className={`${glassCard} flex min-h-0 flex-col p-2 lg:p-2 2xl:p-4`}>
            <div className="mb-2.5 flex shrink-0 items-center justify-between">
              <h2 className="flex items-center gap-2 text-sm font-black text-white xl:text-base 2xl:text-xl">
                <div className="flex h-5 w-7 items-center justify-center rounded-lg bg-emerald-400/20 text-emerald-400 2xl:h-9 2xl:w-9">
                  <Video className="h-3.5 w-3.5 2xl:h-5 2xl:w-5" />
                </div>
                {viewMode === 'single'
                  ? '單鏡頭監控'
                  : viewMode === 'dual'
                  ? '雙鏡頭監控'
                  : '多鏡頭監控'}
              </h2>

              <div className="rounded-lg bg-emerald-400 px-2 py-1 text-[8px] font-black text-emerald-950 shadow-lg shadow-emerald-400/20 2xl:px-3 2xl:py-1.5 2xl:text-[10px]">
                {isMonitoring ? 'MONITORING' : 'IDLE'}
              </div>
            </div>

            <div className="custom-scrollbar min-h-0 flex-1 overflow-y-auto pr-1">
              {viewMode === 'single' && (
                <YoloViewer
                  isMonitoring={isMonitoring}
                  source={selectedCamera}
                />
              )}

              {viewMode === 'dual' && (
                <DualCameraViewer
                  isMonitoring={isMonitoring}
                  source0="0"
                  source1="1"
                />
              )}

              {viewMode === 'twelve' && (
                <MultiCameraViewer
                  isMonitoring={isMonitoring}
                  sources={twelveSources}
                />
              )}
            </div>
          </div>

          <div className="flex min-h-0 flex-col gap-2.5 2xl:gap-4">
            <div className={`${glassCard} p-2.5 2xl:p-4`}>
              <h3 className="mb-2.5 text-[11px] font-black text-white/80 xl:text-xs 2xl:mb-4 2xl:text-base">
                數據概況
              </h3>

              <div className="space-y-2">
                {[
                  {
                    label: 'L3 事件',
                    val: stats.l3Events,
                    color: 'border-red-500/30 bg-red-500/30 text-black-400',
                  },
                  {
                    label: 'L4 緊急',
                    val: stats.l4Events,
                    color: 'border-fuchsia-500/30 bg-fuchsia-500/30 text-black-400',
                  },
                  {
                    label: '處理率',
                    val: `${stats.handledRate}%`,
                    color: 'border-emerald-500/30 bg-emerald-500/30 text-black-400',
                  },
                ].map((s, i) => (
                  <div
                    key={i}
                    className={`flex items-center justify-between rounded-lg border p-2 ${s.color}`}
                  >
                    <span className="text-[9px] font-bold opacity-70 2xl:text-[11px]">{s.label}</span>
                    <span className="text-sm font-black tabular-nums xl:text-base 2xl:text-xl">{s.val}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className={`${glassCard} flex min-h-0 flex-1 flex-col p-2.5 2xl:p-4`}>
              <h3 className="mb-2.5 flex items-center gap-1.5 text-[11px] font-black text-white/80 xl:text-xs 2xl:mb-4 2xl:text-base">
                <Bell className="h-3 w-3 animate-pulse text-red-500 2xl:h-4 2xl:w-4" />
                即時告警
              </h3>

              <div className="custom-scrollbar min-h-0 flex-1 space-y-2 overflow-y-auto pr-1">
                {alerts.length === 0 ? (
                  <div className="rounded-lg border border-white/10 bg-white/5 p-2 text-[10px] text-white/45 2xl:text-xs">
                    目前尚無即時告警
                  </div>
                ) : (
                  alerts.map((alert) => (
                    <div
                      key={alert.id}
                      className="rounded-lg border border-white/5 bg-white/5 p-2 transition-all hover:bg-white/10"
                    >
                      <div className="mb-1 flex items-center justify-between">
                        <span
                          className={`rounded px-1.5 py-0.5 text-[7px] font-black text-white 2xl:text-[9px] ${riskColors[alert.level]}`}
                        >
                          {alert.level}
                        </span>

                        <X
                          className="cursor-pointer text-white/20 hover:text-white"
                          size={10}
                          onClick={() => clearAlert(alert.id)}
                        />
                      </div>

                      <div className="text-[10px] font-bold text-white lg:text-[11px] 2xl:text-sm">
                        {alert.camera}
                      </div>
                      <div className="text-[7px] text-white/40 2xl:text-[9px]">
                        {alert.time} - {alert.description}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>

        <audio ref={audioRef} src="..." preload="auto" />
      </div>

      <style>
        {`
          .custom-scrollbar::-webkit-scrollbar {
            width: 4px;
          }

          .custom-scrollbar::-webkit-scrollbar-track {
            background: transparent;
          }

          .custom-scrollbar::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.12);
            border-radius: 999px;
          }

          .custom-scrollbar::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.22);
          }
        `}
      </style>
    </div>
  )
}

export default Dashboard
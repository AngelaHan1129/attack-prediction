import React, { useEffect, useRef, useState } from 'react'
import { Video, Clock, Bell, Play, X } from 'lucide-react'

import dashboardBg from '../assets/hlogo_al.png'
import workspaceOverlay from '../assets/work-space.svg'

type RiskLevel = 'L0' | 'L1' | 'L2' | 'L3' | 'L4'

const riskColors: Record<RiskLevel, string> = {
  L0: 'bg-emerald-400',
  L1: 'bg-yellow-400',
  L2: 'bg-orange-400',
  L3: 'bg-red-500',
  L4: 'bg-fuchsia-500',
}

const riskLabels: Record<RiskLevel, string> = {
  L0: '正常',
  L1: '低風險',
  L2: '中風險',
  L3: '高風險',
  L4: '緊急',
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
  'relative rounded-[22px] border border-white/20 bg-white/10 backdrop-blur-2xl backdrop-saturate-140 backdrop-brightness-110 shadow-[0_20px_60px_rgba(0,0,0,0.22),inset_0_1px_0_rgba(255,255,255,0.30),inset_0_-16px_28px_rgba(255,255,255,0.05)] ring-1 ring-white/10'

const glassInner =
  'rounded-[24px] border border-white/15 bg-white/10 shadow-[inset_0_1px_0_rgba(255,255,255,0.20),0_10px_30px_rgba(0,0,0,0.12)]'

const Dashboard: React.FC = () => {
  const [currentVenue, setCurrentVenue] = useState<string>(venues[0])

  const [cameras] = useState<Camera[]>(() =>
    Array.from({ length: 12 }, (_, i) => ({
      id: `cam-${i + 1}`,
      name: `鏡頭 ${i + 1}`,
      risk: (
        ['L0', 'L1', 'L0', 'L2', 'L0', 'L3', 'L1', 'L0', 'L4', 'L0', 'L2', 'L0'] as RiskLevel[]
      )[i],
      streamUrl: `https://example.com/stream/cam-${i + 1}.m3u8`,
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

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    const interval = setInterval(() => {
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
        audioRef.current.play().catch(() => { })
      }
    }, 30000)

    return () => clearInterval(interval)
  }, [])

  const clearAlert = (id: string): void => {
    setAlerts((prev) => prev.filter((a) => a.id !== id))
  }

  const handleVenueChange = (venue: string): void => {
    setCurrentVenue(venue)
    console.log('切換場域:', venue)
  }

  return (
    <div className="relative h-[100dvh] w-full overflow-hidden bg-slate-950 text-black">
      {/* 背景層 */}
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


      {/* 主內容 */}
      <div className="relative z-10 grid h-full min-h-0 grid-rows-[auto,minmax(0,1fr)] gap-6 p-4">
        {/* 頂部 */}
        <div className={`${glassCard} min-h-0 px-6 py-4`}>
          <div className="flex items-center justify-between gap-4">
            <div className="flex min-w-0 items-center gap-6">
              <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl border border-white/20 bg-white/10 shadow-lg backdrop-blur-md">
                <Clock className="h-7 w-7 text-white/80" />
              </div>

              <div className="min-w-0">
                <p className="text-[10px] font-bold uppercase tracking-[0.4em] text-white/40">
                  Surveillance Security Platform
                </p>
                <p className="truncate text-2xl font-black tracking-wider text-white">
                  {currentTime.toLocaleString('zh-TW', { hour12: false })}
                </p>
              </div>

              <div
                className={`shrink-0 rounded-full px-4 py-1.5 text-xs font-black shadow-lg ${systemStatus === '正常'
                    ? 'bg-emerald-400 text-emerald-950'
                    : 'bg-red-500 text-white'
                  }`}
              >
                系統{systemStatus}
              </div>
            </div>

            <select
              value={currentVenue}
              onChange={(e) => handleVenueChange(e.target.value)}
              className="rounded-xl border border-white/10 bg-white/5 px-5 py-3 text-sm font-bold text-white outline-none backdrop-blur-xl transition-all hover:bg-white/10 focus:ring-2 focus:ring-emerald-400/50"
            >
              {venues.map((v) => (
                <option key={v} value={v} className="bg-slate-900">
                  {v}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* 內容區 */}
        <div className="grid min-h-0 grid-cols-1 gap-6 lg:grid-cols-4 xl:gap-8">
          {/* 左側監控矩陣 */}
          <div className={`${glassCard} flex min-h-0 flex-col p-6 lg:col-span-3`}>
            <div className="mb-6 flex shrink-0 items-center justify-between">
              <h2 className="flex items-center gap-4 text-2xl font-black text-white">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-400/20 text-emerald-400">
                  <Video className="h-6 w-6" />
                </div>
                即時監控矩陣
              </h2>

              <div className="rounded-lg bg-emerald-400 px-4 py-2 text-xs font-black text-emerald-950 shadow-lg shadow-emerald-400/20">
                LIVE: {cameras.length} UNITS
              </div>
            </div>

            <div className="custom-scrollbar min-h-0 flex-1 overflow-y-auto pr-2">
              <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
                {cameras.map((camera) => (
                  <div
                    key={camera.id}
                    className={`${glassInner} group relative overflow-hidden p-4 transition-all duration-300 hover:scale-[1.02] hover:bg-white/20`}
                  >
                    <div className="relative mb-3 aspect-video overflow-hidden rounded-xl bg-slate-900 shadow-inner">
                      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
                      <div className="flex h-full items-center justify-center">
                        <Play className="h-8 w-8 text-white/20 transition-all group-hover:scale-110 group-hover:text-white/60" />
                      </div>
                    </div>

                    <div
                      className={`absolute right-6 top-6 flex h-10 w-10 items-center justify-center rounded-full text-[10px] font-black text-white shadow-xl ${riskColors[camera.risk]}`}
                    >
                      {camera.risk}
                    </div>

                    <div className="text-sm font-bold text-white">{camera.name}</div>
                    <div className="text-[10px] text-white/40">{riskLabels[camera.risk]}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* 右側統計與告警 */}
          <div className="flex min-h-0 flex-col gap-6 lg:gap-8">
            <div className={`${glassCard} p-6`}>
              <h3 className="mb-6 text-lg font-black text-white/80">數據概況</h3>

              <div className="space-y-3">
                {[
                  {
                    label: 'L3 事件',
                    val: stats.l3Events,
                    color: 'border-red-500/30 bg-red-500/10 text-red-400',
                  },
                  {
                    label: 'L4 緊急',
                    val: stats.l4Events,
                    color: 'border-fuchsia-500/30 bg-fuchsia-500/10 text-fuchsia-400',
                  },
                  {
                    label: '處理率',
                    val: `${stats.handledRate}%`,
                    color: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400',
                  },
                ].map((s, i) => (
                  <div
                    key={i}
                    className={`flex items-center justify-between rounded-xl border p-4 ${s.color}`}
                  >
                    <span className="text-xs font-bold opacity-70">{s.label}</span>
                    <span className="text-2xl font-black">{s.val}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className={`${glassCard} flex min-h-0 flex-1 flex-col p-6`}>
              <h3 className="mb-6 flex items-center gap-2 text-lg font-black text-white/80">
                <Bell className="h-5 w-5 animate-pulse text-red-500" />
                即時告警
              </h3>

              <div className="custom-scrollbar min-h-0 flex-1 space-y-3 overflow-y-auto pr-2">
                {alerts.length === 0 ? (
                  <div className="rounded-xl border border-white/10 bg-white/5 p-4 text-sm text-white/45">
                    目前尚無即時告警
                  </div>
                ) : (
                  alerts.map((alert) => (
                    <div
                      key={alert.id}
                      className="rounded-xl border border-white/5 bg-white/5 p-4 transition-all hover:bg-white/10"
                    >
                      <div className="mb-2 flex items-center justify-between">
                        <span
                          className={`rounded px-2 py-0.5 text-[10px] font-black text-white ${riskColors[alert.level]}`}
                        >
                          {alert.level}
                        </span>

                        <X
                          className="cursor-pointer text-white/20 hover:text-white"
                          size={14}
                          onClick={() => clearAlert(alert.id)}
                        />
                      </div>

                      <div className="text-sm font-bold text-white">{alert.camera}</div>
                      <div className="text-[10px] text-white/40">
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

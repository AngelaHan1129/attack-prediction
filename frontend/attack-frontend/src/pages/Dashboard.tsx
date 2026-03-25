import React, { useState, useEffect, useRef } from 'react'
import { Shield, Video, Clock, Bell, Play, X } from 'lucide-react'
import bgPoster from '../assets/work-space.svg'
import bgWebm from '../assets/login-bg.webm'

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
  'relative rounded-[22px] border border-white/35 bg-white/12 backdrop-blur-2xl backdrop-saturate-150 backdrop-brightness-110 shadow-[0_20px_60px_rgba(0,0,0,0.10),inset_0_1px_0_rgba(255,255,255,0.55),inset_0_-16px_28px_rgba(255,255,255,0.08)] ring-1 ring-white/20'

const glassInner =
  'rounded-[24px] border border-white/25 bg-white/18 shadow-[inset_0_1px_0_rgba(255,255,255,0.45),0_10px_30px_rgba(0,0,0,0.06)]'

const Dashboard: React.FC = () => {
  const [currentVenue] = useState<string>(venues[0])
  const [cameras] = useState<Camera[]>(() =>
    Array.from({ length: 12 }, (_, i) => ({
      id: `cam-${i + 1}`,
      name: `鏡頭 ${i + 1}`,
      risk: (['L0', 'L1', 'L0', 'L2', 'L0', 'L3', 'L1', 'L0', 'L4', 'L0', 'L2', 'L0'] as RiskLevel[])[i],
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
        time: now.toLocaleTimeString('zh-TW'),
        description: '偵測異常行為',
      }

      setAlerts((prev) => [newAlert, ...prev.slice(0, 9)])

      if (audioRef.current) {
        audioRef.current.play().catch(console.error)
      }
    }, 30000)

    return () => clearInterval(interval)
  }, [])

  const clearAlert = (id: string): void => {
    setAlerts((prev) => prev.filter((a) => a.id !== id))
  }

  const handleVenueChange = (venue: string): void => {
    console.log('切換場域:', venue)
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#eef0ee] p-6 text-black">
      <video
        className="absolute inset-0 z-0 h-full w-full object-cover"
        autoPlay
        loop
        muted
        playsInline
        preload="auto"
        poster={bgPoster}
      >
        <source src={bgWebm} type="video/webm" />
        您的瀏覽器不支援影片播放
      </video>

      <div className="pointer-events-none absolute inset-0 z-[1] bg-[linear-gradient(135deg,rgba(255,255,255,0.30)_0%,rgba(255,255,255,0.08)_40%,rgba(255,255,255,0.02)_100%)]" />

      <div className="relative z-10">
        <div className={`${glassCard} mb-6 px-6 py-5`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex h-14 w-14 items-center justify-center rounded-xl border border-white/30 bg-white/25 shadow-[0_8px_24px_rgba(0,0,0,0.08)]">
                <Clock className="h-7 w-7 text-black/70" />
              </div>

              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.35em] text-black/40">
                  Surveillance Security Platform
                </p>
                <p className="text-2xl font-black tracking-wide text-black">
                  {currentTime.toLocaleString('zh-TW')}
                </p>
              </div>

              <div
                className={`rounded-full px-4 py-2 text-sm font-bold shadow-[0_8px_20px_rgba(0,0,0,0.12)] ${
                  systemStatus === '正常' ? 'bg-[rgb(0,255,0)] text-black' : 'bg-red-500 text-white'
                }`}
              >
                {systemStatus}
              </div>
            </div>

            <select
              value={currentVenue}
              onChange={(e) => handleVenueChange(e.target.value)}
              className={`${glassInner} px-5 py-3 text-sm font-semibold text-black shadow-[inset_0_1px_0_rgba(255,255,255,0.45)] focus:outline-none focus:ring-2 focus:ring-emerald-400/40`}
            >
              {venues.map((v) => (
                <option key={v} value={v}>
                  {v}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid h-[calc(100vh-160px)] grid-cols-1 gap-6 lg:grid-cols-4 xl:gap-8">
          <div className={`${glassCard} relative z-10 p-6 lg:col-span-3 xl:p-8`}>
            <div className="mb-8 flex items-center justify-between">
              <h2 className="flex items-center gap-3 text-2xl font-black text-black xl:text-3xl">
                <div className="flex h-14 w-14 items-center justify-center rounded-xl border border-white/30 bg-white/25 shadow-[0_10px_28px_rgba(0,0,0,0.08)]">
                  <Video className="h-7 w-7" />
                </div>
                即時監視畫面
              </h2>

              <div className="rounded-full bg-[rgb(0,255,0)] px-6 py-3 text-sm font-bold text-black shadow-[0_12px_28px_rgba(0,255,0,0.24)]">
                {cameras.length} 路連線中
              </div>
            </div>

            <div className="grid h-[calc(100%-80px)] grid-cols-2 gap-4 xl:grid-cols-4">
              {cameras.map((camera) => (
                <div
                  key={camera.id}
                  className={`${glassInner} group relative overflow-hidden p-4 transition-all duration-300 hover:-translate-y-2 hover:shadow-[0_20px_40px_rgba(0,0,0,0.12)] xl:p-5`}
                >
                  <div className="relative mb-3 h-32 overflow-hidden rounded-[20px] bg-gradient-to-br from-slate-800 via-slate-900 to-black shadow-[inset_0_2px_8px_rgba(0,0,0,0.4)] xl:h-36">
                    <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_15%,rgba(255,255,255,0.25)_0%,transparent_50%)]" />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent/50" />
                    <div className="flex h-full items-center justify-center">
                      <Play className="h-10 w-10 text-white/60 transition-all duration-300 group-hover:scale-110 group-hover:text-white xl:h-12 xl:w-12" />
                    </div>
                  </div>

                  <div
                    className={`absolute right-4 top-4 flex h-12 w-12 items-center justify-center rounded-full text-xs font-black text-white shadow-[0_8px_20px_rgba(0,0,0,0.20)] ${riskColors[camera.risk]}`}
                  >
                    {camera.risk}
                  </div>

                  <div className="px-1">
                    <div className="truncate text-base font-bold text-black">{camera.name}</div>
                    <div className="text-sm text-black/55">{riskLabels[camera.risk]}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-6 lg:space-y-8">
            <div className={`${glassCard} p-6 xl:p-8`}>
              <h3 className="mb-6 flex items-center gap-3 text-xl font-black text-black xl:text-2xl">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-white/30 bg-white/25 shadow-[0_8px_24px_rgba(0,0,0,0.08)]">
                  <Shield className="h-6 w-6" />
                </div>
                今日統計
              </h3>

              <div className="space-y-4">
                <div className="flex items-center justify-between rounded-[22px] border border-red-200/60 bg-red-400/15 px-6 py-5">
                  <span className="font-semibold text-black/70">L3事件</span>
                  <span className="text-3xl font-black text-black xl:text-4xl">{stats.l3Events}</span>
                </div>

                <div className="flex items-center justify-between rounded-[22px] border border-fuchsia-200/60 bg-fuchsia-400/15 px-6 py-5">
                  <span className="font-semibold text-black/70">L4事件</span>
                  <span className="text-3xl font-black text-black xl:text-4xl">{stats.l4Events}</span>
                </div>

                <div className="flex items-center justify-between rounded-[22px] border border-emerald-200/70 bg-emerald-400/20 px-6 py-5">
                  <span className="font-semibold text-black/70">處理率</span>
                  <span className="text-3xl font-black text-black xl:text-4xl">{stats.handledRate}%</span>
                </div>
              </div>
            </div>

            <div className={`${glassCard} flex h-[calc(50vh-3rem)] flex-col p-6 xl:p-8`}>
              <h3 className="mb-6 flex items-center gap-3 text-xl font-black text-black xl:text-2xl">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-white/30 bg-white/25 shadow-[0_8px_24px_rgba(0,0,0,0.08)]">
                  <Bell className="h-6 w-6 animate-pulse" />
                </div>
                即時告警
              </h3>

              <div className="flex-1 space-y-3 overflow-y-auto pr-2">
                {alerts.map((alert) => (
                  <div
                    key={alert.id}
                    className={`${glassInner} group p-4 transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_16px_36px_rgba(0,0,0,0.12)] xl:p-5`}
                  >
                    <div className="mb-3 flex items-start justify-between">
                      <span
                        className={`rounded-full px-3 py-1.5 text-xs font-black text-white shadow-[0_4px_12px_rgba(0,0,0,0.15)] ${riskColors[alert.level]}`}
                      >
                        {alert.level}
                      </span>

                      <button
                        onClick={() => clearAlert(alert.id)}
                        className="text-black/35 opacity-0 transition-all group-hover:opacity-100 hover:text-black/60"
                        title="清除告警"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>

                    <div className="mb-1 font-bold text-black">{alert.camera}</div>
                    <div className="mb-1 text-sm text-black/60">{alert.description}</div>
                    <div className="text-xs text-black/40">{alert.time}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      <audio
        ref={audioRef}
        src="data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAo"
        preload="auto"
      />
    </div>
  )
}

export default Dashboard

import React, { useEffect, useRef, useState } from 'react'
import { Video, Clock, Bell, X, Menu } from 'lucide-react'
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
  'relative rounded-[16px] 2xl:rounded-[18px] border border-white/20 bg-black/20 backdrop-blur-2xl backdrop-saturate-140 backdrop-brightness-110 shadow-lg ring-1 ring-white/10'

const controlButton =
  'rounded-lg px-2 py-1.5 md:px-3 md:py-2 text-[10px] md:text-xs font-bold transition disabled:cursor-not-allowed disabled:opacity-50 whitespace-nowrap'

const Dashboard: React.FC = () => {
  const [currentVenue, setCurrentVenue] = useState<string>(venues[0])
  const [viewMode, setViewMode] = useState<ViewMode>('twelve')
  const [isMonitoring, setIsMonitoring] = useState<boolean>(false)
  const [selectedCamera, setSelectedCamera] = useState<string>('0')

  const [cameras] = useState<Camera[]>(() =>
    Array.from({ length: 12 }, (_, i) => ({
      id: `cam-${i + 1}`,
      name: `鏡頭 ${i + 1}`,
      risk: (['L0', 'L1', 'L0', 'L2', 'L0', 'L3', 'L1', 'L0', 'L4', 'L0', 'L2', 'L0'] as RiskLevel[])[i],
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
      if (audioRef.current) audioRef.current.play().catch(() => {})
    }, 30000)
    return () => clearInterval(interval)
  }, [isMonitoring])

  const clearAlert = (id: string) => setAlerts((prev) => prev.filter((a) => a.id !== id))
  
  const modeButton = (active: boolean) =>
    `${controlButton} ${
      active ? 'bg-emerald-400 text-emerald-950' : 'bg-white/10 text-white hover:bg-white/20'
    }`

  return (
    <div className="relative z-10 flex flex-col h-full gap-3 p-3 md:p-4 lg:p-5 pb-32 lg:pb-5">
      {/* Background Layers */}
      <div className="fixed inset-0 z-0">
        <img src={workspaceOverlay} alt="" className="absolute inset-0 h-full w-full object-cover opacity-50" />
        <img src={dashboardBg} alt="" className="absolute inset-0 h-full w-full object-cover object-center opacity-80" />
      </div>

      <div className="relative z-10 flex flex-col h-full gap-3 p-3 md:p-4 lg:p-5">
        
        {/* Header / Top Bar */}
        <header className={`${glassCard} p-3 md:px-4 md:py-3`}>
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-white/20 bg-white/10 shadow-xl backdrop-blur-md">
                <Clock className="h-5 w-5 text-emerald-400" />
              </div>
              <div className="min-w-0">
                <p className="text-[10px] font-bold uppercase tracking-widest text-white/40">Surveillance Platform</p>
                <p className="truncate text-sm md:text-lg font-black tabular-nums">
                  {currentTime.toLocaleString('zh-TW', { hour12: false })}
                </p>
              </div>
              <div className={`ml-2 rounded-full px-3 py-1 text-[10px] font-black ${
                systemStatus === '正常' ? 'bg-emerald-400 text-emerald-950' : 'bg-red-500 text-white'
              }`}>
                系統{systemStatus}
              </div>
            </div>

            {/* Controls */}
            <div className="flex flex-wrap items-center gap-2">
              <select
                value={currentVenue}
                onChange={(e) => setCurrentVenue(e.target.value)}
                className="rounded-lg border border-white/10 bg-slate-900/50 px-2 py-1.5 text-xs font-bold outline-none focus:ring-2 focus:ring-emerald-400/50"
              >
                {venues.map((v) => <option key={v} value={v}>{v}</option>)}
              </select>

              <div className="flex gap-1 bg-white/5 p-1 rounded-xl">
                <button onClick={() => setViewMode('single')} className={modeButton(viewMode === 'single')}>1</button>
                <button onClick={() => setViewMode('dual')} className={modeButton(viewMode === 'dual')}>2</button>
                <button onClick={() => setViewMode('twelve')} className={modeButton(viewMode === 'twelve')}>12</button>
              </div>

              <div className="flex gap-2 ml-auto md:ml-0">
                <button
                  onClick={() => setIsMonitoring(true)}
                  disabled={isMonitoring}
                  className={`${controlButton} bg-lime-400 text-black hover:bg-lime-300 disabled:bg-gray-600`}
                >
                  開始
                </button>
                <button
                  onClick={() => setIsMonitoring(false)}
                  disabled={!isMonitoring}
                  className={`${controlButton} bg-red-500 text-white hover:bg-red-400 disabled:bg-gray-600`}
                >
                  停止
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="grid flex-1 min-h-0 grid-cols-1 gap-4 lg:grid-cols-4 xl:grid-cols-5">
          
          {/* Left: Video View (Takes more space) */}
          <section className={`${glassCard} flex flex-col p-3 md:p-4 lg:col-span-3 xl:col-span-4 min-h-[500px] lg:min-h-0`}>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="flex items-center gap-2 text-sm md:text-lg font-black">
                <Video className="h-5 w-5 text-emerald-400" />
                {viewMode === 'single' ? '單鏡頭' : viewMode === 'dual' ? '雙鏡頭' : '多鏡頭'} 
                <span className="hidden md:inline">監控介面</span>
              </h2>
              <div className="animate-pulse rounded-lg bg-emerald-400 px-2 py-1 text-[10px] font-black text-emerald-950">
                {isMonitoring ? 'LIVE' : 'IDLE'}
              </div>
            </div>

            <div className="custom-scrollbar flex-1 overflow-y-auto rounded-lg bg-black/40">
              {viewMode === 'single' && <YoloViewer isMonitoring={isMonitoring} source={selectedCamera} />}
              {viewMode === 'dual' && <DualCameraViewer isMonitoring={isMonitoring} source0="0" source1="1" />}
              {viewMode === 'twelve' && <MultiCameraViewer isMonitoring={isMonitoring} sources={twelveSources} />}
            </div>
          </section>

          {/* Right: Sidebar (Stats & Alerts) */}
          <aside className="flex flex-col gap-4 lg:col-span-1 min-w-0">
            
            {/* Stats Card */}
            <div className={`${glassCard} p-4`}>
              <h3 className="mb-3 text-xs font-black text-white/60">數據概況</h3>
              <div className="grid grid-cols-2 gap-2 lg:grid-cols-1">
                {[
                  { label: 'L3 事件', val: stats.l3Events, color: 'bg-red-500/20 text-red-400 border-red-500/30' },
                  { label: 'L4 緊急', val: stats.l4Events, color: 'bg-fuchsia-500/20 text-fuchsia-400 border-fuchsia-500/30' },
                  { label: '處理率', val: `${stats.handledRate}%`, color: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' },
                ].map((s, i) => (
                  <div key={i} className={`flex items-center justify-between rounded-xl border p-2.5 ${s.color}`}>
                    <span className="text-[10px] font-bold opacity-80">{s.label}</span>
                    <span className="text-base font-black tabular-nums">{s.val}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Alerts Card */}
            <div className={`${glassCard} flex flex-1 flex-col p-4 min-h-[300px] lg:min-h-0`}>
              <h3 className="mb-3 flex items-center gap-2 text-xs font-black text-white/60">
                <Bell className="h-4 w-4 animate-bounce text-red-500" />
                即時告警
              </h3>
              <div className="custom-scrollbar flex-1 space-y-2 overflow-y-auto pr-1">
                {alerts.length === 0 ? (
                  <div className="py-10 text-center text-xs text-white/30 italic">目前無異常</div>
                ) : (
                  alerts.map((alert) => (
                    <div key={alert.id} className="group relative rounded-xl border border-white/5 bg-white/5 p-3 transition-all hover:bg-white/10">
                      <div className="flex items-center justify-between mb-1">
                        <span className={`rounded px-1.5 py-0.5 text-[9px] font-black ${riskColors[alert.level]}`}>
                          {alert.level}
                        </span>
                        <button onClick={() => clearAlert(alert.id)} className="opacity-0 group-hover:opacity-100 transition-opacity">
                          <X size={14} className="text-white/40 hover:text-white" />
                        </button>
                      </div>
                      <div className="text-xs font-bold">{alert.camera}</div>
                      <div className="text-[10px] text-white/40">{alert.time} - {alert.description}</div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </aside>
        </main>

        <audio ref={audioRef} src="..." preload="auto" />
      </div>

      <style>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.2); }
      `}</style>
    </div>
  )
}

export default Dashboard
import React, { useState, useEffect, useRef } from 'react';
import { Shield, Video, Clock, Bell, Play, X } from 'lucide-react';

type RiskLevel = 'L0' | 'L1' | 'L2' | 'L3' | 'L4';

const riskColors: Record<RiskLevel, string> = {
  L0: 'bg-green-500',
  L1: 'bg-yellow-500',
  L2: 'bg-orange-500',
  L3: 'bg-red-500',
  L4: 'bg-purple-600'
};

const riskLabels: Record<RiskLevel, string> = {
  L0: '正常',
  L1: '低風險',
  L2: '中風險',
  L3: '高風險',
  L4: '緊急'
};

type Camera = {
  id: string;
  name: string;
  risk: RiskLevel;
  streamUrl: string;
};

type Alert = {
  id: string;
  camera: string;
  level: RiskLevel;
  time: string;
  description: string;
};

const venues = ['車站A', '車站B', '車站C', '商圈'];

const Dashboard: React.FC = () => {
  const [currentVenue] = useState(venues[0]);
  const [cameras] = useState<Camera[]>(() => 
    Array.from({ length: 12 }, (_, i) => ({
      id: `cam-${i + 1}`,
      name: `鏡頭 ${i + 1}`,
      risk: (['L0', 'L1', 'L0', 'L2', 'L0', 'L3', 'L1', 'L0', 'L4', 'L0', 'L2', 'L0'] as RiskLevel[])[i],
      streamUrl: `https://example.com/stream/cam-${i + 1}.m3u8`
    }))
  );
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [stats] = useState({
    l3Events: 5,
    l4Events: 2,
    handledRate: 85
  });
  const [currentTime, setCurrentTime] = useState(new Date());
  const [systemStatus] = useState<'正常' | '警告' | '故障'>('正常');
  const audioRef = useRef<HTMLAudioElement>(null);

  // 即時時間 (移到useEffect外避免依賴)
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // 模擬告警 (移除currentTime依賴，用獨立計時器)
  useEffect(() => {
    const interval = setInterval(() => {
      const now = new Date();
      const newAlert: Alert = {
        id: `alert-${Date.now()}`,
        camera: `鏡頭 ${Math.floor(Math.random() * 12) + 1}`,
        level: (['L3', 'L4'] as RiskLevel[])[Math.floor(Math.random() * 2)],
        time: now.toLocaleTimeString('zh-TW'),
        description: '偵測異常行為'
      };
      setAlerts(prev => [newAlert, ...prev.slice(0, 9)]);

      if (audioRef.current) {
        audioRef.current.play().catch(console.error);
      }
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const clearAlert = (id: string) => {
    setAlerts(prev => prev.filter(a => a.id !== id));
  };

  const handleVenueChange = (venue: string) => {
    // TODO: API切換場域
    console.log('切換場域:', venue);
  };

  return (
    <div className="h-screen bg-gradient-to-br from-gray-900 to-gray-800 text-white p-6 overflow-hidden">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center space-x-4">
          <Clock className="w-6 h-6" />
          <span className="text-2xl font-bold">{currentTime.toLocaleString('zh-TW')}</span>
          <div className={`px-3 py-1 rounded-full text-sm font-medium ${systemStatus === '正常' ? 'bg-green-500' : 'bg-red-500'}`}>
            {systemStatus}
          </div>
        </div>
        <select
          value={currentVenue}
          onChange={(e) => handleVenueChange(e.target.value)}
          className="bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {venues.map(v => (
            <option key={v} value={v}>{v}</option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[calc(100vh-120px)]">
        {/* 12路監視畫面 */}
        <div className="lg:col-span-3 bg-gray-800/50 backdrop-blur-xl rounded-2xl p-6 shadow-2xl border border-gray-700/50">
          <h2 className="text-2xl font-bold mb-6 flex items-center">
            <Video className="w-8 h-8 mr-3" />即時監視畫面
          </h2>
          <div className="grid grid-cols-4 grid-rows-3 gap-4 h-[calc(100%-60px)]">
            {cameras.map((camera) => (
              <div key={camera.id} className="group relative bg-black/70 rounded-xl overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-300 border-4 border-transparent hover:border-blue-500">
                <div className="w-full h-48 bg-gradient-to-r from-gray-700 to-gray-600 flex items-center justify-center relative">
                  <Play className="w-12 h-12 text-gray-400 group-hover:text-white transition-colors" />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/50" />
                </div>
                <div className={`absolute top-3 right-3 w-12 h-12 rounded-full flex items-center justify-center text-white font-bold text-sm shadow-lg ${riskColors[camera.risk]} ring-4 ring-black/50`}>
                  {camera.risk}
                </div>
                <div className="absolute bottom-3 left-3 text-sm">
                  <div className="font-bold">{camera.name}</div>
                  <div className="text-xs opacity-75">{riskLabels[camera.risk]}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 右側面板 */}
        <div className="space-y-6">
          {/* 統計卡片 */}
          <div className="bg-gray-800/70 backdrop-blur-xl rounded-2xl p-6 shadow-2xl border border-gray-700/50">
            <h3 className="text-xl font-bold mb-4 flex items-center">
              <Shield className="w-6 h-6 mr-2" />今日統計
            </h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center p-4 bg-red-500/20 rounded-xl">
                <span>L3事件</span><span className="text-2xl font-bold">{stats.l3Events}</span>
              </div>
              <div className="flex justify-between items-center p-4 bg-purple-500/20 rounded-xl">
                <span>L4事件</span><span className="text-2xl font-bold">{stats.l4Events}</span>
              </div>
              <div className="flex justify-between items-center p-4 bg-green-500/20 rounded-xl">
                <span>處理率</span><span className="text-2xl font-bold">{stats.handledRate}%</span>
              </div>
            </div>
          </div>

          {/* 告警列表 */}
          <div className="bg-gray-800/70 backdrop-blur-xl rounded-2xl p-6 shadow-2xl border border-gray-700/50 flex-1 flex flex-col h-[calc(50vh-3rem)]">
            <h3 className="text-xl font-bold mb-4 flex items-center">
              <Bell className="w-6 h-6 mr-2 animate-pulse" />即時告警
            </h3>
            <div className="flex-1 overflow-y-auto space-y-3 pr-2">
              {alerts.map((alert) => (
                <div key={alert.id} className={`p-4 rounded-xl shadow-lg border-l-4 ${riskColors[alert.level]} border-l-white/20 bg-gradient-to-r from-white/10 to-transparent hover:scale-[1.02] transition-all group`}>
                  <div className="flex justify-between items-start mb-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-bold ${riskColors[alert.level]}`}>
                      {alert.level}
                    </span>
                    <button
                      onClick={() => clearAlert(alert.id)}
                      className="text-gray-400 hover:text-white transition-colors opacity-0 group-hover:opacity-100"
                      title="清除告警"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  <div className="font-bold">{alert.camera}</div>
                  <div className="text-sm opacity-75">{alert.description}</div>
                  <div className="text-xs text-gray-400 mt-1">{alert.time}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 內嵌音效 */}
      <audio ref={audioRef} src="data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAo" preload="auto" />
    </div>
  );
};

export default Dashboard;

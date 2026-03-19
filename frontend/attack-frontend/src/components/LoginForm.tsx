import React, { useState } from 'react';
import type { MouseEvent } from 'react';

const LoginForm: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [mouseX, setMouseX] = useState(0);
  const [mouseY, setMouseY] = useState(0);

  const handleMouseMove = (e: MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setMouseX((e.clientX - rect.left) / rect.width - 0.5);
    setMouseY((e.clientY - rect.top) / rect.height - 0.5);
  };

  const handleMouseLeave = () => {
    setMouseX(0);
    setMouseY(0);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900/50 to-emerald-900 flex items-center justify-center p-8 overflow-hidden relative">
      {/* 裝飾背景 */}
      <div className="absolute inset-0">
        <div className="absolute top-1/4 left-1/4 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-emerald-400/10 rounded-full blur-3xl animate-pulse" style={{animationDelay: '2s'}}></div>
      </div>

      {/* 3D 毛玻璃卡片 */}
      <div
        className="relative w-full max-w-md backdrop-blur-xl bg-white/5 border border-white/20 rounded-3xl p-10 shadow-2xl max-shadow-xl cursor-pointer select-none"
        style={{
          transform: `perspective(1000px) rotateX(${mouseY * 8}deg) rotateY(${mouseX * -8}deg) translateZ(0)`,
          transformOrigin: 'center center',
          transition: 'transform 0.1s ease-out'
        }}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
      >
        <div className="text-center mb-10">
          <h1 className="text-5xl font-black bg-gradient-to-r from-blue-400 via-purple-400 to-emerald-400 bg-clip-text text-transparent mb-4 tracking-tight">
            {isLogin ? 'Welcome Back' : 'Join Us'}
          </h1>
          <p className="text-gray-400 text-lg font-light">安全登入你的監控系統</p>
        </div>

        <form className="space-y-6">
          {!isLogin && (
            <div>
              <label className="block text-sm font-semibold text-gray-300 mb-3">顯示名稱</label>
              <input 
                type="text" 
                className="w-full px-5 py-4 bg-white/5 border border-white/20 rounded-2xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/20 transition-all duration-300 text-lg" 
                placeholder="你的名字" 
              />
            </div>
          )}
          <div>
            <label className="block text-sm font-semibold text-gray-300 mb-3">電子郵件</label>
            <input 
              type="email" 
              className="w-full px-5 py-4 bg-white/5 border border-white/20 rounded-2xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/20 transition-all duration-300 text-lg" 
              placeholder="user@example.com" 
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-gray-300 mb-3">密碼</label>
            <input 
              type="password" 
              className="w-full px-5 py-4 bg-white/5 border border-white/20 rounded-2xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/20 transition-all duration-300 text-lg" 
              placeholder="至少 8 個字元" 
            />
          </div>

          <button
            type="submit"
            className="w-full bg-gradient-to-r from-blue-600 via-purple-600 to-emerald-600 hover:from-blue-700 hover:via-purple-700 hover:to-emerald-700 text-white font-black py-5 px-8 rounded-2xl shadow-2xl hover:shadow-3xl transform hover:scale-[1.02] active:scale-[0.98] transition-all duration-300 text-xl tracking-wide"
          >
            {isLogin ? '進入系統' : '建立帳號'}
          </button>
        </form>

        <div className="mt-10 pt-8 border-t border-white/10 text-center">
          <button
            type="button"
            onClick={() => setIsLogin(!isLogin)}
            className="text-blue-400 hover:text-blue-300 font-semibold transition-all duration-300 text-lg hover:underline flex items-center justify-center gap-2 mx-auto"
          >
            {isLogin ? '👤 註冊新帳號' : '🔑 已擁有帳號？登入'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default LoginForm;

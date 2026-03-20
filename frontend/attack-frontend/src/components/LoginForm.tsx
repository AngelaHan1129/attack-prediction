import React, { useState } from 'react';
import type { MouseEvent } from 'react';
import bgImage from '../assets/login-bg.jpg';

const LoginForm: React.FC = () => {
  const [isLogin, setIsLogin] = useState<boolean>(true);
  const [mouseX, setMouseX] = useState<number>(0);
  const [mouseY, setMouseY] = useState<number>(0);

  const handleMouseMove = (e: MouseEvent<HTMLDivElement>): void => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;

    setMouseX(x);
    setMouseY(y);
  };

  const handleMouseLeave = (): void => {
    setMouseX(0);
    setMouseY(0);
  };

  return (
    <div
      className="relative min-h-screen overflow-hidden flex items-center justify-center p-8 bg-cover bg-center bg-no-repeat"
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{
        backgroundImage: `url(${bgImage})`,
        perspectiveOrigin: 'center center',
      }}
    >
      {/* 背景遮罩 */}
      <div className="absolute inset-0 bg-slate-680/55" />

      {/* 科技感疊色 */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.14),transparent_30%),radial-gradient(circle_at_bottom_right,rgba(168,85,247,0.14),transparent_35%),linear-gradient(135deg,rgba(8,18,31,0.72)_0%,rgba(11,23,48,0.58)_45%,rgba(7,17,27,0.78)_100%)]" />

      {/* 遠景光球 */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          transform: `translate3d(${mouseX * 20}px, ${mouseY * 20}px, -80px)`,
          transformStyle: 'preserve-3d',
          transition: 'transform 120ms ease-out',
        }}
      >
        <div className="absolute -top-16 left-[-4rem] h-80 w-80 rounded-full bg-cyan-400/20 blur-3xl" />
        <div className="absolute bottom-[-5rem] right-[-2rem] h-96 w-96 rounded-full bg-fuchsia-500/20 blur-3xl" />
        <div className="absolute top-[30%] left-[45%] h-72 w-72 rounded-full bg-emerald-400/10 blur-3xl" />
      </div>

      {/* 中景透視格線 */}
      <div
        className="absolute inset-0 pointer-events-none opacity-35"
        style={{
          transform: `rotateX(72deg) translate3d(${mouseX * 12}px, ${120 + mouseY * 12}px, 0px) scale(1.25)`,
          transformStyle: 'preserve-3d',
          transition: 'transform 120ms ease-out',
        }}
      >
        <div
          className="absolute inset-0"
          style={{
            backgroundImage: `
              linear-gradient(rgba(255,255,255,0.14) 1px, transparent 1px),
              linear-gradient(90deg, rgba(255,255,255,0.14) 1px, transparent 1px)
            `,
            backgroundSize: '56px 56px',
            maskImage: 'linear-gradient(to top, black 45%, transparent 100%)',
            WebkitMaskImage: 'linear-gradient(to top, black 45%, transparent 100%)',
          }}
        />
      </div>

      {/* 前景漂浮物件 */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          transformStyle: 'preserve-3d',
          transition: 'transform 100ms ease-out',
        }}
      >
        <div
          className="absolute top-[16%] left-[10%] h-24 w-24 rounded-full border border-white/10 shadow-2xl"
          style={{
            background:
              'radial-gradient(circle at 30% 30%, rgba(255,255,255,0.35), rgba(34,211,238,0.18) 40%, rgba(59,130,246,0.08) 70%, transparent 100%)',
            backdropFilter: 'blur(10px)',
          }}
        />

        <div
          className="absolute top-[24%] right-[15%] h-16 w-16 rounded-2xl border border-cyan-300/20 bg-cyan-300/10"
          style={{
            transform: `translate3d(${mouseX * -28}px, ${mouseY * -28}px, 60px) rotate(35deg)`,
          }}
        />

        <div
          className="absolute bottom-[18%] right-[12%] h-32 w-32 rounded-full border border-purple-300/20 bg-purple-300/10 blur-sm"
          style={{
            transform: `translate3d(${mouseX * 40}px, ${mouseY * 40}px, 100px)`,
          }}
        />
      </div>

      {/* 毛玻璃卡片 */}
      <div
        className="relative z-10 w-[640px] h-[640px] overflow-hidden rounded-full border border-white/20 bg-white/10 px-14 py-12 shadow-[0_8px_40px_rgba(15,23,42,0.45)] backdrop-blur-2xl flex flex-col justify-center"
        style={{
          transform: `rotateX(${mouseY * 8}deg) rotateY(${mouseX * -8}deg) translate3d(0,0,120px)`,
          transformStyle: 'preserve-3d',
          transition: 'transform 100ms ease-out',
        }}
      >
        <div className="pointer-events-none absolute inset-0 rounded-full bg-gradient-to-br from-white/20 via-white/10 to-transparent" />

        <div className="relative z-10 text-center mb-8">
          <h1 className="mb-3 bg-gradient-to-r from-cyan-300 via-green-400 to-emerald-300 bg-clip-text text-4xl font-black tracking-tight text-transparent">
            {isLogin ? 'Welcome Back' : 'Join Us'}
          </h1>
          <p className="text-base font-light text-white/90">安全登入你的監控系統</p>
        </div>

        <form className="relative z-10 space-y-4">
          {!isLogin && (
            <div>
              <label className="mb-2 block text-sm font-semibold text-white/80">顯示名稱</label>
              <input
                type="text"
                className="w-full rounded-full border border-white/20 bg-white/10 px-5 py-3 text-base text-white placeholder-white/40 transition-all duration-300 focus:border-cyan-400 focus:outline-none focus:ring-4 focus:ring-cyan-400/20"
                placeholder="你的名字"
              />
            </div>
          )}

          <div>
            <label className="mb-2 block text-sm font-semibold text-white/80">電子郵件</label>
            <input
              type="email"
              className="w-full rounded-full border border-white/20 bg-white/10 px-5 py-3 text-base text-white placeholder-white/40 transition-all duration-300 focus:border-cyan-400 focus:outline-none focus:ring-4 focus:ring-cyan-400/20"
              placeholder="user@example.com"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-semibold text-white/80">密碼</label>
            <input
              type="password"
              className="w-full rounded-full border border-white/20 bg-white/10 px-5 py-3 text-base text-white placeholder-white/40 transition-all duration-300 focus:border-cyan-400 focus:outline-none focus:ring-4 focus:ring-cyan-400/20"
              placeholder="至少 8 個字元"
            />
          </div>

          <button
            type="submit"
            className="w-full rounded-full bg-gradient-to-r from-lime-500 via-green-600 to-emerald-500 px-8 py-4 text-lg font-black tracking-wide text-white shadow-2xl transition-all duration-300 hover:scale-[1.02] hover:brightness-110 active:scale-[0.98]"
          >
            {isLogin ? '進入系統' : '建立帳號'}
          </button>
        </form>

        <div className="relative z-10 mt-6 border-t border-white/50 pt-5 text-center">
          <button
            type="button"
            onClick={() => setIsLogin((prev) => !prev)}
            className="text-base font-semibold text-teal-300 transition-all duration-300 hover:text-cyan-200"
          >
            {isLogin ? '👤 註冊新帳號' : '🔑 已擁有帳號？登入'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default LoginForm;

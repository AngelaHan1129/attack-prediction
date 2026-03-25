import React, { useState } from 'react';
import type { MouseEvent } from 'react';
import bgWebm from '../assets/login-bg.webm';
import bgPoster from '../assets/work-space.svg';

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
    <div
      className="relative min-h-screen overflow-hidden flex flex-col lg:flex-row items-center justify-between px-6 lg:px-12 xl:px-20 py-10"
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
     <video
  className="absolute inset-0 w-full h-full object-cover object-right z-0"
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

      <div className="pointer-events-none absolute inset-0 z-[1] bg-black/20" />

      {/* 毛玻璃卡片 */}
      <div
        className="
    relative h-[640px] w-[640px] overflow-hidden rounded-full
    border border-white/35
    bg-white/10
    px-16 py-14
    backdrop-blur-2xl backdrop-saturate-150 backdrop-brightness-110
    shadow-[0_20px_60px_rgba(0,0,0,0.12),inset_0_1px_0_rgba(255,255,255,0.65),inset_0_-16px_28px_rgba(255,255,255,0.08)]
    ring-1 ring-white/20
    flex flex-col justify-center
  "
        style={{
          WebkitBackdropFilter: 'blur(24px) saturate(150%) brightness(1.08)',
          backdropFilter: 'blur(24px) saturate(150%) brightness(1.08)',
          transform: `rotateX(${mouseY * 8}deg) rotateY(${mouseX * -8}deg) translate3d(0,0,120px)`,
          transformStyle: 'preserve-3d',
          transition: 'transform 100ms ease-out',
        }}
      >
        {/* 主高光 */}
        <div className="pointer-events-none absolute inset-0 rounded-full bg-[linear-gradient(135deg,rgba(255,255,255,0.42)_0%,rgba(255,255,255,0.18)_18%,rgba(255,255,255,0.06)_38%,rgba(255,255,255,0.02)_55%,rgba(255,255,255,0.10)_100%)]" />

        {/* 左上角霧面反光 */}
        <div className="pointer-events-none absolute left-[8%] top-[10%] h-[38%] w-[38%] rounded-full bg-white/18 blur-2xl" />

        {/* 底部柔光 */}
        <div className="pointer-events-none absolute inset-x-[12%] bottom-[6%] h-[18%] rounded-full bg-white/10 blur-2xl" />

        {/* 邊緣亮線 */}
        <div className="pointer-events-none absolute inset-[1px] rounded-full border border-white/30" />

        <div className="relative z-10 text-center mb-8">
          <h1 className="mb-3 bg-gradient-to-r from-lime-500 via-lime-600 to-lime-700 bg-clip-text text-4xl font-black tracking-tight text-transparent">
            {isLogin ? 'Welcome Back' : 'Join Us'}
          </h1>
          <p className="text-base font-light text-black/80">安全登入你的監控系統</p>
        </div>

        <form className="relative z-10 space-y-4">
          {!isLogin && (
            <div>
              <label className="mb-2 block text-sm font-semibold text-black/75">顯示名稱</label>
              <input
                type="text"
                className="w-full rounded-full border border-black/20 bg-white/22 px-5 py-3 text-base text-black placeholder-black/35 shadow-[inset_0_1px_0_rgba(255,255,255,0.4)] transition-all duration-300 focus:border-cyan-400/60 focus:outline-none focus:ring-4 focus:ring-cyan-400/15"
                placeholder="你的名字"
              />
            </div>
          )}

          <div>
            <label className="mb-2 block text-sm font-semibold text-black/75">電子郵件</label>
            <input
              type="email"
              className="w-full rounded-full border border-black/20 bg-white/22 px-5 py-3 text-base text-black placeholder-black/35 shadow-[inset_0_1px_0_rgba(255,255,255,0.4)] transition-all duration-300 focus:border-cyan-400/60 focus:outline-none focus:ring-4 focus:ring-cyan-400/15"
              placeholder="user@example.com"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-semibold text-black/75">密碼</label>
            <input
              type="password"
              className="w-full rounded-full border border-black/20 bg-white/22 px-5 py-3 text-base text-black placeholder-black/35 shadow-[inset_0_1px_0_rgba(255,255,255,0.4)] transition-all duration-300 focus:border-cyan-400/60 focus:outline-none focus:ring-4 focus:ring-cyan-400/15"
              placeholder="至少 8 個字元"
            />
          </div>

          <button
            type="submit"
            className="
    group relative w-full overflow-hidden rounded-full
    px-8 py-4 text-xl font-black tracking-wide text-black
bg-lime-300
    border border-lime-200/70
    shadow-[0_18px_30px_rgba(0,255,0,0.22),0_8px_16px_rgba(0,0,0,0.14),inset_0_2px_0_rgba(255,255,255,0.55),inset_0_-6px_10px_rgba(0,120,0,0.20)]
    transition-all duration-200
    hover:-translate-y-[2px] hover:shadow-[0_24px_34px_rgba(0,255,0,0.26),0_14px_24px_rgba(0,0,0,0.16),inset_0_2px_0_rgba(255,255,255,0.6),inset_0_-8px_14px_rgba(0,120,0,0.24)]
    active:translate-y-[2px] active:scale-[0.99]
    active:shadow-[0_8px_12px_rgba(0,255,0,0.16),0_4px_8px_rgba(0,0,0,0.12),inset_0_4px_8px_rgba(0,90,0,0.22),inset_0_-2px_4px_rgba(255,255,255,0.18)]
  "
          >
            <span className="pointer-events-none absolute inset-x-[8%] top-[10%] h-[45%] rounded-full bg-white/30 blur-md" />
            <span className="relative z-10">{isLogin ? '進入系統' : '建立帳號'}</span>
          </button>

        </form>

        <div className="relative z-10 mt-6 border-t border-white/30 pt-5 text-center">
          <button
            type="button"
            onClick={() => setIsLogin((prev) => !prev)}
            className="text-base font-semibold text-lime-600 transition-all duration-300 hover:text-lime-500"
          >
            {isLogin ? '註冊新帳號' : '已擁有帳號？登入'}
          </button>
        </div>
      </div>
      {/* 右側品牌區 */}
      <div className="relative z-10 hidden lg:flex flex-1 items-center justify-end pl-10 xl:pl-20">
        <div className="max-w-[520px] text-right">
          <p className="mb-4 text-sm font-semibold uppercase tracking-[0.45em] text-black/45">
            Surveillance Security Platform
          </p>

          <h2 className="text-7xl xl:text-8xl font-black tracking-[0.12em] text-black">
            OBELISK
          </h2>

          <div className="mt-6 ml-auto h-px w-40 bg-gradient-to-r from-transparent via-white/70 to-transparent" />

          <p className="mt-6 text-lg leading-8 text-black/55">
            智慧監控、事件分析與安全驗證整合平台
          </p>
        </div>
      </div>

    </div>
  );
};

export default LoginForm;

import React, { useState } from 'react';
import type { MouseEvent } from 'react';

import bgWebm from '../assets/login-bg.webm';
import bgPoster from '../assets/work-space.svg';
import bgOverlay from '../assets/hlogo-bg2_al.png';


const LoginForm: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [mouseX, setMouseX] = useState(0);
  const [mouseY, setMouseY] = useState(0);

  const handleMouseMove = (e: MouseEvent<HTMLDivElement>) => {
    // 在行動裝置（觸控）上關閉 3D 效果以維持穩定性
    if (window.innerWidth < 1024) return;

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
      className="relative flex min-h-[100dvh] w-full items-center justify-center overflow-hidden px-4 py-6 md:px-8 lg:px-12 2xl:justify-between 2xl:px-24"
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      {/* --- 影片背景層：靠右放大重點 --- */}
      {/* --- 背景層 --- */}
      <div className="absolute inset-0 z-0 overflow-hidden">
        {/* video */}
        <video
          className="
      absolute bottom-0 h-full 
      w-[90%] md:w-[110%] xl:w-[130%] 2xl:w-[150%]
      -left-[250px] md:-left-[350px] xl:-left-[550px] 2xl:-left-[750px]
      object-cover object-left
      z-0
    "
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

        {/* 疊加圖片 */}
        <img
          src={bgOverlay}
          alt="background overlay"
          className="
      pointer-events-none
      absolute bottom-0
      h-full
      w-[90%] md:w-[110%] xl:w-[130%] 2xl:w-[150%]
      object-cover object-left
      z-[1]
      opacity-80
    "
        />
      </div>


      {/* 黑色半透明遮罩：左到右、深到淺 */}
      <div className="pointer-events-none absolute inset-0 z-[1] bg-gradient-to-r from-gray-40 via-black/10 to-transparent" />
      {/* 品牌區 - 平板以下隱藏 */}
      <div className="relative z-10 hidden lg:flex flex-1 flex-col items-start justify-center pl-10 xl:pl-20">
        <div className="max-w-[520px] text-left">
          <p className="mb-2 text-xs font-semibold uppercase tracking-[0.45em] text-black/45 xl:mb-4 xl:text-sm">
            Surveillance Security Platform
          </p>

          <h2 className="text-6xl font-black tracking-[0.12em] text-black xl:text-8xl">
            OBELISK
          </h2>

          <div className="mt-6 ml-auto h-px w-32 bg-gradient-to-r from-transparent via-white/70 to-transparent md:w-40" />

          <p className="mt-6 text-sm leading-relaxed text-black/55 md:text-base xl:text-lg">
            智慧監控、事件分析與安全驗證整合平台
          </p>
        </div>
      </div>
      {/* RWD 正圓形毛玻璃卡片 */}
      <div
        className="
          relative z-10 flex flex-col items-center justify-center overflow-hidden
          aspect-square rounded-full
          w-full max-w-[min(90vw,400px)] md:max-w-[500px] 2xl:max-w-[640px]
          border border-white/35 bg-white/10
          backdrop-blur-2xl backdrop-saturate-150 backdrop-brightness-110
          shadow-[0_20px_60px_rgba(0,0,0,0.12),inset_0_1px_0_rgba(255,255,255,0.65),inset_0_-16px_28px_rgba(255,255,255,0.08)]
          ring-1 ring-white/20
          px-6 py-6 md:px-12 md:py-14 2xl:px-16
        "
        style={{
          WebkitBackdropFilter: 'blur(24px) saturate(150%) brightness(1.08)',
          backdropFilter: 'blur(24px) saturate(150%) brightness(1.08)',
          // 3D 傾斜效果
          transform: `perspective(1000px) rotateX(${mouseY * 8}deg) rotateY(${mouseX * -8}deg)`,
          transformStyle: 'preserve-3d',
          transition: 'transform 150ms ease-out',
        }}
      >
        {/* 卡片內部裝飾光影 */}
        <div className="pointer-events-none absolute inset-0 rounded-full bg-[linear-gradient(135deg,rgba(255,255,255,0.42)_0%,rgba(255,255,255,0.18)_18%,rgba(255,255,255,0.06)_38%,rgba(255,255,255,0.02)_55%,rgba(255,255,255,0.10)_100%)]" />
        <div className="pointer-events-none absolute left-[10%] top-[15%] h-[30%] w-[30%] rounded-full bg-white/20 blur-3xl" />

        {/* 表單內容容器 - 限制寬度以防觸碰到圓形邊緣 */}
        <div className="relative z-10 flex w-full max-w-[260px] flex-col items-center md:max-w-[320px] 2xl:max-w-[380px]">

          {/* 標題區 */}
          <div className="mb-4 text-center md:mb-6">
            <h1 className="mb-1 bg-gradient-to-r from-lime-500 via-lime-600 to-lime-700 bg-clip-text text-xl font-black tracking-tight text-transparent sm:text-2xl md:text-3xl xl:text-4xl">
              {isLogin ? 'Welcome Back' : 'Join Us'}
            </h1>
            <p className="text-[10px] font-light text-black/80 sm:text-xs md:text-sm">安全登入你的監控系統</p>
          </div>

          {/* 表單欄位 */}
          <form className="w-full space-y-3 md:space-y-4">
            {!isLogin && (
              <div className="space-y-1">
                <label className="block px-2 text-[10px] font-semibold text-black/75 md:text-sm">顯示名稱</label>
                <input
                  type="text"
                  className="w-full rounded-full border border-black/10 bg-white/20 px-4 py-2 text-xs text-black placeholder-black/30 shadow-inner transition-all focus:border-lime-500/50 focus:outline-none focus:ring-4 focus:ring-lime-500/10 md:px-5 md:py-2.5 md:text-sm"
                  placeholder="你的名字"
                />
              </div>
            )}

            <div className="space-y-1">
              <label className="block px-2 text-[10px] font-semibold text-black/75 md:text-sm">電子郵件</label>
              <input
                type="email"
                className="w-full rounded-full border border-black/10 bg-white/70 px-4 py-2 text-xs text-black placeholder-black/30 shadow-inner transition-all focus:border-lime-500/50 focus:outline-none focus:ring-4 focus:ring-lime-500/10 md:px-5 md:py-2.5 md:text-sm"
                placeholder="user@example.com"
              />
            </div>

            <div className="space-y-1">
              <label className="block px-2 text-[10px] font-semibold text-black/75 md:text-sm">密碼</label>
              <input
                type="password"
                className="w-full rounded-full border border-black/10 bg-white/70 px-4 py-2 text-xs text-black placeholder-black/30 shadow-inner transition-all focus:border-lime-500/50 focus:outline-none focus:ring-4 focus:ring-lime-500/10 md:px-5 md:py-2.5 md:text-sm"
                placeholder="至少 8 個字元"
              />
            </div>

            {/* 提交按鈕 */}
            <button
              type="submit"
              className="
            group relative w-full overflow-hidden rounded-full
            px-6 py-4 text-lg font-black tracking-wide text-black
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

          {/* 切換模式按鈕 */}
          <div className="mt-4 border-t border-white/20 pt-3 text-center md:mt-6 md:pt-4">
            <button
              type="button"
              onClick={() => setIsLogin((prev) => !prev)}
              className="text-[10px] font-semibold text-lime-700 transition-colors hover:text-lime-600 md:text-xs 2xl:text-sm"
            >
              {isLogin ? '註冊新帳號' : '已擁有帳號？登入'}
            </button>
          </div>
        </div>
      </div>


    </div>
  );
};

export default LoginForm;
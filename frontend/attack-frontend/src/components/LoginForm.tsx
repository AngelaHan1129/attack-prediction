import React, { useState } from 'react';
import type { MouseEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

import bgWebm from '../assets/login-bg.webm';
import bgPoster from '../assets/work-space.svg';
import bgOverlay from '../assets/hlogo-bg2_al.png';

const normalizeErrorMessage = (message: string) => {
  return message
    .replaceAll('body > username', '使用者名稱')
    .replaceAll('body > email', '電子郵件')
    .replaceAll('body > password', '密碼')
    .replaceAll('String should have at least 3 characters', '至少需要 3 個字元')
    .replaceAll('String should have at least 12 characters', '至少需要 12 個字元')
    .replaceAll(
      'value is not a valid email address: The part after the @-sign is not valid. It should have a period.',
      '請輸入正確的電子郵件格式'
    );
};

const LoginForm: React.FC = () => {
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const [isLogin, setIsLogin] = useState(true);
  const [mouseX, setMouseX] = useState(0);
  const [mouseY, setMouseY] = useState(0);

  const [identifier, setIdentifier] = useState('');
  const [email, setEmail] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const validateRegisterForm = () => {
    if (displayName.trim().length < 3) {
      return '使用者名稱至少需要 3 個字元';
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return '請輸入正確的電子郵件格式';
    }

    if (password.length < 12) {
      return '密碼至少需要 12 個字元';
    }

    return '';
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      if (isLogin) {
        await login(identifier, password);
        navigate('/dashboard');
      } else {
        const validationMessage = validateRegisterForm();
        if (validationMessage) {
          setError(validationMessage);
          return;
        }

        await register({
          username: displayName.trim(),
          email: email.trim(),
          password,
        });

        setSuccess('註冊成功，請到電子郵件信箱收取驗證信，完成驗證後再登入。');
        setIsLogin(true);
        setIdentifier(email.trim());
        setPassword('');
      }
    } catch (err: any) {
      const detail = err?.response?.data?.detail;

      if (Array.isArray(detail)) {
        const rawMessage = detail
          .map((item: any) => `${item.loc?.join(' > ') || '欄位'}：${item.msg}`)
          .join('；');
        setError(normalizeErrorMessage(rawMessage));
      } else {
        setError(normalizeErrorMessage(detail || err?.message || '發生錯誤'));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleMouseMove = (e: MouseEvent<HTMLDivElement>) => {
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
      <div className="absolute inset-0 z-0 overflow-hidden">
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

      <div className="pointer-events-none absolute inset-0 z-[1] bg-gradient-to-r from-gray-40 via-black/10 to-transparent" />

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
            智慧監視、事件分析與安全驗證整合平台
          </p>
        </div>
      </div>

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
          transform: `perspective(1000px) rotateX(${mouseY * 8}deg) rotateY(${mouseX * -8}deg)`,
          transformStyle: 'preserve-3d',
          transition: 'transform 150ms ease-out',
        }}
      >
        <div className="pointer-events-none absolute inset-0 rounded-full bg-[linear-gradient(135deg,rgba(255,255,255,0.42)_0%,rgba(255,255,255,0.18)_18%,rgba(255,255,255,0.06)_38%,rgba(255,255,255,0.02)_55%,rgba(255,255,255,0.10)_100%)]" />
        <div className="pointer-events-none absolute left-[10%] top-[15%] h-[30%] w-[30%] rounded-full bg-white/20 blur-3xl" />

        <div className="relative z-10 flex w-full max-w-[260px] flex-col items-center md:max-w-[320px] 2xl:max-w-[380px]">
          <div className="mb-4 text-center md:mb-6">
            <h1 className="mb-1 bg-gradient-to-r from-lime-500 via-lime-600 to-lime-700 bg-clip-text text-xl font-black tracking-tight text-transparent sm:text-2xl md:text-3xl xl:text-4xl">
              {isLogin ? 'Welcome Back' : 'Join Us'}
            </h1>
            <p className="text-[10px] font-light text-black/80 sm:text-xs md:text-sm">
              安全登入你的監視系統
            </p>
          </div>

          <form className="w-full space-y-3 md:space-y-4" onSubmit={handleSubmit}>
            {!isLogin && (
              <div className="space-y-1">
                <label
                  htmlFor="displayName"
                  className="block px-2 text-[10px] font-semibold text-black/75 md:text-sm"
                >
                  使用者名稱
                </label>
                <input
                  id="displayName"
                  name="displayName"
                  type="text"
                  autoComplete="username"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  className="w-full rounded-full border border-black/10 bg-white/20 px-4 py-2 text-xs text-black placeholder-black/30 shadow-inner transition-all focus:border-lime-500/50 focus:outline-none focus:ring-4 focus:ring-lime-500/10 md:px-5 md:py-2.5 md:text-sm"
                  placeholder="至少 3 個字元"
                  required
                />
              </div>
            )}

            {isLogin ? (
              <div className="space-y-1">
                <label
                  htmlFor="login"
                  className="block px-2 text-[10px] font-semibold text-black/75 md:text-sm"
                >
                  使用者名稱或電子郵件
                </label>
                <input
                  id="login"
                  name="username"
                  type="text"
                  autoComplete="username"
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  className="w-full rounded-full border border-black/10 bg-white/70 px-4 py-2 text-xs text-black placeholder-black/30 shadow-inner transition-all focus:border-lime-500/50 focus:outline-none focus:ring-4 focus:ring-lime-500/10 md:px-5 md:py-2.5 md:text-sm"
                  placeholder="請輸入使用者名稱或 user@example.com"
                  required
                />
              </div>
            ) : (
              <div className="space-y-1">
                <label
                  htmlFor="email"
                  className="block px-2 text-[10px] font-semibold text-black/75 md:text-sm"
                >
                  電子郵件
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-full border border-black/10 bg-white/70 px-4 py-2 text-xs text-black placeholder-black/30 shadow-inner transition-all focus:border-lime-500/50 focus:outline-none focus:ring-4 focus:ring-lime-500/10 md:px-5 md:py-2.5 md:text-sm"
                  placeholder="user@example.com"
                  required
                />
              </div>
            )}

            <div className="space-y-1">
              <label
                htmlFor="password"
                className="block px-2 text-[10px] font-semibold text-black/75 md:text-sm"
              >
                密碼
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete={isLogin ? 'current-password' : 'new-password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-full border border-black/10 bg-white/70 px-4 py-2 text-xs text-black placeholder-black/30 shadow-inner transition-all focus:border-lime-500/50 focus:outline-none focus:ring-4 focus:ring-lime-500/10 md:px-5 md:py-2.5 md:text-sm"
                placeholder={isLogin ? '請輸入密碼' : '至少 12 個字元'}
                required
              />
            </div>

            {success && (
              <p className="px-2 text-[10px] text-green-600 md:text-sm">
                {success}
              </p>
            )}

            {error && (
              <p className="px-2 text-[10px] text-red-600 md:text-sm">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
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
                disabled:opacity-60 disabled:cursor-not-allowed
              "
            >
              <span className="pointer-events-none absolute inset-x-[8%] top-[10%] h-[45%] rounded-full bg-white/30 blur-md" />
              <span className="relative z-10">
                {loading ? '處理中...' : isLogin ? '進入系統' : '建立帳號'}
              </span>
            </button>
          </form>

          <div className="mt-4 border-t border-white/20 pt-3 text-center md:mt-6 md:pt-4">
            <button
              type="button"
              onClick={() => {
                setIsLogin((prev) => !prev);
                setError('');
                setSuccess('');
                setPassword('');
              }}
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
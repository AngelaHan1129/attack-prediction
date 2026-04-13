import React from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

type NavItem = {
  to: string
  label: string
}

const NavBar: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const isLoggedIn = Boolean(localStorage.getItem('token'))

  const shouldHideNav =
    location.pathname === '/login' ||
    location.pathname === '/register' ||
    location.pathname === '/'

  if (shouldHideNav) {
    return null
  }

  const handleLogout = (): void => {
    localStorage.removeItem('token')
    navigate('/login')
  }

  const navItems: NavItem[] = isLoggedIn
    ? [
        { to: '/dashboard', label: '主畫面' },
      ]
    : [{ to: '/', label: '首頁' }]

  return (
    <div className="pointer-events-none fixed bottom-6 left-1/2 z-50 flex w-full -translate-x-1/2 justify-center px-4">
    <nav className="pointer-events-auto w-full max-w-xs md:max-w-md"> {/* 縮小導覽列寬度，更像膠囊 */}
      <div className="flex items-center justify-between rounded-full border border-white/20 bg-white/40 px-2 py-2 shadow-2xl backdrop-blur-2xl">
          <div className="flex items-center gap-2">
            {navItems.map((item) => {
              const isActive = location.pathname === item.to

              return (
                <Link
                  key={item.to}
                  to={item.to}
                  className={`rounded-full px-4 py-2 text-xs font-semibold transition-all duration-300 ${
                    isActive
                      ? 'bg-lime-400 text-black shadow-[0_0_16px_rgba(163,230,53,0.35)]'
                      : 'text-slate-700 hover:bg-lime-100 hover:text-slate-900'
                  }`}
                >
                  {item.label}
                </Link>
              )
            })}
          </div>

          <div className="ml-2 shrink-0">
            {isLoggedIn ? (
              <button
                onClick={handleLogout}
                className="rounded-full border border-red-300 bg-red-50/80 px-4 py-2 text-xs font-semibold text-red-700 transition-all duration-300 hover:bg-red-500 hover:text-white"
              >
                登出
              </button>
            ) : (
              <Link
                to="/login"
                className="rounded-full border border-lime-300 bg-lime-50/80 px-4 py-2 text-xs font-semibold text-slate-800 transition-all duration-300 hover:bg-lime-400 hover:text-black"
              >
                登入
              </Link>
            )}
          </div>
        </div>
      </nav>
    </div>
  )
}

export default NavBar
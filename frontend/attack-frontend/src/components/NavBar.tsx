import { Link, useNavigate } from 'react-router-dom'

const NavBar = () => {
  const navigate = useNavigate()
  const isLoggedIn = !!localStorage.getItem('token')

  return (
    <nav className="bg-gray-900/80 backdrop-blur-md border-b border-white/10 p-4">
      <div className="max-w-6xl mx-auto flex justify-between items-center">
        <Link to={isLoggedIn ? '/dashboard' : '/'} className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
          攻擊預測系統
        </Link>
        {isLoggedIn ? (
          <button onClick={() => {localStorage.removeItem('token'); navigate('/')}} className="bg-red-600 px-6 py-2 rounded-xl font-semibold hover:bg-red-700">
            登出
          </button>
        ) : (
          <Link to="/login" className="bg-blue-600 px-6 py-2 rounded-xl font-semibold hover:bg-blue-700">
            登入
          </Link>
        )}
      </div>
    </nav>
  )
}
export default NavBar

import { Routes, Route, Outlet } from 'react-router-dom'
import NavBar from './components/NavBar'
import LoginForm from './components/LoginForm'
import Dashboard from './pages/Dashboard'

const AppLayout = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 via-white to-lime-100 pb-28">
      <Outlet />
      <NavBar />
    </div>
  )
}

function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/login" element={<LoginForm />} />
        <Route path="/" element={<Dashboard />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Route>
    </Routes>
  )
}

export default App

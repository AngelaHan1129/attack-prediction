import { Routes, Route, Outlet, Navigate } from 'react-router-dom'
import NavBar from './components/NavBar'
import LoginForm from './components/LoginForm'
import Dashboard from './pages/Dashboard'
import ProtectedRoute from './components/ProtectedRoute'
import YoloViewer from './pages/YoloViewer'
import DualYoloViewer from './pages/DualYoloViewer'

const AppLayout = () => (
  <div className="min-h-screen bg-gradient-to-br from-slate-100 via-white to-lime-100 pb-28">
    <Outlet />
    <NavBar />
  </div>
)

function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/login" element={<LoginForm />} />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/yolo"
          element={
            <ProtectedRoute>
              <YoloViewer />
            </ProtectedRoute>
          }
        />

        <Route
          path="/yolo-dual"
          element={
            <ProtectedRoute>
              <DualYoloViewer />
            </ProtectedRoute>
          }
        />

        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Route>
    </Routes>
  )
}

export default App
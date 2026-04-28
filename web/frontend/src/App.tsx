import { useEffect } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import ToastContainer from './components/ToastContainer'
import Login from './pages/Login'
import ChangePassword from './pages/ChangePassword'
import Workspace from './pages/Workspace'
import LlmConfig from './pages/admin/LlmConfig'
import Users from './pages/admin/Users'
import Protocols from './pages/admin/Protocols'
import { useAuth } from './stores/auth'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, token, loading, fetchMe } = useAuth()

  useEffect(() => {
    if (token && !user) fetchMe()
  }, [token, user, fetchMe])

  if (!token) return <Navigate to="/login" />
  if (loading || !user) return <div className="min-h-screen flex items-center justify-center text-slate-400">加载中...</div>
  return <>{children}</>
}

export default function App() {
  return (
    <BrowserRouter>
      <ToastContainer />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/change-password" element={<ChangePassword />} />
        <Route
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route path="/" element={<Workspace />} />
          <Route path="/admin/llm" element={<LlmConfig />} />
          <Route path="/admin/users" element={<Users />} />
          <Route path="/admin/protocols" element={<Protocols />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

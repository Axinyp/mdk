import { useEffect } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Login from './pages/Login'
import ChangePassword from './pages/ChangePassword'
import Generator from './pages/Generator'
import History from './pages/History'
import SessionDetail from './pages/SessionDetail'
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
  if (loading || !user) return <div className="min-h-screen flex items-center justify-center text-neutral-400">加载中...</div>
  return <>{children}</>
}

export default function App() {
  return (
    <BrowserRouter>
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
          <Route path="/" element={<Generator />} />
          <Route path="/history" element={<History />} />
          <Route path="/history/:id" element={<SessionDetail />} />
          <Route path="/admin/llm" element={<LlmConfig />} />
          <Route path="/admin/users" element={<Users />} />
          <Route path="/admin/protocols" element={<Protocols />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

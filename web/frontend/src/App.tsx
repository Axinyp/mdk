import { useEffect } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Login from './pages/Login'
import Generator from './pages/Generator'
import History from './pages/History'
import { useAuth } from './stores/auth'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, token, loading, fetchMe } = useAuth()

  useEffect(() => {
    if (token && !user) fetchMe()
  }, [token, user, fetchMe])

  if (!token) return <Navigate to="/login" />
  if (loading) return <div className="min-h-screen flex items-center justify-center text-neutral-400">加载中...</div>
  if (!user) return <Navigate to="/login" />
  return <>{children}</>
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route path="/" element={<Generator />} />
          <Route path="/history" element={<History />} />
          <Route path="/history/:id" element={<Generator />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

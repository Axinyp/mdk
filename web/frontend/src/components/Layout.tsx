import { Link, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../stores/auth'

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const isAdmin = user?.role === 'admin'

  return (
    <div className="flex flex-col h-screen bg-slate-50" style={{ fontFamily: "'Plus Jakarta Sans', sans-serif" }}>
      <header className="shrink-0 bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link to="/" className="text-base font-semibold text-slate-900">
              MDK Control
            </Link>
            {isAdmin && (
              <nav className="flex gap-4">
                <Link to="/admin/protocols" className="text-sm text-slate-600 hover:text-blue-600 transition-colors">
                  协议管理
                </Link>
                <Link to="/admin/llm" className="text-sm text-slate-600 hover:text-blue-600 transition-colors">
                  模型配置
                </Link>
                <Link to="/admin/users" className="text-sm text-slate-600 hover:text-blue-600 transition-colors">
                  用户
                </Link>
              </nav>
            )}
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-500">{user?.username}</span>
            <span className={`text-xs px-2 py-0.5 rounded-full ${
              isAdmin ? 'bg-blue-50 text-blue-600' : 'bg-slate-100 text-slate-600'
            }`}>
              {isAdmin ? '管理员' : '成员'}
            </span>
            <button
              onClick={handleLogout}
              className="text-sm text-slate-500 hover:text-red-500 transition-colors"
            >
              退出
            </button>
          </div>
        </div>
      </header>
      <main className="flex-1 min-h-0">
        <Outlet />
      </main>
    </div>
  )
}

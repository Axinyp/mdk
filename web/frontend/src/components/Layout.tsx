import { Link, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../stores/auth'

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-neutral-50">
      <header className="bg-white border-b border-neutral-200">
        <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link to="/" className="text-lg font-semibold text-neutral-900">
              MDK Control
            </Link>
            <nav className="flex gap-4">
              <Link to="/" className="text-sm text-neutral-600 hover:text-blue-600">
                生成
              </Link>
              <Link to="/history" className="text-sm text-neutral-600 hover:text-blue-600">
                历史
              </Link>
              {user?.role === 'admin' && (
                <>
                  <Link to="/admin/protocols" className="text-sm text-neutral-600 hover:text-blue-600">
                    协议管理
                  </Link>
                  <Link to="/admin/llm" className="text-sm text-neutral-600 hover:text-blue-600">
                    模型配置
                  </Link>
                  <Link to="/admin/users" className="text-sm text-neutral-600 hover:text-blue-600">
                    用户
                  </Link>
                </>
              )}
            </nav>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-neutral-500">{user?.username}</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-600">
              {user?.role === 'admin' ? '管理员' : '成员'}
            </span>
            <button
              onClick={handleLogout}
              className="text-sm text-neutral-500 hover:text-red-500"
            >
              退出
            </button>
          </div>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}

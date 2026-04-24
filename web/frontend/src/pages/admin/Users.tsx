import { useEffect, useState } from 'react'
import api from '../../api/client'

interface UserItem {
  id: number
  username: string
  role: string
  status: string
  created_at: string
}

export default function Users() {
  const [users, setUsers] = useState<UserItem[]>([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ username: '', password: '', role: 'member' })
  const [loading, setLoading] = useState(false)

  const load = async () => {
    const { data } = await api.get('/admin/users')
    setUsers(data)
  }

  useEffect(() => { load() }, [])

  const handleCreate = async () => {
    setLoading(true)
    try {
      await api.post('/admin/users', form)
      await load()
      setShowForm(false)
      setForm({ username: '', password: '', role: 'member' })
    } catch (err: any) {
      alert(err.response?.data?.detail || '创建失败')
    } finally {
      setLoading(false)
    }
  }

  const handleToggleStatus = async (user: UserItem) => {
    const newStatus = user.status === 'active' ? 'disabled' : 'active'
    await api.put(`/admin/users/${user.id}`, { status: newStatus })
    await load()
  }

  const handleToggleRole = async (user: UserItem) => {
    const newRole = user.role === 'admin' ? 'member' : 'admin'
    await api.put(`/admin/users/${user.id}`, { role: newRole })
    await load()
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-neutral-900">用户管理</h1>
        <button onClick={() => setShowForm(true)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg">
          添加用户
        </button>
      </div>

      <div className="bg-white rounded-xl border border-neutral-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-neutral-50 text-left">
              <th className="px-4 py-3 text-xs font-medium text-neutral-500">ID</th>
              <th className="px-4 py-3 text-xs font-medium text-neutral-500">用户名</th>
              <th className="px-4 py-3 text-xs font-medium text-neutral-500">角色</th>
              <th className="px-4 py-3 text-xs font-medium text-neutral-500">状态</th>
              <th className="px-4 py-3 text-xs font-medium text-neutral-500">创建时间</th>
              <th className="px-4 py-3 text-xs font-medium text-neutral-500">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-100">
            {users.map((u) => (
              <tr key={u.id} className="hover:bg-neutral-50">
                <td className="px-4 py-3 text-neutral-400">{u.id}</td>
                <td className="px-4 py-3 font-medium text-neutral-900">{u.username}</td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    u.role === 'admin' ? 'bg-blue-50 text-blue-600' : 'bg-neutral-100 text-neutral-600'
                  }`}>{u.role === 'admin' ? '管理员' : '成员'}</span>
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    u.status === 'active' ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-600'
                  }`}>{u.status === 'active' ? '正常' : '已禁用'}</span>
                </td>
                <td className="px-4 py-3 text-neutral-500 text-xs">{new Date(u.created_at).toLocaleString('zh-CN')}</td>
                <td className="px-4 py-3 space-x-2">
                  <button onClick={() => handleToggleRole(u)} className="text-xs text-blue-600 hover:text-blue-800">
                    {u.role === 'admin' ? '降为成员' : '升为管理员'}
                  </button>
                  <button onClick={() => handleToggleStatus(u)} className="text-xs text-amber-600 hover:text-amber-800">
                    {u.status === 'active' ? '禁用' : '启用'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showForm && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-sm p-6">
            <h2 className="text-lg font-semibold mb-4">添加用户</h2>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-1">用户名</label>
                <input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })}
                  className="w-full px-3 py-2 border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-1">密码</label>
                <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })}
                  className="w-full px-3 py-2 border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-1">角色</label>
                <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}
                  className="w-full px-3 py-2 border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                  <option value="member">成员</option>
                  <option value="admin">管理员</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button onClick={() => setShowForm(false)} className="px-4 py-2 border border-neutral-300 text-sm rounded-lg">取消</button>
              <button onClick={handleCreate} disabled={loading || !form.username || !form.password}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg disabled:opacity-50">
                创建
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

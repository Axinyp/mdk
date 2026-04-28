import { useCallback, useEffect, useState } from 'react'
import api from '../../api/client'
import { errorMessage } from '../../api/errors'
import { toast } from '../../stores/toast'

interface UserItem {
  id: number
  username: string
  role: 'admin' | 'member'
  status: 'active' | 'disabled'
  created_at: string
}

const INPUT_CLS =
  'w-full px-3 py-2 text-sm text-slate-800 placeholder-slate-400 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'

export default function Users() {
  const [users, setUsers] = useState<UserItem[]>([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ username: '', password: '', role: 'member' })
  const [loading, setLoading] = useState(false)

  const load = useCallback(async () => {
    const { data } = await api.get('/admin/users')
    setUsers(data)
  }, [])

  useEffect(() => {
    let cancelled = false
    api.get('/admin/users').then(({ data }) => { if (!cancelled) setUsers(data) })
    return () => { cancelled = true }
  }, [])

  const handleCreate = async () => {
    setLoading(true)
    try {
      await api.post('/admin/users', form)
      await load()
      setShowForm(false)
      setForm({ username: '', password: '', role: 'member' })
      toast.success('用户已创建')
    } catch (err) {
      toast.error(errorMessage(err, '创建失败'))
    } finally {
      setLoading(false)
    }
  }

  const handleToggleStatus = async (user: UserItem) => {
    const newStatus = user.status === 'active' ? 'disabled' : 'active'
    try {
      await api.put(`/admin/users/${user.id}`, { status: newStatus })
      await load()
      toast.success(newStatus === 'active' ? '已启用用户' : '已禁用用户')
    } catch (err) {
      toast.error(errorMessage(err, '操作失败'))
    }
  }

  const handleToggleRole = async (user: UserItem) => {
    const newRole = user.role === 'admin' ? 'member' : 'admin'
    try {
      await api.put(`/admin/users/${user.id}`, { role: newRole })
      await load()
      toast.success(newRole === 'admin' ? '已升为管理员' : '已降为成员')
    } catch (err) {
      toast.error(errorMessage(err, '操作失败'))
    }
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-slate-900">用户管理</h1>
        <button onClick={() => setShowForm(true)} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors">
          + 添加用户
        </button>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50 text-left">
              <th className="px-4 py-3 text-xs font-medium text-slate-500">ID</th>
              <th className="px-4 py-3 text-xs font-medium text-slate-500">用户名</th>
              <th className="px-4 py-3 text-xs font-medium text-slate-500">角色</th>
              <th className="px-4 py-3 text-xs font-medium text-slate-500">状态</th>
              <th className="px-4 py-3 text-xs font-medium text-slate-500">创建时间</th>
              <th className="px-4 py-3 text-xs font-medium text-slate-500">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {users.map(u => (
              <tr key={u.id} className="hover:bg-slate-50">
                <td className="px-4 py-3 text-slate-400">{u.id}</td>
                <td className="px-4 py-3 font-medium text-slate-900">{u.username}</td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    u.role === 'admin' ? 'bg-blue-50 text-blue-600' : 'bg-slate-100 text-slate-600'
                  }`}>{u.role === 'admin' ? '管理员' : '成员'}</span>
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    u.status === 'active' ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-600'
                  }`}>{u.status === 'active' ? '正常' : '已禁用'}</span>
                </td>
                <td className="px-4 py-3 text-slate-500 text-xs">{new Date(u.created_at).toLocaleString('zh-CN')}</td>
                <td className="px-4 py-3 space-x-3">
                  <button onClick={() => handleToggleRole(u)} className="text-xs text-blue-600 hover:text-blue-800 transition-colors">
                    {u.role === 'admin' ? '降为成员' : '升为管理员'}
                  </button>
                  <button onClick={() => handleToggleStatus(u)} className="text-xs text-amber-600 hover:text-amber-800 transition-colors">
                    {u.status === 'active' ? '禁用' : '启用'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showForm && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 px-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-sm p-6">
            <h2 className="text-lg font-semibold text-slate-900 mb-4">添加用户</h2>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">用户名</label>
                <input value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} className={INPUT_CLS} />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">密码</label>
                <input type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} className={INPUT_CLS} />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">角色</label>
                <select value={form.role} onChange={e => setForm({ ...form, role: e.target.value })} className={INPUT_CLS}>
                  <option value="member">成员</option>
                  <option value="admin">管理员</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setShowForm(false)}
                className="px-4 py-2 border border-slate-300 text-slate-700 text-sm rounded-lg hover:bg-slate-50 transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleCreate}
                disabled={loading || !form.username || !form.password}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg disabled:opacity-50 transition-colors"
              >
                {loading ? '创建中...' : '创建'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

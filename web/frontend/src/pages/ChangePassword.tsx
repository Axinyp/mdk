import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'

export default function ChangePassword() {
  const [oldPassword, setOldPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (newPassword !== confirm) {
      setError('两次密码不一致')
      return
    }
    if (newPassword.length < 6) {
      setError('新密码至少 6 位')
      return
    }
    setLoading(true)
    try {
      await api.put('/auth/password', { old_password: oldPassword, new_password: newPassword })
      navigate('/')
    } catch (err: any) {
      setError(err.response?.data?.detail || '修改失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
      <div className="w-full max-w-sm">
        <div className="bg-white rounded-xl shadow-lg p-8">
          <h1 className="text-xl font-semibold text-neutral-900 text-center mb-2">修改密码</h1>
          <p className="text-sm text-neutral-500 text-center mb-6">首次登录需要修改默认密码</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">当前密码</label>
              <input
                type="password"
                value={oldPassword}
                onChange={(e) => setOldPassword(e.target.value)}
                className="w-full px-3 py-2 border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">新密码</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full px-3 py-2 border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">确认新密码</label>
              <input
                type="password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                className="w-full px-3 py-2 border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            {error && (
              <div className="text-sm text-red-500 bg-red-50 rounded-md px-3 py-2">{error}</div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-md transition-colors disabled:opacity-50"
            >
              {loading ? '修改中...' : '确认修改'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

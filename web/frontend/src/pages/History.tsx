import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'

interface Session {
  id: string
  title: string | null
  status: string
  description: string | null
  llm_model: string | null
  created_at: string
  updated_at: string
}

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  created: { label: '已创建', color: 'bg-neutral-100 text-neutral-600' },
  parsing: { label: '解析中', color: 'bg-blue-50 text-blue-600' },
  parsed: { label: '已解析', color: 'bg-indigo-50 text-indigo-600' },
  confirmed: { label: '已确认', color: 'bg-amber-50 text-amber-600' },
  generating: { label: '生成中', color: 'bg-blue-50 text-blue-600' },
  completed: { label: '已完成', color: 'bg-emerald-50 text-emerald-700' },
  error: { label: '错误', color: 'bg-red-50 text-red-600' },
}

export default function History() {
  const [sessions, setSessions] = useState<Session[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/gen/sessions').then(({ data }) => {
      setSessions(data)
      setLoading(false)
    })
  }, [])

  if (loading) return <div className="text-center py-12 text-neutral-400">加载中...</div>

  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-xl font-semibold text-neutral-900 mb-6">生成历史</h1>
      {sessions.length === 0 ? (
        <div className="text-center py-12 text-neutral-400">
          暂无记录，<Link to="/" className="text-blue-600 hover:underline">去生成</Link>
        </div>
      ) : (
        <div className="space-y-3">
          {sessions.map((s) => {
            const st = STATUS_MAP[s.status] || STATUS_MAP.created
            return (
              <Link
                key={s.id}
                to={`/history/${s.id}`}
                className="block bg-white rounded-lg border border-neutral-200 p-4 hover:border-blue-300 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-medium text-neutral-900">{s.title || '未命名'}</h3>
                    <p className="text-xs text-neutral-500 mt-1 line-clamp-1">{s.description}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${st.color}`}>{st.label}</span>
                    <span className="text-xs text-neutral-400">
                      {new Date(s.updated_at).toLocaleString('zh-CN')}
                    </span>
                  </div>
                </div>
              </Link>
            )
          })}
        </div>
      )}
    </div>
  )
}

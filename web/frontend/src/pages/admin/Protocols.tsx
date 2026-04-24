import { useEffect, useState } from 'react'
import api from '../../api/client'

interface ProtocolItem {
  id: number
  category: string
  brand_model: string
  comm_type: string
  filename: string | null
}

interface ProtocolDetail extends ProtocolItem {
  content: string
}

export default function Protocols() {
  const [protocols, setProtocols] = useState<ProtocolItem[]>([])
  const [selected, setSelected] = useState<ProtocolDetail | null>(null)
  const [filter, setFilter] = useState('')

  const load = async () => {
    const { data } = await api.get('/protocols', { params: { keyword: filter || undefined } })
    setProtocols(data)
  }

  useEffect(() => { load() }, [filter])

  const handleView = async (id: number) => {
    const { data } = await api.get(`/protocols/${id}`)
    setSelected(data)
  }

  const handleDelete = async (id: number) => {
    if (!confirm('确认删除？')) return
    await api.delete(`/protocols/${id}`)
    setSelected(null)
    await load()
  }

  const categories: Record<string, string> = {
    projector: '投影仪', curtain: '窗帘', ac: '空调', audio: '音频',
    display: '显示', camera: '摄像机', matrix: '矩阵', screen: '投影幕',
    lighting: '调光器', custom: '自定义',
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-neutral-900">协议管理</h1>
        <input
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="搜索协议..."
          className="px-3 py-2 border border-neutral-200 rounded-lg text-sm w-64 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="flex gap-4">
        {/* List */}
        <div className="w-1/3 space-y-2">
          {protocols.length === 0 ? (
            <div className="text-center py-8 text-neutral-400 text-sm">暂无协议</div>
          ) : (
            protocols.map((p) => (
              <button
                key={p.id}
                onClick={() => handleView(p.id)}
                className={`w-full text-left px-3 py-2.5 rounded-lg border text-sm transition-colors ${
                  selected?.id === p.id
                    ? 'border-blue-300 bg-blue-50'
                    : 'border-neutral-200 bg-white hover:border-blue-200'
                }`}
              >
                <div className="font-medium text-neutral-900">{p.brand_model}</div>
                <div className="text-xs text-neutral-500 mt-0.5">
                  {categories[p.category] || p.category} · {p.comm_type}
                </div>
              </button>
            ))
          )}
        </div>

        {/* Detail */}
        <div className="flex-1 bg-white rounded-xl border border-neutral-200">
          {selected ? (
            <div>
              <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-200">
                <div>
                  <h2 className="text-sm font-semibold text-neutral-900">{selected.brand_model}</h2>
                  <p className="text-xs text-neutral-500">{selected.category} · {selected.comm_type} · {selected.filename}</p>
                </div>
                <button onClick={() => handleDelete(selected.id)} className="text-xs text-red-500 hover:text-red-700">删除</button>
              </div>
              <pre className="p-4 text-xs leading-5 font-mono text-neutral-700 overflow-auto max-h-[600px] whitespace-pre-wrap">
                {selected.content}
              </pre>
            </div>
          ) : (
            <div className="flex items-center justify-center h-64 text-neutral-400 text-sm">
              选择一个协议查看详情
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

import { useCallback, useEffect, useState } from 'react'
import api from '../../api/client'

// ── Library types ────────────────────────────────────────────────────────────

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

// ── Review Queue types ───────────────────────────────────────────────────────

interface Submission {
  id: string
  brand_model?: string
  source_type: 'paste' | 'file'
  filename?: string
  review_status: 'pending_review' | 'processing' | 'approved' | 'rejected'
  created_at: string
  submitter?: string
  raw_content?: string
  extracted_protocol?: string
}

type AdminTab = 'library' | 'review'

// ── Constants ────────────────────────────────────────────────────────────────

const CATEGORIES: Record<string, string> = {
  projector: '投影仪', curtain: '窗帘', ac: '空调', audio: '音频',
  display: '显示', camera: '摄像机', matrix: '矩阵', screen: '投影幕',
  lighting: '调光器', custom: '自定义',
}

// ── Main component ───────────────────────────────────────────────────────────

export default function Protocols() {
  const [activeTab, setActiveTab] = useState<AdminTab>('library')
  const [pendingCount, setPendingCount] = useState(0)

  const fetchPendingCount = useCallback(async () => {
    try {
      const { data } = await api.get('/admin/protocol-submissions', { params: { status: 'pending_review', page: 1, page_size: 1 } })
      setPendingCount(data.total ?? 0)
    } catch { /* ignore */ }
  }, [])

  useEffect(() => { fetchPendingCount() }, [fetchPendingCount])

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-neutral-900">协议管理</h1>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 mb-5 border-b border-neutral-200">
        <TabButton active={activeTab === 'library'} onClick={() => setActiveTab('library')}>
          协议库
        </TabButton>
        <TabButton active={activeTab === 'review'} onClick={() => setActiveTab('review')} badge={pendingCount}>
          待审核
        </TabButton>
      </div>

      {activeTab === 'library' && <LibraryTab />}
      {activeTab === 'review'  && <ReviewTab onCountChange={setPendingCount} />}
    </div>
  )
}

// ── Tab button ───────────────────────────────────────────────────────────────

function TabButton({ active, onClick, badge, children }: {
  active: boolean
  onClick: () => void
  badge?: number
  children: React.ReactNode
}) {
  return (
    <button
      onClick={onClick}
      className={`relative px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors cursor-pointer ${
        active
          ? 'text-blue-600 border-blue-500'
          : 'text-neutral-500 border-transparent hover:text-neutral-700'
      }`}
    >
      {children}
      {badge != null && badge > 0 && (
        <span className="absolute -top-0.5 -right-1 min-w-[16px] h-4 flex items-center justify-center px-1 bg-orange-400 text-white text-[10px] font-bold rounded-full">
          {badge > 99 ? '99+' : badge}
        </span>
      )}
    </button>
  )
}

// ── Library tab ──────────────────────────────────────────────────────────────

function LibraryTab() {
  const [protocols, setProtocols] = useState<ProtocolItem[]>([])
  const [selected, setSelected] = useState<ProtocolDetail | null>(null)
  const [filter, setFilter] = useState('')

  const load = useCallback(async () => {
    const { data } = await api.get('/protocols', { params: { keyword: filter || undefined } })
    setProtocols(data)
  }, [filter])

  useEffect(() => { load() }, [load])

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

  return (
    <div className="flex gap-4">
      {/* List */}
      <div className="w-1/3 space-y-1.5">
        <input
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="搜索协议..."
          className="w-full px-3 py-2 border border-neutral-200 rounded-lg text-sm mb-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        {protocols.length === 0 ? (
          <div className="text-center py-8 text-neutral-400 text-sm">暂无协议</div>
        ) : (
          protocols.map((p) => (
            <button
              key={p.id}
              onClick={() => handleView(p.id)}
              className={`w-full text-left px-3 py-2.5 rounded-lg border text-sm transition-colors cursor-pointer ${
                selected?.id === p.id
                  ? 'border-blue-300 bg-blue-50'
                  : 'border-neutral-200 bg-white hover:border-blue-200'
              }`}
            >
              <div className="font-medium text-neutral-900">{p.brand_model}</div>
              <div className="text-xs text-neutral-500 mt-0.5">
                {CATEGORIES[p.category] || p.category} · {p.comm_type}
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
              <button onClick={() => handleDelete(selected.id)} className="text-xs text-red-500 hover:text-red-700 cursor-pointer">删除</button>
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
  )
}

// ── Review tab ───────────────────────────────────────────────────────────────

function ReviewTab({ onCountChange }: { onCountChange: (n: number) => void }) {
  const [submissions, setSubmissions] = useState<Submission[]>([])
  const [selected, setSelected] = useState<Submission | null>(null)
  const [rejectMode, setRejectMode] = useState(false)
  const [rejectNote, setRejectNote] = useState('')
  const [acting, setActing] = useState(false)

  const load = useCallback(async () => {
    try {
      const { data } = await api.get('/admin/protocol-submissions', { params: { status: 'pending_review' } })
      const list: Submission[] = data.items ?? data ?? []
      setSubmissions(list)
      onCountChange(list.length)
    } catch {
      setSubmissions([])
    }
  }, [onCountChange])

  useEffect(() => { load() }, [load])

  const loadDetail = async (sub: Submission) => {
    try {
      const { data } = await api.get(`/admin/protocol-submissions/${sub.id}`)
      setSelected(data)
    } catch {
      setSelected(sub)
    }
    setRejectMode(false)
    setRejectNote('')
  }

  const handleApprove = async (edited = false) => {
    if (!selected) return
    setActing(true)
    try {
      await api.post(`/admin/protocol-submissions/${selected.id}/approve`, edited ? { edited_data: selected.extracted_protocol } : {})
      setSelected(null)
      await load()
    } finally { setActing(false) }
  }

  const handleReject = async () => {
    if (!selected) return
    setActing(true)
    try {
      await api.post(`/admin/protocol-submissions/${selected.id}/reject`, { note: rejectNote })
      setSelected(null)
      setRejectMode(false)
      setRejectNote('')
      await load()
    } finally { setActing(false) }
  }

  const formatTime = (iso: string) => {
    try { return new Date(iso).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) }
    catch { return iso }
  }

  return (
    <div className="flex gap-4 min-h-[500px]">
      {/* List panel */}
      <div className="w-[40%] border border-neutral-200 rounded-xl bg-white overflow-hidden">
        <div className="px-4 py-3 border-b border-neutral-200 bg-neutral-50">
          <p className="text-xs font-medium text-neutral-500">{submissions.length} 条待审核</p>
        </div>

        {submissions.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center px-4">
            <div className="w-10 h-10 rounded-xl bg-neutral-100 flex items-center justify-center mb-3">
              <svg className="w-5 h-5 text-neutral-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-sm text-neutral-500">暂无待审核提交</p>
          </div>
        ) : (
          <div className="divide-y divide-neutral-100 overflow-y-auto max-h-[600px]">
            {submissions.map(sub => (
              <button
                key={sub.id}
                onClick={() => loadDetail(sub)}
                className={`w-full text-left px-4 py-3 hover:bg-neutral-50 transition-colors cursor-pointer relative ${
                  selected?.id === sub.id ? 'bg-blue-50' : ''
                }`}
              >
                {selected?.id === sub.id && (
                  <span className="absolute left-0 top-0 bottom-0 w-0.5 bg-blue-500 rounded-r" />
                )}
                <p className="text-sm font-medium text-neutral-800 truncate">
                  {sub.brand_model || '未知设备'}
                </p>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-xs text-neutral-400">
                    {sub.source_type === 'file' ? `文件·${sub.filename ?? ''}` : '粘贴文本'}
                  </span>
                  <span className="text-neutral-300">·</span>
                  <span className="text-xs text-neutral-400">{formatTime(sub.created_at)}</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Detail panel */}
      <div className="flex-1 border border-neutral-200 rounded-xl bg-white flex flex-col overflow-hidden">
        {!selected ? (
          <div className="flex-1 flex items-center justify-center text-neutral-400 text-sm">
            选择一条记录查看详情
          </div>
        ) : (
          <>
            {/* Detail header */}
            <div className="px-4 py-3 border-b border-neutral-200 bg-neutral-50 shrink-0">
              <p className="text-sm font-semibold text-neutral-800">{selected.brand_model || '未知设备'}</p>
              <p className="text-xs text-neutral-500 mt-0.5">{formatTime(selected.created_at)}</p>
            </div>

            {/* Compare area */}
            <div className="flex-1 overflow-y-auto">
              <div className="grid grid-cols-2 divide-x divide-neutral-200 min-h-full">
                {/* Raw content */}
                <div className="p-4">
                  <p className="text-xs font-medium text-neutral-500 mb-2">原始内容</p>
                  <pre className="text-xs leading-5 font-mono text-neutral-700 whitespace-pre-wrap break-all">
                    {selected.raw_content ?? '（加载中...）'}
                  </pre>
                </div>

                {/* AI extracted */}
                <div className="p-4">
                  <p className="text-xs font-medium text-neutral-500 mb-2">AI 提取结果</p>
                  {selected.extracted_protocol ? (
                    <textarea
                      value={selected.extracted_protocol}
                      onChange={e => setSelected({ ...selected, extracted_protocol: e.target.value })}
                      className="w-full text-xs leading-5 font-mono text-neutral-700 bg-slate-50 border border-neutral-200 rounded-lg p-3 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                      style={{ minHeight: '300px' }}
                    />
                  ) : (
                    <div className="text-xs text-neutral-400 italic">尚未提取，仍在处理中</div>
                  )}
                </div>
              </div>

              {/* Reject reason */}
              {rejectMode && (
                <div className="px-4 pb-4">
                  <label className="block text-xs font-medium text-neutral-600 mb-1.5">拒绝原因</label>
                  <textarea
                    value={rejectNote}
                    onChange={e => setRejectNote(e.target.value)}
                    placeholder="请说明拒绝原因（将通知提交人）..."
                    rows={3}
                    className="w-full px-3 py-2 text-sm bg-red-50 border border-red-200 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-red-400"
                  />
                </div>
              )}
            </div>

            {/* Action bar */}
            <div className="px-4 py-3 border-t border-neutral-200 shrink-0">
              {rejectMode ? (
                <div className="flex gap-2">
                  <button
                    onClick={() => setRejectMode(false)}
                    className="flex-1 py-2 border border-neutral-300 text-neutral-600 text-sm rounded-lg hover:bg-neutral-50 transition-colors cursor-pointer"
                  >
                    取消
                  </button>
                  <button
                    onClick={handleReject}
                    disabled={acting || !rejectNote.trim()}
                    className="flex-1 py-2 bg-red-500 hover:bg-red-600 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-40 cursor-pointer"
                  >
                    {acting ? '处理中...' : '确认拒绝'}
                  </button>
                </div>
              ) : (
                <div className="flex gap-2">
                  <button
                    onClick={() => setRejectMode(true)}
                    className="py-2 px-4 border border-red-300 text-red-500 text-sm rounded-lg hover:bg-red-50 transition-colors cursor-pointer"
                  >
                    拒绝
                  </button>
                  <button
                    onClick={() => handleApprove(true)}
                    disabled={acting}
                    className="flex-1 py-2 bg-neutral-100 hover:bg-neutral-200 text-neutral-700 text-sm font-medium rounded-lg transition-colors disabled:opacity-40 cursor-pointer"
                  >
                    编辑后批准
                  </button>
                  <button
                    onClick={() => handleApprove(false)}
                    disabled={acting}
                    className="flex-1 py-2 bg-emerald-500 hover:bg-emerald-600 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-40 cursor-pointer"
                  >
                    {acting ? '处理中...' : '直接批准'}
                  </button>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

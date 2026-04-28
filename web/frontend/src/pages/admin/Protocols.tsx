import { useCallback, useEffect, useState } from 'react'
import api from '../../api/client'
import { errorMessage } from '../../api/errors'
import ProtocolUploadDrawer from '../../components/ProtocolUploadDrawer'
import { toast } from '../../stores/toast'

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

const CATEGORIES: Record<string, string> = {
  projector: '投影仪', curtain: '窗帘', ac: '空调', audio: '音频',
  display: '显示', camera: '摄像机', matrix: '矩阵', screen: '投影幕',
  lighting: '调光器', custom: '自定义',
}

// ── Main component ───────────────────────────────────────────────────────────

export default function Protocols() {
  const [activeTab, setActiveTab] = useState<AdminTab>('library')
  const [pendingCount, setPendingCount] = useState(0)
  const [showUploadDrawer, setShowUploadDrawer] = useState(false)
  const [libraryReloadKey, setLibraryReloadKey] = useState(0)

  const fetchPendingCount = useCallback(async () => {
    try {
      const { data } = await api.get('/admin/protocol-submissions', { params: { status: 'pending_review', page: 1, page_size: 1 } })
      setPendingCount(data.total ?? 0)
    } catch { /* ignore */ }
  }, [])

  useEffect(() => {
    let cancelled = false
    api.get('/admin/protocol-submissions', { params: { status: 'pending_review', page: 1, page_size: 1 } })
      .then(({ data }) => { if (!cancelled) setPendingCount(data.total ?? 0) })
      .catch(() => { /* ignore */ })
    return () => { cancelled = true }
  }, [])

  return (
    <div className="max-w-6xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-slate-900">协议管理</h1>
        {activeTab === 'library' && (
          <button
            onClick={() => setShowUploadDrawer(true)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
          >
            + 提交协议
          </button>
        )}
      </div>

      <div className="flex gap-1 mb-5 border-b border-slate-200">
        <TabButton active={activeTab === 'library'} onClick={() => setActiveTab('library')}>
          协议库
        </TabButton>
        <TabButton active={activeTab === 'review'} onClick={() => setActiveTab('review')} badge={pendingCount}>
          待审核
        </TabButton>
      </div>

      {activeTab === 'library' && <LibraryTab reloadKey={libraryReloadKey} />}
      {activeTab === 'review'  && <ReviewTab onCountChange={setPendingCount} />}

      {showUploadDrawer && (
        <ProtocolUploadDrawer
          onClose={() => setShowUploadDrawer(false)}
          onSubmitted={() => {
            fetchPendingCount()
            setLibraryReloadKey(k => k + 1)
            toast.success('已提交，等待审核')
          }}
        />
      )}
    </div>
  )
}

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
          : 'text-slate-500 border-transparent hover:text-slate-700'
      }`}
    >
      {children}
      {badge != null && badge > 0 && (
        <span className="absolute -top-0.5 -right-1 min-w-[16px] h-4 flex items-center justify-center px-1 bg-amber-500 text-white text-[10px] font-bold rounded-full">
          {badge > 99 ? '99+' : badge}
        </span>
      )}
    </button>
  )
}

// ── Library tab ──────────────────────────────────────────────────────────────

function LibraryTab({ reloadKey }: { reloadKey: number }) {
  const [protocols, setProtocols] = useState<ProtocolItem[]>([])
  const [selected, setSelected] = useState<ProtocolDetail | null>(null)
  const [filter, setFilter] = useState('')
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null)

  const load = useCallback(async () => {
    const { data } = await api.get('/protocols', { params: { keyword: filter || undefined } })
    setProtocols(data)
  }, [filter])

  useEffect(() => {
    let cancelled = false
    const timer = setTimeout(() => {
      api.get('/protocols', { params: { keyword: filter || undefined } })
        .then(({ data }) => { if (!cancelled) setProtocols(data) })
        .catch(() => { /* ignore */ })
    }, filter ? 300 : 0)
    return () => { cancelled = true; clearTimeout(timer) }
  }, [filter, reloadKey])

  const handleView = async (id: number) => {
    const { data } = await api.get(`/protocols/${id}`)
    setSelected(data)
  }

  const handleDelete = async (id: number) => {
    setConfirmDeleteId(null)
    try {
      await api.delete(`/protocols/${id}`)
      setSelected(null)
      await load()
      toast.success('已删除')
    } catch (err) {
      toast.error(errorMessage(err, '删除失败'))
    }
  }

  return (
    <div className="flex gap-4">
      <div className="w-1/3 space-y-1.5">
        <input
          value={filter}
          onChange={e => setFilter(e.target.value)}
          placeholder="搜索协议..."
          className="w-full px-3 py-2 text-sm text-slate-800 placeholder-slate-400 border border-slate-200 rounded-lg mb-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        {protocols.length === 0 ? (
          <div className="text-center py-8 text-slate-400 text-sm">暂无协议</div>
        ) : (
          protocols.map(p => (
            <button
              key={p.id}
              onClick={() => handleView(p.id)}
              className={`w-full text-left px-3 py-2.5 rounded-lg border text-sm transition-colors cursor-pointer ${
                selected?.id === p.id
                  ? 'border-blue-300 bg-blue-50'
                  : 'border-slate-200 bg-white hover:border-blue-200'
              }`}
            >
              <div className="font-medium text-slate-900">{p.brand_model}</div>
              <div className="text-xs text-slate-500 mt-0.5">
                {CATEGORIES[p.category] || p.category} · {p.comm_type}
              </div>
            </button>
          ))
        )}
      </div>

      <div className="flex-1 bg-white rounded-xl border border-slate-200 shadow-sm">
        {selected ? (
          <div>
            <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200">
              <div className="min-w-0">
                <h2 className="text-sm font-semibold text-slate-900 truncate">{selected.brand_model}</h2>
                <p className="text-xs text-slate-500 truncate">{selected.category} · {selected.comm_type}{selected.filename ? ` · ${selected.filename}` : ''}</p>
              </div>
              <button onClick={() => setConfirmDeleteId(selected.id)} className="text-xs text-red-500 hover:text-red-700 cursor-pointer shrink-0 ml-2">删除</button>
            </div>
            <pre className="p-4 text-xs leading-5 font-mono text-slate-700 overflow-auto max-h-[600px] whitespace-pre-wrap">
              {selected.content}
            </pre>
          </div>
        ) : (
          <div className="flex items-center justify-center h-64 text-slate-400 text-sm">
            选择一个协议查看详情
          </div>
        )}
      </div>

      {confirmDeleteId !== null && (
        <ConfirmModal
          title="确认删除该协议？"
          description="删除后将无法恢复，使用此协议的设备需重新选择。"
          confirmText="删除"
          danger
          onConfirm={() => handleDelete(confirmDeleteId)}
          onCancel={() => setConfirmDeleteId(null)}
        />
      )}
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

  useEffect(() => {
    let cancelled = false
    api.get('/admin/protocol-submissions', { params: { status: 'pending_review' } })
      .then(({ data }) => {
        if (cancelled) return
        const list: Submission[] = data.items ?? data ?? []
        setSubmissions(list)
        onCountChange(list.length)
      })
      .catch(() => { if (!cancelled) setSubmissions([]) })
    return () => { cancelled = true }
  }, [onCountChange])

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
      toast.success(edited ? '已编辑后批准' : '已批准入库')
    } catch (err) {
      toast.error(errorMessage(err, '操作失败'))
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
      toast.success('已拒绝')
    } catch (err) {
      toast.error(errorMessage(err, '操作失败'))
    } finally { setActing(false) }
  }

  const formatTime = (iso: string) => {
    try { return new Date(iso).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) }
    catch { return iso }
  }

  return (
    <div className="flex gap-4 min-h-[500px]">
      <div className="w-[40%] border border-slate-200 rounded-xl bg-white shadow-sm overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-200 bg-slate-50">
          <p className="text-xs font-medium text-slate-500">{submissions.length} 条待审核</p>
        </div>

        {submissions.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center px-4">
            <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center mb-3">
              <svg className="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-sm text-slate-500">暂无待审核提交</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100 overflow-y-auto max-h-[600px]">
            {submissions.map(sub => (
              <button
                key={sub.id}
                onClick={() => loadDetail(sub)}
                className={`w-full text-left px-4 py-3 hover:bg-slate-50 transition-colors cursor-pointer relative ${
                  selected?.id === sub.id ? 'bg-blue-50' : ''
                }`}
              >
                {selected?.id === sub.id && (
                  <span className="absolute left-0 top-0 bottom-0 w-0.5 bg-blue-500 rounded-r" />
                )}
                <p className="text-sm font-medium text-slate-800 truncate">
                  {sub.brand_model || '未知设备'}
                </p>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-xs text-slate-400">
                    {sub.source_type === 'file' ? `文件·${sub.filename ?? ''}` : '粘贴文本'}
                  </span>
                  <span className="text-slate-300">·</span>
                  <span className="text-xs text-slate-400">{formatTime(sub.created_at)}</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="flex-1 border border-slate-200 rounded-xl bg-white shadow-sm flex flex-col overflow-hidden">
        {!selected ? (
          <div className="flex-1 flex items-center justify-center text-slate-400 text-sm">
            选择一条记录查看详情
          </div>
        ) : (
          <>
            <div className="px-4 py-3 border-b border-slate-200 bg-slate-50 shrink-0">
              <p className="text-sm font-semibold text-slate-800">{selected.brand_model || '未知设备'}</p>
              <p className="text-xs text-slate-500 mt-0.5">{formatTime(selected.created_at)}</p>
            </div>

            <div className="flex-1 overflow-y-auto">
              <div className="grid grid-cols-2 divide-x divide-slate-200 min-h-full">
                <div className="p-4">
                  <p className="text-xs font-medium text-slate-500 mb-2">原始内容</p>
                  <pre className="text-xs leading-5 font-mono text-slate-700 whitespace-pre-wrap break-all">
                    {selected.raw_content ?? '（加载中...）'}
                  </pre>
                </div>
                <div className="p-4">
                  <p className="text-xs font-medium text-slate-500 mb-2">AI 提取结果</p>
                  {selected.extracted_protocol ? (
                    <textarea
                      value={selected.extracted_protocol}
                      onChange={e => setSelected({ ...selected, extracted_protocol: e.target.value })}
                      className="w-full text-xs leading-5 font-mono text-slate-700 bg-slate-50 border border-slate-200 rounded-lg p-3 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                      style={{ minHeight: '300px' }}
                    />
                  ) : (
                    <div className="text-xs text-slate-400 italic">尚未提取，仍在处理中</div>
                  )}
                </div>
              </div>

              {rejectMode && (
                <div className="px-4 pb-4">
                  <label className="block text-xs font-medium text-slate-600 mb-1.5">拒绝原因</label>
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

            <div className="px-4 py-3 border-t border-slate-200 shrink-0">
              {rejectMode ? (
                <div className="flex gap-2">
                  <button
                    onClick={() => setRejectMode(false)}
                    className="flex-1 py-2 border border-slate-300 text-slate-700 text-sm rounded-lg hover:bg-slate-50 transition-colors"
                  >
                    取消
                  </button>
                  <button
                    onClick={handleReject}
                    disabled={acting || !rejectNote.trim()}
                    className="flex-1 py-2 bg-red-500 hover:bg-red-600 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-40"
                  >
                    {acting ? '处理中...' : '确认拒绝'}
                  </button>
                </div>
              ) : (
                <div className="flex gap-2">
                  <button
                    onClick={() => setRejectMode(true)}
                    className="py-2 px-4 border border-red-300 text-red-500 text-sm rounded-lg hover:bg-red-50 transition-colors"
                  >
                    拒绝
                  </button>
                  <button
                    onClick={() => handleApprove(true)}
                    disabled={acting}
                    className="flex-1 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-medium rounded-lg transition-colors disabled:opacity-40"
                  >
                    编辑后批准
                  </button>
                  <button
                    onClick={() => handleApprove(false)}
                    disabled={acting}
                    className="flex-1 py-2 bg-emerald-500 hover:bg-emerald-600 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-40"
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

function ConfirmModal({
  title, description, confirmText = '确认', danger = false, onConfirm, onCancel,
}: {
  title: string
  description?: string
  confirmText?: string
  danger?: boolean
  onConfirm: () => void
  onCancel: () => void
}) {
  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 px-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-sm p-6">
        <h3 className="text-base font-semibold text-slate-900">{title}</h3>
        {description && <p className="text-sm text-slate-500 mt-2">{description}</p>}
        <div className="mt-6 flex justify-end gap-2">
          <button
            onClick={onCancel}
            className="px-4 py-2 border border-slate-300 text-slate-700 text-sm rounded-lg hover:bg-slate-50 transition-colors"
          >
            取消
          </button>
          <button
            onClick={onConfirm}
            className={`px-4 py-2 text-white text-sm font-medium rounded-lg transition-colors ${
              danger ? 'bg-red-500 hover:bg-red-600' : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  )
}

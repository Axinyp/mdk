import { useCallback, useEffect, useMemo, useState } from 'react'
import api from '../api/client'
import { errorMessage } from '../api/errors'
import { consumeSSE } from '../api/sse'
import ConfirmationView, { type ParsedData } from '../components/ConfirmationView'
import ResultView from '../components/ResultView'
import { toast } from '../stores/toast'

// ── Types ──────────────────────────────────────────────────────────────────────

interface SessionSummary {
  id: string
  title: string | null
  status: string
  updated_at: string
}

interface ValidationReport {
  summary?: { critical: number; warning: number }
  cht_syntax?: { details: string[] }
}

interface ResultData {
  xml: string
  cht: string
  report: ValidationReport | null
}

interface GenProgress {
  phase: 'xml' | 'cht'
  chars: number
  elapsed: number
}

interface ParseProgress {
  chars: number
  elapsed: number
}

const PHASE_LABEL: Record<GenProgress['phase'], string> = {
  xml: 'Project.xml',
  cht: 'output.cht',
}

type UIStatus =
  | 'idle' | 'parsing' | 'parsed' | 'generating' | 'completed' | 'error'

// ── Constants ──────────────────────────────────────────────────────────────────

const DB_TO_UI: Record<string, UIStatus> = {
  created: 'idle',
  parsing: 'parsing',
  clarifying: 'parsed',  // legacy compat
  parsed: 'parsed',
  confirmed: 'parsed',
  generating: 'generating',
  completed: 'completed',
  error: 'error',
  aborted: 'error',
}

const STATUS_DOT: Record<string, string> = {
  created: 'bg-slate-300',
  parsing: 'bg-blue-400 animate-pulse',
  clarifying: 'bg-blue-400',
  parsed: 'bg-blue-500',
  confirmed: 'bg-amber-500',
  generating: 'bg-purple-500 animate-pulse',
  completed: 'bg-emerald-500',
  error: 'bg-red-500',
  aborted: 'bg-red-500',
}

const STATUS_LABEL: Record<string, string> = {
  created: '新建',
  parsing: '解析中',
  clarifying: '已解析',
  parsed: '已解析',
  confirmed: '待生成',
  generating: '生成中',
  completed: '已完成',
  error: '出错',
  aborted: '已中止',
}

const SIDEBAR_MIN = 180
const SIDEBAR_MAX = 360
const SIDEBAR_DEFAULT = 240
const SIDEBAR_LS_KEY = 'mdk_sidebar_width'

const PLACEHOLDER_HINTS = [
  '示例 1：会议室一台索尼投影 VPL-EX455（HDMI），一对天花板音响（IR），一面电动幕布；需要开机/关机、源切换、音量加减、幕布升降。',
  '示例 2：教室部署一块 75 寸触摸屏（RS232），白板软件一键启动；下课自动关投影 + 收幕布。',
  '示例 3：多功能厅四联矩阵（IP），左右双投影，无线话筒；需要会议/演讲两种场景模式。',
]

// ── Helpers ────────────────────────────────────────────────────────────────────

function formatRelativeDate(iso: string): string {
  try {
    const d = new Date(iso)
    const now = new Date()
    const sameDay = d.toDateString() === now.toDateString()
    if (sameDay) {
      return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
    }
    return `${d.getMonth() + 1}月${d.getDate()}日`
  } catch {
    return iso
  }
}

function sidebarStatusText(s: SessionSummary): string {
  const label = STATUS_LABEL[s.status] ?? s.status
  if (s.status === 'completed' || s.status === 'error' || s.status === 'aborted') {
    return `${label} · ${formatRelativeDate(s.updated_at)}`
  }
  return label
}

// ── Workspace ──────────────────────────────────────────────────────────────────

export default function Workspace() {
  // Sessions
  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [activeId, setActiveId] = useState<string | null>(null)
  const [loadingSessions, setLoadingSessions] = useState(true)

  // Sidebar resizable
  const [sidebarWidth, setSidebarWidth] = useState<number>(() => {
    const v = parseInt(localStorage.getItem(SIDEBAR_LS_KEY) || '', 10)
    return Number.isFinite(v) && v >= SIDEBAR_MIN && v <= SIDEBAR_MAX ? v : SIDEBAR_DEFAULT
  })

  // Session-scoped state
  const [sessionStatus, setSessionStatus] = useState<UIStatus>('idle')
  const [description, setDescription] = useState('')          // committed description shown in fold bar
  const [parsedData, setParsedData] = useState<ParsedData | null>(null)
  const [result, setResult] = useState<ResultData | null>(null)
  const [genStatus, setGenStatus] = useState('')
  const [genProgress, setGenProgress] = useState<GenProgress | null>(null)
  const [parseStatus, setParseStatus] = useState('')
  const [parseProgress, setParseProgress] = useState<ParseProgress | null>(null)
  const [error, setError] = useState('')

  // Step 1 input draft
  const [draftDescription, setDraftDescription] = useState('')
  const [placeholderIdx] = useState(() => Math.floor(Math.random() * PLACEHOLDER_HINTS.length))

  // Description fold bar (Step 2/3)
  const [descExpanded, setDescExpanded] = useState(false)
  const [descEditBuffer, setDescEditBuffer] = useState('')
  const [reparseLoading, setReparseLoading] = useState(false)

  // Generation polling control: only when loading an in-progress session
  const [shouldPoll, setShouldPoll] = useState(false)

  // New-chat unsaved-edit confirmation
  const [pendingNewChat, setPendingNewChat] = useState(false)

  // Sidebar delete-session confirmation (id of the row pending deletion)
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null)

  // viewStep is what the user is currently looking at; it follows
  // ``reachedStep`` by default but can be overridden by clicking the
  // step indicator to revisit a finished phase.
  const [viewStep, setViewStep] = useState<1 | 2 | 3>(1)

  // ── Sessions list ──
  const fetchSessions = useCallback(async () => {
    try {
      const { data } = await api.get('/gen/sessions')
      setSessions(data)
    } finally {
      setLoadingSessions(false)
    }
  }, [])

  useEffect(() => { fetchSessions() }, [fetchSessions])

  // ── Sidebar resize ──
  const handleResizeStart = (e: React.MouseEvent) => {
    e.preventDefault()
    const startX = e.clientX
    const startWidth = sidebarWidth
    let finalWidth = startWidth
    const onMove = (ev: MouseEvent) => {
      const next = Math.max(SIDEBAR_MIN, Math.min(SIDEBAR_MAX, startWidth + ev.clientX - startX))
      finalWidth = next
      setSidebarWidth(next)
    }
    const onUp = () => {
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseup', onUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
      localStorage.setItem(SIDEBAR_LS_KEY, String(finalWidth))
    }
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
    document.addEventListener('mousemove', onMove)
    document.addEventListener('mouseup', onUp)
  }

  // ── Reset to step 1 ──
  const resetToIdle = useCallback(() => {
    setActiveId(null)
    setSessionStatus('idle')
    setDescription('')
    setParsedData(null)
    setResult(null)
    setGenStatus('')
    setGenProgress(null)
    setError('')
    setDescExpanded(false)
    setDescEditBuffer('')
    setShouldPoll(false)
  }, [])

  // ── Load existing session ──
  const loadSession = useCallback(async (id: string) => {
    setError('')
    setActiveId(id)
    setShouldPoll(false)
    setDescExpanded(false)
    setDescEditBuffer('')
    setGenStatus('')
    try {
      const { data } = await api.get(`/gen/sessions/${id}`)
      const uiStatus = DB_TO_UI[data.status] ?? 'idle'

      setDescription(data.description || '')

      if (data.parsed_data) {
        const pd: ParsedData = typeof data.parsed_data === 'string'
          ? JSON.parse(data.parsed_data)
          : data.parsed_data
        setParsedData(pd)
      } else {
        setParsedData(null)
      }

      const parsedReport: ValidationReport | { details?: string[] } | null = data.validation_report
        ? (typeof data.validation_report === 'string'
            ? JSON.parse(data.validation_report)
            : data.validation_report)
        : null

      if (data.status === 'completed' && data.xml_content) {
        setResult({
          xml: data.xml_content,
          cht: data.cht_content,
          report: parsedReport as ValidationReport | null,
        })
      } else {
        setResult(null)
      }

      if (uiStatus === 'error') {
        const detail = (parsedReport as { details?: string[] } | null)?.details?.[0]
        if (detail) setError(`上次失败：${detail}`)
      }

      // Error session with no parsed_data falls back to Step 1 (DescribeStep);
      // surface the original description so the user can review and re-submit.
      if (uiStatus === 'error' && !data.parsed_data) {
        setDraftDescription(data.description || '')
      } else if (uiStatus !== 'idle') {
        // Switching to a healthy non-idle session — clear any half-typed draft
        // from a previous Step 1 attempt to avoid contaminating its textarea.
        setDraftDescription('')
      }

      setSessionStatus(uiStatus)
      if (uiStatus === 'generating') setShouldPoll(true)
    } catch (err) {
      setError(errorMessage(err, '加载会话失败'))
      setSessionStatus('error')
    }
  }, [])

  // ── Polling for in-progress generation ──
  useEffect(() => {
    if (!shouldPoll || !activeId) return
    let cancelled = false

    const tick = async () => {
      try {
        const { data } = await api.get(`/gen/sessions/${activeId}`)
        if (cancelled) return
        const ui = DB_TO_UI[data.status] ?? 'idle'
        if (ui === 'completed') {
          const { data: r } = await api.get(`/gen/sessions/${activeId}/result`)
          if (cancelled) return
          setResult({
            xml: r.xml_content,
            cht: r.cht_content,
            report: (r.validation_report as ValidationReport | null) ?? null,
          })
          setSessionStatus('completed')
          setShouldPoll(false)
          fetchSessions()
        } else if (ui === 'error') {
          setSessionStatus('error')
          setShouldPoll(false)
          fetchSessions()
        }
      } catch { /* keep polling */ }
    }

    const id = setInterval(tick, 2500)
    tick()
    return () => { cancelled = true; clearInterval(id) }
  }, [shouldPoll, activeId, fetchSessions])

  // ── Shared parse-stream handlers (used by Start + Re-parse) ──
  // Consumes SSE events: status / progress / parsed_done / done / error.
  // Returns a Promise that resolves once parsing succeeds; throws on error.
  const consumeParseStream = async (sessionId: string, body?: object) => {
    setParseStatus('正在解析需求...')
    setParseProgress(null)
    let parsed: ParsedData | null = null
    await consumeSSE(`/api/gen/sessions/${sessionId}/parse`, {
      status: (data) => { setParseStatus(data); setParseProgress(null) },
      progress: (data) => {
        try { setParseProgress(JSON.parse(data) as ParseProgress) } catch { /* skip */ }
      },
      parsed_done: (data) => {
        try { parsed = JSON.parse(data) as ParsedData } catch { /* keep null */ }
      },
      done: () => { /* status + messages refresh handled via fetchSessions */ },
    }, { body })
    if (!parsed) throw new Error('解析未返回数据')
    return parsed as ParsedData
  }

  // ── Start parse from Step 1 ──
  // Two entry paths share this handler:
  //   1. Brand-new chat — no activeId yet, we create the session first.
  //   2. Retrying a failed session (status=error, parsed_data=null) — activeId
  //      already exists, we re-parse against the (possibly edited) description
  //      instead of creating a duplicate session.
  const handleStartParse = async () => {
    const text = draftDescription.trim()
    if (!text) return
    setError('')
    setSessionStatus('parsing')
    try {
      let sessionId = activeId
      if (!sessionId) {
        const { data: session } = await api.post('/gen/sessions', { description: text })
        sessionId = session.id as string
        setActiveId(sessionId)
        setDescription(text)
        // Newly created session — backend already has the description, so no body needed.
        const pd = await consumeParseStream(sessionId)
        setParsedData(pd)
      } else {
        // Re-parse path: send description so backend updates session.description first.
        setDescription(text)
        const pd = await consumeParseStream(sessionId, { description: text })
        setParsedData(pd)
      }
      setSessionStatus('parsed')
      setDraftDescription('')
      setParseStatus('')
      setParseProgress(null)
      fetchSessions()
    } catch (err) {
      setError(errorMessage(err, '解析失败'))
      setSessionStatus('error')
      setParseStatus('')
      setParseProgress(null)
    }
  }

  // ── Re-parse from fold bar ──
  const handleReParse = async () => {
    const text = descEditBuffer.trim()
    if (!text || !activeId) return
    setReparseLoading(true)
    setError('')
    try {
      const pd = await consumeParseStream(activeId, { description: text })
      setParsedData(pd)
      setDescription(text)
      setDescExpanded(false)
      setSessionStatus('parsed')
      fetchSessions()
      toast.success('已重新解析')
    } catch (err) {
      setError(errorMessage(err, '重新解析失败'))
    } finally {
      setReparseLoading(false)
      setParseStatus('')
      setParseProgress(null)
    }
  }

  // ── Confirm + generate (SSE) ──
  const handleConfirm = async (data: ParsedData) => {
    if (!activeId) return
    setError('')
    setGenStatus('正在确认...')
    setGenProgress(null)
    setSessionStatus('generating')
    setResult(null)

    try {
      await api.post(`/gen/sessions/${activeId}/confirm`, { data })
      fetchSessions()

      let hadError = false
      try {
        await consumeSSE(`/api/gen/sessions/${activeId}/generate`, {
          status: (raw) => { setGenStatus(raw); setGenProgress(null) },
          progress: (raw) => {
            try { setGenProgress(JSON.parse(raw) as GenProgress) } catch { /* skip */ }
          },
          xml_done: () => setGenProgress(null),
          cht_done: () => setGenProgress(null),
          validation: () => { /* surface via final result fetch */ },
          done: () => { /* loop will exit naturally */ },
        }, {
          onError: () => { hadError = true; setError('生成失败'); setSessionStatus('error') },
        })
      } catch (streamErr) {
        if (!hadError) {
          hadError = true
          setError(errorMessage(streamErr, '生成失败'))
          setSessionStatus('error')
        }
      }

      if (!hadError) {
        const { data: resultData } = await api.get(`/gen/sessions/${activeId}/result`)
        setResult({
          xml: resultData.xml_content,
          cht: resultData.cht_content,
          report: (resultData.validation_report as ValidationReport | null) ?? null,
        })
        setSessionStatus('completed')
        toast.success('生成完成')
        fetchSessions()
      }
    } catch (err) {
      setError(errorMessage(err, '生成失败'))
      setSessionStatus('error')
    }
  }

  // ── Step computation ──
  // ``reachedStep`` = furthest step the session has progressed to (drives
  // which step buttons are clickable). ``viewStep`` is what the user is
  // currently looking at — auto-follows reached on advance, or jumps back
  // when the user clicks a prior step button.
  const reachedStep: 1 | 2 | 3 = useMemo(() => {
    if (sessionStatus === 'generating' || sessionStatus === 'completed') return 3
    if (sessionStatus === 'parsed' || (sessionStatus === 'error' && parsedData)) return 2
    return 1
  }, [sessionStatus, parsedData])

  useEffect(() => {
    // Auto-follow when the session advances; user can still click an earlier
    // step afterwards to revisit it.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setViewStep(reachedStep)
  }, [reachedStep])

  const handleStepClick = (n: 1 | 2 | 3) => {
    // Step 1 is only meaningful when no session exists yet; once parsed,
    // the description fold-bar handles re-editing. Disallow jumping back
    // to Step 1 so the user can't lose the in-flight state.
    if (n === 1 && reachedStep > 1) return
    if (n <= reachedStep) setViewStep(n)
  }

  // ── Has unsaved work ── (used to warn on new chat)
  const hasUnsavedWork = useMemo(() => {
    if (sessionStatus === 'idle') return draftDescription.trim().length > 0
    if (sessionStatus === 'parsed') return descExpanded && descEditBuffer.trim() !== description.trim()
    return false
  }, [sessionStatus, draftDescription, descExpanded, descEditBuffer, description])

  const handleNewChatClick = () => {
    if (hasUnsavedWork) {
      setPendingNewChat(true)
    } else {
      resetToIdle()
      setDraftDescription('')
    }
  }

  const confirmNewChat = () => {
    setPendingNewChat(false)
    resetToIdle()
    setDraftDescription('')
  }

  // ── Delete session (sidebar trash button) ──
  const confirmDeleteSession = async () => {
    const id = pendingDeleteId
    if (!id) return
    setPendingDeleteId(null)
    try {
      await api.delete(`/gen/sessions/${id}`)
      setSessions(prev => prev.filter(s => s.id !== id))
      if (activeId === id) {
        resetToIdle()
        setDraftDescription('')
      }
      toast.success('已删除会话')
    } catch (err) {
      toast.error(errorMessage(err, '删除失败'))
    }
  }

  const pendingDeleteTitle = useMemo(() => {
    if (!pendingDeleteId) return ''
    return sessions.find(s => s.id === pendingDeleteId)?.title || '未命名'
  }, [pendingDeleteId, sessions])

  return (
    <div className="flex h-full bg-slate-50" style={{ fontFamily: "'Plus Jakarta Sans', sans-serif" }}>
      {/* ── Sidebar ── */}
      <aside
        className="shrink-0 border-r border-slate-200 bg-white flex flex-col"
        style={{ width: sidebarWidth }}
      >
        <div className="p-2.5 border-b border-slate-100 shrink-0">
          <button
            onClick={handleNewChatClick}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-slate-600 hover:bg-slate-100 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            新建对话
          </button>
        </div>

        <div className="flex-1 overflow-y-auto py-1">
          {loadingSessions ? (
            <p className="px-4 py-3 text-xs text-slate-400">加载中...</p>
          ) : sessions.length === 0 ? (
            <p className="px-4 py-6 text-xs text-slate-400 text-center">暂无记录</p>
          ) : (
            sessions.map(s => {
              const isActive = s.id === activeId
              const dotCls = STATUS_DOT[s.status] ?? STATUS_DOT.created
              const onActivate = () => loadSession(s.id)
              return (
                <div
                  key={s.id}
                  role="button"
                  tabIndex={0}
                  onClick={onActivate}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault()
                      onActivate()
                    }
                  }}
                  className={`group relative w-full text-left px-3 py-2.5 flex items-start gap-2 transition-colors cursor-pointer ${
                    isActive ? 'bg-slate-100' : 'hover:bg-slate-50'
                  }`}
                >
                  <span className={`mt-1.5 w-2 h-2 rounded-full shrink-0 ${dotCls}`} />
                  <div className="min-w-0 flex-1 pr-6">
                    <p className={`text-sm truncate ${isActive ? 'font-medium text-slate-900' : 'text-slate-700'}`}>
                      {s.title || '未命名'}
                    </p>
                    <p className="text-xs text-slate-400 mt-0.5 truncate">
                      {sidebarStatusText(s)}
                    </p>
                  </div>
                  <button
                    type="button"
                    aria-label="删除会话"
                    onClick={(e) => { e.stopPropagation(); setPendingDeleteId(s.id) }}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded text-slate-400 opacity-0 group-hover:opacity-100 hover:bg-slate-200 hover:text-red-600 transition-all focus:opacity-100 focus:outline-none"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                      <path fillRule="evenodd" d="M8.75 1A2.75 2.75 0 0 0 6 3.75v.443c-.795.077-1.584.176-2.365.298a.75.75 0 1 0 .23 1.482l.149-.022.841 10.518A2.75 2.75 0 0 0 7.596 19h4.807a2.75 2.75 0 0 0 2.742-2.53l.841-10.52.149.023a.75.75 0 0 0 .23-1.482A41.03 41.03 0 0 0 14 4.193V3.75A2.75 2.75 0 0 0 11.25 1h-2.5ZM10 4c.84 0 1.673.025 2.5.075V3.75c0-.69-.56-1.25-1.25-1.25h-2.5c-.69 0-1.25.56-1.25 1.25v.325C8.327 4.025 9.16 4 10 4ZM8.58 7.72a.75.75 0 0 0-1.5.06l.3 7.5a.75.75 0 1 0 1.5-.06l-.3-7.5Zm4.34.06a.75.75 0 1 0-1.5-.06l-.3 7.5a.75.75 0 1 0 1.5.06l.3-7.5Z" clipRule="evenodd" />
                    </svg>
                  </button>
                </div>
              )
            })
          )}
        </div>
      </aside>

      {/* ── Resize handle ── */}
      <div
        onMouseDown={handleResizeStart}
        className="w-1 shrink-0 cursor-col-resize hover:bg-blue-200 active:bg-blue-300 transition-colors"
        title="拖动调宽"
      />

      {/* ── Main ── */}
      <main className="flex-1 min-w-0 flex flex-col">
        <StepIndicator
          viewStep={viewStep}
          reachedStep={reachedStep}
          onStepClick={handleStepClick}
        />

        {reachedStep >= 2 && (
          <DescriptionFoldBar
            description={description}
            expanded={descExpanded}
            buffer={descEditBuffer}
            onExpand={() => { setDescEditBuffer(description); setDescExpanded(true) }}
            onCancel={() => { setDescExpanded(false); setDescEditBuffer('') }}
            onChange={setDescEditBuffer}
            onReParse={handleReParse}
            canReParse={reachedStep === 2}
            loading={reparseLoading}
          />
        )}

        <div className="flex-1 min-h-0 overflow-y-auto">
          <div className="max-w-7xl mx-auto px-6 py-6 h-full flex flex-col">
            {error && (
              <div className="mb-3 px-3 py-2 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 shrink-0">
                {error}
              </div>
            )}

            {viewStep === 1 && reachedStep === 1 && (
              <DescribeStep
                value={draftDescription}
                onChange={setDraftDescription}
                placeholder={PLACEHOLDER_HINTS[placeholderIdx]}
                onStart={handleStartParse}
                isParsing={sessionStatus === 'parsing'}
                parseStatus={parseStatus}
                parseProgress={parseProgress}
              />
            )}

            {viewStep === 2 && parsedData && (
              <ConfirmationView
                data={parsedData}
                onConfirm={handleConfirm}
                readOnly={reachedStep > 2}
              />
            )}

            {viewStep === 3 && (
              sessionStatus === 'generating' || !result ? (
                <GeneratingPanel statusText={genStatus || '正在生成...'} progress={genProgress} />
              ) : (
                <ResultView
                  xml={result.xml}
                  cht={result.cht}
                  report={result.report}
                  sessionId={activeId!}
                />
              )
            )}
          </div>
        </div>
      </main>

      {pendingNewChat && (
        <ConfirmModal
          title="放弃当前编辑？"
          description="检测到尚未提交的修改，新建对话将丢失这些内容。"
          confirmText="新建对话"
          danger
          onConfirm={confirmNewChat}
          onCancel={() => setPendingNewChat(false)}
        />
      )}

      {pendingDeleteId && (
        <ConfirmModal
          title="删除该会话？"
          description={`「${pendingDeleteTitle}」及其对话记录、解析快照将永久删除，无法撤销。`}
          confirmText="删除"
          danger
          onConfirm={confirmDeleteSession}
          onCancel={() => setPendingDeleteId(null)}
        />
      )}
    </div>
  )
}

// ── Step indicator ────────────────────────────────────────────────────────────

function StepIndicator({
  viewStep, reachedStep, onStepClick,
}: {
  viewStep: 1 | 2 | 3
  reachedStep: 1 | 2 | 3
  onStepClick: (n: 1 | 2 | 3) => void
}) {
  const steps: { n: 1 | 2 | 3; label: string }[] = [
    { n: 1, label: '描述需求' },
    { n: 2, label: '确认清单' },
    { n: 3, label: '生成结果' },
  ]
  return (
    <div className="bg-white border-b border-slate-200 px-6 py-3 shrink-0">
      <div className="max-w-7xl mx-auto flex items-center gap-3">
        {steps.map((s, i) => {
          const isViewing = viewStep === s.n
          const isReached = reachedStep >= s.n
          // Step 1 is not navigable once the session has progressed past it.
          const clickable = isReached && !(s.n === 1 && reachedStep > 1)
          // Reached but not currently viewed → show as completed.
          const completed = isReached && !isViewing
          return (
            <div key={s.n} className="flex items-center gap-3 flex-1">
              <button
                type="button"
                onClick={() => clickable && onStepClick(s.n)}
                disabled={!clickable}
                className={`flex items-center gap-2 rounded-lg px-2 py-1 -mx-2 transition-colors ${
                  clickable ? 'cursor-pointer hover:bg-slate-50' : 'cursor-default'
                }`}
              >
                <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold transition-colors ${
                  isViewing ? 'bg-blue-600 text-white'
                  : completed ? 'bg-emerald-500 text-white'
                  : 'bg-slate-100 text-slate-400'
                }`}>
                  {completed ? (
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : s.n}
                </span>
                <span className={`text-sm font-medium whitespace-nowrap ${
                  isViewing ? 'text-slate-900'
                  : completed ? 'text-slate-700'
                  : 'text-slate-400'
                }`}>
                  {s.label}
                </span>
              </button>
              {i < steps.length - 1 && (
                <span className={`flex-1 h-px ${reachedStep > s.n ? 'bg-emerald-300' : 'bg-slate-200'}`} />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ── Step 1: Describe ──────────────────────────────────────────────────────────

function DescribeStep({
  value, onChange, placeholder, onStart, isParsing, parseStatus, parseProgress,
}: {
  value: string
  onChange: (v: string) => void
  placeholder: string
  onStart: () => void
  isParsing: boolean
  parseStatus: string
  parseProgress: ParseProgress | null
}) {
  const handleKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault()
      if (value.trim() && !isParsing) onStart()
    }
  }
  const canStart = value.trim().length > 0 && !isParsing

  return (
    <div className="flex-1 flex flex-col gap-4 min-h-0">
      <div>
        <h2 className="text-base font-semibold text-slate-900">描述您的中控需求</h2>
        <p className="text-sm text-slate-500 mt-1">
          越具体越好，包括设备清单、品牌型号、通信方式、控制功能与场景模式。
        </p>
      </div>

      <div className="flex-1 bg-white border border-slate-200 rounded-xl shadow-sm flex flex-col min-h-[280px]">
        <textarea
          value={value}
          onChange={e => onChange(e.target.value)}
          onKeyDown={handleKey}
          placeholder={placeholder}
          disabled={isParsing}
          className="flex-1 w-full px-4 py-3 text-sm text-slate-800 placeholder-slate-400 resize-none focus:outline-none disabled:opacity-60 rounded-t-xl"
        />
        <div className="flex items-center justify-between px-3 py-2 border-t border-slate-100">
          <span className="text-xs text-slate-400">{value.length} 字符 · ⌘/Ctrl + Enter 提交</span>
          <button
            onClick={onStart}
            disabled={!canStart}
            className="flex items-center gap-2 px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {isParsing
              ? <><span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />解析中...</>
              : '开始解析'}
          </button>
        </div>
      </div>

      {isParsing && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 flex items-center gap-3">
          <span className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin shrink-0" />
          <div className="flex-1 min-w-0">
            <div className="text-sm font-medium text-blue-900">{parseStatus || '正在解析需求...'}</div>
            {parseProgress && (
              <div className="text-xs text-blue-700 mt-0.5">
                已接收 {parseProgress.chars.toLocaleString()} 字符 · {parseProgress.elapsed.toFixed(1)}s
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// ── Description fold bar (Step 2 / 3) ─────────────────────────────────────────

function DescriptionFoldBar({
  description, expanded, buffer, onExpand, onCancel, onChange, onReParse, canReParse, loading,
}: {
  description: string
  expanded: boolean
  buffer: string
  onExpand: () => void
  onCancel: () => void
  onChange: (v: string) => void
  onReParse: () => void
  /** Step 2 enables editing + 重新解析; Step 3 keeps the bar collapsible but read-only. */
  canReParse: boolean
  loading: boolean
}) {
  if (!expanded) {
    return (
      <div className="bg-white border-b border-slate-200 px-6 py-2.5 shrink-0">
        <div className="max-w-7xl mx-auto flex items-center gap-3">
          <span className="text-xs font-medium text-slate-400 shrink-0">需求</span>
          <p className="flex-1 text-sm text-slate-700 truncate">{description || '(空)'}</p>
          <button
            onClick={onExpand}
            className="text-xs text-blue-600 hover:text-blue-800 transition-colors shrink-0"
          >
            {canReParse ? '展开 / 重新解析' : '展开查看'}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white border-b border-slate-200 px-6 py-3 shrink-0">
      <div className="max-w-7xl mx-auto">
        <textarea
          value={buffer}
          onChange={e => onChange(e.target.value)}
          rows={5}
          readOnly={!canReParse}
          className={`w-full px-3 py-2 text-sm text-slate-800 border border-slate-200 rounded-lg resize-y focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            canReParse ? '' : 'bg-slate-50 cursor-default'
          }`}
        />
        <div className="flex items-center justify-end gap-2 mt-2">
          <button
            onClick={onCancel}
            disabled={loading}
            className="px-4 py-1.5 border border-slate-300 text-slate-700 text-sm rounded-lg hover:bg-slate-50 transition-colors disabled:opacity-50"
          >
            {canReParse ? '取消' : '收起'}
          </button>
          {canReParse && (
            <button
              onClick={onReParse}
              disabled={loading || !buffer.trim()}
              className="flex items-center gap-2 px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
            >
              {loading
                ? <><span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />解析中...</>
                : '重新解析'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Step 3: Generating panel ──────────────────────────────────────────────────

function GeneratingPanel({
  statusText, progress,
}: {
  statusText: string
  progress: GenProgress | null
}) {
  const phaseLabel = progress ? PHASE_LABEL[progress.phase] : null
  return (
    <div className="flex-1 flex flex-col items-center justify-center bg-white border border-slate-200 rounded-xl text-center p-12">
      <div className="w-12 h-12 border-2 border-purple-200 border-t-purple-600 rounded-full animate-spin mb-4" />
      <p className="text-sm font-medium text-slate-900 mb-1">{statusText}</p>
      {progress ? (
        <p className="text-xs text-slate-500 mt-2 tabular-nums">
          {phaseLabel} · 已生成 <span className="font-semibold text-slate-700">{progress.chars.toLocaleString()}</span> 字符 ·
          已用 <span className="font-semibold text-slate-700">{progress.elapsed.toFixed(0)}s</span>
        </p>
      ) : (
        <p className="text-xs text-slate-400 mt-2">连接中...</p>
      )}
      <p className="text-xs text-slate-400 mt-3">生成过程独立运行，可切换到其他会话或离开页面，返回后会自动继续。</p>
    </div>
  )
}

// ── Confirm modal ─────────────────────────────────────────────────────────────

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

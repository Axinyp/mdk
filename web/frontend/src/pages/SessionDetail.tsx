import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../api/client'
import ConfirmationView from '../components/ConfirmationView'

interface SessionData {
  id: string
  title: string | null
  status: string
  description: string | null
  parsed_data: string | null
  confirmed_data: string | null
  join_registry: string | null
  xml_content: string | null
  cht_content: string | null
  validation_report: string | null
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

const STEPS = [
  { key: 'description', label: '需求描述' },
  { key: 'parsed', label: '解析结果' },
  { key: 'confirmed', label: '确认清单' },
  { key: 'generated', label: '生成结果' },
  { key: 'validation', label: '校验报告' },
] as const

export default function SessionDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [session, setSession] = useState<SessionData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeStep, setActiveStep] = useState<string>('description')
  const [codeTab, setCodeTab] = useState<'xml' | 'cht'>('xml')

  // Resume states
  const [resumeMode, setResumeMode] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [genStatus, setGenStatus] = useState('')

  const fetchSession = () => {
    if (!id) return
    api.get(`/gen/sessions/${id}`)
      .then(({ data }) => {
        setSession(data)
        // auto-select the most advanced available step
        if (data.xml_content) setActiveStep('generated')
        else if (data.confirmed_data) setActiveStep('confirmed')
        else if (data.parsed_data) setActiveStep('parsed')
        else setActiveStep('description')
      })
      .catch((err: any) => setError(err.response?.data?.detail || '加载失败'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchSession() }, [id])

  if (loading) return <div className="text-center py-12 text-neutral-400">加载中...</div>
  if (error && !session) return (
    <div className="max-w-6xl mx-auto text-center py-12">
      <p className="text-red-500 mb-4">{error}</p>
      <button onClick={() => navigate('/history')} className="text-sm text-blue-600 hover:underline">返回历史</button>
    </div>
  )
  if (!session) return null

  const st = STATUS_MAP[session.status] || STATUS_MAP.created
  const parsed = session.parsed_data ? JSON.parse(session.parsed_data) : null
  const confirmed = session.confirmed_data ? JSON.parse(session.confirmed_data) : null
  const joins = session.join_registry ? JSON.parse(session.join_registry) : null
  const report = session.validation_report ? JSON.parse(session.validation_report) : null

  // Determine what resume actions are available
  const canResume = session.status === 'parsed' || session.status === 'confirmed' || session.status === 'error'
  const resumeLabel = (() => {
    if (session.status === 'parsed') return '继续确认'
    if (session.status === 'confirmed') return '继续生成'
    if (session.status === 'error') {
      if (confirmed) return '重新生成'
      if (parsed) return '重新确认'
    }
    return ''
  })()

  const stepAvailable = (key: string) => {
    switch (key) {
      case 'description': return true
      case 'parsed': return !!parsed
      case 'confirmed': return !!confirmed
      case 'generated': return !!session.xml_content || !!session.cht_content
      case 'validation': return !!report
      default: return false
    }
  }

  const handleCopy = (content: string) => navigator.clipboard.writeText(content)

  const handleDownload = (content: string, filename: string) => {
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleDownloadZip = async () => {
    const token = localStorage.getItem('token')
    const res = await fetch(`/api/gen/sessions/${session.id}/download`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `mdk_${session.id.slice(0, 8)}.zip`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleResume = () => {
    if (session.status === 'parsed') {
      setResumeMode(true)
      setActiveStep('parsed')
    } else if (session.status === 'confirmed' || (session.status === 'error' && confirmed)) {
      handleGenerate()
    } else if (session.status === 'error' && parsed) {
      setResumeMode(true)
      setActiveStep('parsed')
    }
  }

  const handleConfirm = async (data: any) => {
    setError('')
    setGenerating(true)
    setGenStatus('正在确认...')
    setResumeMode(false)
    try {
      await api.post(`/gen/sessions/${session.id}/confirm`, { data })
      await runGenerate()
    } catch (err: any) {
      setError(err.response?.data?.detail || '确认失败')
      setGenerating(false)
    }
  }

  const handleGenerate = async () => {
    setError('')
    setGenerating(true)
    setGenStatus('正在生成...')
    try {
      await runGenerate()
    } catch (err: any) {
      setError(err.response?.data?.detail || '生成失败')
      setGenerating(false)
    }
  }

  const runGenerate = async () => {
    setActiveStep('generated')
    const response = await fetch(`/api/gen/sessions/${session.id}/generate`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
    })

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()
    if (!reader) throw new Error('No stream')

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const text = decoder.decode(value)
      for (const line of text.split('\n')) {
        if (line.startsWith('event: ')) {
          const event = line.replace('event: ', '')
          if (event === 'error') {
            setError('生成失败')
            setGenerating(false)
            return
          }
        }
        if (line.startsWith('data: ')) {
          try {
            const payload = JSON.parse(line.replace('data: ', ''))
            if (typeof payload === 'string') setGenStatus(payload)
            else setGenStatus(JSON.stringify(payload))
          } catch { /* skip */ }
        }
      }
    }

    setGenerating(false)
    setGenStatus('')
    fetchSession()
  }

  const summary = report?.summary || { critical: 0, warning: 0 }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center gap-3">
            <button onClick={() => navigate('/history')} className="text-neutral-400 hover:text-neutral-600">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <h1 className="text-lg font-semibold text-neutral-900">{session.title || '未命名'}</h1>
            <span className={`text-xs px-2 py-0.5 rounded-full ${st.color}`}>{st.label}</span>
          </div>
          <p className="text-xs text-neutral-400 mt-1 ml-8">
            {session.llm_model && <span className="mr-3">模型: {session.llm_model}</span>}
            创建: {new Date(session.created_at).toLocaleString('zh-CN')}
            <span className="ml-3">更新: {new Date(session.updated_at).toLocaleString('zh-CN')}</span>
          </p>
        </div>
        <div className="flex items-center gap-2">
          {canResume && !generating && resumeLabel && (
            <button onClick={handleResume}
              className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white text-sm font-medium rounded-lg">
              {resumeLabel}
            </button>
          )}
          {session.xml_content && session.cht_content && (
            <button onClick={handleDownloadZip}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg">
              打包下载
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="mb-4 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="flex gap-6">
        {/* Step nav */}
        <div className="w-40 shrink-0">
          <nav className="space-y-1">
            {STEPS.map((step, i) => {
              const available = stepAvailable(step.key)
              const active = activeStep === step.key
              return (
                <button
                  key={step.key}
                  onClick={() => available && setActiveStep(step.key)}
                  disabled={!available}
                  className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-left transition-colors ${
                    active
                      ? 'bg-blue-50 text-blue-700 font-medium'
                      : available
                        ? 'text-neutral-700 hover:bg-neutral-50'
                        : 'text-neutral-300 cursor-not-allowed'
                  }`}
                >
                  <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs shrink-0 ${
                    active ? 'bg-blue-600 text-white'
                      : available ? 'bg-neutral-200 text-neutral-600'
                        : 'bg-neutral-100 text-neutral-300'
                  }`}>{i + 1}</span>
                  {step.label}
                </button>
              )
            })}
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Generating overlay */}
          {generating && (
            <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-8 text-center">
              <div className="animate-spin w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4" />
              <p className="text-neutral-700 font-medium">正在生成...</p>
              <p className="text-sm text-neutral-500 mt-2">{genStatus}</p>
            </div>
          )}

          {/* Description */}
          {!generating && activeStep === 'description' && (
            <div className="bg-white rounded-xl border border-neutral-200 p-5">
              <h3 className="text-sm font-semibold text-neutral-900 mb-3">需求描述</h3>
              <p className="text-sm text-neutral-700 whitespace-pre-wrap leading-relaxed">
                {session.description || '无描述'}
              </p>
            </div>
          )}

          {/* Parsed data - editable when resuming */}
          {!generating && activeStep === 'parsed' && parsed && (
            resumeMode ? (
              <ConfirmationView
                data={parsed}
                onConfirm={handleConfirm}
                onReParse={() => setResumeMode(false)}
              />
            ) : (
              <div className="space-y-4">
                <ReadOnlyTable
                  title="设备清单"
                  columns={['设备名', '类型', '编号', '通信方式']}
                  rows={parsed.devices?.map((d: any) => [d.name, d.type, d.board, d.comm]) || []}
                />
                <ReadOnlyTable
                  title="功能清单"
                  columns={['功能', 'Join', '来源', '控件类型', '按钮类型', '设备', '图片']}
                  rows={parsed.functions?.map((f: any) => [
                    f.name, f.join_number, f.join_source === 'user_specified' ? '用户指定' : '自动',
                    f.control_type, f.btn_type || '-', f.device || '-', f.image || '-',
                  ]) || []}
                />
                <ReadOnlyTable
                  title="页面结构"
                  columns={['页面名', '类型', '背景图片']}
                  rows={parsed.pages?.map((p: any) => [p.name, p.type, p.bg_image || '-']) || []}
                />
                {parsed.missing_info?.length > 0 && (
                  <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                    <p className="text-sm font-medium text-amber-800 mb-1">缺失信息</p>
                    {parsed.missing_info.map((info: string, i: number) => (
                      <p key={i} className="text-sm text-amber-700">- {info}</p>
                    ))}
                  </div>
                )}
              </div>
            )
          )}

          {/* Confirmed data */}
          {!generating && activeStep === 'confirmed' && (
            <div className="space-y-4">
              {confirmed && (
                <>
                  <ReadOnlyTable
                    title="确认的设备清单"
                    columns={['设备名', '类型', '编号', '通信方式']}
                    rows={confirmed.devices?.map((d: any) => [d.name, d.type, d.board, d.comm]) || []}
                  />
                  <ReadOnlyTable
                    title="确认的页面"
                    columns={['页面名', '类型', '背景图片']}
                    rows={confirmed.pages?.map((p: any) => [p.name, p.type, p.bg_image || '-']) || []}
                  />
                </>
              )}
              {joins && (
                <ReadOnlyTable
                  title="Join 分配表"
                  columns={['功能', 'Join', '来源', '控件', '按钮类型', '设备', '动作']}
                  rows={joins.map((f: any) => [
                    f.name, f.join_number, f.join_source === 'user_specified' ? '用户指定' : '自动',
                    f.control_type, f.btn_type || '-', f.device || '-', f.action || '-',
                  ])}
                />
              )}
            </div>
          )}

          {/* Generated content */}
          {!generating && activeStep === 'generated' && (session.xml_content || session.cht_content) && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <button onClick={() => setCodeTab('xml')}
                  className={`px-3 py-1.5 text-xs rounded-md border ${
                    codeTab === 'xml' ? 'bg-blue-600 text-white border-blue-600' : 'border-neutral-300 text-neutral-600'
                  }`}>
                  Project.xml ({session.xml_content?.length || 0} chars)
                </button>
                <button onClick={() => setCodeTab('cht')}
                  className={`px-3 py-1.5 text-xs rounded-md border ${
                    codeTab === 'cht' ? 'bg-blue-600 text-white border-blue-600' : 'border-neutral-300 text-neutral-600'
                  }`}>
                  output.cht ({session.cht_content?.length || 0} chars)
                </button>
                <div className="flex-1" />
                {codeTab === 'xml' && session.xml_content && (
                  <>
                    <button onClick={() => handleCopy(session.xml_content!)} className="text-xs text-blue-600 hover:text-blue-800">复制</button>
                    <button onClick={() => handleDownload(session.xml_content!, 'Project.xml')} className="text-xs text-blue-600 hover:text-blue-800">下载</button>
                  </>
                )}
                {codeTab === 'cht' && session.cht_content && (
                  <>
                    <button onClick={() => handleCopy(session.cht_content!)} className="text-xs text-blue-600 hover:text-blue-800">复制</button>
                    <button onClick={() => handleDownload(session.cht_content!, 'output.cht')} className="text-xs text-blue-600 hover:text-blue-800">下载</button>
                  </>
                )}
              </div>
              <div className="bg-white rounded-xl border border-neutral-200 overflow-hidden" style={{ height: '480px' }}>
                <pre className="h-full overflow-auto p-3 text-xs leading-5 font-mono text-neutral-800 bg-neutral-50">
                  {(codeTab === 'xml' ? session.xml_content : session.cht_content)?.split('\n').map((line, i) => (
                    <div key={i} className="flex">
                      <span className="w-10 text-right pr-3 text-neutral-400 select-none shrink-0">{i + 1}</span>
                      <span className="whitespace-pre">{line}</span>
                    </div>
                  ))}
                </pre>
              </div>
            </div>
          )}

          {/* Validation report */}
          {!generating && activeStep === 'validation' && report && (
            <div className="bg-white rounded-xl border border-neutral-200 p-5 space-y-4">
              <div className="flex items-center gap-4">
                <h3 className="text-sm font-semibold text-neutral-900">校验报告</h3>
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  summary.critical > 0 ? 'bg-red-50 text-red-700' : 'bg-emerald-50 text-emerald-700'
                }`}>
                  Critical: {summary.critical}
                </span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-amber-50 text-amber-700">
                  Warning: {summary.warning}
                </span>
              </div>

              {report.cht_syntax && (
                <ReportSection title="CHT 语法检查" data={report.cht_syntax} />
              )}
              {report.cross_check && (
                <ReportSection title="交叉校验" data={report.cross_check} />
              )}

              {summary.critical === 0 && summary.warning === 0 && (
                <p className="text-sm text-emerald-600">校验通过，无异常</p>
              )}
            </div>
          )}

          {/* Error state */}
          {!generating && session.status === 'error' && report?.details && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm font-medium text-red-800 mb-2">错误信息</p>
              {report.details.map((d: string, i: number) => (
                <p key={i} className="text-xs text-red-700 font-mono">{d}</p>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function ReadOnlyTable({ title, columns, rows }: { title: string; columns: string[]; rows: any[][] }) {
  return (
    <div className="bg-white rounded-xl border border-neutral-200 overflow-hidden">
      <div className="px-4 py-2.5 bg-neutral-50 border-b border-neutral-200">
        <span className="text-sm font-medium text-neutral-700">{title}</span>
        <span className="ml-2 text-xs text-neutral-400">{rows.length} 项</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-neutral-50/50">
              {columns.map((col) => (
                <th key={col} className="px-3 py-2 text-xs font-medium text-neutral-500 text-left">{col}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-100">
            {rows.map((row, i) => (
              <tr key={i} className="hover:bg-neutral-50/50">
                {row.map((cell: any, j: number) => (
                  <td key={j} className="px-3 py-2 text-sm text-neutral-700">{String(cell ?? '-')}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function ReportSection({ title, data }: { title: string; data: { critical: number; warning: number; details: string[] } }) {
  if (!data.details?.length) return null
  return (
    <div>
      <p className="text-xs font-medium text-neutral-600 mb-1">
        {title}
        <span className="ml-2 text-neutral-400">({data.critical} critical, {data.warning} warning)</span>
      </p>
      <div className="text-xs text-neutral-600 space-y-0.5 max-h-48 overflow-y-auto bg-neutral-50 rounded-lg p-3 font-mono">
        {data.details.map((d, i) => (
          <p key={i}>{d}</p>
        ))}
      </div>
    </div>
  )
}

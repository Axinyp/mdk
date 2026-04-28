import { useState } from 'react'
import { errorMessage } from '../api/errors'
import { toast } from '../stores/toast'

interface ValidationReport {
  summary?: { critical: number; warning: number }
  cht_syntax?: { details: string[] }
}

interface Props {
  xml: string
  cht: string
  report: ValidationReport | null
  sessionId: string
}

type ViewMode = 'split' | 'tabs'
type ActiveTab = 'xml' | 'cht'

export default function ResultView({ xml, cht, report, sessionId }: Props) {
  const [viewMode, setViewMode] = useState<ViewMode>('split')
  const [activeTab, setActiveTab] = useState<ActiveTab>('xml')

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
    try {
      const token = localStorage.getItem('token')
      const res = await fetch(`/api/gen/sessions/${sessionId}/download`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: '下载失败' }))
        toast.error(err.detail || '下载失败')
        return
      }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `mdk_${sessionId.slice(0, 8)}.zip`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      toast.error(errorMessage(err, '下载失败'))
    }
  }

  const handleCopy = async (content: string, label: string) => {
    try {
      await navigator.clipboard.writeText(content)
      toast.success(`${label} 已复制`)
    } catch {
      toast.error('复制失败，请手动选择')
    }
  }

  const summary = report?.summary || { critical: 0, warning: 0 }
  const reportDetails = report?.cht_syntax?.details ?? []

  return (
    <div className="flex flex-col h-full gap-3 min-h-0">
      <div className="flex items-center justify-between shrink-0">
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode('split')}
            className={`px-3 py-1.5 text-xs rounded-lg border transition-colors ${
              viewMode === 'split'
                ? 'bg-blue-600 text-white border-blue-600'
                : 'border-slate-300 text-slate-700 hover:bg-slate-50'
            }`}
          >
            分栏
          </button>
          <button
            onClick={() => setViewMode('tabs')}
            className={`px-3 py-1.5 text-xs rounded-lg border transition-colors ${
              viewMode === 'tabs'
                ? 'bg-blue-600 text-white border-blue-600'
                : 'border-slate-300 text-slate-700 hover:bg-slate-50'
            }`}
          >
            标签页
          </button>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => handleDownload(xml, 'Project.xml')}
            className="px-3 py-1.5 border border-slate-300 text-slate-700 text-xs rounded-lg hover:bg-slate-50 transition-colors"
          >
            下载 XML
          </button>
          <button
            onClick={() => handleDownload(cht, 'output.cht')}
            className="px-3 py-1.5 border border-slate-300 text-slate-700 text-xs rounded-lg hover:bg-slate-50 transition-colors"
          >
            下载 .cht
          </button>
          <button
            onClick={handleDownloadZip}
            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium rounded-lg transition-colors"
          >
            打包 .zip
          </button>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex-1 flex flex-col min-h-0">
        {viewMode === 'split' ? (
          <div className="flex divide-x divide-slate-200 flex-1 min-h-0">
            <CodePanel title="Project.xml" content={xml} onCopy={() => handleCopy(xml, 'Project.xml')} />
            <CodePanel title="output.cht" content={cht} onCopy={() => handleCopy(cht, 'output.cht')} />
          </div>
        ) : (
          <>
            <div className="flex border-b border-slate-200 shrink-0">
              <button
                onClick={() => setActiveTab('xml')}
                className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
                  activeTab === 'xml' ? 'text-blue-600 border-blue-500' : 'text-slate-500 border-transparent hover:text-slate-700'
                }`}
              >
                Project.xml
              </button>
              <button
                onClick={() => setActiveTab('cht')}
                className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
                  activeTab === 'cht' ? 'text-blue-600 border-blue-500' : 'text-slate-500 border-transparent hover:text-slate-700'
                }`}
              >
                output.cht
              </button>
            </div>
            <div className="flex-1 min-h-0 flex">
              {activeTab === 'xml'
                ? <CodePanel title="" content={xml} onCopy={() => handleCopy(xml, 'Project.xml')} />
                : <CodePanel title="" content={cht} onCopy={() => handleCopy(cht, 'output.cht')} />
              }
            </div>
          </>
        )}
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 shrink-0">
        <div className="flex items-center gap-3 flex-wrap">
          <h3 className="text-sm font-semibold text-slate-900">校验报告</h3>
          <span className={`text-xs px-2 py-0.5 rounded-full ${
            summary.critical > 0 ? 'bg-red-50 text-red-700' : 'bg-emerald-50 text-emerald-700'
          }`}>
            Critical: {summary.critical}
          </span>
          <span className={`text-xs px-2 py-0.5 rounded-full ${
            summary.warning > 0 ? 'bg-amber-50 text-amber-700' : 'bg-slate-100 text-slate-600'
          }`}>
            Warning: {summary.warning}
          </span>
        </div>
        {reportDetails.length > 0 && (
          <div className="text-xs text-slate-600 space-y-1 max-h-40 overflow-y-auto mt-3">
            {reportDetails.map((d, i) => <p key={i}>{d}</p>)}
          </div>
        )}
        {summary.critical === 0 && summary.warning === 0 && (
          <p className="text-sm text-emerald-600 mt-2">校验通过，无异常</p>
        )}
      </div>
    </div>
  )
}

function CodePanel({ title, content, onCopy }: { title: string; content: string; onCopy: () => void }) {
  return (
    <div className="flex-1 flex flex-col min-w-0">
      {title && (
        <div className="flex items-center justify-between px-3 py-2 bg-slate-50 border-b border-slate-200 shrink-0">
          <span className="text-xs font-medium text-slate-600">{title}</span>
          <button onClick={onCopy} className="text-xs text-blue-600 hover:text-blue-800 transition-colors">复制</button>
        </div>
      )}
      <pre className="flex-1 overflow-auto p-3 text-xs leading-5 font-mono text-slate-800 bg-slate-50 min-h-0">
        {content.split('\n').map((line, i) => (
          <div key={i} className="flex">
            <span className="w-10 text-right pr-3 text-slate-400 select-none shrink-0">{i + 1}</span>
            <span className="whitespace-pre">{line}</span>
          </div>
        ))}
      </pre>
    </div>
  )
}

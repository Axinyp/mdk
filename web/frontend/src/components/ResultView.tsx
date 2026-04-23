import { useState } from 'react'

interface Props {
  xml: string
  cht: string
  report: any
  sessionId: string
  onReset: () => void
}

type ViewMode = 'split' | 'tabs'
type ActiveTab = 'xml' | 'cht'

export default function ResultView({ xml, cht, report, sessionId, onReset }: Props) {
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
    const token = localStorage.getItem('token')
    const res = await fetch(`/api/gen/sessions/${sessionId}/download`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `mdk_${sessionId.slice(0, 8)}.zip`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleCopy = (content: string) => {
    navigator.clipboard.writeText(content)
  }

  const summary = report?.summary || { critical: 0, warning: 0 }

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode('split')}
            className={`px-3 py-1.5 text-xs rounded-md border ${
              viewMode === 'split' ? 'bg-blue-600 text-white border-blue-600' : 'border-neutral-300 text-neutral-600'
            }`}
          >
            分栏
          </button>
          <button
            onClick={() => setViewMode('tabs')}
            className={`px-3 py-1.5 text-xs rounded-md border ${
              viewMode === 'tabs' ? 'bg-blue-600 text-white border-blue-600' : 'border-neutral-300 text-neutral-600'
            }`}
          >
            标签页
          </button>
        </div>
        <button onClick={onReset} className="text-sm text-neutral-500 hover:text-blue-600">
          新建生成
        </button>
      </div>

      {/* Code preview */}
      <div className="bg-white rounded-xl shadow-sm border border-neutral-200 overflow-hidden">
        {viewMode === 'split' ? (
          <div className="flex divide-x divide-neutral-200" style={{ height: '500px' }}>
            <CodePanel title="Project.xml" content={xml} onCopy={() => handleCopy(xml)} />
            <CodePanel title="output.cht" content={cht} onCopy={() => handleCopy(cht)} />
          </div>
        ) : (
          <>
            <div className="flex border-b border-neutral-200">
              <button
                onClick={() => setActiveTab('xml')}
                className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${
                  activeTab === 'xml' ? 'text-blue-600 border-blue-500' : 'text-neutral-500 border-transparent'
                }`}
              >
                Project.xml
              </button>
              <button
                onClick={() => setActiveTab('cht')}
                className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${
                  activeTab === 'cht' ? 'text-blue-600 border-blue-500' : 'text-neutral-500 border-transparent'
                }`}
              >
                output.cht
              </button>
            </div>
            <div style={{ height: '500px' }}>
              {activeTab === 'xml'
                ? <CodePanel title="" content={xml} onCopy={() => handleCopy(xml)} />
                : <CodePanel title="" content={cht} onCopy={() => handleCopy(cht)} />
              }
            </div>
          </>
        )}
      </div>

      {/* Validation report */}
      <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-4">
        <div className="flex items-center gap-4 mb-3">
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
        {report?.cht_syntax?.details?.length > 0 && (
          <div className="text-xs text-neutral-600 space-y-1 max-h-40 overflow-y-auto">
            {report.cht_syntax.details.map((d: string, i: number) => (
              <p key={i}>{d}</p>
            ))}
          </div>
        )}
        {summary.critical === 0 && summary.warning === 0 && (
          <p className="text-sm text-emerald-600">校验通过，无异常</p>
        )}
      </div>

      {/* Download bar */}
      <div className="flex gap-3">
        <button onClick={() => handleDownload(xml, 'Project.xml')}
          className="px-4 py-2 border border-neutral-300 text-sm rounded-lg hover:bg-neutral-50">
          下载 XML
        </button>
        <button onClick={() => handleDownload(cht, 'output.cht')}
          className="px-4 py-2 border border-neutral-300 text-sm rounded-lg hover:bg-neutral-50">
          下载 .cht
        </button>
        <button onClick={handleDownloadZip}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg">
          打包下载 .zip
        </button>
      </div>
    </div>
  )
}

function CodePanel({ title, content, onCopy }: { title: string; content: string; onCopy: () => void }) {
  return (
    <div className="flex-1 flex flex-col min-w-0">
      {title && (
        <div className="flex items-center justify-between px-3 py-2 bg-neutral-50 border-b border-neutral-200">
          <span className="text-xs font-medium text-neutral-600">{title}</span>
          <button onClick={onCopy} className="text-xs text-blue-600 hover:text-blue-800">复制</button>
        </div>
      )}
      <pre className="flex-1 overflow-auto p-3 text-xs leading-5 font-mono text-neutral-800 bg-neutral-50">
        {content.split('\n').map((line, i) => (
          <div key={i} className="flex">
            <span className="w-10 text-right pr-3 text-neutral-400 select-none shrink-0">{i + 1}</span>
            <span className="whitespace-pre">{line}</span>
          </div>
        ))}
      </pre>
    </div>
  )
}

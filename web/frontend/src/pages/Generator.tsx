import { useState } from 'react'
import api from '../api/client'
import ConfirmationView from '../components/ConfirmationView'
import ResultView from '../components/ResultView'

type Stage = 'input' | 'parsing' | 'confirm' | 'generating' | 'result'

interface ParsedData {
  devices: any[]
  functions: any[]
  pages: any[]
  missing_info: string[]
  image_path: string | null
}

export default function Generator() {
  const [description, setDescription] = useState('')
  const [stage, setStage] = useState<Stage>('input')
  const [sessionId, setSessionId] = useState('')
  const [parsedData, setParsedData] = useState<ParsedData | null>(null)
  const [result, setResult] = useState<{ xml: string; cht: string; report: any } | null>(null)
  const [error, setError] = useState('')
  const [genStatus, setGenStatus] = useState('')
  const [showPrevDesc, setShowPrevDesc] = useState(false)

  const handleParse = async () => {
    if (!description.trim()) return
    setError('')
    setStage('parsing')
    try {
      const { data: session } = await api.post('/gen/sessions', { description })
      setSessionId(session.id)
      const { data: parseResult } = await api.post(`/gen/sessions/${session.id}/parse`)
      setParsedData(parseResult.data)
      setStage('confirm')
    } catch (err: any) {
      setError(err.response?.data?.detail || '解析失败')
      setStage('input')
    }
  }

  const handleConfirm = async (data: ParsedData) => {
    setError('')
    setStage('generating')
    try {
      await api.post(`/gen/sessions/${sessionId}/confirm`, { data })
      const response = await fetch(`/api/gen/sessions/${sessionId}/generate`, {
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
            if (event === 'status') continue
            if (event === 'error') {
              setError('生成失败')
              setStage('input')
              return
            }
          }
          if (line.startsWith('data: ')) {
            try {
              const payload = JSON.parse(line.replace('data: ', ''))
              if (typeof payload === 'string') {
                setGenStatus(payload)
              } else {
                setGenStatus(JSON.stringify(payload))
              }
            } catch { /* skip */ }
          }
        }
      }

      const { data: resultData } = await api.get(`/gen/sessions/${sessionId}/result`)
      setResult({
        xml: resultData.xml_content,
        cht: resultData.cht_content,
        report: resultData.validation_report,
      })
      setStage('result')
    } catch (err: any) {
      setError(err.response?.data?.detail || '生成失败')
      setStage('confirm')
    }
  }

  const handleReset = () => {
    setStage('input')
    setParsedData(null)
    setResult(null)
    setSessionId('')
    setGenStatus('')
    setError('')
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Step indicator */}
      <div className="flex items-center gap-2 mb-6">
        {['描述需求', '确认清单', '生成中', '查看结果'].map((label, i) => {
          const stageMap: Stage[] = ['input', 'confirm', 'generating', 'result']
          const current = stageMap.indexOf(stage === 'parsing' ? 'input' : stage)
          return (
            <div key={label} className="flex items-center gap-2">
              <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-medium ${
                i <= current ? 'bg-blue-600 text-white' : 'bg-neutral-200 text-neutral-500'
              }`}>
                {i + 1}
              </div>
              <span className={`text-sm ${i <= current ? 'text-neutral-900' : 'text-neutral-400'}`}>
                {label}
              </span>
              {i < 3 && <div className="w-8 h-px bg-neutral-200" />}
            </div>
          )
        })}
      </div>

      {error && (
        <div className="mb-4 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Previous step context */}
      {stage !== 'input' && stage !== 'parsing' && description && (
        <div className="mb-4 bg-neutral-50 rounded-lg border border-neutral-200 overflow-hidden">
          <button
            onClick={() => setShowPrevDesc(!showPrevDesc)}
            className="w-full px-4 py-2.5 flex items-center justify-between text-left hover:bg-neutral-100 transition-colors"
          >
            <div className="flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-neutral-200 text-neutral-600 flex items-center justify-center text-xs">1</span>
              <span className="text-sm text-neutral-600 font-medium">需求描述</span>
            </div>
            <svg className={`w-4 h-4 text-neutral-400 transition-transform ${showPrevDesc ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {showPrevDesc && (
            <div className="px-4 pb-3 border-t border-neutral-200 pt-2">
              <p className="text-sm text-neutral-700 whitespace-pre-wrap leading-relaxed max-h-40 overflow-y-auto">{description}</p>
            </div>
          )}
        </div>
      )}

      {/* Stage: Input */}
      {(stage === 'input' || stage === 'parsing') && (
        <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6">
          <h2 className="text-lg font-semibold text-neutral-900 mb-4">描述您的中控需求</h2>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="例如：我需要用 TS-9101 控制 4 路灯光，触摸屏编号 10，继电器编号 1，灯光 1 连接号 103，灯光 2 连接号 105，实现全开全关和单独控制..."
            className="w-full min-h-[200px] px-4 py-3 border border-neutral-200 rounded-lg text-sm resize-y focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <div className="mt-4 flex justify-end">
            <button
              onClick={handleParse}
              disabled={stage === 'parsing' || !description.trim()}
              className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
            >
              {stage === 'parsing' ? '正在解析...' : '开始解析'}
            </button>
          </div>
        </div>
      )}

      {/* Stage: Confirm */}
      {stage === 'confirm' && parsedData && (
        <ConfirmationView
          data={parsedData}
          onConfirm={handleConfirm}
          onReParse={() => setStage('input')}
        />
      )}

      {/* Stage: Generating */}
      {stage === 'generating' && (
        <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-8 text-center">
          <div className="animate-spin w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-neutral-700 font-medium">正在生成...</p>
          <p className="text-sm text-neutral-500 mt-2">{genStatus}</p>
        </div>
      )}

      {/* Stage: Result */}
      {stage === 'result' && result && (
        <ResultView
          xml={result.xml}
          cht={result.cht}
          report={result.report}
          sessionId={sessionId}
          onReset={handleReset}
        />
      )}
    </div>
  )
}

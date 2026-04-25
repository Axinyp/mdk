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

const STEPS = ['描述需求', '确认清单', '生成中', '查看结果']
const STAGE_TO_STEP: Record<Stage, number> = {
  input: 0, parsing: 0, confirm: 1, generating: 2, result: 3,
}

export default function Generator() {
  const [description, setDescription] = useState('')
  const [supplement, setSupplement] = useState('')
  const [stage, setStage] = useState<Stage>('input')
  const [viewStep, setViewStep] = useState(0)
  const [sessionId, setSessionId] = useState('')
  const [parsedData, setParsedData] = useState<ParsedData | null>(null)
  const [result, setResult] = useState<{ xml: string; cht: string; report: any } | null>(null)
  const [error, setError] = useState('')
  const [genStatus, setGenStatus] = useState('')

  const currentStep = STAGE_TO_STEP[stage]

  const handleParse = async (desc?: string) => {
    const finalDesc = desc ?? (supplement.trim() ? `${description}\n\n补充信息：\n${supplement}` : description)
    if (!finalDesc.trim()) return
    setError('')
    setSupplement('')
    setStage('parsing')
    try {
      const { data: session } = await api.post('/gen/sessions', { description: finalDesc })
      setSessionId(session.id)
      const { data: parseResult } = await api.post(`/gen/sessions/${session.id}/parse`)
      setParsedData(parseResult.data)
      setStage('confirm')
      setViewStep(1)
    } catch (err: any) {
      setError(err.response?.data?.detail || '解析失败')
      setStage('input')
      setViewStep(0)
    }
  }

  const handleConfirm = async (data: ParsedData) => {
    setError('')
    setStage('generating')
    setViewStep(2)
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
            if (event === 'error') {
              setError('生成失败')
              setStage('confirm')
              setViewStep(1)
              return
            }
          }
          if (line.startsWith('data: ')) {
            try {
              const payload = JSON.parse(line.replace('data: ', ''))
              setGenStatus(typeof payload === 'string' ? payload : JSON.stringify(payload))
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
      setViewStep(3)
    } catch (err: any) {
      setError(err.response?.data?.detail || '生成失败')
      setStage('confirm')
      setViewStep(1)
    }
  }

  const handleReset = () => {
    setStage('input')
    setViewStep(0)
    setParsedData(null)
    setResult(null)
    setSessionId('')
    setGenStatus('')
    setError('')
    setDescription('')
    setSupplement('')
  }

  const canViewStep = (i: number) => i <= currentStep

  return (
    <div className="max-w-6xl mx-auto">
      {/* Step indicator — clickable */}
      <div className="flex items-center gap-2 mb-6">
        {STEPS.map((label, i) => {
          const done = i < currentStep
          const active = i === currentStep
          const clickable = canViewStep(i) && i !== currentStep
          return (
            <div key={label} className="flex items-center gap-2">
              <button
                onClick={() => clickable && setViewStep(i)}
                disabled={!canViewStep(i)}
                className={`flex items-center gap-2 rounded-lg px-2 py-1 transition-colors ${
                  clickable ? 'hover:bg-neutral-100 cursor-pointer' : 'cursor-default'
                }`}
              >
                <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-medium transition-colors ${
                  viewStep === i
                    ? 'bg-blue-600 text-white ring-2 ring-blue-300'
                    : done
                      ? 'bg-blue-100 text-blue-700'
                      : active
                        ? 'bg-blue-600 text-white'
                        : 'bg-neutral-200 text-neutral-500'
                }`}>
                  {done && viewStep !== i ? (
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : i + 1}
                </div>
                <span className={`text-sm ${active || viewStep === i ? 'text-neutral-900 font-medium' : done ? 'text-blue-700' : 'text-neutral-400'}`}>
                  {label}
                </span>
              </button>
              {i < STEPS.length - 1 && <div className="w-8 h-px bg-neutral-200" />}
            </div>
          )
        })}
      </div>

      {error && (
        <div className="mb-4 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Step 0: 描述需求 */}
      {viewStep === 0 && (
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
              onClick={() => handleParse(description)}
              disabled={stage === 'parsing' || !description.trim()}
              className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
            >
              {stage === 'parsing' ? '正在解析...' : '开始解析'}
            </button>
          </div>
        </div>
      )}

      {/* Step 0 回看：已解析后点击 step1 返回查看描述，并可补充信息 */}
      {viewStep === 0 && currentStep > 0 && (
        <div className="mt-4 space-y-4">
          <div className="bg-white rounded-xl border border-neutral-200 p-5">
            <p className="text-xs font-medium text-neutral-500 mb-2">已提交的需求描述</p>
            <p className="text-sm text-neutral-700 whitespace-pre-wrap leading-relaxed">{description}</p>
          </div>

          {/* 缺失信息 + 补充输入 */}
          {parsedData?.missing_info && parsedData.missing_info.length > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
              <p className="text-sm font-medium text-amber-800 mb-2">解析时发现缺失信息，请补充后重新解析：</p>
              <ul className="mb-3 space-y-1">
                {parsedData.missing_info.map((info, i) => (
                  <li key={i} className="text-sm text-amber-700">• {info}</li>
                ))}
              </ul>
              <textarea
                value={supplement}
                onChange={(e) => setSupplement(e.target.value)}
                placeholder="在此补充缺失的信息..."
                className="w-full min-h-[100px] px-3 py-2 border border-amber-300 rounded-lg text-sm resize-y focus:outline-none focus:ring-2 focus:ring-amber-400 bg-white"
              />
              <div className="mt-3 flex justify-end">
                <button
                  onClick={() => handleParse()}
                  disabled={stage === 'parsing' || !supplement.trim()}
                  className="px-5 py-2 bg-amber-500 hover:bg-amber-600 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                >
                  {stage === 'parsing' ? '正在解析...' : '补充后重新解析'}
                </button>
              </div>
            </div>
          )}

          <div className="flex justify-end">
            <button
              onClick={() => setViewStep(currentStep)}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              返回当前步骤 →
            </button>
          </div>
        </div>
      )}

      {/* Step 1: 确认清单 */}
      {viewStep === 1 && parsedData && (
        <ConfirmationView
          data={parsedData}
          onConfirm={handleConfirm}
          onReParse={() => setViewStep(0)}
        />
      )}

      {/* Step 2: 生成中 */}
      {viewStep === 2 && (
        <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-8 text-center">
          {stage === 'generating' ? (
            <>
              <div className="animate-spin w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4" />
              <p className="text-neutral-700 font-medium">正在生成...</p>
              <p className="text-sm text-neutral-500 mt-2">{genStatus}</p>
            </>
          ) : (
            <>
              <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-4">
                <svg className="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <p className="text-neutral-700 font-medium">生成已完成</p>
              <button onClick={() => setViewStep(3)} className="mt-3 text-sm text-blue-600 hover:text-blue-800">
                查看生成结果 →
              </button>
            </>
          )}
        </div>
      )}

      {/* Step 3: 查看结果 */}
      {viewStep === 3 && result && (
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

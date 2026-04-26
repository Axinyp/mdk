import { useEffect, useRef, useState } from 'react'
import api from '../api/client'
import ConfirmationView from '../components/ConfirmationView'
import ResultView from '../components/ResultView'

interface ParsedData {
  devices: any[]
  functions: any[]
  pages: any[]
  missing_info: string[]
  image_path: string | null
}

interface ChatMessage {
  id: number | string
  role: 'user' | 'assistant'
  kind: string
  content: string
  created_at?: string
}

type SessionStatus =
  | 'idle' | 'creating' | 'parsing' | 'clarifying'
  | 'parsed' | 'generating' | 'completed' | 'error'

const STATUS_BADGE: Record<string, { label: string; cls: string }> = {
  idle:       { label: '待描述',  cls: 'bg-slate-100 text-slate-500' },
  creating:   { label: '初始化', cls: 'bg-slate-100 text-slate-500' },
  parsing:    { label: '解析中', cls: 'bg-blue-100 text-blue-700' },
  clarifying: { label: '追问中', cls: 'bg-orange-100 text-orange-700' },
  parsed:     { label: '已解析', cls: 'bg-blue-100 text-blue-700' },
  generating: { label: '生成中', cls: 'bg-purple-100 text-purple-700 animate-pulse' },
  completed:  { label: '已完成', cls: 'bg-emerald-100 text-emerald-700' },
  error:      { label: '出错了', cls: 'bg-red-100 text-red-700' },
}

const WELCOME: ChatMessage = {
  id: '__welcome__',
  role: 'assistant',
  kind: 'system',
  content: '您好！请描述您的中控需求，例如设备清单、品牌型号、控制功能等。我会帮您自动生成中控程序。',
}

export default function Generator() {
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME])
  const [sessionId, setSessionId] = useState('')
  const [sessionStatus, setSessionStatus] = useState<SessionStatus>('idle')
  const [parsedData, setParsedData] = useState<ParsedData | null>(null)
  const [result, setResult] = useState<{ xml: string; cht: string; report: any } | null>(null)
  const [inputText, setInputText] = useState('')
  const [isThinking, setIsThinking] = useState(false)
  const [genStatus, setGenStatus] = useState('')
  const [error, setError] = useState('')

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const appendMessage = (msg: ChatMessage) => {
    setMessages(prev => {
      if (prev.some(m => m.id === msg.id)) return prev
      return [...prev, msg]
    })
  }

  const handleSend = async () => {
    const text = inputText.trim()
    if (!text || isThinking) return
    setInputText('')
    setError('')

    const userMsg: ChatMessage = {
      id: `local_${Date.now()}`,
      role: 'user',
      kind: sessionId ? 'answer' : 'description',
      content: text,
    }
    appendMessage(userMsg)
    setIsThinking(true)

    try {
      if (!sessionId) {
        await startNewSession(text)
      } else {
        await sendReply(text)
      }
    } catch (e: any) {
      setError(e.response?.data?.detail || String(e.message || '操作失败'))
      setSessionStatus('error')
    } finally {
      setIsThinking(false)
    }
  }

  const startNewSession = async (description: string) => {
    setSessionStatus('creating')
    const { data: session } = await api.post('/gen/sessions', { description })
    setSessionId(session.id)
    setSessionStatus('parsing')

    const { data: parseResult } = await api.post(`/gen/sessions/${session.id}/parse`)
    const pd: ParsedData = parseResult.parsed_data ?? parseResult.data
    setParsedData(pd)

    const { data: history } = await api.get(`/gen/sessions/${session.id}/messages`)
    syncMessages(history)

    const newStatus: SessionStatus = (pd.missing_info?.length > 0) ? 'clarifying' : 'parsed'
    setSessionStatus(newStatus)
  }

  const sendReply = async (content: string) => {
    setSessionStatus('parsing')
    const { data } = await api.post(`/gen/sessions/${sessionId}/messages`, { content })
    const pd: ParsedData = data.parsed_data
    setParsedData(pd)
    syncMessages(data.messages)
    const newStatus: SessionStatus = (pd.missing_info?.length > 0) ? 'clarifying' : 'parsed'
    setSessionStatus(newStatus)
  }

  const syncMessages = (serverMessages: any[]) => {
    setMessages(prev => {
      const existingIds = new Set(prev.map(m => m.id))
      const newOnes = serverMessages.filter((m: any) => !existingIds.has(m.id))
      return [...prev, ...newOnes]
    })
  }

  const handleConfirm = async (data: ParsedData) => {
    setError('')
    setSessionStatus('generating')
    setGenStatus('正在生成 Project.xml...')
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
          if (line.startsWith('event: error')) {
            setError('生成失败')
            setSessionStatus('error')
            return
          }
          if (line.startsWith('data: ')) {
            try {
              const payload = JSON.parse(line.replace('data: ', ''))
              if (typeof payload === 'string') setGenStatus(payload)
              else if (payload?.status) setGenStatus(payload.status)
            } catch { /* skip */ }
          }
        }
      }
      const { data: resultData } = await api.get(`/gen/sessions/${sessionId}/result`)
      setResult({ xml: resultData.xml_content, cht: resultData.cht_content, report: resultData.validation_report })
      setSessionStatus('completed')

      const summary: ChatMessage = {
        id: `gen_done_${Date.now()}`,
        role: 'assistant',
        kind: 'summary',
        content: '生成完成！Project.xml 和 .cht 文件已准备好，可在右侧查看和下载。',
      }
      appendMessage(summary)
    } catch (e: any) {
      setError(e.response?.data?.detail || '生成失败')
      setSessionStatus('error')
    }
  }

  const handleReset = () => {
    setMessages([WELCOME])
    setSessionId('')
    setSessionStatus('idle')
    setParsedData(null)
    setResult(null)
    setInputText('')
    setGenStatus('')
    setError('')
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const canSend = inputText.trim().length > 0 && !isThinking &&
    sessionStatus !== 'generating' && sessionStatus !== 'completed'

  const showConfirmPanel = sessionStatus === 'parsed' && parsedData && !result
  const showResultPanel = sessionStatus === 'completed' && result
  const badge = STATUS_BADGE[sessionStatus] ?? STATUS_BADGE.idle

  return (
    <div className="flex gap-4 h-[calc(100vh-7rem)]" style={{ fontFamily: "'Plus Jakarta Sans', sans-serif" }}>
      {/* ── 左栏：对话区 ── */}
      <div className="flex flex-col w-[55%] min-w-0">
        {/* 消息流 */}
        <div className="flex-1 overflow-y-auto space-y-3 pr-1 pb-2">
          {messages.map((msg, idx) => (
            <MessageBubble key={`${msg.id}_${idx}`} message={msg} />
          ))}
          {isThinking && <ThinkingBubble />}
          <div ref={messagesEndRef} />
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="mb-2 px-3 py-2 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            {error}
          </div>
        )}

        {/* 输入区 */}
        {sessionStatus !== 'completed' && (
          <div className="border border-slate-200 rounded-xl bg-white overflow-hidden shadow-sm">
            <textarea
              ref={textareaRef}
              value={inputText}
              onChange={e => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                sessionStatus === 'clarifying'
                  ? '请补充缺失的信息（Enter 发送，Shift+Enter 换行）...'
                  : '描述您的中控需求（Enter 发送，Shift+Enter 换行）...'
              }
              rows={3}
              className="w-full px-4 pt-3 pb-1 text-sm text-slate-800 placeholder-slate-400 resize-none focus:outline-none"
              style={{ maxHeight: '120px' }}
            />
            <div className="flex justify-end px-3 pb-2">
              <button
                onClick={handleSend}
                disabled={!canSend}
                className="flex items-center gap-1.5 px-4 py-1.5 bg-slate-700 hover:bg-slate-900 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {isThinking ? (
                  <>
                    <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    处理中
                  </>
                ) : '发送'}
              </button>
            </div>
          </div>
        )}

        {sessionStatus === 'completed' && (
          <button
            onClick={handleReset}
            className="mt-2 w-full py-2 border border-slate-300 text-slate-600 text-sm rounded-xl hover:bg-slate-50 transition-colors"
          >
            开始新会话
          </button>
        )}
      </div>

      {/* ── 右栏：元数据 / 操作区 ── */}
      <div className="flex flex-col w-[45%] min-w-0 gap-3">
        {/* 状态徽章 + 会话信息 */}
        <div className="flex items-center justify-between px-4 py-2.5 bg-white border border-slate-200 rounded-xl shadow-sm">
          <div className="flex items-center gap-2">
            <span className={`text-xs font-medium px-2.5 py-0.5 rounded-full ${badge.cls}`}>
              {badge.label}
            </span>
            {sessionId && (
              <span className="text-xs text-slate-400 font-mono">#{sessionId.slice(0, 8)}</span>
            )}
          </div>
          {sessionStatus === 'generating' && (
            <span className="text-xs text-slate-500">{genStatus}</span>
          )}
        </div>

        {/* 解析结果 / 确认面板 */}
        {showConfirmPanel && (
          <div className="flex-1 overflow-y-auto">
            <ConfirmationView
              data={parsedData}
              onConfirm={handleConfirm}
              onReParse={handleReset}
            />
          </div>
        )}

        {/* 生成结果面板 */}
        {showResultPanel && (
          <div className="flex-1 overflow-y-auto">
            <ResultView
              xml={result.xml}
              cht={result.cht}
              report={result.report}
              sessionId={sessionId}
              onReset={handleReset}
            />
          </div>
        )}

        {/* 等待状态占位 */}
        {!showConfirmPanel && !showResultPanel && (
          <div className="flex-1 flex flex-col items-center justify-center bg-white border border-slate-200 rounded-xl text-center p-8">
            {sessionStatus === 'idle' && (
              <>
                <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mb-3">
                  <svg className="w-6 h-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                      d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18" />
                  </svg>
                </div>
                <p className="text-sm text-slate-500">在左侧输入需求描述后，<br />解析结果将在此处显示</p>
              </>
            )}
            {(sessionStatus === 'parsing' || sessionStatus === 'creating') && (
              <>
                <div className="w-8 h-8 border-3 border-slate-300 border-t-slate-700 rounded-full animate-spin mb-3" />
                <p className="text-sm text-slate-500">正在解析需求...</p>
              </>
            )}
            {sessionStatus === 'clarifying' && (
              <>
                <div className="w-12 h-12 rounded-full bg-orange-50 flex items-center justify-center mb-3">
                  <svg className="w-6 h-6 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                      d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <p className="text-sm text-slate-500">请在左侧回答追问<br />补全信息后将自动解析</p>
              </>
            )}
            {sessionStatus === 'generating' && (
              <>
                <div className="w-8 h-8 border-3 border-purple-200 border-t-purple-600 rounded-full animate-spin mb-3" />
                <p className="text-sm text-slate-500">{genStatus || '正在生成...'}</p>
              </>
            )}
            {sessionStatus === 'error' && (
              <p className="text-sm text-red-500">生成出错，请重试或新建会话</p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user'
  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] bg-slate-700 text-white text-sm rounded-2xl rounded-tr-sm px-4 py-3 leading-relaxed whitespace-pre-wrap">
          {message.content}
        </div>
      </div>
    )
  }
  const isClarification = message.kind === 'clarification'
  return (
    <div className="flex items-start gap-2.5">
      <div className="w-7 h-7 rounded-full bg-slate-700 text-white flex items-center justify-center shrink-0 mt-0.5 text-xs font-bold">
        AI
      </div>
      <div className={`max-w-[85%] text-sm rounded-2xl rounded-tl-sm px-4 py-3 leading-relaxed whitespace-pre-wrap shadow-sm ${
        isClarification
          ? 'bg-orange-50 border border-orange-200 text-orange-900'
          : 'bg-white border border-slate-200 text-slate-700'
      }`}>
        {message.content}
      </div>
    </div>
  )
}

function ThinkingBubble() {
  return (
    <div className="flex items-start gap-2.5">
      <div className="w-7 h-7 rounded-full bg-slate-700 text-white flex items-center justify-center shrink-0 text-xs font-bold">
        AI
      </div>
      <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
        <div className="flex gap-1 items-center h-4">
          <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
          <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
          <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    </div>
  )
}

import { useRef, useState } from 'react'
import api from '../api/client'
import { errorMessage } from '../api/errors'

interface Props {
  /** When provided, the submission is bound to that session; otherwise it is standalone. */
  sessionId?: string
  deviceHint?: string
  onClose: () => void
  onSubmitted?: () => void
}

type UploadTab = 'paste' | 'file'
type SubmitStatus = 'idle' | 'submitting' | 'pending_review' | 'error'

const MAX_FILE_MB = 10
const ACCEPT_MIME = ['text/plain', 'text/markdown', 'application/pdf']
const ACCEPT_EXT = '.txt,.md,.pdf'

export default function ProtocolUploadDrawer({ sessionId, deviceHint = '', onClose, onSubmitted }: Props) {
  const [tab, setTab] = useState<UploadTab>('paste')
  const [pasteText, setPasteText] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [dragging, setDragging] = useState(false)
  const [brand, setBrand] = useState('')
  const [model, setModel] = useState(() => deviceHint)
  const [status, setStatus] = useState<SubmitStatus>('idle')
  const [errorMsg, setErrorMsg] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const canSubmit = status === 'idle' && brand.trim() && model.trim() &&
    (tab === 'paste' ? pasteText.trim().length > 20 : file !== null)

  const handleFile = (f: File) => {
    if (f.size > MAX_FILE_MB * 1024 * 1024) {
      setErrorMsg(`文件不能超过 ${MAX_FILE_MB}MB`)
      return
    }
    if (!ACCEPT_MIME.includes(f.type) && !f.name.match(/\.(txt|md|pdf)$/i)) {
      setErrorMsg('仅支持 .txt .md .pdf 格式')
      return
    }
    setErrorMsg('')
    setFile(f)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f) handleFile(f)
  }

  const handleSubmit = async () => {
    if (!canSubmit) return
    setStatus('submitting')
    setErrorMsg('')
    try {
      const formData = new FormData()
      formData.append('brand', brand.trim())
      formData.append('model', model.trim())
      if (tab === 'paste') {
        formData.append('source_type', 'paste')
        formData.append('raw_content', pasteText.trim())
      } else if (file) {
        formData.append('source_type', 'file')
        formData.append('file', file)
      }
      const url = sessionId
        ? `/gen/sessions/${sessionId}/protocol-submissions`
        : '/protocols/submissions'
      await api.post(url, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setStatus('pending_review')
      onSubmitted?.()
    } catch (e) {
      setErrorMsg(errorMessage(e, '提交失败，请稍后重试'))
      setStatus('error')
    }
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-900/40 backdrop-blur-[2px] z-40"
        onClick={onClose}
      />

      {/* Drawer panel */}
      <div className="fixed right-0 top-0 bottom-0 w-[480px] bg-white shadow-2xl border-l border-slate-200 z-50 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 shrink-0">
          <div>
            <h2 className="text-base font-semibold text-slate-800">提交协议文档</h2>
            <p className="text-xs text-slate-400 mt-0.5">提交后将由研发人员审核并入库</p>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Submitted state */}
        {status === 'pending_review' ? (
          <div className="flex-1 flex flex-col items-center justify-center px-8 text-center">
            <div className="relative mb-5">
              <div className="w-14 h-14 rounded-full bg-orange-100 flex items-center justify-center">
                <svg className="w-7 h-7 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-orange-400 animate-ping opacity-75" />
              <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-orange-400" />
            </div>
            <p className="text-sm font-semibold text-slate-800 mb-1">提交成功，审核中</p>
            <p className="text-xs text-slate-500 leading-relaxed">
              研发人员将在工作日内完成审核。<br />审核通过后该协议将自动入库，后续生成时可直接使用。
            </p>
            <button
              onClick={onClose}
              className="mt-6 px-5 py-2 border border-slate-300 text-slate-700 text-sm rounded-lg hover:bg-slate-50 transition-colors cursor-pointer"
            >
              关闭
            </button>
          </div>
        ) : (
          <>
            {/* Scrollable content */}
            <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5">
              {/* Tab switcher */}
              <div className="flex bg-slate-100 rounded-lg p-0.5">
                {(['paste', 'file'] as UploadTab[]).map(t => (
                  <button
                    key={t}
                    onClick={() => setTab(t)}
                    className={`flex-1 py-1.5 text-sm font-medium rounded-[7px] transition-all cursor-pointer ${
                      tab === t
                        ? 'bg-white shadow-sm text-slate-800'
                        : 'text-slate-500 hover:text-slate-700'
                    }`}
                  >
                    {t === 'paste' ? '粘贴文本' : '上传文件'}
                  </button>
                ))}
              </div>

              {/* Paste tab */}
              {tab === 'paste' && (
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1.5">协议内容</label>
                  <textarea
                    value={pasteText}
                    onChange={e => setPasteText(e.target.value)}
                    placeholder="粘贴设备说明书中的通信协议部分，例如串口指令表、IR码表等..."
                    rows={10}
                    className="w-full px-3 py-2.5 text-sm text-slate-800 bg-slate-50 border border-slate-200 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-slate-400"
                  />
                  <p className="text-xs text-slate-400 mt-1">{pasteText.length} 字符</p>
                </div>
              )}

              {/* File tab */}
              {tab === 'file' && (
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1.5">选择文件</label>
                  <div
                    onDragOver={e => { e.preventDefault(); setDragging(true) }}
                    onDragLeave={() => setDragging(false)}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                    className={`border-2 border-dashed rounded-xl px-6 py-10 flex flex-col items-center justify-center cursor-pointer transition-colors ${
                      dragging
                        ? 'border-blue-400 bg-blue-50'
                        : file
                        ? 'border-emerald-300 bg-emerald-50'
                        : 'border-slate-300 bg-slate-50 hover:border-blue-400 hover:bg-blue-50/40'
                    }`}
                  >
                    {file ? (
                      <>
                        <svg className="w-8 h-8 text-emerald-500 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <p className="text-sm font-medium text-emerald-700">{file.name}</p>
                        <p className="text-xs text-emerald-500 mt-0.5">{(file.size / 1024).toFixed(0)} KB</p>
                        <button
                          onClick={e => { e.stopPropagation(); setFile(null) }}
                          className="mt-2 text-xs text-slate-400 hover:text-red-400 transition-colors"
                        >
                          移除
                        </button>
                      </>
                    ) : (
                      <>
                        <svg className="w-8 h-8 text-slate-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                        </svg>
                        <p className="text-sm text-slate-500">拖拽文件到此处，或<span className="text-blue-500">点击选择</span></p>
                        <p className="text-xs text-slate-400 mt-1">支持 .txt .md .pdf，最大 {MAX_FILE_MB}MB</p>
                      </>
                    )}
                  </div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept={ACCEPT_EXT}
                    className="hidden"
                    onChange={e => { const f = e.target.files?.[0]; if (f) handleFile(f) }}
                  />
                </div>
              )}

              {/* Device info */}
              <div className="space-y-3">
                <p className="text-xs font-medium text-slate-600">设备信息</p>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-slate-500 mb-1">品牌</label>
                    <input
                      value={brand}
                      onChange={e => setBrand(e.target.value)}
                      placeholder="如：Sony"
                      className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-slate-500 mb-1">型号</label>
                    <input
                      value={model}
                      onChange={e => setModel(e.target.value)}
                      placeholder="如：VPL-EX455"
                      className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>

              {errorMsg && (
                <div className="px-3 py-2 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
                  {errorMsg}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="px-6 py-4 border-t border-slate-200 shrink-0">
              <button
                onClick={handleSubmit}
                disabled={!canSubmit}
                className="w-full py-2.5 bg-slate-800 hover:bg-slate-900 text-white text-sm font-medium rounded-xl transition-colors disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer flex items-center justify-center gap-2"
              >
                {status === 'submitting' ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    提交中...
                  </>
                ) : '提交审核'}
              </button>
              <p className="text-center text-xs text-slate-400 mt-2">
                需填写品牌、型号及协议内容后方可提交
              </p>
            </div>
          </>
        )}
      </div>
    </>
  )
}

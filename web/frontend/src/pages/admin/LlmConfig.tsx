import { useCallback, useEffect, useState } from 'react'
import api from '../../api/client'
import { errorMessage } from '../../api/errors'
import { toast } from '../../stores/toast'

interface LlmConfigItem {
  id: number
  name: string
  provider: string
  model: string
  api_base: string | null
  api_key_set: boolean
  is_default: boolean
  is_active: boolean
}

const PROVIDERS = [
  { value: 'openai', label: 'OpenAI 兼容（DeepSeek/通义千问等）' },
  { value: 'anthropic', label: 'Anthropic (Claude)' },
  { value: 'ollama', label: 'Ollama (本地模型)' },
] as const

const INPUT_CLS =
  'w-full px-3 py-2 text-sm text-slate-800 placeholder-slate-400 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'

export default function LlmConfig() {
  const [configs, setConfigs] = useState<LlmConfigItem[]>([])
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<LlmConfigItem | null>(null)
  const [form, setForm] = useState({ name: '', provider: 'openai', model: '', api_base: '', api_key: '', is_default: false })
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null)
  const [loading, setLoading] = useState(false)
  const [showDetail, setShowDetail] = useState(false)
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null)
  // Model catalogue probed from the provider's list-models endpoint.
  // Keys: per-form-instance — cleared on form open / provider change.
  const [availableModels, setAvailableModels] = useState<string[]>([])
  const [fetchingModels, setFetchingModels] = useState(false)

  const load = useCallback(async () => {
    const { data } = await api.get('/admin/llm/config')
    setConfigs(data)
  }, [])

  useEffect(() => {
    let cancelled = false
    api.get('/admin/llm/config').then(({ data }) => { if (!cancelled) setConfigs(data) })
    return () => { cancelled = true }
  }, [])

  const resetForm = () => {
    setForm({ name: '', provider: 'openai', model: '', api_base: '', api_key: '', is_default: false })
    setEditing(null)
    setShowForm(false)
    setTestResult(null)
    setShowDetail(false)
    setAvailableModels([])
  }

  const handleEdit = (cfg: LlmConfigItem) => {
    setForm({ name: cfg.name, provider: cfg.provider, model: cfg.model, api_base: cfg.api_base || '', api_key: '', is_default: cfg.is_default })
    setEditing(cfg)
    setShowForm(true)
    setTestResult(null)
    setAvailableModels([])
  }

  // Fetch model catalogue from the provider. For an existing config the server
  // reuses its stored api_key; for a brand-new form, sends provider/api_base/api_key.
  const handleFetchModels = async () => {
    setFetchingModels(true)
    try {
      const payload = editing
        ? { config_id: editing.id }
        : { provider: form.provider, api_base: form.api_base || null, api_key: form.api_key || null }
      const { data } = await api.post('/admin/llm/list-models', payload)
      if (data.success) {
        setAvailableModels(data.models)
        if (data.models.length > 0) {
          toast.success(data.message)
          // Auto-pick when current input is empty and we got at least one option.
          if (!form.model.trim()) setForm(f => ({ ...f, model: data.models[0] }))
        } else {
          toast.info(data.message)
        }
      } else {
        setAvailableModels([])
        toast.error(data.message)
      }
    } catch (err) {
      setAvailableModels([])
      toast.error(errorMessage(err, '获取模型失败'))
    } finally {
      setFetchingModels(false)
    }
  }

  const handleSave = async () => {
    setLoading(true)
    try {
      const payload: Record<string, unknown> = {
        ...form,
        api_base: form.api_base || null,
        api_key: form.api_key || null,
      }
      if (editing && !form.api_key) delete payload.api_key
      if (editing) {
        await api.put(`/admin/llm/config/${editing.id}`, payload)
      } else {
        await api.post('/admin/llm/config', payload)
      }
      await load()
      resetForm()
      toast.success(editing ? '已更新模型配置' : '已添加模型')
    } catch (err) {
      toast.error(errorMessage(err, '保存失败'))
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: number) => {
    setConfirmDeleteId(null)
    try {
      await api.delete(`/admin/llm/config/${id}`)
      await load()
      toast.success('已删除')
    } catch (err) {
      toast.error(errorMessage(err, '删除失败'))
    }
  }

  const handleTest = async () => {
    setTestResult(null)
    setShowDetail(false)
    setLoading(true)
    try {
      const payload = editing
        ? { config_id: editing.id }
        : { provider: form.provider, model: form.model, api_base: form.api_base || null, api_key: form.api_key || null }
      const { data } = await api.post('/admin/llm/test', payload)
      setTestResult(data)
    } catch (err) {
      setTestResult({ success: false, message: errorMessage(err, '测试失败') })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-slate-900">LLM 模型配置</h1>
        <button
          onClick={() => { resetForm(); setShowForm(true) }}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
        >
          + 添加模型
        </button>
      </div>

      {configs.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 bg-white rounded-xl border border-slate-200">
          <div className="w-12 h-12 rounded-2xl bg-slate-100 flex items-center justify-center mb-3">
            <svg className="w-6 h-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <p className="text-sm text-slate-500 mb-1">暂无模型配置</p>
          <p className="text-xs text-slate-400">请添加一个 LLM 模型用于解析与生成</p>
        </div>
      ) : (
        <div className="space-y-3">
          {configs.map(cfg => (
            <div key={cfg.id} className="bg-white rounded-xl border border-slate-200 hover:border-slate-300 shadow-sm p-4 flex items-center justify-between transition-colors">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-semibold text-slate-900">{cfg.name}</span>
                  {cfg.is_default && <span className="text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-600 font-medium">默认</span>}
                  {!cfg.is_active && <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-500">已禁用</span>}
                </div>
                <p className="text-xs text-slate-500 mt-1 truncate">
                  {cfg.provider}/{cfg.model}{cfg.api_base ? ` · ${cfg.api_base}` : ''} · {cfg.api_key_set ? 'Key 已配置' : '无 Key'}
                </p>
              </div>
              <div className="flex gap-3 shrink-0 ml-4">
                <button onClick={() => handleEdit(cfg)} className="text-xs text-blue-600 hover:text-blue-800 transition-colors">编辑</button>
                <button onClick={() => setConfirmDeleteId(cfg.id)} className="text-xs text-red-500 hover:text-red-700 transition-colors">删除</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {showForm && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 px-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-semibold text-slate-900 mb-4">{editing ? '编辑模型' : '添加模型'}</h2>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">显示名称</label>
                <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="如：DeepSeek V3" className={INPUT_CLS} />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">提供商</label>
                <select
                  value={form.provider}
                  onChange={e => { setForm({ ...form, provider: e.target.value }); setAvailableModels([]) }}
                  className={INPUT_CLS}
                >
                  {PROVIDERS.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
                </select>
              </div>
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-sm font-medium text-slate-700">模型 ID</label>
                  <button
                    type="button"
                    onClick={handleFetchModels}
                    disabled={fetchingModels || (!editing && !form.api_key && form.provider !== 'ollama')}
                    title={!editing && !form.api_key && form.provider !== 'ollama'
                      ? '请先填写 API Key 后再获取'
                      : '从该 API 拉取可用模型列表'}
                    className="text-xs text-blue-600 hover:text-blue-800 disabled:text-slate-400 disabled:cursor-not-allowed transition-colors flex items-center gap-1"
                  >
                    {fetchingModels && <span className="w-3 h-3 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />}
                    {fetchingModels ? '获取中...' : '获取模型'}
                  </button>
                </div>
                <input
                  list="llm-model-options"
                  value={form.model}
                  onChange={e => setForm({ ...form, model: e.target.value })}
                  placeholder={availableModels.length > 0 ? `点击选择或输入 (${availableModels.length} 个可用)` : '如：deepseek-chat / gpt-4o / qwen-max'}
                  className={INPUT_CLS}
                />
                <datalist id="llm-model-options">
                  {availableModels.map(m => <option key={m} value={m} />)}
                </datalist>
                {availableModels.length > 0 && (
                  <p className="text-xs text-slate-500 mt-1">已加载 {availableModels.length} 个模型，点击输入框可下拉选择。</p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">API 地址（可选）</label>
                <input value={form.api_base} onChange={e => setForm({ ...form, api_base: e.target.value })} placeholder="如：https://api.deepseek.com 或 http://localhost:11434" className={INPUT_CLS} />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">API Key{editing ? '（留空不修改）' : ''}</label>
                <input type="password" value={form.api_key} onChange={e => setForm({ ...form, api_key: e.target.value })} placeholder="sk-..." className={INPUT_CLS} />
              </div>
              <label className="flex items-center gap-2 text-sm text-slate-700">
                <input type="checkbox" checked={form.is_default} onChange={e => setForm({ ...form, is_default: e.target.checked })} className="rounded border-slate-300" />
                设为默认模型
              </label>

              {testResult && (
                <div className={`px-3 py-2 rounded-lg text-sm ${testResult.success ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{testResult.success ? '连接成功' : '连接失败'}</span>
                    {testResult.message.length > 60 && (
                      <button onClick={() => setShowDetail(!showDetail)} className="text-xs underline opacity-70 hover:opacity-100 ml-2 shrink-0">
                        {showDetail ? '收起' : '查看详情'}
                      </button>
                    )}
                  </div>
                  {testResult.message.length <= 60 ? (
                    <p className="mt-1 break-all">{testResult.message}</p>
                  ) : !showDetail ? (
                    <p className="mt-1 break-all">{testResult.message.slice(0, 60)}…</p>
                  ) : (
                    <pre className="mt-1 max-h-32 overflow-y-auto whitespace-pre-wrap break-all text-xs leading-relaxed font-mono">{testResult.message}</pre>
                  )}
                </div>
              )}
            </div>

            <div className="flex justify-between mt-6">
              <button
                onClick={handleTest}
                disabled={loading || !form.model}
                className="px-4 py-2 border border-slate-300 text-slate-700 text-sm rounded-lg hover:bg-slate-50 disabled:opacity-50 transition-colors"
              >
                {loading ? '测试中...' : '测试连接'}
              </button>
              <div className="flex gap-2">
                <button
                  onClick={resetForm}
                  className="px-4 py-2 border border-slate-300 text-slate-700 text-sm rounded-lg hover:bg-slate-50 transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={handleSave}
                  disabled={loading || !form.name || !form.model}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg disabled:opacity-50 transition-colors"
                >
                  {loading ? '保存中...' : '保存'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {confirmDeleteId !== null && (
        <ConfirmModal
          title="确认删除该模型配置？"
          description="删除后将无法恢复，正在使用此配置的会话会受影响。"
          confirmText="删除"
          danger
          onConfirm={() => handleDelete(confirmDeleteId)}
          onCancel={() => setConfirmDeleteId(null)}
        />
      )}
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

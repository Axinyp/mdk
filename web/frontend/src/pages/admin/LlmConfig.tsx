import { useEffect, useState } from 'react'
import api from '../../api/client'

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

export default function LlmConfig() {
  const [configs, setConfigs] = useState<LlmConfigItem[]>([])
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<LlmConfigItem | null>(null)
  const [form, setForm] = useState({ name: '', provider: 'openai', model: '', api_base: '', api_key: '', is_default: false })
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null)
  const [loading, setLoading] = useState(false)
  const [showDetail, setShowDetail] = useState(false)

  const load = async () => {
    const { data } = await api.get('/admin/llm/config')
    setConfigs(data)
  }

  useEffect(() => { load() }, [])

  const resetForm = () => {
    setForm({ name: '', provider: 'openai', model: '', api_base: '', api_key: '', is_default: false })
    setEditing(null)
    setShowForm(false)
    setTestResult(null)
  }

  const handleEdit = (cfg: LlmConfigItem) => {
    setForm({ name: cfg.name, provider: cfg.provider, model: cfg.model, api_base: cfg.api_base || '', api_key: '', is_default: cfg.is_default })
    setEditing(cfg)
    setShowForm(true)
    setTestResult(null)
  }

  const handleSave = async () => {
    setLoading(true)
    try {
      const payload: any = { ...form, api_base: form.api_base || null, api_key: form.api_key || null }
      if (editing) {
        if (!form.api_key) delete payload.api_key
        await api.put(`/admin/llm/config/${editing.id}`, payload)
      } else {
        await api.post('/admin/llm/config', payload)
      }
      await load()
      resetForm()
    } catch (err: any) {
      alert(err.response?.data?.detail || '保存失败')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('确认删除？')) return
    await api.delete(`/admin/llm/config/${id}`)
    await load()
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
    } catch (err: any) {
      setTestResult({ success: false, message: err.response?.data?.detail || '测试失败' })
    } finally {
      setLoading(false)
    }
  }

  const providers = [
    { value: 'openai', label: 'OpenAI 兼容（DeepSeek/通义千问等）' },
    { value: 'anthropic', label: 'Anthropic (Claude)' },
    { value: 'ollama', label: 'Ollama (本地模型)' },
  ]

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-neutral-900">LLM 模型配置</h1>
        <button onClick={() => { resetForm(); setShowForm(true) }}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg">
          添加模型
        </button>
      </div>

      {/* Config list */}
      {configs.length === 0 ? (
        <div className="text-center py-12 text-neutral-400 bg-white rounded-xl border border-neutral-200">
          暂无配置，请添加一个 LLM 模型
        </div>
      ) : (
        <div className="space-y-3">
          {configs.map((cfg) => (
            <div key={cfg.id} className="bg-white rounded-lg border border-neutral-200 p-4 flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-neutral-900">{cfg.name}</span>
                  {cfg.is_default && <span className="text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-600">默认</span>}
                  {!cfg.is_active && <span className="text-xs px-2 py-0.5 rounded-full bg-neutral-100 text-neutral-500">已禁用</span>}
                </div>
                <p className="text-xs text-neutral-500 mt-1">
                  {cfg.provider}/{cfg.model} {cfg.api_base ? `(${cfg.api_base})` : ''} {cfg.api_key_set ? '• Key 已配置' : '• 无 Key'}
                </p>
              </div>
              <div className="flex gap-2">
                <button onClick={() => handleEdit(cfg)} className="text-xs text-blue-600 hover:text-blue-800">编辑</button>
                <button onClick={() => handleDelete(cfg.id)} className="text-xs text-red-500 hover:text-red-700">删除</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Form modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-semibold mb-4">{editing ? '编辑模型' : '添加模型'}</h2>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-1">显示名称</label>
                <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="如：DeepSeek V3"
                  className="w-full px-3 py-2 border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-1">提供商</label>
                <select value={form.provider} onChange={(e) => setForm({ ...form, provider: e.target.value })}
                  className="w-full px-3 py-2 border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                  {providers.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-1">模型 ID</label>
                <input value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })}
                  placeholder="如：deepseek-chat / gpt-4o / qwen-max"
                  className="w-full px-3 py-2 border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-1">API 地址（可选）</label>
                <input value={form.api_base} onChange={(e) => setForm({ ...form, api_base: e.target.value })}
                  placeholder="如：https://api.deepseek.com 或 http://localhost:11434"
                  className="w-full px-3 py-2 border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-1">API Key{editing ? '（留空不修改）' : ''}</label>
                <input type="password" value={form.api_key} onChange={(e) => setForm({ ...form, api_key: e.target.value })}
                  placeholder="sk-..."
                  className="w-full px-3 py-2 border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={form.is_default} onChange={(e) => setForm({ ...form, is_default: e.target.checked })}
                  className="rounded border-neutral-300" />
                设为默认模型
              </label>

              {testResult && (
                <div className={`px-3 py-2 rounded-md text-sm ${testResult.success ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'}`}>
                  <div className="flex items-center justify-between">
                    <span>{testResult.success ? '连接成功' : '连接失败'}</span>
                    {testResult.message.length > 60 && (
                      <button onClick={() => setShowDetail(!showDetail)}
                        className="text-xs underline opacity-70 hover:opacity-100 ml-2 shrink-0">
                        {showDetail ? '收起' : '查看详情'}
                      </button>
                    )}
                  </div>
                  {testResult.message.length <= 60 ? (
                    <p className="mt-1 break-all">{testResult.message}</p>
                  ) : !showDetail ? (
                    <p className="mt-1 break-all">{testResult.message.slice(0, 60)}...</p>
                  ) : (
                    <pre className="mt-1 max-h-32 overflow-y-auto whitespace-pre-wrap break-all text-xs leading-relaxed">{testResult.message}</pre>
                  )}
                </div>
              )}
            </div>

            <div className="flex justify-between mt-6">
              <button onClick={handleTest} disabled={loading || !form.model}
                className="px-4 py-2 border border-neutral-300 text-sm rounded-lg hover:bg-neutral-50 disabled:opacity-50">
                {loading ? '测试中...' : '测试连接'}
              </button>
              <div className="flex gap-2">
                <button onClick={resetForm} className="px-4 py-2 border border-neutral-300 text-sm rounded-lg hover:bg-neutral-50">
                  取消
                </button>
                <button onClick={handleSave} disabled={loading || !form.name || !form.model}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg disabled:opacity-50">
                  {loading ? '保存中...' : '保存'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

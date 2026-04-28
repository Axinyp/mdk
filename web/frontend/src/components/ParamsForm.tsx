import { useState } from 'react'

const CONTRACT: Record<string, { required: string[]; forbidden?: string[] }> = {
  ON_RELAY:           { required: ['dev', 'channel'] },
  OFF_RELAY:          { required: ['dev', 'channel'] },
  SEND_COM:           { required: ['dev', 'channel', 'str'] },
  SET_COM:            { required: ['dev', 'channel', 'sband', 'databit', 'jo', 'stopbit', 'dataStream', 'comType'] },
  SEND_IRCODE:        { required: ['dev', 'channel', 'str'] },
  SEND_LITE:          { required: ['dev', 'channel', 'val'] },
  SEND_IO:            { required: ['dev', 'channel', 'vol'] },
  SEND_UDP:           { required: ['ip', 'port', 'str'], forbidden: ['dev', 'channel'] },
  SEND_TCP:           { required: ['ip', 'port', 'str'], forbidden: ['dev', 'channel'] },
  WAKEUP_ONLAN:       { required: ['MAC'] },
  SEND_M2M_DATA:      { required: ['ip', 'data'] },
  SEND_M2M_JNPUSH:    { required: ['ip', 'jNumber'] },
  SEND_M2M_JNRELEASE: { required: ['ip', 'jNumber'] },
  SEND_M2M_LEVEL:     { required: ['ip', 'jNumber', 'val'] },
  SET_BUTTON:         { required: ['dev', 'channel', 'state'] },
  SET_LEVEL:          { required: ['dev', 'channel', 'val'] },
  SEND_TEXT:          { required: ['dev', 'channel', 'text'] },
  SEND_PAGING:        { required: ['dev', 'channel', 'text'] },
  SEND_PICTURE:       { required: ['dev', 'channel', 'picIndex'] },
  SET_VOL_M:          { required: ['channel', 'mute', 'vol'], forbidden: ['dev'] },
  SET_MATRIX_M:       { required: ['out', 'in'], forbidden: ['dev'] },
  SLEEP:              { required: ['time'] },
  START_TIMER:        { required: ['name', 'time'] },
  CANCEL_TIMER:       { required: ['name'] },
  CANCEL_WAIT:        { required: ['name'] },
  TRACE:              { required: ['msg'] },
}

interface Props {
  action: string
  params: Record<string, unknown>
  onChange: (params: Record<string, unknown>) => void
  readOnly?: boolean
}

export function missingRequired(action: string, params: Record<string, unknown>): string[] {
  const contract = CONTRACT[action?.toUpperCase() ?? '']
  if (!contract) return []
  return contract.required.filter(k => params[k] === undefined || params[k] === '' || params[k] === null)
}

export default function ParamsForm({ action, params, onChange, readOnly = false }: Props) {
  const contract = CONTRACT[action?.toUpperCase() ?? ''] ?? { required: [] }
  const requiredKeys = contract.required
  const existingExtra = Object.keys(params).filter(k => !requiredKeys.includes(k))
  const allKeys = [...requiredKeys, ...existingExtra]
  const [newKey, setNewKey] = useState('')

  if (allKeys.length === 0 && readOnly) return <span className="text-xs text-slate-400">无参数</span>

  const updateParam = (key: string, value: string) => onChange({ ...params, [key]: value })

  const removeParam = (key: string) => {
    const next = { ...params }
    delete next[key]
    onChange(next)
  }

  const addParam = () => {
    const k = newKey.trim()
    if (!k) return
    onChange({ ...params, [k]: '' })
    setNewKey('')
  }

  return (
    <div className="space-y-1">
      {allKeys.map(key => {
        const isRequired = requiredKeys.includes(key)
        const isMissing = isRequired && (params[key] === undefined || params[key] === '' || params[key] === null)
        return (
          <div key={key} className="flex items-center gap-1.5">
            <span className={`w-24 shrink-0 text-[10px] font-mono font-medium truncate ${isMissing ? 'text-red-500' : 'text-slate-500'}`}>
              {key}{isRequired ? ' *' : ''}
            </span>
            <input
              value={String(params[key] ?? '')}
              onChange={e => !readOnly && updateParam(key, e.target.value)}
              readOnly={readOnly}
              className={`flex-1 min-w-0 px-2 py-0.5 text-xs border rounded focus:outline-none focus:ring-1 ${
                isMissing
                  ? 'border-red-300 bg-red-50 text-red-700 focus:ring-red-400'
                  : 'border-slate-200 bg-white focus:ring-blue-400'
              } ${readOnly ? 'cursor-default' : ''}`}
            />
            {!readOnly && !isRequired && (
              <button
                type="button"
                onClick={() => removeParam(key)}
                className="shrink-0 text-slate-300 hover:text-red-400 transition-colors text-sm leading-none"
              >
                ×
              </button>
            )}
          </div>
        )
      })}
      {!readOnly && (
        <div className="flex items-center gap-1.5 pt-0.5 border-t border-dashed border-slate-100">
          <input
            value={newKey}
            onChange={e => setNewKey(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && addParam()}
            placeholder="新参数键名"
            className="w-24 px-2 py-0.5 text-[10px] border border-dashed border-slate-200 rounded focus:outline-none focus:ring-1 focus:ring-blue-400 placeholder:text-slate-300"
          />
          <button
            type="button"
            onClick={addParam}
            className="text-[10px] text-blue-500 hover:text-blue-700 transition-colors"
          >
            + 添加
          </button>
        </div>
      )}
    </div>
  )
}

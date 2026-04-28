import { Fragment, useState } from 'react'
import ParamsForm, { missingRequired } from './ParamsForm'

export interface Device {
  name: string
  type: string
  board: number
  comm: string
}

export interface FunctionItem {
  name: string
  join_number: number
  join_source: 'auto' | 'user_specified'
  btn_type?: string
  control_type?: string
  action?: string
  params?: Record<string, unknown>
  template_id?: string | null
  image?: string
}

export interface PageItem {
  name: string
  type: 'main' | 'dialog' | 'subpage'
  bg_image?: string
}

export interface ParsedData {
  devices: Device[]
  functions: FunctionItem[]
  pages: PageItem[]
  missing_info: string[]
  image_path: string | null
}

interface Props {
  data: ParsedData
  onConfirm: (data: ParsedData) => void
  /** Render as a frozen snapshot — disables every editor and hides action buttons. */
  readOnly?: boolean
}

type Tab = 'devices' | 'functions' | 'pages'

const CELL_INPUT =
  'w-full px-2 py-1 text-sm text-slate-800 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
const CELL_INPUT_XS =
  'w-full px-2 py-1 text-xs text-slate-800 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'

export default function ConfirmationView({ data, onConfirm, readOnly = false }: Props) {
  const [editData, setEditData] = useState<ParsedData>(data)
  const [activeTab, setActiveTab] = useState<Tab>('devices')
  const [expandedFunctions, setExpandedFunctions] = useState<Set<number>>(new Set())
  const [showMissingConfirm, setShowMissingConfirm] = useState(false)

  // ── Device helpers ──────────────────────────────────────────────────────
  const updateDevice = (i: number, field: string, value: unknown) => {
    const devices = [...editData.devices]
    devices[i] = { ...devices[i], [field]: value }
    setEditData({ ...editData, devices })
  }
  const removeDevice = (i: number) =>
    setEditData({ ...editData, devices: editData.devices.filter((_, idx) => idx !== i) })
  const addDevice = () =>
    setEditData({ ...editData, devices: [...editData.devices, { name: '', type: '', board: 0, comm: 'RS232' }] })

  // ── Function helpers ─────────────────────────────────────────────────────
  const updateFunction = (i: number, field: string, value: unknown) => {
    const functions = [...editData.functions]
    functions[i] = { ...functions[i], [field]: value }
    setEditData({ ...editData, functions })
  }
  const removeFunction = (i: number) =>
    setEditData({ ...editData, functions: editData.functions.filter((_, idx) => idx !== i) })
  const addFunction = () =>
    setEditData({ ...editData, functions: [...editData.functions, { name: '', join_number: 0, join_source: 'auto', btn_type: '', control_type: '', action: '', params: {} }] })
  const toggleExpandFn = (i: number) =>
    setExpandedFunctions(prev => {
      const next = new Set(prev)
      if (next.has(i)) next.delete(i); else next.add(i)
      return next
    })

  // ── Page helpers ─────────────────────────────────────────────────────────
  const updatePage = (i: number, field: string, value: unknown) => {
    const pages = [...editData.pages]
    pages[i] = { ...pages[i], [field]: value }
    setEditData({ ...editData, pages })
  }
  const removePage = (i: number) =>
    setEditData({ ...editData, pages: editData.pages.filter((_, idx) => idx !== i) })
  const addPage = () =>
    setEditData({ ...editData, pages: [...editData.pages, { name: '', type: 'main' }] })

  const tabs: { key: Tab; label: string; count: number }[] = [
    { key: 'devices',   label: '设备清单', count: editData.devices.length },
    { key: 'functions', label: '功能清单', count: editData.functions.length },
    { key: 'pages',     label: '页面结构', count: editData.pages.length },
  ]

  const handleConfirmClick = () => {
    if (editData.missing_info.length > 0) {
      setShowMissingConfirm(true)
      return
    }
    onConfirm(editData)
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200">
      {editData.missing_info.length > 0 && (
        <div className="mx-4 mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
          <p className="text-sm font-medium text-amber-800 mb-1.5">以下信息待补充 — 可直接编辑下方表格，或返回上一步重新解析</p>
          {editData.missing_info.map((info, i) => (
            <p key={i} className="text-sm text-amber-700">• {info}</p>
          ))}
        </div>
      )}

      {!editData.image_path && (
        <div className="mx-4 mt-3 px-3 py-2 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-700">
          未提供图片，将使用纯色按钮方案生成
        </div>
      )}

      <div className="flex border-b border-slate-200 px-4 mt-4 overflow-x-auto">
        {tabs.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors whitespace-nowrap ${
              activeTab === tab.key
                ? 'text-blue-600 border-blue-500'
                : 'text-slate-500 border-transparent hover:text-slate-700'
            }`}
          >
            {tab.label}
            <span className="ml-1.5 px-1.5 py-0.5 text-xs rounded-full bg-slate-100 text-slate-600">
              {tab.count}
            </span>
          </button>
        ))}
      </div>

      <fieldset disabled={readOnly} className="contents">
      {activeTab === 'devices' && (
        <div className="p-4 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 text-left">
                <th className="px-3 py-2 text-xs font-medium text-slate-500">设备名</th>
                <th className="px-3 py-2 text-xs font-medium text-slate-500">类型</th>
                <th className="px-3 py-2 text-xs font-medium text-slate-500">编号</th>
                <th className="px-3 py-2 text-xs font-medium text-slate-500">通信方式</th>
                <th className="px-3 py-2 text-xs font-medium text-slate-500 w-16">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {editData.devices.map((d, i) => (
                <tr key={i} className="hover:bg-slate-50">
                  <td className="px-3 py-2">
                    <input value={d.name} onChange={e => updateDevice(i, 'name', e.target.value)} className={CELL_INPUT} />
                  </td>
                  <td className="px-3 py-2">
                    <input value={d.type} onChange={e => updateDevice(i, 'type', e.target.value)} className={CELL_INPUT} />
                  </td>
                  <td className="px-3 py-2">
                    <input type="number" value={d.board} onChange={e => updateDevice(i, 'board', parseInt(e.target.value) || 0)} className={`${CELL_INPUT} w-20`} />
                  </td>
                  <td className="px-3 py-2">
                    <input value={d.comm} onChange={e => updateDevice(i, 'comm', e.target.value)} className={CELL_INPUT} />
                  </td>
                  <td className="px-3 py-2">
                    <button onClick={() => removeDevice(i)} className="text-xs text-red-400 hover:text-red-600 transition-colors">删除</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <button onClick={addDevice} className="mt-2 px-3 py-1.5 text-xs text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-lg transition-colors">
            + 添加设备
          </button>
        </div>
      )}

      {activeTab === 'functions' && (
        <div className="p-4 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 text-left">
                <th className="px-3 py-2 text-xs font-medium text-slate-500">功能</th>
                <th className="px-3 py-2 text-xs font-medium text-slate-500">Join</th>
                <th className="px-3 py-2 text-xs font-medium text-slate-500">来源</th>
                <th className="px-3 py-2 text-xs font-medium text-slate-500">控件</th>
                <th className="px-3 py-2 text-xs font-medium text-slate-500">Action</th>
                <th className="px-3 py-2 text-xs font-medium text-slate-500">图片路径</th>
                <th className="px-3 py-2 text-xs font-medium text-slate-500 w-24">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {editData.functions.map((f, i) => {
                const params = f.params ?? {}
                const action = f.action ?? ''
                const missing = missingRequired(action, params)
                const expanded = expandedFunctions.has(i)
                return (
                  <Fragment key={i}>
                    <tr className="hover:bg-slate-50">
                      <td className="px-3 py-2">
                        <input value={f.name} onChange={e => updateFunction(i, 'name', e.target.value)} className={CELL_INPUT} />
                      </td>
                      <td className="px-3 py-2">
                        <input
                          type="number" value={f.join_number}
                          onChange={e => {
                            const val = parseInt(e.target.value) || 0
                            updateFunction(i, 'join_number', val)
                            updateFunction(i, 'join_source', val > 0 ? 'user_specified' : 'auto')
                          }}
                          className={`${CELL_INPUT} w-20`}
                        />
                      </td>
                      <td className="px-3 py-2">
                        <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${
                          f.join_source === 'user_specified'
                            ? 'bg-emerald-50 text-emerald-700'
                            : 'bg-blue-50 text-blue-600'
                        }`}>
                          {f.join_source === 'user_specified' ? '用户指定' : '自动分配'}
                        </span>
                      </td>
                      <td className="px-3 py-2">
                        <input value={f.btn_type || f.control_type || ''} onChange={e => updateFunction(i, 'control_type', e.target.value)} className={CELL_INPUT_XS} />
                      </td>
                      <td className="px-3 py-2 min-w-[130px]">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <input
                            value={action}
                            onChange={e => updateFunction(i, 'action', e.target.value)}
                            placeholder="函数名"
                            className={`${CELL_INPUT_XS} w-32 font-mono`}
                          />
                          {missing.length > 0 && (
                            <span className="text-[10px] text-red-500 font-medium">
                              缺{missing.length}参
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-3 py-2">
                        <input value={f.image || ''} onChange={e => updateFunction(i, 'image', e.target.value)} placeholder="选填" className={CELL_INPUT_XS} />
                      </td>
                      <td className="px-3 py-2">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => toggleExpandFn(i)}
                            className={`text-xs transition-colors ${expanded ? 'text-blue-600 hover:text-blue-800' : 'text-slate-400 hover:text-slate-600'}`}
                          >
                            {expanded ? '▲ 参数' : '▼ 参数'}
                          </button>
                          <button onClick={() => removeFunction(i)} className="text-xs text-red-400 hover:text-red-600 transition-colors">删除</button>
                        </div>
                      </td>
                    </tr>
                    {expanded && (
                      <tr>
                        <td colSpan={7} className="px-6 py-3 bg-slate-50 border-t border-slate-100">
                          <div className="max-w-lg">
                            <ParamsForm
                              action={action}
                              params={params}
                              onChange={next => updateFunction(i, 'params', next)}
                              readOnly={readOnly}
                            />
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                )
              })}
            </tbody>
          </table>
          <button onClick={addFunction} className="mt-2 px-3 py-1.5 text-xs text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-lg transition-colors">
            + 添加功能
          </button>
        </div>
      )}

      {activeTab === 'pages' && (
        <div className="p-4 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 text-left">
                <th className="px-3 py-2 text-xs font-medium text-slate-500">页面名</th>
                <th className="px-3 py-2 text-xs font-medium text-slate-500">类型</th>
                <th className="px-3 py-2 text-xs font-medium text-slate-500">背景图片</th>
                <th className="px-3 py-2 text-xs font-medium text-slate-500 w-16">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {editData.pages.map((p, i) => (
                <tr key={i} className="hover:bg-slate-50">
                  <td className="px-3 py-2">
                    <input value={p.name} onChange={e => updatePage(i, 'name', e.target.value)} className={CELL_INPUT} />
                  </td>
                  <td className="px-3 py-2">
                    <select value={p.type} onChange={e => updatePage(i, 'type', e.target.value)} className={`${CELL_INPUT} w-32`}>
                      <option value="main">main</option>
                      <option value="dialog">dialog</option>
                      <option value="subpage">subpage</option>
                    </select>
                  </td>
                  <td className="px-3 py-2">
                    <input value={p.bg_image || ''} onChange={e => updatePage(i, 'bg_image', e.target.value)} placeholder="选填" className={CELL_INPUT_XS} />
                  </td>
                  <td className="px-3 py-2">
                    <button onClick={() => removePage(i)} className="text-xs text-red-400 hover:text-red-600 transition-colors">删除</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <button onClick={addPage} className="mt-2 px-3 py-1.5 text-xs text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-lg transition-colors">
            + 添加页面
          </button>
        </div>
      )}

      </fieldset>

      {!readOnly && (
        <div className="px-4 py-4 border-t border-slate-200 flex justify-end">
          <button
            onClick={handleConfirmClick}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
          >
            确认并生成
          </button>
        </div>
      )}

      {showMissingConfirm && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 px-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-sm p-6">
            <h3 className="text-base font-semibold text-slate-900">仍有 {editData.missing_info.length} 项信息未补充</h3>
            <p className="text-sm text-slate-500 mt-2">未补充的信息将以默认值处理。如需更精确的结果，建议返回上一步重新解析。</p>
            <div className="mt-6 flex justify-end gap-2">
              <button
                onClick={() => setShowMissingConfirm(false)}
                className="px-4 py-2 border border-slate-300 text-slate-700 text-sm rounded-lg hover:bg-slate-50 transition-colors"
              >
                我再补充
              </button>
              <button
                onClick={() => { setShowMissingConfirm(false); onConfirm(editData) }}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
              >
                继续生成
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

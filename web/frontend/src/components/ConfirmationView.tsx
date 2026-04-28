import { useState } from 'react'

export interface SceneActionItem {
  device: string
  action: string
  value?: string
}

export interface SceneModeItem {
  name: string
  scene_type: 'meeting' | 'rest' | 'leave' | 'custom'
  trigger_join: number
  actions: SceneActionItem[]
}

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
  device?: string
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
  scenes?: SceneModeItem[]
}

interface Props {
  data: ParsedData
  onConfirm: (data: ParsedData) => void
  /** Render as a frozen snapshot — disables every editor and hides action buttons. */
  readOnly?: boolean
}

type Tab = 'devices' | 'functions' | 'pages' | 'scenes'

const SCENE_TYPE_BADGE: Record<SceneModeItem['scene_type'], { label: string; cls: string }> = {
  meeting: { label: '会议',   cls: 'bg-blue-50 text-blue-600' },
  rest:    { label: '休息',   cls: 'bg-slate-100 text-slate-500' },
  leave:   { label: '离场',   cls: 'bg-amber-50 text-amber-700' },
  custom:  { label: '自定义', cls: 'bg-purple-100 text-purple-600' },
}

const ACTION_OPTIONS = ['RELAY.On', 'RELAY.Off', 'COM.Send', 'IR.Send', 'DIMMER.Set', 'IP.Send']

const CELL_INPUT =
  'w-full px-2 py-1 text-sm text-slate-800 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
const CELL_INPUT_XS =
  'w-full px-2 py-1 text-xs text-slate-800 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'

export default function ConfirmationView({ data, onConfirm, readOnly = false }: Props) {
  const [editData, setEditData] = useState<ParsedData>({
    ...data,
    scenes: data.scenes ?? [],
  })
  const [activeTab, setActiveTab] = useState<Tab>('devices')
  const [collapsedScenes, setCollapsedScenes] = useState<Set<number>>(new Set())
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
    setEditData({ ...editData, functions: [...editData.functions, { name: '', join_number: 0, join_source: 'auto', btn_type: '', control_type: '', device: '' }] })

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

  // ── Scene helpers ────────────────────────────────────────────────────────
  const updateScene = (i: number, field: keyof SceneModeItem, value: unknown) => {
    const scenes = [...(editData.scenes ?? [])]
    scenes[i] = { ...scenes[i], [field]: value }
    setEditData({ ...editData, scenes })
  }
  const removeScene = (i: number) => {
    setEditData({ ...editData, scenes: (editData.scenes ?? []).filter((_, idx) => idx !== i) })
    setCollapsedScenes(prev => {
      const next = new Set(prev)
      next.delete(i)
      return next
    })
  }
  const addScene = () => {
    const newScene: SceneModeItem = { name: '新场景', scene_type: 'custom', trigger_join: 0, actions: [] }
    setEditData({ ...editData, scenes: [...(editData.scenes ?? []), newScene] })
  }
  const updateAction = (si: number, ai: number, field: keyof SceneActionItem, value: string) => {
    const scenes = [...(editData.scenes ?? [])]
    const actions = [...scenes[si].actions]
    actions[ai] = { ...actions[ai], [field]: value }
    scenes[si] = { ...scenes[si], actions }
    setEditData({ ...editData, scenes })
  }
  const removeAction = (si: number, ai: number) => {
    const scenes = [...(editData.scenes ?? [])]
    scenes[si] = { ...scenes[si], actions: scenes[si].actions.filter((_, idx) => idx !== ai) }
    setEditData({ ...editData, scenes })
  }
  const addAction = (si: number) => {
    const scenes = [...(editData.scenes ?? [])]
    scenes[si] = { ...scenes[si], actions: [...scenes[si].actions, { device: '', action: 'RELAY.On', value: '' }] }
    setEditData({ ...editData, scenes })
  }
  const toggleCollapse = (i: number) => {
    setCollapsedScenes(prev => {
      const next = new Set(prev)
      if (next.has(i)) next.delete(i)
      else next.add(i)
      return next
    })
  }

  const scenes = editData.scenes ?? []
  const tabs: { key: Tab; label: string; count: number }[] = [
    { key: 'devices',   label: '设备清单', count: editData.devices.length },
    { key: 'functions', label: '功能清单', count: editData.functions.length },
    { key: 'pages',     label: '页面结构', count: editData.pages.length },
    { key: 'scenes',    label: '场景模式', count: scenes.length },
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
                <th className="px-3 py-2 text-xs font-medium text-slate-500">设备</th>
                <th className="px-3 py-2 text-xs font-medium text-slate-500">图片路径</th>
                <th className="px-3 py-2 text-xs font-medium text-slate-500 w-16">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {editData.functions.map((f, i) => (
                <tr key={i} className="hover:bg-slate-50">
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
                  <td className="px-3 py-2">
                    <input value={f.device || ''} onChange={e => updateFunction(i, 'device', e.target.value)} className={CELL_INPUT_XS} />
                  </td>
                  <td className="px-3 py-2">
                    <input value={f.image || ''} onChange={e => updateFunction(i, 'image', e.target.value)} placeholder="选填" className={CELL_INPUT_XS} />
                  </td>
                  <td className="px-3 py-2">
                    <button onClick={() => removeFunction(i)} className="text-xs text-red-400 hover:text-red-600 transition-colors">删除</button>
                  </td>
                </tr>
              ))}
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

      {activeTab === 'scenes' && (
        <div className="p-4 space-y-3">
          {scenes.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 text-center">
              <div className="w-12 h-12 rounded-2xl bg-slate-100 flex items-center justify-center mb-3">
                <svg className="w-6 h-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
              </div>
              <p className="text-sm text-slate-500 mb-1">暂未检测到场景模式</p>
              <p className="text-xs text-slate-400 mb-4">可手动添加会议、休息、离场等联动场景</p>
              <button onClick={addScene} className="px-4 py-2 bg-slate-900 hover:bg-slate-700 text-white text-xs font-medium rounded-lg transition-colors">
                + 新增场景
              </button>
            </div>
          ) : (
            <>
              {scenes.map((scene, si) => {
                const collapsed = collapsedScenes.has(si)
                const badge = SCENE_TYPE_BADGE[scene.scene_type]
                return (
                  <div key={si} className="border border-slate-200 rounded-xl overflow-hidden bg-white shadow-sm">
                    <div className="flex items-center gap-2 px-4 py-3 bg-slate-50 border-b border-slate-200">
                      <button
                        onClick={() => toggleCollapse(si)}
                        className="text-slate-400 hover:text-slate-600 transition-colors"
                      >
                        <svg
                          className={`w-4 h-4 transition-transform duration-200 ${collapsed ? '' : 'rotate-90'}`}
                          fill="none" stroke="currentColor" viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </button>

                      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${badge.cls}`}>
                        {badge.label}
                      </span>

                      <input
                        value={scene.name}
                        onChange={e => updateScene(si, 'name', e.target.value)}
                        className="flex-1 bg-transparent border-b border-transparent hover:border-slate-300 focus:border-slate-400 focus:outline-none text-sm font-semibold text-slate-800 transition-colors"
                      />

                      <div className="flex items-center gap-1.5 shrink-0">
                        <span className="text-xs text-slate-400">Join</span>
                        <input
                          type="number"
                          value={scene.trigger_join}
                          onChange={e => updateScene(si, 'trigger_join', parseInt(e.target.value) || 0)}
                          className="w-14 text-xs font-semibold text-center bg-slate-100 border border-slate-200 rounded-lg px-1 py-1 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                        />
                      </div>

                      <select
                        value={scene.scene_type}
                        onChange={e => updateScene(si, 'scene_type', e.target.value as SceneModeItem['scene_type'])}
                        className="text-xs border border-slate-200 rounded-lg px-2 py-1 bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                      >
                        <option value="meeting">会议</option>
                        <option value="rest">休息</option>
                        <option value="leave">离场</option>
                        <option value="custom">自定义</option>
                      </select>

                      <button
                        onClick={() => removeScene(si)}
                        className="w-6 h-6 flex items-center justify-center text-slate-300 hover:text-red-400 transition-colors rounded-lg"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>

                    {!collapsed && (
                      <div className="p-3 space-y-2">
                        {scene.actions.length > 0 && (
                          <div className="grid grid-cols-[1fr_1fr_90px_28px] gap-2 px-1 mb-1">
                            <span className="text-[10px] font-medium text-slate-400">设备</span>
                            <span className="text-[10px] font-medium text-slate-400">动作</span>
                            <span className="text-[10px] font-medium text-slate-400">值</span>
                            <span />
                          </div>
                        )}

                        {scene.actions.map((act, ai) => (
                          <div key={ai} className="grid grid-cols-[1fr_1fr_90px_28px] gap-2 items-center">
                            <input
                              value={act.device}
                              onChange={e => updateAction(si, ai, 'device', e.target.value)}
                              placeholder="设备名"
                              className="px-2 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                            />
                            <select
                              value={act.action}
                              onChange={e => updateAction(si, ai, 'action', e.target.value)}
                              className="px-2 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                            >
                              {ACTION_OPTIONS.map(opt => (
                                <option key={opt} value={opt}>{opt}</option>
                              ))}
                            </select>
                            <input
                              value={act.value ?? ''}
                              onChange={e => updateAction(si, ai, 'value', e.target.value)}
                              placeholder="选填"
                              className="px-2 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                            />
                            <button
                              onClick={() => removeAction(si, ai)}
                              className="w-7 h-7 flex items-center justify-center text-slate-300 hover:text-red-400 transition-colors rounded-lg"
                            >
                              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                              </svg>
                            </button>
                          </div>
                        ))}

                        <button
                          onClick={() => addAction(si)}
                          className="w-full mt-1 py-1.5 border border-dashed border-blue-200 text-blue-400 text-xs rounded-lg hover:border-blue-400 hover:text-blue-600 transition-colors"
                        >
                          + 添加动作
                        </button>
                      </div>
                    )}
                  </div>
                )
              })}

              <button
                onClick={addScene}
                className="w-full py-3 border-2 border-dashed border-slate-200 text-slate-400 text-sm rounded-xl hover:border-slate-300 hover:text-slate-600 transition-colors"
              >
                + 新增场景
              </button>
            </>
          )}
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

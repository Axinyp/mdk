import { useState } from 'react'

interface ParsedData {
  devices: any[]
  functions: any[]
  pages: any[]
  missing_info: string[]
  image_path: string | null
}

interface Props {
  data: ParsedData
  onConfirm: (data: ParsedData) => void
  onReParse: () => void
}

type Tab = 'devices' | 'functions' | 'pages'

export default function ConfirmationView({ data, onConfirm, onReParse }: Props) {
  const [editData, setEditData] = useState<ParsedData>({ ...data })
  const [activeTab, setActiveTab] = useState<Tab>('devices')

  const updateDevice = (index: number, field: string, value: any) => {
    const devices = [...editData.devices]
    devices[index] = { ...devices[index], [field]: value }
    setEditData({ ...editData, devices })
  }

  const updateFunction = (index: number, field: string, value: any) => {
    const functions = [...editData.functions]
    functions[index] = { ...functions[index], [field]: value }
    setEditData({ ...editData, functions })
  }

  const removeDevice = (index: number) => {
    setEditData({ ...editData, devices: editData.devices.filter((_, i) => i !== index) })
  }

  const removeFunction = (index: number) => {
    setEditData({ ...editData, functions: editData.functions.filter((_, i) => i !== index) })
  }

  const addDevice = () => {
    setEditData({ ...editData, devices: [...editData.devices, { name: '', type: '', board: 0, comm: 'RS232' }] })
  }

  const addFunction = () => {
    setEditData({ ...editData, functions: [...editData.functions, { name: '', join_number: 0, join_source: 'auto', btn_type: '', control_type: '', device: '' }] })
  }

  const updatePage = (index: number, field: string, value: any) => {
    const pages = [...editData.pages]
    pages[index] = { ...pages[index], [field]: value }
    setEditData({ ...editData, pages })
  }

  const removePage = (index: number) => {
    setEditData({ ...editData, pages: editData.pages.filter((_, i) => i !== index) })
  }

  const addPage = () => {
    setEditData({ ...editData, pages: [...editData.pages, { name: '', type: 'main' }] })
  }

  const tabs: { key: Tab; label: string; count: number }[] = [
    { key: 'devices', label: '设备清单', count: editData.devices.length },
    { key: 'functions', label: '功能清单', count: editData.functions.length },
    { key: 'pages', label: '页面结构', count: editData.pages.length },
  ]

  return (
    <div className="bg-white rounded-xl shadow-sm border border-neutral-200">
      {/* Missing info alerts */}
      {editData.missing_info.length > 0 && (
        <div className="mx-4 mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
          <p className="text-sm font-medium text-amber-800 mb-1">缺失信息</p>
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

      {/* Tabs */}
      <div className="flex border-b border-neutral-200 px-4 mt-4">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors ${
              activeTab === tab.key
                ? 'text-blue-600 border-blue-500'
                : 'text-neutral-500 border-transparent hover:text-neutral-700'
            }`}
          >
            {tab.label}
            <span className="ml-1.5 px-1.5 py-0.5 text-xs rounded-full bg-neutral-100">
              {tab.count}
            </span>
          </button>
        ))}
      </div>

      {/* Device table */}
      {activeTab === 'devices' && (
        <div className="p-4">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-neutral-50 text-left">
                <th className="px-3 py-2 text-xs font-medium text-neutral-500">设备名</th>
                <th className="px-3 py-2 text-xs font-medium text-neutral-500">类型</th>
                <th className="px-3 py-2 text-xs font-medium text-neutral-500">编号</th>
                <th className="px-3 py-2 text-xs font-medium text-neutral-500">通信方式</th>
                <th className="px-3 py-2 text-xs font-medium text-neutral-500 w-16">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {editData.devices.map((d, i) => (
                <tr key={i} className="hover:bg-neutral-50">
                  <td className="px-3 py-2">
                    <input value={d.name} onChange={(e) => updateDevice(i, 'name', e.target.value)}
                      className="w-full px-2 py-1 border border-neutral-200 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </td>
                  <td className="px-3 py-2">
                    <input value={d.type} onChange={(e) => updateDevice(i, 'type', e.target.value)}
                      className="w-full px-2 py-1 border border-neutral-200 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </td>
                  <td className="px-3 py-2">
                    <input type="number" value={d.board} onChange={(e) => updateDevice(i, 'board', parseInt(e.target.value) || 0)}
                      className="w-20 px-2 py-1 border border-neutral-200 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </td>
                  <td className="px-3 py-2">
                    <input value={d.comm} onChange={(e) => updateDevice(i, 'comm', e.target.value)}
                      className="w-full px-2 py-1 border border-neutral-200 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </td>
                  <td className="px-3 py-2">
                    <button onClick={() => removeDevice(i)} className="text-red-400 hover:text-red-600 text-xs">删除</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <button onClick={addDevice}
            className="mt-2 px-3 py-1.5 text-xs text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-md transition-colors">
            + 添加设备
          </button>
        </div>
      )}

      {/* Function table */}
      {activeTab === 'functions' && (
        <div className="p-4 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-neutral-50 text-left">
                <th className="px-3 py-2 text-xs font-medium text-neutral-500">功能</th>
                <th className="px-3 py-2 text-xs font-medium text-neutral-500">Join</th>
                <th className="px-3 py-2 text-xs font-medium text-neutral-500">来源</th>
                <th className="px-3 py-2 text-xs font-medium text-neutral-500">控件</th>
                <th className="px-3 py-2 text-xs font-medium text-neutral-500">设备</th>
                <th className="px-3 py-2 text-xs font-medium text-neutral-500 w-16">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {editData.functions.map((f, i) => (
                <tr key={i} className="hover:bg-neutral-50">
                  <td className="px-3 py-2">
                    <input value={f.name} onChange={(e) => updateFunction(i, 'name', e.target.value)}
                      className="w-full px-2 py-1 border border-neutral-200 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </td>
                  <td className="px-3 py-2">
                    <input type="number" value={f.join_number} onChange={(e) => {
                      const val = parseInt(e.target.value) || 0
                      updateFunction(i, 'join_number', val)
                      updateFunction(i, 'join_source', val > 0 ? 'user_specified' : 'auto')
                    }} className="w-20 px-2 py-1 border border-neutral-200 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </td>
                  <td className="px-3 py-2">
                    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${
                      f.join_source === 'user_specified'
                        ? 'bg-emerald-50 text-emerald-700'
                        : 'bg-indigo-50 text-indigo-700'
                    }`}>
                      {f.join_source === 'user_specified' ? '用户指定' : '自动分配'}
                    </span>
                  </td>
                  <td className="px-3 py-2">
                    <input value={f.btn_type || f.control_type || ''} onChange={(e) => updateFunction(i, 'control_type', e.target.value)}
                      className="w-full px-2 py-1 border border-neutral-200 rounded text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </td>
                  <td className="px-3 py-2">
                    <input value={f.device || ''} onChange={(e) => updateFunction(i, 'device', e.target.value)}
                      className="w-full px-2 py-1 border border-neutral-200 rounded text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </td>
                  <td className="px-3 py-2">
                    <button onClick={() => removeFunction(i)} className="text-red-400 hover:text-red-600 text-xs">删除</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <button onClick={addFunction}
            className="mt-2 px-3 py-1.5 text-xs text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-md transition-colors">
            + 添加功能
          </button>
        </div>
      )}

      {/* Page table */}
      {activeTab === 'pages' && (
        <div className="p-4">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-neutral-50 text-left">
                <th className="px-3 py-2 text-xs font-medium text-neutral-500">页面名</th>
                <th className="px-3 py-2 text-xs font-medium text-neutral-500">类型</th>
                <th className="px-3 py-2 text-xs font-medium text-neutral-500 w-16">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {editData.pages.map((p, i) => (
                <tr key={i} className="hover:bg-neutral-50">
                  <td className="px-3 py-2">
                    <input value={p.name} onChange={(e) => updatePage(i, 'name', e.target.value)}
                      className="w-full px-2 py-1 border border-neutral-200 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </td>
                  <td className="px-3 py-2">
                    <select value={p.type} onChange={(e) => updatePage(i, 'type', e.target.value)}
                      className="px-2 py-1 border border-neutral-200 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none">
                      <option value="main">main</option>
                      <option value="dialog">dialog</option>
                      <option value="subpage">subpage</option>
                    </select>
                  </td>
                  <td className="px-3 py-2">
                    <button onClick={() => removePage(i)} className="text-red-400 hover:text-red-600 text-xs">删除</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <button onClick={addPage}
            className="mt-2 px-3 py-1.5 text-xs text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-md transition-colors">
            + 添加页面
          </button>
        </div>
      )}

      {/* Actions */}
      <div className="px-4 py-4 border-t border-neutral-200 flex justify-between">
        <button onClick={onReParse}
          className="px-4 py-2 border border-neutral-300 text-neutral-700 text-sm rounded-lg hover:bg-neutral-50">
          修改后重新解析
        </button>
        <button onClick={() => onConfirm(editData)}
          className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg">
          确认生成
        </button>
      </div>
    </div>
  )
}

interface Props {
  currentMissing: string[]
  initialMissing: string[]
}

export default function ClarificationCard({ currentMissing, initialMissing }: Props) {
  const total = initialMissing.length
  const resolvedCount = Math.max(0, total - currentMissing.length)
  const progress = total > 0 ? (resolvedCount / total) * 100 : 0
  const resolvedItems = initialMissing.filter(item => !currentMissing.includes(item))
  const allDone = resolvedCount === total && total > 0

  return (
    <div className="bg-orange-50 border border-orange-200 rounded-xl p-5 shadow-sm">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <div className="w-6 h-6 rounded-full bg-orange-100 flex items-center justify-center shrink-0">
          <svg className="w-3.5 h-3.5 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <span className="text-sm font-semibold text-orange-800">缺失信息</span>
        <span className="ml-auto text-xs text-orange-500 font-medium tabular-nums">
          已收集 {resolvedCount}/{total} 项
        </span>
      </div>

      {/* Items */}
      <div className="space-y-2 mb-4">
        {resolvedItems.map((item, i) => (
          <div
            key={`resolved_${i}`}
            className="flex items-start gap-2.5 bg-emerald-50 border border-emerald-100 rounded-lg px-3 py-2 opacity-60 transition-all duration-500 ease-out"
          >
            <span className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
              ✓
            </span>
            <span className="text-xs text-slate-400 line-through leading-relaxed">{item}</span>
          </div>
        ))}

        {currentMissing.map((item, i) => (
          <div
            key={`pending_${i}`}
            className="flex items-start gap-2.5 bg-white border border-orange-100 rounded-lg px-3 py-2 transition-all duration-300"
          >
            <span className="w-5 h-5 rounded-full bg-orange-100 text-orange-600 flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
              {resolvedCount + i + 1}
            </span>
            <span className="text-xs text-slate-700 leading-relaxed flex-1">{item}</span>
            <span className="w-1.5 h-1.5 rounded-full bg-orange-300 animate-pulse shrink-0 mt-1.5" />
          </div>
        ))}
      </div>

      {/* Progress bar */}
      {total > 0 && (
        <div>
          <div className="h-1.5 bg-orange-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-orange-400 to-orange-500 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-[10px] text-orange-400 mt-1.5 leading-snug">
            {allDone
              ? '所有信息已收集，正在重新解析...'
              : '请在左侧逐项补充，完成后将自动重新解析'}
          </p>
        </div>
      )}
    </div>
  )
}

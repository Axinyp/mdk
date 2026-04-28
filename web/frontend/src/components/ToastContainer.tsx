import { useToast } from '../stores/toast'

const VARIANT_CLS: Record<string, string> = {
  success: 'border-l-4 border-emerald-500',
  error: 'border-l-4 border-red-500',
  info: 'border-l-4 border-slate-500',
}

export default function ToastContainer() {
  const { messages, dismiss } = useToast()

  if (messages.length === 0) return null

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
      {messages.map(m => (
        <div
          key={m.id}
          onClick={() => dismiss(m.id)}
          className={`pointer-events-auto bg-slate-800 text-white text-sm rounded-lg shadow-xl px-4 py-3 max-w-sm cursor-pointer transition-all ${VARIANT_CLS[m.variant]}`}
        >
          {m.text}
        </div>
      ))}
    </div>
  )
}

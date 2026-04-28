import { create } from 'zustand'

export type ToastVariant = 'success' | 'error' | 'info'

export interface ToastMessage {
  id: number
  text: string
  variant: ToastVariant
}

interface ToastState {
  messages: ToastMessage[]
  push: (text: string, variant?: ToastVariant) => void
  dismiss: (id: number) => void
}

let counter = 0

export const useToast = create<ToastState>((set, get) => ({
  messages: [],
  push: (text, variant = 'info') => {
    const id = ++counter
    set(s => ({ messages: [...s.messages, { id, text, variant }] }))
    setTimeout(() => get().dismiss(id), 3000)
  },
  dismiss: id => set(s => ({ messages: s.messages.filter(m => m.id !== id) })),
}))

export const toast = {
  success: (text: string) => useToast.getState().push(text, 'success'),
  error: (text: string) => useToast.getState().push(text, 'error'),
  info: (text: string) => useToast.getState().push(text, 'info'),
}

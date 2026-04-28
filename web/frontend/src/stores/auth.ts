import { create } from 'zustand'
import api from '../api/client'

interface User {
  id: number
  username: string
  role: 'admin' | 'member'
  status: 'active' | 'disabled'
}

interface AuthState {
  user: User | null
  token: string | null
  loading: boolean
  login: (username: string, password: string) => Promise<{ must_change_password: boolean }>
  logout: () => void
  fetchMe: () => Promise<void>
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('token'),
  loading: false,

  login: async (username, password) => {
    const { data } = await api.post('/auth/login', { username, password })
    localStorage.setItem('token', data.access_token)
    set({ token: data.access_token })
    const me = await api.get('/auth/me')
    set({ user: me.data })
    return { must_change_password: data.must_change_password }
  },

  logout: () => {
    localStorage.removeItem('token')
    set({ user: null, token: null })
  },

  fetchMe: async () => {
    set({ loading: true })
    try {
      const { data } = await api.get('/auth/me')
      set({ user: data, loading: false })
    } catch {
      localStorage.removeItem('token')
      set({ user: null, token: null, loading: false })
    }
  },
}))

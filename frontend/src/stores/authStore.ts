import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { api } from '../services/api'

export interface User {
  id: string
  username: string
  email: string
  full_name: string
  is_admin: boolean
}

export interface Device {
  id: string
  name: string
  device_type: string
  platform: string
  last_seen: string | null
}

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  deviceToken: string | null
  devices: Device[]
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  
  login: (username: string, password: string, deviceInfo?: Partial<Device>) => Promise<void>
  register: (username: string, email: string, password: string, fullName: string) => Promise<void>
  logout: () => Promise<void>
  refreshAccessToken: () => Promise<void>
  fetchUser: () => Promise<void>
  fetchDevices: () => Promise<void>
  registerDevice: (device: Partial<Device>) => Promise<string>
  clearError: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      deviceToken: null,
      devices: [],
      isAuthenticated: false,
      isLoading: false,
      error: null,

      clearError: () => set({ error: null }),

      login: async (username: string, password: string, deviceInfo = {}) => {
        set({ isLoading: true, error: null })
        try {
          const response = await api.post('/auth/login', {
            username,
            password,
            device_name: deviceInfo.name || navigator.userAgent,
            device_type: deviceInfo.device_type || 'web',
            platform: deviceInfo.platform || navigator.platform,
          })
          
          const { access_token, refresh_token, expires_in } = response.data
          
          set({
            accessToken: access_token,
            refreshToken: refresh_token,
            isAuthenticated: true,
            isLoading: false,
          })
          
          await get().fetchUser()
          await get().fetchDevices()
        } catch (error: any) {
          set({ 
            error: error.response?.data?.detail || 'Login failed', 
            isLoading: false,
            isAuthenticated: false,
          })
          throw error
        }
      },

      register: async (username: string, email: string, password: string, fullName: string) => {
        set({ isLoading: true, error: null })
        try {
          const response = await api.post('/auth/register', {
            username,
            email,
            password,
            full_name: fullName,
          })
          
          const { access_token, refresh_token } = response.data
          
          set({
            accessToken: access_token,
            refreshToken: refresh_token,
            isAuthenticated: true,
            isLoading: false,
          })
          
          await get().fetchUser()
        } catch (error: any) {
          set({ 
            error: error.response?.data?.detail || 'Registration failed', 
            isLoading: false,
          })
          throw error
        }
      },

      logout: async () => {
        try {
          await api.post('/auth/logout')
        } catch {
          // Ignore logout errors
        }
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          deviceToken: null,
          devices: [],
          isAuthenticated: false,
        })
      },

      refreshAccessToken: async () => {
        const { refreshToken } = get()
        if (!refreshToken) return
        
        try {
          const response = await api.post('/auth/refresh', { refresh_token: refreshToken })
          const { access_token, refresh_token } = response.data
          set({ accessToken: access_token, refreshToken: refresh_token })
        } catch {
          get().logout()
        }
      },

      fetchUser: async () => {
        try {
          const response = await api.get('/auth/me')
          set({ user: response.data })
        } catch {
          set({ user: null })
        }
      },

      fetchDevices: async () => {
        try {
          const response = await api.get('/auth/devices')
          set({ devices: response.data })
        } catch {
          set({ devices: [] })
        }
      },

      registerDevice: async (deviceInfo) => {
        const response = await api.post('/auth/devices', deviceInfo)
        const { device_id, device_token } = response.data
        
        set((state) => ({
          devices: [...state.devices, { 
            id: device_id, 
            ...deviceInfo,
            last_seen: null,
          } as Device],
          deviceToken: device_token,
        }))
        
        return device_token
      },
    }),
    {
      name: 'miniclaw-auth',
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        deviceToken: state.deviceToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)

export const useAuth = () => useAuthStore((state) => ({
  user: state.user,
  isAuthenticated: state.isAuthenticated,
  isLoading: state.isLoading,
  error: state.error,
  login: state.login,
  register: state.register,
  logout: state.logout,
  clearError: state.clearError,
}))
import { create } from 'zustand'

type ConnectionType = 'websocket' | 'polling' | 'disconnected'

interface ConnectionState {
  isConnected: boolean
  connectionType: ConnectionType
  setConnected: (connected: boolean) => void
  setConnectionType: (type: ConnectionType) => void
}

export const useConnectionStore = create<ConnectionState>((set) => ({
  isConnected: false,
  connectionType: 'disconnected',
  setConnected: (isConnected) => set({ isConnected }),
  setConnectionType: (connectionType) => set({ connectionType }),
}))
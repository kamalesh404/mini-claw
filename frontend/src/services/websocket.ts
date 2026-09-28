import { useAuthStore } from '../stores/authStore'
import { wsUrl } from './api'

type MessageHandler = (data: any) => void

interface WebSocketService {
  connect: (path: string) => void
  disconnect: () => void
  send: (data: any) => void
  onMessage: (handler: MessageHandler) => () => void
  onOpen: (handler: () => void) => () => void
  onClose: (handler: () => void) => () => void
  onError: (handler: (error: Event) => void) => () => void
}

class WebSocketManager implements WebSocketService {
  private ws: WebSocket | null = null
  private messageHandlers: Set<MessageHandler> = new Set()
  private openHandlers: Set<() => void> = new Set()
  private closeHandlers: Set<() => void> = new Set()
  private errorHandlers: Set<(error: Event) => void> = new Set()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private currentPath = ''

  connect(path: string) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return
    }

    this.currentPath = path
    const token = useAuthStore.getState().accessToken
    if (!token) {
      console.warn('No access token for WebSocket connection')
      return
    }

    const url = `${wsUrl(path)}?token=${encodeURIComponent(token)}`
    this.ws = new WebSocket(url)

    this.ws.onopen = () => {
      console.log(`WebSocket connected: ${path}`)
      this.reconnectAttempts = 0
      this.openHandlers.forEach((h) => h())
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        this.messageHandlers.forEach((h) => h(data))
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    }

    this.ws.onclose = () => {
      console.log(`WebSocket disconnected: ${path}`)
      this.closeHandlers.forEach((h) => h())
      this.attemptReconnect()
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      this.errorHandlers.forEach((h) => h(error))
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Max reconnect attempts reached')
      return
    }

    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
    
    setTimeout(() => {
      if (this.currentPath) {
        console.log(`Reconnecting... (attempt ${this.reconnectAttempts})`)
        this.connect(this.currentPath)
      }
    }, delay)
  }

  disconnect() {
    this.maxReconnectAttempts = 0
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    } else {
      console.warn('WebSocket not connected, cannot send:', data)
    }
  }

  onMessage(handler: MessageHandler) {
    this.messageHandlers.add(handler)
    return () => this.messageHandlers.delete(handler)
  }

  onOpen(handler: () => void) {
    this.openHandlers.add(handler)
    return () => this.openHandlers.delete(handler)
  }

  onClose(handler: () => void) {
    this.closeHandlers.add(handler)
    return () => this.closeHandlers.delete(handler)
  }

  onError(handler: (error: Event) => void) {
    this.errorHandlers.add(handler)
    return () => this.errorHandlers.delete(handler)
  }
}

export const wsManager = new WebSocketManager()

export const createWebSocketService = (path: string) => ({
  connect: () => wsManager.connect(path),
  disconnect: () => wsManager.disconnect(),
  send: (data: any) => wsManager.send(data),
  onMessage: (handler: MessageHandler) => wsManager.onMessage(handler),
  onOpen: (handler: () => void) => wsManager.onOpen(handler),
  onClose: (handler: () => void) => wsManager.onClose(handler),
  onError: (handler: (error: Event) => void) => wsManager.onError(handler),
})
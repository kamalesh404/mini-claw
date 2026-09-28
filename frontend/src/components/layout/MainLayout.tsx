import { Outlet } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { useAuth } from '../../stores/authStore'
import { useTheme } from '../../stores/themeStore'
import { wsManager } from '../../services/websocket'
import { useConnectionStore } from '../../stores/connectionStore'

export function MainLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { isAuthenticated } = useAuth()
  const { initializeTheme } = useTheme()
  const { setConnected, setConnectionType } = useConnectionStore()

  useEffect(() => {
    initializeTheme()
  }, [initializeTheme])

  useEffect(() => {
    if (!isAuthenticated) return

    const unsubOpen = wsManager.onOpen(() => {
      setConnected(true)
      setConnectionType('websocket')
    })

    const unsubClose = wsManager.onClose(() => {
      setConnected(false)
      setConnectionType('disconnected')
    })

    const unsubError = wsManager.onError(() => {
      setConnected(false)
      setConnectionType('disconnected')
    })

    wsManager.connect('/events')

    return () => {
      unsubOpen()
      unsubClose()
      unsubError()
      wsManager.disconnect()
    }
  }, [isAuthenticated, setConnected, setConnectionType])

  if (!isAuthenticated) {
    return <Outlet />
  }

  return (
    <div className="min-h-screen bg-dark-50 dark:bg-dark-950">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <Header />
      <main className="lg:pl-64 min-h-[calc(100vh-4rem)]">
        <div className="p-4 lg:p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
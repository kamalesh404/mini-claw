import { clsx } from 'clsx'
import { Sun, Moon, Monitor, Bell, ChevronDown, Wifi, WifiOff } from 'lucide-react'
import { useTheme } from '../../stores/themeStore'
import { useAuth } from '../../stores/authStore'
import { Button } from '../ui/Button'
import { useConnectionStore } from '../../stores/connectionStore'

export function Header() {
  const { resolvedTheme, toggleTheme } = useTheme()
  const { user } = useAuth()
  const { isConnected, connectionType } = useConnectionStore()

  return (
    <header className="sticky top-0 z-30 bg-white/80 dark:bg-dark-950/80 backdrop-blur-sm border-b border-dark-200 dark:border-dark-800">
      <div className="flex items-center justify-between h-16 px-4 lg:px-6">
        <div className="flex items-center gap-4 lg:hidden">
          <button className="p-2 rounded-lg hover:bg-dark-100 dark:hover:bg-dark-800" aria-label="Open menu">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        </div>

        <div className="flex-1 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-lg font-semibold text-dark-900 dark:text-white hidden sm:block">
              MiniClaw
            </h1>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleTheme}
              aria-label={resolvedTheme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {resolvedTheme === 'dark' ? (
                <Moon className="w-5 h-5" />
              ) : (
                <Sun className="w-5 h-5" />
              )}
            </Button>

            <div className="flex items-center gap-2 px-2 py-1 rounded-full bg-green-100 dark:bg-green-900/30">
              {connectionType === 'websocket' ? (
                <Wifi className="w-4 h-4 text-green-600 dark:text-green-400" />
              ) : connectionType === 'polling' ? (
                <Monitor className="w-4 h-4 text-yellow-600 dark:text-yellow-400" />
              ) : (
                <WifiOff className="w-4 h-4 text-red-600 dark:text-red-400" />
              )}
              <span className="text-xs font-medium text-dark-700 dark:text-dark-300">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>

            <Button variant="ghost" size="sm" className="relative">
              <Bell className="w-5 h-5" />
              <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                3
              </span>
            </Button>

            <div className="hidden sm:flex items-center gap-3 pl-4 border-l border-dark-200 dark:border-dark-800">
              <div className="w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
                <span className="text-sm font-medium text-primary-600 dark:text-primary-400">
                  {user?.full_name?.charAt(0) || user?.username?.charAt(0) || 'U'}
                </span>
              </div>
              <div className="text-left">
                <p className="text-sm font-medium text-dark-900 dark:text-white">
                  {user?.full_name || user?.username}
                </p>
                <p className="text-xs text-dark-500 dark:text-dark-400">
                  {user?.email}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}
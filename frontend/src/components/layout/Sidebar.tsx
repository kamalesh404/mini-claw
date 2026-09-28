import { NavLink, useLocation } from 'react-router-dom'
import { clsx } from 'clsx'
import {
  LayoutDashboard,
  MessageSquare,
  CheckSquare,
  Cpu,
  FolderOpen,
  GitBranch,
  Zap,
  Database,
  Activity,
  Settings,
  LogOut,
  Menu,
  X,
} from 'lucide-react'
import { useAuth } from '../../stores/authStore'
import { Button } from '../ui/Button'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Chat', href: '/chat', icon: MessageSquare },
  { name: 'Tasks', href: '/tasks', icon: CheckSquare },
  { name: 'PC Status', href: '/pc', icon: Cpu },
  { name: 'Files', href: '/files', icon: FolderOpen },
  { name: 'GitHub', href: '/github', icon: GitBranch },
  { name: 'Automations', href: '/automations', icon: Zap },
  { name: 'Memory', href: '/memory', icon: Database },
  { name: 'Activity', href: '/activity', icon: Activity },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export function Sidebar({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const location = useLocation()
  const { user, logout } = useAuth()

  return (
    <>
      <button
        className={clsx('fixed top-4 left-4 z-50 lg:hidden p-2 rounded-lg bg-white dark:bg-dark-900 shadow-lg', isOpen && 'left-64')}
        onClick={onClose}
        aria-label={isOpen ? 'Close sidebar' : 'Open sidebar'}
      >
        {isOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>

      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-40 w-64 transform bg-white dark:bg-dark-950 border-r border-dark-200 dark:border-dark-800 transition-transform duration-300 ease-in-out lg:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
        aria-label="Sidebar"
      >
        <div className="flex flex-col h-full">
          <div className="flex items-center gap-3 px-6 py-5 border-b border-dark-200 dark:border-dark-800">
            <div className="w-9 h-9 rounded-lg bg-primary-600 flex items-center justify-center">
              <Cpu className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-dark-900 dark:text-white">MiniClaw</h1>
              <p className="text-xs text-dark-500 dark:text-dark-400">Personal AI Agent</p>
            </div>
          </div>

          <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto" aria-label="Main navigation">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href || 
                (item.href !== '/' && location.pathname.startsWith(item.href))
              const Icon = item.icon
              
              return (
                <NavLink
                  key={item.name}
                  to={item.href}
                  onClick={onClose}
                  className={({ isActive: active }) => clsx(
                    'sidebar-link',
                    active && 'sidebar-link-active',
                    isActive && 'bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300'
                  )}
                  aria-current={isActive ? 'page' : undefined}
                >
                  <Icon className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
                  <span>{item.name}</span>
                </NavLink>
              )
            })}
          </nav>

          <div className="p-3 border-t border-dark-200 dark:border-dark-800">
            <div className="flex items-center gap-3 px-3 py-2 mb-2">
              <div className="w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
                <Cpu className="w-4 h-4 text-primary-600 dark:text-primary-400" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-dark-900 dark:text-white truncate">
                  {user?.full_name || user?.username}
                </p>
                <p className="text-xs text-dark-500 dark:text-dark-400 truncate">
                  {user?.email}
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              className="w-full justify-start"
              onClick={() => { logout(); onClose(); }}
            >
              <LogOut className="w-5 h-5" />
              <span>Sign out</span>
            </Button>
          </div>
        </div>
      </aside>

      {isOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}
    </>
  )
}
import { useEffect, useState } from 'react'
import { User, Shield, Bell, HardDrive, Cpu, Palette, Key, Loader2, Save, Check } from 'lucide-react'
import { api } from '../services/api'
import { Card, CardHeader, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Badge } from '../components/ui/Badge'
import { useAuth } from '../stores/authStore'
import { useTheme } from '../stores/themeStore'
import { clsx } from 'clsx'

export function Settings() {
  const { user, logout } = useAuth()
  const { theme, resolvedTheme, setTheme } = useTheme()
  const [settings, setSettings] = useState<any>({})
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [tabs, setTabs] = useState<'profile' | 'security' | 'notifications' | 'appearance' | 'advanced'>('profile')

  useEffect(() => {
    fetchSettings()
  }, [])

  const fetchSettings = async () => {
    try {
      const res = await api.get('/settings')
      setSettings(res.data.user || {})
    } catch (error) {
      console.error('Failed to fetch settings:', error)
    }
  }

  const handleSave = async (key: string, value: string) => {
    setSaving(true)
    try {
      await api.post('/settings', { key, value })
      setSettings(prev => ({ ...prev, [key]: value }))
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (error) {
      console.error('Failed to save setting:', error)
    } finally {
      setSaving(false)
    }
  }

  const SettingItem = ({ label, children, description }: { label: string; children: React.ReactNode; description?: string }) => (
    <div className="flex items-start justify-between gap-4 py-4 border-b border-dark-100 dark:border-dark-800 last:border-0">
      <div className="flex-1">
        <p className="font-medium text-dark-900 dark:text-white">{label}</p>
        {description && <p className="text-sm text-dark-500 dark:text-dark-400 mt-1">{description}</p>}
      </div>
      <div className="flex-shrink-0">{children}</div>
    </div>
  )

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-dark-900 dark:text-white">Settings</h1>
        <p className="text-dark-500 dark:text-dark-400">Manage your account and preferences</p>
      </div>

      <div className="flex gap-2 border-b border-dark-200 dark:border-dark-800">
        {(['profile', 'security', 'notifications', 'appearance', 'advanced'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setTabs(tab)}
            className={clsx(
              'px-4 py-2 text-sm font-medium rounded-t-lg border-b-2 transition-colors',
              tabs === tab
                ? 'border-primary-600 text-primary-600 dark:text-primary-400'
                : 'border-transparent text-dark-500 hover:text-dark-700 dark:text-dark-400 dark:hover:text-dark-200'
            )}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {tabs === 'profile' && (
        <Card>
          <CardHeader title="Profile" subtitle="Manage your account information" />
          <CardContent>
            <div className="space-y-4">
              <SettingItem label="Username" description="Your unique username">
                <span className="text-dark-900 dark:text-white font-mono">{user?.username}</span>
              </SettingItem>
              <SettingItem label="Email" description="Your email address">
                <span className="text-dark-900 dark:text-white">{user?.email}</span>
              </SettingItem>
              <SettingItem label="Full Name" description="Your display name">
                <Input
                  value={settings.full_name || ''}
                  onChange={(e) => handleSave('full_name', e.target.value)}
                  placeholder="Enter your name"
                />
              </SettingItem>
              <SettingItem label="Admin Access" description="Administrative privileges">
                <Badge variant={user?.is_admin ? 'success' : 'gray'}>
                  {user?.is_admin ? 'Enabled' : 'Disabled'}
                </Badge>
              </SettingItem>
            </div>
          </CardContent>
        </Card>
      )}

      {tabs === 'security' && (
        <Card>
          <CardHeader title="Security" subtitle="Authentication and device management" />
          <CardContent>
            <div className="space-y-4">
              <SettingItem label="Active Sessions" description="Manage your logged-in devices">
                <Button variant="secondary" size="sm" asChild>
                  <a href="/settings/devices">Manage Devices</a>
                </Button>
              </SettingItem>
              <SettingItem label="API Keys" description="Manage API access tokens">
                <Button variant="secondary" size="sm" asChild>
                  <a href="/settings/api-keys">Manage Keys</a>
                </Button>
              </SettingItem>
              <SettingItem label="Change Password" description="Update your password">
                <Button variant="secondary" size="sm" asChild>
                  <a href="/settings/password">Change Password</a>
                </Button>
              </SettingItem>
              <SettingItem label="Two-Factor Authentication" description="Add an extra layer of security">
                <Badge variant="gray">Coming Soon</Badge>
              </SettingItem>
            </div>
          </CardContent>
        </Card>
      )}

      {tabs === 'notifications' && (
        <Card>
          <CardHeader title="Notifications" subtitle="Configure how you receive alerts" />
          <CardContent>
            <div className="space-y-4">
              <SettingItem label="Push Notifications" description="Receive push notifications on your devices">
                <Button variant="secondary" size="sm" asChild>
                  <a href="/notifications/devices">Manage Devices</a>
                </Button>
              </SettingItem>
              <SettingItem label="Email Notifications" description="Receive email notifications for important events">
                <Badge variant="gray">Coming Soon</Badge>
              </SettingItem>
              <SettingItem label="Web Notifications" description="Browser notifications when tab is open">
                <Badge variant="gray">Coming Soon</Badge>
              </SettingItem>
              <SettingItem label="Telegram" description="Receive notifications via Telegram bot">
                <Badge variant="gray">Coming Soon</Badge>
              </SettingItem>
              <SettingItem label="Discord" description="Receive notifications via Discord webhook">
                <Badge variant="gray">Coming Soon</Badge>
              </SettingItem>
            </div>
          </CardContent>
        </Card>
      )}

      {tabs === 'appearance' && (
        <Card>
          <CardHeader title="Appearance" subtitle="Customize the look and feel" />
          <CardContent>
            <div className="space-y-4">
              <SettingItem label="Theme" description="Choose your preferred color scheme">
                <div className="flex gap-2">
                  {(['light', 'dark', 'system'] as const).map((t) => (
                    <button
                      key={t}
                      onClick={() => setTheme(t)}
                      className={clsx(
                        'px-4 py-2 rounded-lg border-2 transition-colors flex items-center gap-2',
                        theme === t
                          ? 'border-primary-600 bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
                          : 'border-dark-200 dark:border-dark-700 hover:border-dark-300 dark:hover:border-dark-600'
                      )}
                    >
                      {t === 'light' && <span className="w-3 h-3 rounded-full bg-yellow-300" />}
                      {t === 'dark' && <span className="w-3 h-3 rounded-full bg-dark-900" />}
                      {t === 'system' && <span className="w-3 h-3 rounded-full bg-gradient-to-r from-yellow-300 to-dark-900" />}
                      <span className="capitalize">{t}</span>
                    </button>
                  ))}
                </div>
              </SettingItem>
              <SettingItem label="Current Theme" description="Resolved theme based on your selection">
                <Badge variant="info">{resolvedTheme}</Badge>
              </SettingItem>
            </div>
          </CardContent>
        </Card>
      )}

      {tabs === 'advanced' && (
        <Card>
          <CardHeader title="Advanced" subtitle="System configuration and debugging" />
          <CardContent>
            <div className="space-y-4">
              <SettingItem label="Agent Status" description="Current agent configuration">
                <div className="flex items-center gap-4 text-sm">
                  <span className="text-dark-500 dark:text-dark-400">Model:</span>
                  <span className="font-mono text-dark-900 dark:text-white">{settings.model_name || 'Not configured'}</span>
                  <span className="text-dark-500 dark:text-dark-400">Provider:</span>
                  <span className="font-mono text-dark-900 dark:text-white">{settings.model_provider || 'Not configured'}</span>
                </div>
              </SettingItem>
              <SettingItem label="Browser Automation" description="Enable browser automation features">
                <Badge variant={settings.enable_browser ? 'success' : 'gray'}>
                  {settings.enable_browser ? 'Enabled' : 'Disabled'}
                </Badge>
              </SettingItem>
              <SettingItem label="GitHub Integration" description="Enable GitHub features">
                <Badge variant={settings.enable_github ? 'success' : 'gray'}>
                  {settings.enable_github ? 'Enabled' : 'Disabled'}
                </Badge>
              </SettingItem>
              <SettingItem label="Scheduler" description="Enable task scheduling">
                <Badge variant={settings.enable_scheduler ? 'success' : 'gray'}>
                  {settings.enable_scheduler ? 'Enabled' : 'Disabled'}
                </Badge>
              </SettingItem>
              <SettingItem label="Notifications" description="Enable notification system">
                <Badge variant={settings.enable_notifications ? 'success' : 'gray'}>
                  {settings.enable_notifications ? 'Enabled' : 'Disabled'}
                </Badge>
              </SettingItem>
              <SettingItem label="Remote Access" description="Allow external connections (requires secure tunnel)">
                <Badge variant={settings.enable_remote_access ? 'warning' : 'gray'}>
                  {settings.enable_remote_access ? 'Enabled' : 'Disabled'}
                </Badge>
              </SettingItem>
              <SettingItem label="Run Diagnostics" description="Check system health and connectivity">
                <Button variant="secondary" size="sm" onClick={async () => {
                  try {
                    const res = await api.get('/api/health')
                    alert('System healthy: ' + JSON.stringify(res.data))
                  } catch (e) {
                    alert('Diagnostics failed')
                  }
                }}>
                  <Cpu className="w-4 h-4 mr-1" />
                  Run Diagnostics
                </Button>
              </SettingItem>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="flex justify-end pt-4 border-t border-dark-200 dark:border-dark-800">
        <Button variant="secondary" onClick={logout}>
          <User className="w-4 h-4 mr-2" />
          Sign Out
        </Button>
      </div>
    </div>
  )
}
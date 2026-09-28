import { useEffect, useState } from 'react'
import { RefreshCw, Loader2, AlertTriangle, CheckCircle } from 'lucide-react'
import { api } from '../services/api'
import { wsManager } from '../services/websocket'
import { Card, CardHeader, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { ScrollArea } from '../components/ui/ScrollArea'
import type { PCStatus } from '../types'
import { clsx } from 'clsx'
import {
  Cpu,
  HardDrive,
  MemoryStick,
  Zap,
  Wifi,
  Battery,
  Thermometer,
  Activity,
  Server,
} from 'lucide-react'

export function PC() {
  const [pcStatus, setPcStatus] = useState<PCStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [wsConnected, setWsConnected] = useState(false)

  useEffect(() => {
    fetchStatus()
    const unsub = wsManager.onMessage((data) => {
      if (data.type === 'pc_status') {
        setPcStatus(data.data)
        setWsConnected(true)
      }
    })
    wsManager.connect('/pc')
    return () => {
      unsub()
      wsManager.disconnect()
    }
  }, [])

  const fetchStatus = async () => {
    try {
      const res = await api.get('/pc/status')
      setPcStatus(res.data)
    } catch (error) {
      console.error('Failed to fetch PC status:', error)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  const handleRefresh = () => {
    setRefreshing(true)
    fetchStatus()
  }

  const getCpuUsage = () => {
    if (!pcStatus?.cpu) return 0
    const usage = pcStatus.cpu.usage_percent
    return Array.isArray(usage) ? usage.reduce((a, b) => a + b, 0) / usage.length : usage
  }

  const getGpuUsage = () => {
    if (!pcStatus?.gpu?.gpus?.length) return 0
    return pcStatus.gpu.gpus.reduce((a, b) => a + b.load_percent, 0) / pcStatus.gpu.gpus.length
  }

  const getGpuTemp = () => {
    if (!pcStatus?.gpu?.gpus?.length) return 0
    return pcStatus.gpu.gpus.reduce((a, b) => a + b.temperature_c, 0) / pcStatus.gpu.gpus.length
  }

  const getRamPercent = () => pcStatus?.ram?.ram?.percent || 0
  const getDiskPercent = () => pcStatus?.disk?.percent || 0

  const getBattery = () => pcStatus?.battery

  const MetricCard = ({ 
    title, 
    value, 
    subtitle, 
    icon: Icon, 
    percent, 
    variant = 'default',
    color = 'primary'
  }: { 
    title: string
    value: string | number
    subtitle?: string
    icon: React.ComponentType<{ className?: string }>
    percent?: number
    variant?: 'default' | 'warning' | 'error'
    color?: string
  }) => {
    const colors = {
      primary: 'bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400',
      green: 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400',
      blue: 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400',
      orange: 'bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400',
      red: 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400',
    }

    const variants = {
      default: 'border-dark-200 dark:border-dark-700',
      warning: 'border-yellow-200 dark:border-yellow-800 bg-yellow-50 dark:bg-yellow-900/20',
      error: 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20',
    }

    return (
      <Card className={variants[variant]}>
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm text-dark-500 dark:text-dark-400">{title}</p>
            <p className="text-3xl font-bold text-dark-900 dark:text-white mt-1">{value}</p>
            {subtitle && <p className="text-xs text-dark-500 dark:text-dark-400 mt-1">{subtitle}</p>}
            {percent !== undefined && (
              <div className="mt-3 h-2 bg-dark-200 dark:bg-dark-700 rounded-full overflow-hidden">
                <div 
                  className="h-full rounded-full transition-all duration-500"
                  style={{ 
                    width: `${Math.min(100, Math.max(0, percent))}%`,
                    backgroundColor: percent > 90 ? '#ef4444' : percent > 70 ? '#f59e0b' : '#22c55e'
                  }} 
                />
              </div>
            )}
          </div>
          <div className={clsx('w-12 h-12 rounded-xl flex items-center justify-center', colors[color as keyof typeof colors])}>
            <Icon className="w-6 h-6" />
          </div>
        </div>
      </Card>
    )
  }

  if (loading) {
    return (
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <Card key={i} className="animate-pulse">
            <div className="h-4 bg-dark-200 dark:bg-dark-700 rounded w-3/4 mb-4" />
            <div className="h-10 bg-dark-200 dark:bg-dark-700 rounded w-1/2" />
          </Card>
        ))}
      </div>
    )
  }

  const cpuUsage = getCpuUsage()
  const gpuUsage = getGpuUsage()
  const gpuTemp = getGpuTemp()
  const ramPercent = getRamPercent()
  const diskPercent = getDiskPercent()
  const battery = getBattery()

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-dark-900 dark:text-white">PC Status</h1>
          <p className="text-dark-500 dark:text-dark-400">Real-time system monitoring</p>
        </div>
        <div className="flex items-center gap-3">
          <div className={clsx('flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium', 
            wsConnected 
              ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' 
              : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
          )}>
            {wsConnected ? (
              <>
                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                Live
              </>
            ) : (
              <>
                <span className="w-2 h-2 rounded-full bg-yellow-500" />
                Polling
              </>
            )}
          </div>
          <Button variant="secondary" onClick={handleRefresh} disabled={refreshing}>
            <RefreshCw className={clsx('w-4 h-4', refreshing && 'animate-spin')} />
            Refresh
          </Button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="CPU Usage"
          value={`${cpuUsage.toFixed(1)}%`}
          subtitle={`${pcStatus?.cpu?.core_count} cores • ${pcStatus?.cpu?.thread_count} threads`}
          icon={Cpu}
          percent={cpuUsage}
          variant={cpuUsage > 80 ? 'error' : cpuUsage > 60 ? 'warning' : 'default'}
          color="blue"
        />
        <MetricCard
          title="GPU Usage"
          value={`${gpuUsage.toFixed(1)}%`}
          subtitle={`Temp: ${gpuTemp.toFixed(0)}°C • ${pcStatus?.gpu?.gpus?.[0]?.name || 'N/A'}`}
          icon={Zap}
          percent={gpuUsage}
          variant={gpuUsage > 80 ? 'error' : gpuUsage > 60 ? 'warning' : 'default'}
          color="orange"
        />
        <MetricCard
          title="RAM Usage"
          value={`${ramPercent.toFixed(1)}%`}
          subtitle={`${pcStatus?.ram?.ram?.used_gb?.toFixed(1)} / ${pcStatus?.ram?.ram?.total_gb?.toFixed(1)} GB`}
          icon={MemoryStick}
          percent={ramPercent}
          variant={ramPercent > 85 ? 'error' : ramPercent > 70 ? 'warning' : 'default'}
          color="green"
        />
        <MetricCard
          title="Disk Usage"
          value={`${diskPercent.toFixed(1)}%`}
          subtitle={`${pcStatus?.disk?.free_gb?.toFixed(1)} GB free of ${pcStatus?.disk?.total_gb?.toFixed(1)} GB`}
          icon={HardDrive}
          percent={diskPercent}
          variant={diskPercent > 90 ? 'error' : diskPercent > 80 ? 'warning' : 'default'}
          color="red"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card>
          <CardHeader title="System Info" />
          <CardContent className="space-y-3">
            {pcStatus?.system && (
              <>
                <div className="flex justify-between text-sm">
                  <span className="text-dark-500 dark:text-dark-400">Platform</span>
                  <span className="font-medium text-dark-900 dark:text-white">{pcStatus.system.platform} {pcStatus.system.platform_release}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-dark-500 dark:text-dark-400">Architecture</span>
                  <span className="font-medium text-dark-900 dark:text-white">{pcStatus.system.architecture}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-dark-500 dark:text-dark-400">Processor</span>
                  <span className="font-medium text-dark-900 dark:text-white truncate max-w-[200px]">{pcStatus.system.processor}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-dark-500 dark:text-dark-400">Hostname</span>
                  <span className="font-medium text-dark-900 dark:text-white">{pcStatus.system.hostname}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-dark-500 dark:text-dark-400">Python</span>
                  <span className="font-medium text-dark-900 dark:text-white">{pcStatus.system.python_version}</span>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader title="GPU Details" />
          <CardContent className="space-y-3">
            {pcStatus?.gpu?.gpus?.map((gpu, i) => (
              <div key={i} className="space-y-2 p-3 rounded-lg bg-dark-50 dark:bg-dark-800/50">
                <p className="font-medium text-dark-900 dark:text-white">{gpu.name}</p>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-dark-500 dark:text-dark-400">Load</span>
                    <p className="font-medium">{gpu.load_percent.toFixed(1)}%</p>
                  </div>
                  <div>
                    <span className="text-dark-500 dark:text-dark-400">Temp</span>
                    <p className="font-medium">{gpu.temperature_c}°C</p>
                  </div>
                  <div>
                    <span className="text-dark-500 dark:text-dark-400">VRAM Used</span>
                    <p className="font-medium">{gpu.memory_used_mb} MB</p>
                  </div>
                  <div>
                    <span className="text-dark-500 dark:text-dark-400">VRAM Total</span>
                    <p className="font-medium">{gpu.memory_total_mb} MB</p>
                  </div>
                </div>
                <div className="h-2 bg-dark-200 dark:bg-dark-700 rounded-full overflow-hidden">
                  <div className="h-full bg-orange-500" style={{ width: `${gpu.load_percent}%` }} />
                </div>
              </div>
            ))}
            {!pcStatus?.gpu?.gpus?.length && (
              <p className="text-dark-500 dark:text-dark-400 text-center py-4">No GPU detected</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader title="Battery & Network" />
          <CardContent className="space-y-4">
            {battery?.has_battery ? (
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-dark-500 dark:text-dark-400">Battery Level</span>
                    <span className="font-medium">{battery.percent}%</span>
                  </div>
                  <div className="h-3 bg-dark-200 dark:bg-dark-700 rounded-full overflow-hidden">
                    <div 
                      className="h-full transition-all duration-500"
                      style={{ 
                        width: `${battery.percent}%`,
                        backgroundColor: battery.percent > 20 ? '#22c55e' : '#ef4444'
                      }} 
                    />
                  </div>
                  <div className="flex justify-between text-xs text-dark-500 dark:text-dark-400">
                    <span>{battery.power_plugged ? 'Charging' : 'On Battery'}</span>
                    {battery.time_left_seconds && (
                      <span>{Math.floor(battery.time_left_seconds / 60)} min remaining</span>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-dark-500 dark:text-dark-400 text-center py-4">No battery (desktop)</p>
            )}

            <div className="pt-4 border-t border-dark-200 dark:border-dark-700">
              <h4 className="font-medium text-dark-900 dark:text-white mb-3">Network Interfaces</h4>
              <ScrollArea className="max-h-48">
                {pcStatus?.network?.interfaces?.filter(i => i.is_up).map((iface) => (
                  <div key={iface.name} className="p-3 rounded-lg bg-dark-50 dark:bg-dark-800/50 mb-2">
                    <div className="flex justify-between text-sm mb-1">
                      <span className="font-medium text-dark-900 dark:text-white">{iface.name}</span>
                      <Badge variant="success" size="sm" dot>Up</Badge>
                    </div>
                    <div className="text-xs text-dark-500 dark:text-dark-400 space-y-1">
                      {iface.addresses.map((addr, i) => (
                        <div key={i}>{addr.address} / {addr.netmask}</div>
                      ))}
                      <div>Speed: {iface.speed_mbps} Mbps</div>
                      <div>↑ {(iface.bytes_sent / 1024 / 1024).toFixed(1)} MB ↓ {(iface.bytes_recv / 1024 / 1024).toFixed(1)} MB</div>
                    </div>
                  </div>
                ))}
              </ScrollArea>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader title="Top Processes" subtitle="By CPU usage" />
        <CardContent>
          <ScrollArea className="max-h-96">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-dark-200 dark:border-dark-700">
                  <th className="text-left p-3 font-medium text-dark-500 dark:text-dark-400">PID</th>
                  <th className="text-left p-3 font-medium text-dark-500 dark:text-dark-400">Name</th>
                  <th className="text-right p-3 font-medium text-dark-500 dark:text-dark-400">CPU %</th>
                  <th className="text-right p-3 font-medium text-dark-500 dark:text-dark-400">RAM %</th>
                  <th className="text-left p-3 font-medium text-dark-500 dark:text-dark-400">Status</th>
                </tr>
              </thead>
              <tbody>
                {pcStatus?.processes?.processes?.slice(0, 20).map((proc: any) => (
                  <tr key={proc.pid} className="border-b border-dark-100 dark:border-dark-800 hover:bg-dark-50 dark:hover:bg-dark-800/50">
                    <td className="p-3 text-dark-900 dark:text-white">{proc.pid}</td>
                    <td className="p-3 text-dark-900 dark:text-white truncate max-w-[200px]">{proc.name}</td>
                    <td className="p-3 text-right font-mono text-dark-900 dark:text-white">
                      {proc.cpu_percent?.toFixed(1) || 0}%
                    </td>
                    <td className="p-3 text-right font-mono text-dark-900 dark:text-white">
                      {proc.memory_percent?.toFixed(1) || 0}%
                    </td>
                    <td className="p-3">
                      <Badge variant={proc.status === 'running' ? 'success' : 'gray'} size="sm">
                        {proc.status}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  )
}
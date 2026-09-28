import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Cpu,
  HardDrive,
  MemoryStick,
  Github,
  Zap,
  Database,
  CheckCircle,
  AlertCircle,
  Clock,
  TrendingUp,
  TrendingDown,
} from 'lucide-react'
import { api } from '../services/api'
import { Card, CardHeader, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { ScrollArea } from '../components/ui/ScrollArea'
import type { PCStatus, Task, Automation, GitHubWorkflowRun } from '../types'

interface StatCardProps {
  title: string
  value: string | number
  icon: React.ReactNode
  trend?: { value: number; label: string }
  variant?: 'default' | 'warning' | 'error'
}

function StatCard({ title, value, icon, trend, variant = 'default' }: StatCardProps) {
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
          <p className="text-2xl font-bold text-dark-900 dark:text-white mt-1">{value}</p>
          {trend && (
            <div className="flex items-center gap-1 mt-2">
              {trend.value >= 0 ? (
                <TrendingUp className="w-4 h-4 text-green-600" />
              ) : (
                <TrendingDown className="w-4 h-4 text-red-600" />
              )}
              <span className="text-sm text-dark-500 dark:text-dark-400">{trend.label}</span>
            </div>
          )}
        </div>
        <div className="w-12 h-12 rounded-xl bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center text-primary-600 dark:text-primary-400">
          {icon}
        </div>
      </div>
    </Card>
  )
}

export function Dashboard() {
  const [pcStatus, setPcStatus] = useState<PCStatus | null>(null)
  const [recentTasks, setRecentTasks] = useState<Task[]>([])
  const [automations, setAutomations] = useState<Automation[]>([])
  const [githubWorkflows, setGithubWorkflows] = useState<GitHubWorkflowRun[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [pc, tasks, autos, workflows] = await Promise.allSettled([
          api.get('/pc/status'),
          api.get('/tasks?limit=5'),
          api.get('/automations?enabled_only=true&limit=5'),
          api.get('/github/workflows?limit=5'),
        ])

        if (pc.status === 'fulfilled') setPcStatus(pc.value)
        if (tasks.status === 'fulfilled') setRecentTasks(tasks.value)
        if (autos.status === 'fulfilled') setAutomations(autos.value)
        if (workflows.status === 'fulfilled') setGithubWorkflows(workflows.value)
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  const getCpuUsage = () => {
    if (!pcStatus?.cpu) return 0
    const usage = pcStatus.cpu.usage_percent
    return Array.isArray(usage) ? usage.reduce((a, b) => a + b, 0) / usage.length : usage
  }

  const getGpuUsage = () => {
    if (!pcStatus?.gpu?.gpus?.length) return 0
    return pcStatus.gpu.gpus.reduce((a, b) => a + b.load_percent, 0) / pcStatus.gpu.gpus.length
  }

  const getRamPercent = () => pcStatus?.ram?.ram?.percent || 0
  const getDiskPercent = () => pcStatus?.disk?.percent || 0

  if (loading) {
    return (
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="animate-pulse">
            <div className="h-4 bg-dark-200 dark:bg-dark-700 rounded w-3/4 mb-4" />
            <div className="h-8 bg-dark-200 dark:bg-dark-700 rounded w-1/2" />
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-dark-900 dark:text-white">Dashboard</h1>
          <p className="text-dark-500 dark:text-dark-400">System overview and recent activity</p>
        </div>
        <Button variant="secondary" asChild>
          <Link to="/chat">New Chat</Link>
        </Button>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="CPU Usage"
          value={`${getCpuUsage().toFixed(1)}%`}
          icon={<Cpu className="w-6 h-6" />}
          variant={getCpuUsage() > 80 ? 'error' : getCpuUsage() > 60 ? 'warning' : 'default'}
        />
        <StatCard
          title="GPU Usage"
          value={`${getGpuUsage().toFixed(1)}%`}
          icon={<Cpu className="w-6 h-6" />}
          variant={getGpuUsage() > 80 ? 'error' : getGpuUsage() > 60 ? 'warning' : 'default'}
        />
        <StatCard
          title="RAM Usage"
          value={`${getRamPercent().toFixed(1)}%`}
          icon={<MemoryStick className="w-6 h-6" />}
          variant={getRamPercent() > 85 ? 'error' : getRamPercent() > 70 ? 'warning' : 'default'}
        />
        <StatCard
          title="Disk Usage"
          value={`${getDiskPercent().toFixed(1)}%`}
          icon={<HardDrive className="w-6 h-6" />}
          variant={getDiskPercent() > 90 ? 'error' : getDiskPercent() > 80 ? 'warning' : 'default'}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader title="PC Status" subtitle="Real-time system metrics" />
          <CardContent>
            <ScrollArea className="h-64">
              <div className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <p className="text-sm text-dark-500 dark:text-dark-400">CPU</p>
                    <p className="text-lg font-semibold text-dark-900 dark:text-white">
                      {getCpuUsage().toFixed(1)}%
                    </p>
                    <p className="text-xs text-dark-500 dark:text-dark-400">
                      {pcStatus?.cpu?.core_count} cores / {pcStatus?.cpu?.thread_count} threads
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-dark-500 dark:text-dark-400">GPU</p>
                    <p className="text-lg font-semibold text-dark-900 dark:text-white">
                      {getGpuUsage().toFixed(1)}%
                    </p>
                    <p className="text-xs text-dark-500 dark:text-dark-400">
                      {pcStatus?.gpu?.gpus?.[0]?.name || 'N/A'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-dark-500 dark:text-dark-400">RAM</p>
                    <p className="text-lg font-semibold text-dark-900 dark:text-white">
                      {getRamPercent().toFixed(1)}%
                    </p>
                    <p className="text-xs text-dark-500 dark:text-dark-400">
                      {pcStatus?.ram?.ram?.used_gb?.toFixed(1)} / {pcStatus?.ram?.ram?.total_gb?.toFixed(1)} GB
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-dark-500 dark:text-dark-400">Disk</p>
                    <p className="text-lg font-semibold text-dark-900 dark:text-white">
                      {getDiskPercent().toFixed(1)}%
                    </p>
                    <p className="text-xs text-dark-500 dark:text-dark-400">
                      {pcStatus?.disk?.free_gb?.toFixed(1)} GB free
                    </p>
                  </div>
                </div>
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        <Card>
          <CardHeader 
            title="Recent Tasks" 
            subtitle="Latest task executions"
            action={<Link to="/tasks" className="text-sm text-primary-600 hover:underline">View all</Link>}
          />
          <CardContent>
            <ScrollArea className="h-64">
              {recentTasks.length === 0 ? (
                <p className="text-dark-500 dark:text-dark-400 text-center py-8">No recent tasks</p>
              ) : (
                <div className="space-y-3">
                  {recentTasks.map((task) => (
                    <div key={task.id} className="flex items-center justify-between p-3 rounded-lg bg-dark-50 dark:bg-dark-800/50">
                      <div className="flex items-center gap-3">
                        <div className={clsx('w-2 h-2 rounded-full', 
                          task.status === 'completed' && 'bg-green-500',
                          task.status === 'failed' && 'bg-red-500',
                          task.status === 'running' && 'bg-blue-500 animate-pulse',
                          task.status === 'waiting_for_approval' && 'bg-yellow-500',
                          ['queued', 'planning', 'cancelled'].includes(task.status) && 'bg-dark-400'
                        )} />
                        <div>
                          <p className="text-sm font-medium text-dark-900 dark:text-white">{task.title}</p>
                          <p className="text-xs text-dark-500 dark:text-dark-400 capitalize">{task.status.replace('_', ' ')}</p>
                        </div>
                      </div>
                      <span className="text-xs text-dark-500 dark:text-dark-400">
                        {new Date(task.created_at).toLocaleTimeString()}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader 
            title="Active Automations" 
            subtitle="Scheduled and event-triggered tasks"
            action={<Link to="/automations" className="text-sm text-primary-600 hover:underline">View all</Link>}
          />
          <CardContent>
            {automations.length === 0 ? (
              <p className="text-dark-500 dark:text-dark-400 text-center py-8">No active automations</p>
            ) : (
              <div className="space-y-3">
                {automations.map((auto) => (
                  <div key={auto.id} className="flex items-center justify-between p-3 rounded-lg bg-dark-50 dark:bg-dark-800/50">
                    <div>
                      <p className="text-sm font-medium text-dark-900 dark:text-white">{auto.name}</p>
                      <p className="text-xs text-dark-500 dark:text-dark-400 capitalize">{auto.trigger_type} trigger</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge variant={auto.is_enabled ? 'success' : 'gray'}>
                        {auto.is_enabled ? 'Enabled' : 'Disabled'}
                      </Badge>
                      {auto.next_run_at && (
                        <span className="text-xs text-dark-500 dark:text-dark-400">
                          Next: {new Date(auto.next_run_at).toLocaleString()}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader 
            title="GitHub Workflows" 
            subtitle="Recent CI/CD runs"
            action={<Link to="/github" className="text-sm text-primary-600 hover:underline">View all</Link>}
          />
          <CardContent>
            {githubWorkflows.length === 0 ? (
              <p className="text-dark-500 dark:text-dark-400 text-center py-8">No recent workflows</p>
            ) : (
              <div className="space-y-3">
                {githubWorkflows.map((wf) => (
                  <div key={wf.id} className="flex items-center justify-between p-3 rounded-lg bg-dark-50 dark:bg-dark-800/50">
                    <div className="flex items-center gap-3">
                      <div className={clsx('w-2 h-2 rounded-full',
                        wf.conclusion === 'success' && 'bg-green-500',
                        wf.conclusion === 'failure' && 'bg-red-500',
                        wf.status === 'in_progress' && 'bg-blue-500 animate-pulse',
                        ['queued', 'waiting'].includes(wf.status) && 'bg-yellow-500'
                      )} />
                      <div>
                        <p className="text-sm font-medium text-dark-900 dark:text-white">{wf.name}</p>
                        <p className="text-xs text-dark-500 dark:text-dark-400">#{wf.run_number} · {wf.head_branch}</p>
                      </div>
                    </div>
                    <span className="text-xs text-dark-500 dark:text-dark-400">
                      {wf.conclusion || wf.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

import { clsx } from 'clsx'
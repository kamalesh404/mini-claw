import { useEffect, useState } from 'react'
import { Plus, Play, Trash2, Edit, Loader2, ToggleLeft, ToggleRight, Clock, Zap, Repeat, Calendar, Bell, ExternalLink } from 'lucide-react'
import { api } from '../services/api'
import { Card, CardHeader, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Badge } from '../components/ui/Badge'
import { ScrollArea } from '../components/ui/ScrollArea'
import type { Automation } from '../types'
import { clsx } from 'clsx'

export function Automations() {
  const [automations, setAutomations] = useState<Automation[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [editing, setEditing] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    trigger_type: 'cron',
    trigger_config: { expression: '0 * * * *' },
    action_type: 'run_task',
    action_config: {},
  })
  const [triggerConfig, setTriggerConfig] = useState('')
  const [actionConfig, setActionConfig] = useState('')

  useEffect(() => {
    fetchAutomations()
  }, [])

  const fetchAutomations = async () => {
    setLoading(true)
    try {
      const res = await api.get('/automations')
      setAutomations(res.data.tasks || [])
    } catch (error) {
      console.error('Failed to fetch automations:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const triggerConfigParsed = JSON.parse(triggerConfig || '{}')
      const actionConfigParsed = JSON.parse(actionConfig || '{}')
      
      if (editing) {
        await api.patch(`/automations/${editing}`, {
          ...formData,
          trigger_config: triggerConfigParsed,
          action_config: actionConfigParsed,
        })
      } else {
        await api.post('/automations', {
          ...formData,
          trigger_config: triggerConfigParsed,
          action_config: actionConfigParsed,
        })
      }
      setCreating(false)
      setEditing(null)
      fetchAutomations()
    } catch (error) {
      console.error('Failed to save automation:', error)
    }
  }

  const handleEdit = (auto: Automation) => {
    setEditing(auto.id)
    setCreating(true)
    setFormData({
      name: auto.name,
      description: auto.description || '',
      trigger_type: auto.trigger_type,
      trigger_config: auto.trigger_config,
      action_type: auto.action_type,
      action_config: auto.action_config,
    })
    setTriggerConfig(JSON.stringify(auto.trigger_config, null, 2))
    setActionConfig(JSON.stringify(auto.action_config, null, 2))
  }

  const handleRun = async (id: string) => {
    try {
      await api.post(`/automations/${id}/run`)
      fetchAutomations()
    } catch (error) {
      console.error('Failed to run automation:', error)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this automation?')) return
    try {
      await api.delete(`/automations/${id}`)
      fetchAutomations()
    } catch (error) {
      console.error('Failed to delete automation:', error)
    }
  }

  const handleToggle = async (auto: Automation) => {
    try {
      await api.patch(`/automations/${auto.id}`, { is_enabled: !auto.is_enabled })
      fetchAutomations()
    } catch (error) {
      console.error('Failed to toggle automation:', error)
    }
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never'
    return new Date(dateStr).toLocaleString()
  }

  const getTriggerIcon = (type: string) => {
    switch (type) {
      case 'cron': return <Clock className="w-4 h-4" />
      case 'interval': return <Repeat className="w-4 h-4" />
      case 'date': return <Calendar className="w-4 h-4" />
      case 'event': return <Bell className="w-4 h-4" />
      default: return <Zap className="w-4 h-4" />
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map(i => (
          <Card key={i} className="animate-pulse">
            <div className="h-4 bg-dark-200 dark:bg-dark-700 rounded w-1/4 mb-4" />
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
          <h1 className="text-2xl font-bold text-dark-900 dark:text-white">Automations</h1>
          <p className="text-dark-500 dark:text-dark-400">Scheduled tasks and event-driven automations</p>
        </div>
        <Button onClick={() => { setCreating(true); setEditing(null); setFormData({ name: '', description: '', trigger_type: 'cron', trigger_config: { expression: '0 * * * *' }, action_type: 'run_task', action_config: {} }); setTriggerConfig('{}'); setActionConfig('{}') }}>
          <Plus className="w-4 h-4" />
          New Automation
        </Button>
      </div>

      {(creating || editing) && (
        <Card>
          <CardHeader title={editing ? 'Edit Automation' : 'Create Automation'} />
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid gap-4 md:grid-cols-2">
                <Input
                  label="Name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Automation name"
                  required
                />
                <Input
                  label="Description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Optional description"
                />
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-dark-700 dark:text-dark-300 mb-1">Trigger Type</label>
                  <select
                    value={formData.trigger_type}
                    onChange={(e) => setFormData({ ...formData, trigger_type: e.target.value })}
                    className="input"
                  >
                    <option value="cron">Cron Schedule</option>
                    <option value="interval">Interval</option>
                    <option value="date">One-time Date</option>
                    <option value="event">Event Trigger</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-dark-700 dark:text-dark-300 mb-1">Action Type</label>
                  <select
                    value={formData.action_type}
                    onChange={(e) => setFormData({ ...formData, action_type: e.target.value })}
                    className="input"
                  >
                    <option value="run_task">Run Task</option>
                    <option value="send_notification">Send Notification</option>
                    <option value="run_command">Run Command</option>
                    <option value="trigger_workflow">Trigger GitHub Workflow</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-dark-700 dark:text-dark-300 mb-1">Trigger Config (JSON)</label>
                <textarea
                  value={triggerConfig}
                  onChange={(e) => setTriggerConfig(e.target.value)}
                  className="input font-mono text-sm min-h-[120px] resize-y"
                  placeholder='{"expression": "0 * * * *"}'
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-dark-700 dark:text-dark-300 mb-1">Action Config (JSON)</label>
                <textarea
                  value={actionConfig}
                  onChange={(e) => setActionConfig(e.target.value)}
                  className="input font-mono text-sm min-h-[120px] resize-y"
                  placeholder='{}'
                />
              </div>

              <div className="flex justify-end gap-2">
                <Button type="button" variant="secondary" onClick={() => { setCreating(false); setEditing(null) }}>Cancel</Button>
                <Button type="submit" disabled={creating && editing}>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  {editing ? 'Update' : 'Create'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {automations.length === 0 && !creating && !editing ? (
        <Card className="text-center py-12">
          <Zap className="w-16 h-16 mx-auto mb-4 text-dark-300 dark:text-dark-700" />
          <h3 className="text-lg font-medium text-dark-900 dark:text-white">No automations yet</h3>
          <p className="text-dark-500 dark:text-dark-400 mt-1">Create your first automation to get started</p>
          <Button className="mt-4" onClick={() => setCreating(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Create Automation
          </Button>
        </Card>
      ) : (
        <div className="space-y-4">
          {automations.map((auto) => (
            <Card key={auto.id}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 flex-wrap">
                      <h3 className="font-semibold text-dark-900 dark:text-white">{auto.name}</h3>
                      {getTriggerIcon(auto.trigger_type)}
                      <Badge variant={auto.trigger_type === 'cron' ? 'info' : auto.trigger_type === 'interval' ? 'warning' : 'gray'} size="sm">
                        {auto.trigger_type}
                      </Badge>
                      <Badge variant={auto.is_enabled ? 'success' : 'gray'} size="sm">
                        {auto.is_enabled ? 'Enabled' : 'Disabled'}
                      </Badge>
                    </div>
                    {auto.description && (
                      <p className="text-sm text-dark-500 dark:text-dark-400 mt-1">{auto.description}</p>
                    )}
                    <div className="flex items-center gap-4 mt-2 text-xs text-dark-500 dark:text-dark-400">
                      <span>Runs: {auto.run_count} (✓{auto.success_count} ✗{auto.failure_count})</span>
                      {auto.last_run_at && <span>Last: {formatDate(auto.last_run_at)}</span>}
                      {auto.next_run_at && <span>Next: {formatDate(auto.next_run_at)}</span>}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <Button variant="ghost" size="sm" onClick={() => handleRun(auto.id)} title="Run now">
                      <Play className="w-4 h-4" />
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => handleToggle(auto)} title={auto.is_enabled ? 'Disable' : 'Enable'}>
                      {auto.is_enabled ? <ToggleLeft className="w-4 h-4" /> : <ToggleRight className="w-4 h-4" />}
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => handleEdit(auto)} title="Edit">
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => handleDelete(auto.id)} title="Delete" className="text-red-600 hover:text-red-700">
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
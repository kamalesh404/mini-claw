import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Play, X, Loader2, AlertTriangle, CheckCircle, Clock, ChevronRight } from 'lucide-react'
import { api } from '../services/api'
import { Card, CardHeader, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Input } from '../components/ui/Input'
import { ScrollArea } from '../components/ui/ScrollArea'
import type { Task, TaskStatus } from '../types'
import { clsx } from 'clsx'

export function Tasks() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [newTaskTitle, setNewTaskTitle] = useState('')
  const [newTaskDesc, setNewTaskDesc] = useState('')
  const [filterStatus, setFilterStatus] = useState<TaskStatus | 'all'>('all')

  const statusColors: Record<TaskStatus, string> = {
    queued: 'gray',
    planning: 'info',
    waiting_for_approval: 'warning',
    running: 'info',
    completed: 'success',
    failed: 'error',
    cancelled: 'gray',
  }

  useEffect(() => {
    fetchTasks()
  }, [filterStatus])

  const fetchTasks = async () => {
    setLoading(true)
    try {
      const res = await api.get(`/tasks?${filterStatus !== 'all' ? `status=${filterStatus}` : ''}`)
      setTasks(res.data)
    } catch (error) {
      console.error('Failed to fetch tasks:', error)
    } finally {
      setLoading(false)
    }
  }

  const createTask = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newTaskTitle.trim()) return
    
    setCreating(true)
    try {
      const res = await api.post('/tasks', {
        title: newTaskTitle,
        description: newTaskDesc,
      })
      setTasks([res.data, ...tasks])
      setNewTaskTitle('')
      setNewTaskDesc('')
    } catch (error) {
      console.error('Failed to create task:', error)
    } finally {
      setCreating(false)
    }
  }

  const executeTask = async (taskId: string) => {
    try {
      await api.post(`/tasks/${taskId}/execute`)
      fetchTasks()
    } catch (error) {
      console.error('Failed to execute task:', error)
    }
  }

  const deleteTask = async (taskId: string) => {
    if (!confirm('Are you sure you want to delete this task?')) return
    try {
      await api.delete(`/tasks/${taskId}`)
      setTasks(tasks.filter(t => t.id !== taskId))
    } catch (error) {
      console.error('Failed to delete task:', error)
    }
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '—'
    return new Date(dateStr).toLocaleString()
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
          <h1 className="text-2xl font-bold text-dark-900 dark:text-white">Tasks</h1>
          <p className="text-dark-500 dark:text-dark-400">Manage and execute automation tasks</p>
        </div>
        <Button onClick={() => setCreating(!creating)}>
          <Plus className="w-4 h-4" />
          {creating ? 'Cancel' : 'New Task'}
        </Button>
      </div>

      {creating && (
        <Card>
          <CardHeader title="Create New Task" />
          <CardContent>
            <form onSubmit={createTask} className="space-y-4">
              <Input
                label="Title"
                value={newTaskTitle}
                onChange={(e) => setNewTaskTitle(e.target.value)}
                placeholder="Enter task title"
                required
              />
              <div>
                <label className="block text-sm font-medium text-dark-700 dark:text-dark-300 mb-1">Description</label>
                <textarea
                  value={newTaskDesc}
                  onChange={(e) => setNewTaskDesc(e.target.value)}
                  placeholder="Optional description"
                  className="input min-h-[100px] resize-y"
                  rows={4}
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button type="button" variant="secondary" onClick={() => setCreating(false)}>Cancel</Button>
                <Button type="submit" disabled={creating}>
                  {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Create Task'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <div className="flex gap-2 overflow-x-auto pb-2">
        {(['all', 'queued', 'planning', 'waiting_for_approval', 'running', 'completed', 'failed', 'cancelled'] as const).map((status) => (
          <button
            key={status}
            onClick={() => setFilterStatus(status)}
            className={clsx(
              'px-3 py-1 rounded-full text-sm font-medium whitespace-nowrap transition-colors',
              filterStatus === status
                ? 'bg-primary-600 text-white'
                : 'bg-dark-100 text-dark-700 hover:bg-dark-200 dark:bg-dark-800 dark:text-dark-300 dark:hover:bg-dark-700'
            )}
          >
            {status.charAt(0).toUpperCase() + status.slice(1).replace('_', ' ')}
          </button>
        ))}
      </div>

      {tasks.length === 0 ? (
        <Card className="text-center py-12">
          <svg className="w-16 h-16 mx-auto mb-4 text-dark-300 dark:text-dark-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
          </svg>
          <h3 className="text-lg font-medium text-dark-900 dark:text-white">No tasks found</h3>
          <p className="text-dark-500 dark:text-dark-400 mt-1">Create your first task to get started</p>
        </Card>
      ) : (
        <div className="space-y-4">
          {tasks.map((task) => (
            <Card key={task.id}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 flex-wrap">
                      <h3 className="font-semibold text-dark-900 dark:text-white truncate">{task.title}</h3>
                      <Badge variant={statusColors[task.status] as any}>
                        {task.status.replace('_', ' ')}
                      </Badge>
                      {task.progress > 0 && task.status === 'running' && (
                        <div className="w-32 h-2 bg-dark-200 dark:bg-dark-700 rounded-full overflow-hidden">
                          <div className="h-full bg-primary-600 transition-all" style={{ width: `${task.progress}%` }} />
                        </div>
                      )}
                    </div>
                    {task.description && (
                      <p className="text-sm text-dark-500 dark:text-dark-400 mt-1 line-clamp-2">{task.description}</p>
                    )}
                    <div className="flex items-center gap-4 mt-2 text-xs text-dark-500 dark:text-dark-400">
                      <span>Created: {formatDate(task.created_at)}</span>
                      {task.started_at && <span>Started: {formatDate(task.started_at)}</span>}
                      {task.completed_at && <span>Completed: {formatDate(task.completed_at)}</span>}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    {task.status === 'queued' || task.status === 'failed' ? (
                      <Button size="sm" onClick={() => executeTask(task.id)}>
                        <Play className="w-4 h-4" />
                        Run
                      </Button>
                    ) : task.status === 'running' ? (
                      <Button size="sm" variant="secondary" disabled>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Running
                      </Button>
                    ) : task.status === 'waiting_for_approval' ? (
                      <Button size="sm" variant="secondary" disabled>
                        <AlertTriangle className="w-4 h-4" />
                        Waiting
                      </Button>
                    ) : (
                      <Button size="sm" variant="ghost" onClick={() => deleteTask(task.id)}>
                        <X className="w-4 h-4" />
                      </Button>
                    )}
                    <Link to={`/tasks/${task.id}`}>
                      <Button variant="ghost" size="sm">
                        <ChevronRight className="w-4 h-4" />
                      </Button>
                    </Link>
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
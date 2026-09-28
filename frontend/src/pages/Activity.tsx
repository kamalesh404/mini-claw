import { useEffect, useState } from 'react'
import { Filter, Loader2, AlertTriangle, CheckCircle, XCircle, Info, Clock, Github, Zap, Database, Terminal, Monitor, Bell } from 'lucide-react'
import { api } from '../services/api'
import { Card, CardHeader, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { ScrollArea } from '../components/ui/ScrollArea'
import type { Event } from '../types'
import { clsx } from 'clsx'

export function Activity() {
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('all')
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(true)
  const pageSize = 50

  const eventTypes = [
    { value: 'all', label: 'All Events', icon: Info },
    { value: 'agent.task', label: 'Agent Tasks', icon: Terminal },
    { value: 'agent.approval', label: 'Approvals', icon: AlertTriangle },
    { value: 'github', label: 'GitHub', icon: Github },
    { value: 'system', label: 'System', icon: Monitor },
    { value: 'automation', label: 'Automations', icon: Zap },
  ]

  useEffect(() => {
    fetchEvents(true)
  }, [filter])

  const fetchEvents = async (reset = false) => {
    if (reset) {
      setPage(1)
      setEvents([])
      setHasMore(true)
    }
    setLoading(true)
    try {
      const params = new URLSearchParams({ limit: pageSize.toString(), page: page.toString() })
      if (filter !== 'all') params.append('type', filter)
      
      const res = await api.get(`/events?${params.toString()}`)
      const newEvents = res.data.events || []
      
      if (reset) {
        setEvents(newEvents)
      } else {
        setEvents(prev => [...prev, ...newEvents])
      }
      setHasMore(newEvents.length === pageSize)
    } catch (error) {
      console.error('Failed to fetch events:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadMore = () => {
    if (!loading && hasMore) {
      setPage(p => p + 1)
    }
  }

  const getEventIcon = (type: string) => {
    if (type.startsWith('agent.task')) return <Terminal className="w-4 h-4" />
    if (type.startsWith('agent.approval')) return <AlertTriangle className="w-4 h-4" />
    if (type.startsWith('github')) return <Github className="w-4 h-4" />
    if (type.startsWith('system')) return <Monitor className="w-4 h-4" />
    if (type.startsWith('automation')) return <Zap className="w-4 h-4" />
    return <Info className="w-4 h-4" />
  }

  const getEventColor = (type: string) => {
    if (type.includes('completed') || type.includes('success')) return 'success'
    if (type.includes('failed') || type.includes('error')) return 'error'
    if (type.includes('started') || type.includes('created')) return 'info'
    if (type.includes('approval')) return 'warning'
    return 'gray'
  }

  const getEventTitle = (type: string) => {
    const parts = type.split('.')
    return parts.map(p => p.charAt(0).toUpperCase() + p.slice(1)).join(' • ')
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString()
  }

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, scrollHeight, clientHeight } = e.currentTarget
    if (scrollHeight - scrollTop - clientHeight < 100) {
      loadMore()
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-dark-900 dark:text-white">Activity Log</h1>
          <p className="text-dark-500 dark:text-dark-400">System events and audit trail</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex gap-1 bg-dark-100 dark:bg-dark-800 rounded-lg p-1">
            {eventTypes.map(({ value, label, icon: Icon }) => (
              <button
                key={value}
                onClick={() => setFilter(value)}
                className={clsx(
                  'px-3 py-1.5 rounded-md text-sm font-medium transition-colors flex items-center gap-1',
                  filter === value
                    ? 'bg-white dark:bg-dark-900 shadow-sm text-primary-600 dark:text-primary-400'
                    : 'text-dark-600 dark:text-dark-400 hover:text-dark-900 dark:hover:text-white'
                )}
              >
                <Icon className="w-3 h-3" />
                <span>{label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          {loading && events.length === 0 ? (
            <div className="p-8 text-center">
              <Loader2 className="w-8 h-8 animate-spin mx-auto text-primary-600" />
            </div>
          ) : events.length === 0 ? (
            <div className="p-8 text-center">
              <Info className="w-16 h-16 mx-auto mb-4 text-dark-300 dark:text-dark-700" />
              <h3 className="text-lg font-medium text-dark-900 dark:text-white">No events found</h3>
              <p className="text-dark-500 dark:text-dark-400 mt-1">Try changing the filter or check back later</p>
            </div>
          ) : (
            <ScrollArea className="max-h-[700px]" onScroll={handleScroll}>
              <div className="divide-y divide-dark-200 dark:divide-dark-700">
                {events.map((event) => (
                  <div key={event.id} className="p-4 hover:bg-dark-50 dark:hover:bg-dark-800/50">
                    <div className="flex items-start gap-3">
                      <div className={clsx('w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0', 
                        getEventColor(event.event_type) === 'success' && 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400',
                        getEventColor(event.event_type) === 'error' && 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400',
                        getEventColor(event.event_type) === 'warning' && 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-600 dark:text-yellow-400',
                        getEventColor(event.event_type) === 'info' && 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400',
                        'bg-dark-100 dark:bg-dark-800 text-dark-600 dark:text-dark-400'
                      )}>
                        {getEventIcon(event.event_type)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h4 className="font-medium text-dark-900 dark:text-white">{getEventTitle(event.event_type)}</h4>
                          <Badge variant={getEventColor(event.event_type)} size="sm">
                            {event.source}
                          </Badge>
                          {event.user_id && (
                            <Badge variant="gray" size="sm">
                              User: {event.user_id.slice(0, 8)}
                            </Badge>
                          )}
                        </div>
                        <div className="mt-1 text-sm text-dark-600 dark:text-dark-400 font-mono bg-dark-100 dark:bg-dark-800 px-2 py-1 rounded max-w-full overflow-auto">
                          {JSON.stringify(event.payload, null, 2)}
                        </div>
                        <div className="flex items-center gap-3 mt-2 text-xs text-dark-500 dark:text-dark-400">
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {formatDate(event.created_at)}
                          </span>
                          {event.event_type.includes('approval') && event.payload.status && (
                            <Badge variant={event.payload.status === 'approved' ? 'success' : event.payload.status === 'rejected' ? 'error' : 'warning'} size="sm">
                              {event.payload.status}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              {hasMore && (
                <div className="p-4 text-center border-t border-dark-200 dark:border-dark-700">
                  <Button variant="secondary" onClick={loadMore} disabled={loading}>
                    {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : 'Load More'}
                  </Button>
                </div>
              )}
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
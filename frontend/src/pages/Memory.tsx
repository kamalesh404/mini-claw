import { useEffect, useState } from 'react'
import { Plus, Search, Trash2, Edit, Loader2, Database, Key, Eye, EyeOff, Copy } from 'lucide-react'
import { api } from '../services/api'
import { Card, CardHeader, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Badge } from '../components/ui/Badge'
import { ScrollArea } from '../components/ui/ScrollArea'
import type { Memory } from '../types'
import { clsx } from 'clsx'

export function Memory() {
  const [memories, setMemories] = useState<Memory[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [editing, setEditing] = useState<string | null>(null)
  const [showSensitive, setShowSensitive] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [formData, setFormData] = useState({
    category: 'general',
    key: '',
    value: '',
    is_sensitive: false,
  })
  const categories = ['all', 'general', 'projects', 'preferences', 'tasks', 'technical', 'facts']

  useEffect(() => {
    fetchMemories()
  }, [selectedCategory])

  const fetchMemories = async () => {
    setLoading(true)
    try {
      const res = await api.get(`/memory${selectedCategory !== 'all' ? `?category=${selectedCategory}` : ''}`)
      setMemories(res.data)
    } catch (error) {
      console.error('Failed to fetch memories:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      fetchMemories()
      return
    }
    try {
      const res = await api.get(`/memory/search?query=${encodeURIComponent(searchQuery)}${selectedCategory !== 'all' ? `&category=${selectedCategory}` : ''}`)
      setMemories(res.data)
    } catch (error) {
      console.error('Search failed:', error)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editing) {
        await api.put(`/memory/${formData.category}/${formData.key}`, { value: formData.value })
      } else {
        await api.post('/memory', formData)
      }
      setCreating(false)
      setEditing(null)
      setFormData({ category: 'general', key: '', value: '', is_sensitive: false })
      fetchMemories()
    } catch (error) {
      console.error('Failed to save memory:', error)
    }
  }

  const handleEdit = (memory: Memory) => {
    setEditing(memory.id)
    setCreating(true)
    setFormData({
      category: memory.category,
      key: memory.key,
      value: memory.value,
      is_sensitive: memory.is_sensitive,
    })
  }

  const handleDelete = async (memory: Memory) => {
    if (!confirm(`Delete memory "${memory.key}"?`)) return
    try {
      await api.delete(`/memory/${memory.category}/${memory.key}`)
      fetchMemories()
    } catch (error) {
      console.error('Failed to delete memory:', error)
    }
  }

  const handleCopy = (value: string) => {
    navigator.clipboard.writeText(value)
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
          <h1 className="text-2xl font-bold text-dark-900 dark:text-white">Memory</h1>
          <p className="text-dark-500 dark:text-dark-400">Long-term memory storage with semantic search</p>
        </div>
        <Button onClick={() => { setCreating(true); setEditing(null); setFormData({ category: 'general', key: '', value: '', is_sensitive: false }) }}>
          <Plus className="w-4 h-4" />
          Add Memory
        </Button>
      </div>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2 flex-1 min-w-[200px]">
              <Search className="w-4 h-4 text-dark-400" />
              <Input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search memories..."
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              />
              <Button variant="ghost" size="sm" onClick={handleSearch}>Search</Button>
            </div>
            <div className="flex items-center gap-2">
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="input w-auto"
              >
                {categories.map(c => <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>)}
              </select>
            </div>
            <label className="flex items-center gap-2 text-sm text-dark-600 dark:text-dark-400 cursor-pointer">
              <input
                type="checkbox"
                checked={showSensitive}
                onChange={(e) => setShowSensitive(e.target.checked)}
                className="rounded border-dark-300 text-primary-600 focus:ring-primary-500"
              />
              Show sensitive
            </label>
          </div>
        </CardContent>
      </Card>

      {(creating || editing) && (
        <Card>
          <CardHeader title={editing ? 'Edit Memory' : 'Add Memory'} />
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="input"
                  disabled={editing}
                >
                  {categories.filter(c => c !== 'all').map(c => <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>)}
                </select>
                <Input
                  label="Key"
                  value={formData.key}
                  onChange={(e) => setFormData({ ...formData, key: e.target.value })}
                  placeholder="memory-key"
                  required
                  disabled={editing}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-dark-700 dark:text-dark-300 mb-1">Value</label>
                <textarea
                  value={formData.value}
                  onChange={(e) => setFormData({ ...formData, value: e.target.value })}
                  className="input min-h-[100px] resize-y"
                  placeholder="Memory value..."
                  required
                />
              </div>
              <label className="flex items-center gap-2 text-sm text-dark-600 dark:text-dark-400 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.is_sensitive}
                  onChange={(e) => setFormData({ ...formData, is_sensitive: e.target.checked })}
                  className="rounded border-dark-300 text-primary-600 focus:ring-primary-500"
                />
                Mark as sensitive (excluded from search, hidden by default)
              </label>
              <div className="flex justify-end gap-2">
                <Button type="button" variant="secondary" onClick={() => { setCreating(false); setEditing(null) }}>Cancel</Button>
                <Button type="submit">{editing ? 'Update' : 'Create'}</Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {memories.length === 0 && !creating && !editing ? (
        <Card className="text-center py-12">
          <Database className="w-16 h-16 mx-auto mb-4 text-dark-300 dark:text-dark-700" />
          <h3 className="text-lg font-medium text-dark-900 dark:text-white">No memories yet</h3>
          <p className="text-dark-500 dark:text-dark-400 mt-1">Add your first memory to get started</p>
          <Button className="mt-4" onClick={() => setCreating(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Add Memory
          </Button>
        </Card>
      ) : (
        <Card>
          <CardContent className="p-0">
            <ScrollArea className="max-h-[600px]">
              <div className="divide-y divide-dark-200 dark:divide-dark-700">
                {memories.map((memory) => (
                  <div key={memory.id} className="p-4 hover:bg-dark-50 dark:hover:bg-dark-800/50">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-xs font-mono text-primary-600 dark:text-primary-400 bg-primary-100 dark:bg-primary-900/30 px-2 py-0.5 rounded">
                            {memory.category}
                          </span>
                          <span className="font-medium text-dark-900 dark:text-white truncate max-w-[300px]">{memory.key}</span>
                          {memory.is_sensitive && (
                            <Badge variant="warning" size="sm">
                              <Key className="w-3 h-3 mr-1" /> Sensitive
                            </Badge>
                          )}
                        </div>
                        <div className="mt-2">
                          <code className="text-sm text-dark-600 dark:text-dark-300 font-mono bg-dark-100 dark:bg-dark-800 px-2 py-1 rounded break-all block max-h-32 overflow-auto">
                            {showSensitive || !memory.is_sensitive ? memory.value : '••••••••'}
                          </code>
                        </div>
                        <div className="flex items-center gap-3 mt-2 text-xs text-dark-500 dark:text-dark-400">
                          <span>Updated: {new Date(memory.updated_at).toLocaleString()}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-1 flex-shrink-0">
                        {(!memory.is_sensitive || showSensitive) && (
                          <Button variant="ghost" size="sm" className="p-1 h-auto" onClick={() => handleCopy(memory.value)} title="Copy value">
                            <Copy className="w-3 h-3" />
                          </Button>
                        )}
                        <Button variant="ghost" size="sm" className="p-1 h-auto" onClick={() => handleEdit(memory)} title="Edit">
                          <Edit className="w-3 h-3" />
                        </Button>
                        {memory.is_sensitive && !showSensitive && (
                          <Button variant="ghost" size="sm" className="p-1 h-auto" title="Show value">
                            <Eye className="w-3 h-3" />
                          </Button>
                        )}
                        {memory.is_sensitive && showSensitive && (
                          <Button variant="ghost" size="sm" className="p-1 h-auto" title="Hide value">
                            <EyeOff className="w-3 h-3" />
                          </Button>
                        )}
                        <Button variant="ghost" size="sm" className="p-1 h-auto text-red-600 hover:text-red-700" onClick={() => handleDelete(memory)} title="Delete">
                          <Trash2 className="w-3 h-3" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
import { useEffect, useState } from 'react'
import { FolderOpen, File, ChevronRight, ChevronDown, Search, Plus, Download, Edit, Trash2, Copy, Move, MoreVertical, Loader2, Home, RefreshCw } from 'lucide-react'
import { api } from '../services/api'
import { Card, CardHeader, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Badge } from '../components/ui/Badge'
import { ScrollArea } from '../components/ui/ScrollArea'
import type { FileInfo } from '../types'
import { clsx } from 'clsx'

export function Files() {
  const [currentPath, setCurrentPath] = useState('.')
  const [files, setFiles] = useState<FileInfo[]>([])
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<FileInfo[] | null>(null)
  const [showHidden, setShowHidden] = useState(false)
  const [creating, setCreating] = useState<'file' | 'folder' | null>(null)
  const [newName, setNewName] = useState('')

  useEffect(() => {
    loadFiles()
  }, [currentPath, showHidden])

  const loadFiles = async () => {
    setLoading(true)
    try {
      const res = await api.post('/files/list', {
        path: currentPath,
        recursive: false,
        include_hidden: showHidden,
      })
      setFiles(res.data.files || [])
      setSearchResults(null)
    } catch (error) {
      console.error('Failed to load files:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults(null)
      return
    }
    try {
      const res = await api.post('/files/search', {
        pattern: searchQuery,
        path: currentPath,
        max_results: 100,
      })
      setSearchResults(res.data.results || [])
    } catch (error) {
      console.error('Search failed:', error)
    }
  }

  const navigate = (path: string) => {
    setCurrentPath(path)
    setSearchQuery('')
  }

  const goUp = () => {
    if (currentPath === '.' || currentPath === '/') return
    const parts = currentPath.split('/').filter(Boolean)
    parts.pop()
    navigate(parts.join('/') || '.')
  }

  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
  }

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString()
  }

  const handleCreate = async (type: 'file' | 'folder') => {
    if (!newName.trim()) return
    try {
      await api.post('/files/create', {
        path: currentPath + '/' + newName,
        content: type === 'file' ? '' : undefined,
      })
      setCreating(null)
      setNewName('')
      loadFiles()
    } catch (error) {
      console.error('Failed to create:', error)
    }
  }

  const handleDelete = async (file: FileInfo) => {
    if (!confirm(`Delete ${file.name}?`)) return
    try {
      await api.post('/files/delete', {
        path: currentPath + '/' + file.name,
        recursive: file.is_dir,
        confirm: true,
      })
      loadFiles()
    } catch (error) {
      console.error('Failed to delete:', error)
    }
  }

  const fileList = searchResults !== null ? searchResults : files
  const breadcrumbs = currentPath === '.' || currentPath === '/' 
    ? [] 
    : currentPath.split('/').filter(Boolean).map((part, i) => ({
        name: part,
        path: currentPath.split('/').filter(Boolean).slice(0, i + 1).join('/')
      }))

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-dark-900 dark:text-white">Files</h1>
          <p className="text-dark-500 dark:text-dark-400">Browse and manage files</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" onClick={goUp} disabled={currentPath === '.'}>
            <Home className="w-4 h-4" />
          </Button>
          <Button variant="secondary" onClick={loadFiles}>
            <RefreshCw className="w-4 h-4" />
          </Button>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => setCreating('folder')}>
              <Plus className="w-4 h-4" />
              Folder
            </Button>
            <Button onClick={() => setCreating('file')}>
              <Plus className="w-4 h-4" />
              File
            </Button>
          </div>
        </div>
      </div>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2 flex-1 min-w-[200px]">
              <Search className="w-4 h-4 text-dark-400" />
              <Input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search files..."
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              />
              <Button variant="ghost" size="sm" onClick={handleSearch}>
                Search
              </Button>
            </div>
            <div className="flex items-center gap-2">
              <label className="flex items-center gap-2 text-sm text-dark-600 dark:text-dark-400 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showHidden}
                  onChange={(e) => setShowHidden(e.target.checked)}
                  className="rounded border-dark-300 text-primary-600 focus:ring-primary-500"
                />
                Show hidden
              </label>
            </div>
            <div className="text-sm text-dark-500 dark:text-dark-400">
              {breadcrumbs.map((b, i) => (
                <span key={b.path} className="flex items-center gap-1">
                  <Button variant="ghost" size="sm" className="p-1 h-auto" onClick={() => navigate(b.path)}>
                    {i === 0 ? <Home className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                    {b.name}
                  </Button>
                </span>
              ))}
              {breadcrumbs.length === 0 && (
                <span className="text-dark-500 dark:text-dark-400">/ (root)</span>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {creating && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-4 max-w-md">
              <h3 className="font-medium">Create new {creating}</h3>
              <Input
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder={creating === 'folder' ? 'folder-name' : 'file-name.txt'}
                onKeyDown={(e) => e.key === 'Enter' && handleCreate(creating)}
                autoFocus
              />
              <Button onClick={() => handleCreate(creating)}>Create</Button>
              <Button variant="ghost" onClick={() => { setCreating(null); setNewName('') }}>
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-8 text-center">
              <Loader2 className="w-8 h-8 animate-spin mx-auto text-primary-600" />
            </div>
          ) : fileList.length === 0 ? (
            <div className="p-8 text-center">
              <FolderOpen className="w-16 h-16 mx-auto mb-4 text-dark-300 dark:text-dark-700" />
              <h3 className="text-lg font-medium text-dark-900 dark:text-white">No files found</h3>
              <p className="text-dark-500 dark:text-dark-400 mt-1">
                {searchResults !== null ? `No results for "${searchQuery}"` : 'This folder is empty'}
              </p>
            </div>
          ) : (
            <ScrollArea className="max-h-[600px]">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-dark-200 dark:border-dark-700">
                    <th className="text-left p-3 font-medium text-dark-500 dark:text-dark-400 w-10"></th>
                    <th className="text-left p-3 font-medium text-dark-500 dark:text-dark-400">Name</th>
                    <th className="text-right p-3 font-medium text-dark-500 dark:text-dark-400 w-24">Size</th>
                    <th className="text-left p-3 font-medium text-dark-500 dark:text-dark-400 w-40">Modified</th>
                    <th className="text-right p-3 font-medium text-dark-500 dark:text-dark-400 w-24"></th>
                  </tr>
                </thead>
                <tbody>
                  {fileList.map((file) => (
                    <tr key={file.path} className="border-b border-dark-100 dark:border-dark-800 hover:bg-dark-50 dark:hover:bg-dark-800/50">
                      <td className="p-3">
                        {file.is_dir ? (
                          <FolderOpen className="w-5 h-5 text-yellow-500" />
                        ) : (
                          <File className="w-5 h-5 text-dark-400" />
                        )}
                      </td>
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          <span className={clsx('font-medium truncate', file.is_dir && 'text-blue-600 dark:text-blue-400')}>
                            {file.name}
                          </span>
                          {file.is_dir && (
                            <Button variant="ghost" size="sm" className="p-1 h-auto" onClick={() => navigate(currentPath + '/' + file.name)}>
                              <ChevronRight className="w-3 h-3" />
                            </Button>
                          )}
                        </div>
                      </td>
                      <td className="p-3 text-right text-sm text-dark-500 dark:text-dark-400 font-mono">
                        {file.is_dir ? '—' : formatSize(file.size)}
                      </td>
                      <td className="p-3 text-sm text-dark-500 dark:text-dark-400">
                        {formatDate(file.modified)}
                      </td>
                      <td className="p-3 text-right">
                        <div className="flex items-center justify-end gap-1">
                          {!file.is_dir && (
                            <Button variant="ghost" size="sm" className="p-1 h-auto" title="Download">
                              <Download className="w-3 h-3" />
                            </Button>
                          )}
                          <Button variant="ghost" size="sm" className="p-1 h-auto" title="Rename">
                            <Edit className="w-3 h-3" />
                          </Button>
                          <Button variant="ghost" size="sm" className="p-1 h-auto text-red-600 hover:text-red-700" onClick={() => handleDelete(file)} title="Delete">
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
import { useEffect, useRef, useState } from 'react'
import { Send, X, Copy, Check, Loader2 } from 'lucide-react'
import { api } from '../services/api'
import { wsManager } from '../services/websocket'
import { useAuth } from '../stores/authStore'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Card, CardHeader, CardContent } from '../components/ui/Card'
import { ScrollArea } from '../components/ui/ScrollArea'
import { Badge } from '../components/ui/Badge'
import type { Message, Conversation, ToolCall } from '../types'
import { clsx } from 'clsx'

export function Chat() {
  const { user, accessToken } = useAuth()
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [streaming, setStreaming] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const sidebarOpen = useRef(false)

  useEffect(() => {
    fetchConversations()
  }, [])

  useEffect(() => {
    if (currentConversation) {
      fetchMessages(currentConversation.id)
    }
  }, [currentConversation])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const fetchConversations = async () => {
    try {
      const res = await api.get('/chat/conversations')
      setConversations(res.data)
    } catch (error) {
      console.error('Failed to fetch conversations:', error)
    }
  }

  const fetchMessages = async (conversationId: string) => {
    try {
      const res = await api.get(`/chat/conversations/${conversationId}`)
      setMessages(res.data.messages || [])
    } catch (error) {
      console.error('Failed to fetch messages:', error)
    }
  }

  const createConversation = async () => {
    try {
      const res = await api.post('/chat/conversations', { title: 'New Conversation' })
      const conv = res.data
      setConversations([conv, ...conversations])
      setCurrentConversation(conv)
    } catch (error) {
      console.error('Failed to create conversation:', error)
    }
  }

  const selectConversation = (conv: Conversation) => {
    setCurrentConversation(conv)
    sidebarOpen.current = false
  }

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || sending) return

    const userMessage: Message = {
      id: 'temp-' + Date.now(),
      conversation_id: currentConversation?.id || '',
      role: 'user',
      content: input,
      tool_calls: null,
      tool_call_id: null,
      metadata: null,
      created_at: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])
    const messageToSend = input
    setInput('')
    setSending(true)
    setStreaming(true)

    try {
      if (!currentConversation) {
        await createConversation()
        // Wait for conversation to be created
        await new Promise(r => setTimeout(r, 100))
      }

      const ws = wsManager
      let fullResponse = ''
      let toolCalls: ToolCall[] | null = null

      const unsubMessage = ws.onMessage((data) => {
        if (data.type === 'chat_chunk') {
          if (data.content) {
            fullResponse += data.content
            setMessages((prev) => {
              const last = prev[prev.length - 1]
              if (last.id === userMessage.id) {
                return [...prev.slice(0, -1), { ...last, content: messageToSend }]
              }
              return prev
            })
            setMessages((prev) => {
              const assistantMsg = prev.find(m => m.role === 'assistant' && m.content.startsWith(fullResponse.slice(0, -data.content.length)))
              if (assistantMsg) {
                return prev.map(m => m.id === assistantMsg.id ? { ...m, content: fullResponse } : m)
              }
              return [...prev, { ...userMessage, id: 'assistant-' + Date.now(), role: 'assistant', content: fullResponse }]
            })
          }
          if (data.tool_calls) {
            toolCalls = data.tool_calls
          }
          if (data.finish_reason) {
            setStreaming(false)
            setSending(false)
          }
        } else if (data.type === 'error') {
          setSending(false)
          setStreaming(false)
        }
      })

      ws.send({
        type: 'chat',
        conversation_id: currentConversation?.id,
        message: messageToSend,
      })

      return () => unsubMessage()
    } catch (error) {
      console.error('Failed to send message:', error)
      setSending(false)
      setStreaming(false)
    }
  }

  const formatToolCalls = (toolCalls: ToolCall[] | null) => {
    if (!toolCalls || toolCalls.length === 0) return null
    return (
      <div className="mt-2 space-y-1">
        {toolCalls.map((tc) => (
          <div key={tc.id} className="text-xs bg-dark-100 dark:bg-dark-800 rounded p-2 font-mono">
            <span className="text-primary-600 dark:text-primary-400">{tc.function.name}</span>
            <span className="text-dark-500 dark:text-dark-400">({tc.function.arguments})</span>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col lg:flex-row">
      <aside className={clsx(
        'w-72 border-r border-dark-200 dark:border-dark-800 bg-white dark:bg-dark-950 flex flex-col transition-transform duration-300 lg:relative',
        sidebarOpen.current ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
      )}>
        <div className="p-4 border-b border-dark-200 dark:border-dark-800 flex items-center justify-between">
          <h2 className="font-semibold text-dark-900 dark:text-white">Conversations</h2>
          <Button variant="ghost" size="sm" onClick={createConversation}>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </Button>
        </div>
        <ScrollArea className="flex-1">
          <div className="p-3 space-y-2">
            {conversations.length === 0 ? (
              <p className="text-sm text-dark-500 dark:text-dark-400 text-center py-8">No conversations yet</p>
            ) : (
              conversations.map((conv) => (
                <button
                  key={conv.id}
                  onClick={() => selectConversation(conv)}
                  className={clsx(
                    'w-full text-left p-3 rounded-lg transition-colors',
                    currentConversation?.id === conv.id
                      ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300'
                      : 'hover:bg-dark-100 dark:hover:bg-dark-800 text-dark-700 dark:text-dark-300'
                  )}
                >
                  <p className="font-medium truncate">{conv.title}</p>
                  <p className="text-xs text-dark-500 dark:text-dark-400 truncate mt-1">
                    {new Date(conv.updated_at).toLocaleDateString()}
                  </p>
                </button>
              ))
            )}
          </div>
        </ScrollArea>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <div className="lg:hidden p-4 border-b border-dark-200 dark:border-dark-800 flex items-center justify-between">
          <Button variant="ghost" size="sm" onClick={() => sidebarOpen.current = true}>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </Button>
          <h2 className="font-semibold text-dark-900 dark:text-white">
            {currentConversation?.title || 'Select a conversation'}
          </h2>
          <Button variant="ghost" size="sm" onClick={createConversation}>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </Button>
        </div>

        <div className="flex-1 overflow-hidden flex flex-col">
          {currentConversation ? (
            <>
              <ScrollArea className="flex-1 p-4 space-y-4">
                {messages.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full text-dark-500 dark:text-dark-400">
                    <svg className="w-16 h-16 mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                    <p className="text-lg">Start a conversation</p>
                    <p className="text-sm">Type a message below to begin</p>
                  </div>
                ) : (
                  messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={clsx('flex gap-3 max-w-3xl', msg.role === 'user' && 'flex-row-reverse')}
                    >
                      <div
                        className={clsx(
                          'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
                          msg.role === 'user'
                            ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400'
                            : 'bg-dark-100 dark:bg-dark-800 text-dark-600 dark:text-dark-400'
                        )}
                      >
                        {msg.role === 'user' ? (
                          <span className="text-sm font-medium">{user?.full_name?.charAt(0) || 'U'}</span>
                        ) : (
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                          </svg>
                        )}
                      </div>
                      <div
                        className={clsx(
                          'max-w-[70%] rounded-2xl px-4 py-2',
                          msg.role === 'user'
                            ? 'bg-primary-600 text-white rounded-br-none'
                            : 'bg-white dark:bg-dark-900 border border-dark-200 dark:border-dark-700 rounded-bl-none'
                        )}
                      >
                        <div className="whitespace-pre-wrap text-sm">{msg.content}</div>
                        {formatToolCalls(msg.tool_calls)}
                        <div className="flex items-center gap-2 mt-1 text-xs text-dark-500 dark:text-dark-400">
                          <span>{new Date(msg.created_at).toLocaleTimeString()}</span>
                          <Button variant="ghost" size="sm" className="h-6 px-2" onClick={() => navigator.clipboard.writeText(msg.content)}>
                            <Copy className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                {streaming && (
                  <div className="flex gap-3 max-w-3xl">
                    <div className="w-8 h-8 rounded-full bg-dark-100 dark:bg-dark-800 flex items-center justify-center flex-shrink-0">
                      <Loader2 className="w-5 h-5 animate-spin text-dark-600 dark:text-dark-400" />
                    </div>
                    <div className="bg-white dark:bg-dark-900 border border-dark-200 dark:border-dark-700 rounded-2xl rounded-bl-none px-4 py-2">
                      <div className="flex items-center gap-2 text-sm text-dark-500 dark:text-dark-400">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Thinking...</span>
                      </div>
                    </div>
                  </div>
                )}
              </ScrollArea>

              <form onSubmit={handleSend} className="p-4 border-t border-dark-200 dark:border-dark-800 bg-white/50 dark:bg-dark-950/50 backdrop-blur-sm">
                <div className="flex gap-2">
                  <Input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Type a message..."
                    disabled={sending}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault()
                        handleSend(e)
                      }
                    }}
                    className="flex-1"
                  />
                  <Button type="submit" disabled={sending || !input.trim()} size="lg">
                    <Send className="w-5 h-5" />
                  </Button>
                </div>
                <p className="text-xs text-dark-500 dark:text-dark-400 mt-1 text-center">
                  Press Enter to send, Shift+Enter for new line
                </p>
              </form>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <svg className="w-16 h-16 mx-auto mb-4 text-dark-300 dark:text-dark-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                <h3 className="text-lg font-medium text-dark-900 dark:text-white">No conversation selected</h3>
                <p className="text-dark-500 dark:text-dark-400 mt-1">Create a new conversation or select one from the sidebar</p>
                <Button onClick={createConversation} className="mt-4">
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  New Conversation
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
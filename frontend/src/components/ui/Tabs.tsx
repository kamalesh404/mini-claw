import { createContext, useContext, useState, ReactNode } from 'react'
import { clsx } from 'clsx'

interface TabsContextType {
  value: string
  onValueChange: (value: string) => void
}

const TabsContext = createContext<TabsContextType | null>(null)

function useTabsContext() {
  const context = useContext(TabsContext)
  if (!context) {
    throw new Error('Tabs components must be used within Tabs')
  }
  return context
}

interface TabsProps {
  value: string
  onValueChange: (value: string) => void
  children: ReactNode
  className?: string
}

export function Tabs({ value, onValueChange, children, className }: TabsProps) {
  return (
    <TabsContext.Provider value={{ value, onValueChange }}>
      <div className={clsx(className)}>{children}</div>
    </TabsContext.Provider>
  )
}

interface TabListProps {
  children: ReactNode
  className?: string
}

export function TabList({ children, className }: TabListProps) {
  return (
    <div className={clsx('flex gap-1', className)} role="tablist">
      {children}
    </div>
  )
}

interface TabTriggerProps {
  value: string
  children: ReactNode
  className?: string
  disabled?: boolean
}

export function TabTrigger({ value, children, className, disabled }: TabTriggerProps) {
  const { value: currentValue, onValueChange } = useTabsContext()
  const isActive = currentValue === value

  return (
    <button
      role="tab"
      aria-selected={isActive}
      aria-disabled={disabled}
      disabled={disabled}
      onClick={() => !disabled && onValueChange(value)}
      className={clsx(
        'px-4 py-2 text-sm font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
        isActive
          ? 'bg-primary-600 text-white'
          : 'text-dark-600 hover:text-dark-900 hover:bg-dark-100 dark:text-dark-400 dark:hover:text-white dark:hover:bg-dark-800',
        disabled && 'opacity-50 cursor-not-allowed',
        className
      )}
    >
      {children}
    </button>
  )
}

interface TabContentProps {
  value: string
  children: ReactNode
  className?: string
}

export function TabContent({ value, children, className }: TabContentProps) {
  const { value: currentValue } = useTabsContext()

  if (currentValue !== value) return null

  return <div className={clsx(className)} role="tabpanel">{children}</div>
}
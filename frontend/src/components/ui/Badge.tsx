import { clsx } from 'clsx'

interface BadgeProps {
  className?: string
  children: React.ReactNode
  variant?: 'success' | 'warning' | 'error' | 'info' | 'gray' | 'primary'
  size?: 'sm' | 'md'
  dot?: boolean
}

export function Badge({ className, children, variant = 'gray', size = 'md', dot }: BadgeProps) {
  const variants = {
    success: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    warning: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
    error: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
    info: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
    gray: 'bg-dark-100 text-dark-800 dark:bg-dark-700 dark:text-dark-300',
    primary: 'bg-primary-100 text-primary-800 dark:bg-primary-900/30 dark:text-primary-400',
  }

  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-0.5 text-xs',
  }

  return (
    <span className={clsx('inline-flex items-center gap-1 rounded-full font-medium', variants[variant], sizes[size], className)}>
      {dot && <span className="w-1.5 h-1.5 rounded-full bg-current" />}
      {children}
    </span>
  )
}
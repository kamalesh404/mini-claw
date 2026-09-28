import { clsx } from 'clsx'

interface CardProps {
  className?: string
  children: React.ReactNode
  padding?: 'none' | 'sm' | 'md' | 'lg'
}

export function Card({ className, children, padding = 'md' }: CardProps) {
  const paddings = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  }

  return (
    <div className={clsx('rounded-xl border border-dark-200 bg-white shadow-sm dark:border-dark-700 dark:bg-dark-900', paddings[padding], className)}>
      {children}
    </div>
  )
}

interface CardHeaderProps {
  className?: string
  children: React.ReactNode
  title?: string
  subtitle?: string
  action?: React.ReactNode
}

export function CardHeader({ className, children, title, subtitle, action }: CardHeaderProps) {
  return (
    <div className={clsx('flex items-start justify-between mb-4', className)}>
      <div>
        {title && <h3 className="text-lg font-semibold text-dark-900 dark:text-dark-100">{title}</h3>}
        {subtitle && <p className="text-sm text-dark-500 dark:text-dark-400 mt-0.5">{subtitle}</p>}
      </div>
      {action && <div>{action}</div>}
      {children}
    </div>
  )
}

interface CardContentProps {
  className?: string
  children: React.ReactNode
}

export function CardContent({ className, children }: CardContentProps) {
  return <div className={clsx(className)}>{children}</div>
}

interface CardFooterProps {
  className?: string
  children: React.ReactNode
}

export function CardFooter({ className, children }: CardFooterProps) {
  return (
    <div className={clsx('flex items-center justify-end gap-2 mt-4 pt-4 border-t border-dark-200 dark:border-dark-700', className)}>
      {children}
    </div>
  )
}
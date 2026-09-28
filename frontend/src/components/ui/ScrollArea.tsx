import { forwardRef, HTMLAttributes } from 'react'
import { clsx } from 'clsx'

interface ScrollAreaProps extends HTMLAttributes<HTMLDivElement> {
  className?: string
}

export const ScrollArea = forwardRef<HTMLDivElement, ScrollAreaProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={clsx('scrollbar-thin overflow-auto', className)}
        {...props}
      >
        {children}
      </div>
    )
  }
)

ScrollArea.displayName = 'ScrollArea'
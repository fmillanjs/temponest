import * as React from 'react'
import { motion } from 'framer-motion'
import { cn } from '@temponest/utils'

export interface ProgressProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'role'> {
  value?: number
  max?: number
  showLabel?: boolean
  animated?: boolean
  animate?: boolean  // Alias for animated
  variant?: 'default' | 'success' | 'warning' | 'error'
}

const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(
  ({
    className,
    value = 0,
    max = 100,
    showLabel = false,
    animated = true,
    animate,
    variant = 'default',
    ...props
  }, ref) => {
    const percentage = Math.min(Math.max((value / max) * 100, 0), 100)
    const isAnimated = animate !== undefined ? animate : animated

    const variantColors = {
      default: 'bg-primary',
      success: 'bg-green-500',
      warning: 'bg-yellow-500',
      error: 'bg-red-500',
    }

    return (
      <div
        ref={ref}
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={max}
        className={cn('relative w-full overflow-hidden rounded-full bg-secondary', className)}
        {...props}
      >
        <div className="h-full w-full flex-1">
          <motion.div
            className={cn('h-full flex items-center justify-end pr-2', variantColors[variant])}
            initial={{ width: 0 }}
            animate={{ width: `${percentage}%` }}
            transition={{
              duration: isAnimated ? 0.5 : 0,
              ease: 'easeOut',
            }}
          >
            {showLabel && (
              <motion.span
                className="text-xs font-semibold text-primary-foreground"
                initial={{ opacity: 0 }}
                animate={{ opacity: percentage > 10 ? 1 : 0 }}
                transition={{ delay: 0.2 }}
              >
                {Math.round(percentage)}%
              </motion.span>
            )}
          </motion.div>
        </div>
      </div>
    )
  }
)
Progress.displayName = 'Progress'

export { Progress }

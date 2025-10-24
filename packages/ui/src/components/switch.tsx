import * as React from 'react'
import { motion } from 'framer-motion'
import { cn } from '@temponest/utils'

export interface SwitchProps extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'onChange' | 'type'> {
  checked?: boolean
  onCheckedChange?: (checked: boolean) => void
  disabled?: boolean
  className?: string
  size?: 'sm' | 'default' | 'lg'
}

const Switch = React.forwardRef<HTMLButtonElement, SwitchProps>(
  ({ checked = false, onCheckedChange, disabled = false, className, size = 'default', ...props }, ref) => {
    const [isChecked, setIsChecked] = React.useState(checked)

    React.useEffect(() => {
      setIsChecked(checked)
    }, [checked])

    const handleToggle = () => {
      if (disabled) return
      const newValue = !isChecked
      setIsChecked(newValue)
      onCheckedChange?.(newValue)
    }

    const sizes = {
      sm: {
        track: 'h-5 w-9',
        thumb: 'h-4 w-4',
        translate: 16,
      },
      default: {
        track: 'h-6 w-11',
        thumb: 'h-5 w-5',
        translate: 20,
      },
      lg: {
        track: 'h-7 w-14',
        thumb: 'h-6 w-6',
        translate: 28,
      },
    }

    const currentSize = sizes[size]

    return (
      <button
        ref={ref}
        type="button"
        role="switch"
        aria-checked={isChecked}
        data-state={isChecked ? 'checked' : 'unchecked'}
        disabled={disabled}
        onClick={handleToggle}
        className={cn(
          'relative inline-flex flex-shrink-0 rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:cursor-not-allowed disabled:opacity-50',
          currentSize.track,
          isChecked ? 'bg-primary' : 'bg-input',
          className
        )}
        {...props}
      >
        <motion.span
          className={cn(
            'pointer-events-none block rounded-full bg-background shadow-lg ring-0',
            currentSize.thumb
          )}
          initial={false}
          animate={{
            x: isChecked ? currentSize.translate : 0,
          }}
          transition={{
            type: 'spring',
            stiffness: 500,
            damping: 30,
          }}
        />
      </button>
    )
  }
)
Switch.displayName = 'Switch'

export { Switch }

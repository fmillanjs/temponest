import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button } from '@/components/ui/button'

describe('Button Component', () => {
  describe('Rendering', () => {
    it('renders button with text', () => {
      render(<Button>Click me</Button>)
      expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument()
    })

    it('renders as child component when asChild is true', () => {
      render(
        <Button asChild>
          <a href="/test">Link Button</a>
        </Button>
      )
      expect(screen.getByRole('link', { name: 'Link Button' })).toBeInTheDocument()
    })

    it('applies custom className', () => {
      render(<Button className="custom-class">Button</Button>)
      expect(screen.getByRole('button')).toHaveClass('custom-class')
    })
  })

  describe('Variants', () => {
    it('renders default variant', () => {
      render(<Button>Default</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('bg-primary')
    })

    it('renders destructive variant', () => {
      render(<Button variant="destructive">Delete</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('bg-destructive')
    })

    it('renders outline variant', () => {
      render(<Button variant="outline">Outline</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('border')
    })

    it('renders secondary variant', () => {
      render(<Button variant="secondary">Secondary</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('bg-secondary')
    })

    it('renders ghost variant', () => {
      render(<Button variant="ghost">Ghost</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('hover:bg-accent')
    })

    it('renders link variant', () => {
      render(<Button variant="link">Link</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('underline-offset-4')
    })
  })

  describe('Sizes', () => {
    it('renders default size', () => {
      render(<Button>Default Size</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('h-10')
    })

    it('renders small size', () => {
      render(<Button size="sm">Small</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('h-9')
    })

    it('renders large size', () => {
      render(<Button size="lg">Large</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('h-11')
    })

    it('renders icon size', () => {
      render(<Button size="icon">🔍</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('h-10', 'w-10')
    })
  })

  describe('States', () => {
    it('handles disabled state', () => {
      render(<Button disabled>Disabled</Button>)
      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
      expect(button).toHaveClass('disabled:opacity-50')
    })

    it('does not call onClick when disabled', async () => {
      const user = userEvent.setup()
      const onClick = vi.fn()
      render(
        <Button disabled onClick={onClick}>
          Disabled
        </Button>
      )
      await user.click(screen.getByRole('button'))
      expect(onClick).not.toHaveBeenCalled()
    })
  })

  describe('Interactions', () => {
    it('calls onClick when clicked', async () => {
      const user = userEvent.setup()
      const onClick = vi.fn()
      render(<Button onClick={onClick}>Click me</Button>)
      await user.click(screen.getByRole('button'))
      expect(onClick).toHaveBeenCalledTimes(1)
    })

    it('handles multiple clicks', async () => {
      const user = userEvent.setup()
      const onClick = vi.fn()
      render(<Button onClick={onClick}>Click me</Button>)
      const button = screen.getByRole('button')
      await user.click(button)
      await user.click(button)
      await user.click(button)
      expect(onClick).toHaveBeenCalledTimes(3)
    })

    it('forwards ref to button element', () => {
      const ref = vi.fn()
      render(<Button ref={ref}>Button</Button>)
      expect(ref).toHaveBeenCalled()
    })
  })

  describe('Accessibility', () => {
    it('has correct button role', () => {
      render(<Button>Accessible Button</Button>)
      expect(screen.getByRole('button')).toBeInTheDocument()
    })

    it('supports aria-label', () => {
      render(<Button aria-label="Close dialog">×</Button>)
      expect(screen.getByLabelText('Close dialog')).toBeInTheDocument()
    })

    it('supports type attribute', () => {
      render(<Button type="submit">Submit</Button>)
      expect(screen.getByRole('button')).toHaveAttribute('type', 'submit')
    })
  })
})

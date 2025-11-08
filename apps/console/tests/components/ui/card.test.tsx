import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '@/components/ui/card'

describe('Card Components', () => {
  describe('Card', () => {
    it('renders card with children', () => {
      render(<Card data-testid="card">Card content</Card>)
      expect(screen.getByTestId('card')).toBeInTheDocument()
      expect(screen.getByText('Card content')).toBeInTheDocument()
    })

    it('applies custom className', () => {
      render(
        <Card className="custom-card" data-testid="card">
          Content
        </Card>
      )
      expect(screen.getByTestId('card')).toHaveClass('custom-card')
    })

    it('forwards ref', () => {
      const ref = { current: null }
      render(<Card ref={ref}>Content</Card>)
      expect(ref.current).toBeInstanceOf(HTMLDivElement)
    })
  })

  describe('CardHeader', () => {
    it('renders header with children', () => {
      render(<CardHeader data-testid="header">Header content</CardHeader>)
      expect(screen.getByTestId('header')).toBeInTheDocument()
      expect(screen.getByText('Header content')).toBeInTheDocument()
    })

    it('applies custom className', () => {
      render(
        <CardHeader className="custom-header" data-testid="header">
          Header
        </CardHeader>
      )
      expect(screen.getByTestId('header')).toHaveClass('custom-header')
    })
  })

  describe('CardTitle', () => {
    it('renders title with children', () => {
      render(<CardTitle>Card Title</CardTitle>)
      expect(screen.getByText('Card Title')).toBeInTheDocument()
    })

    it('applies custom className', () => {
      render(<CardTitle className="custom-title">Title</CardTitle>)
      expect(screen.getByText('Title')).toHaveClass('custom-title')
    })
  })

  describe('CardDescription', () => {
    it('renders description with children', () => {
      render(<CardDescription>Card description text</CardDescription>)
      expect(screen.getByText('Card description text')).toBeInTheDocument()
    })

    it('applies custom className', () => {
      render(
        <CardDescription className="custom-desc">Description</CardDescription>
      )
      expect(screen.getByText('Description')).toHaveClass('custom-desc')
    })
  })

  describe('CardContent', () => {
    it('renders content with children', () => {
      render(<CardContent data-testid="content">Content area</CardContent>)
      expect(screen.getByTestId('content')).toBeInTheDocument()
      expect(screen.getByText('Content area')).toBeInTheDocument()
    })

    it('applies custom className', () => {
      render(
        <CardContent className="custom-content" data-testid="content">
          Content
        </CardContent>
      )
      expect(screen.getByTestId('content')).toHaveClass('custom-content')
    })
  })

  describe('CardFooter', () => {
    it('renders footer with children', () => {
      render(<CardFooter data-testid="footer">Footer content</CardFooter>)
      expect(screen.getByTestId('footer')).toBeInTheDocument()
      expect(screen.getByText('Footer content')).toBeInTheDocument()
    })

    it('applies custom className', () => {
      render(
        <CardFooter className="custom-footer" data-testid="footer">
          Footer
        </CardFooter>
      )
      expect(screen.getByTestId('footer')).toHaveClass('custom-footer')
    })
  })

  describe('Card Composition', () => {
    it('renders complete card structure', () => {
      render(
        <Card data-testid="card">
          <CardHeader>
            <CardTitle>Title</CardTitle>
            <CardDescription>Description</CardDescription>
          </CardHeader>
          <CardContent>Content</CardContent>
          <CardFooter>Footer</CardFooter>
        </Card>
      )

      expect(screen.getByTestId('card')).toBeInTheDocument()
      expect(screen.getByText('Title')).toBeInTheDocument()
      expect(screen.getByText('Description')).toBeInTheDocument()
      expect(screen.getByText('Content')).toBeInTheDocument()
      expect(screen.getByText('Footer')).toBeInTheDocument()
    })

    it('renders card without header', () => {
      render(
        <Card data-testid="card">
          <CardContent>Content only</CardContent>
        </Card>
      )

      expect(screen.getByTestId('card')).toBeInTheDocument()
      expect(screen.getByText('Content only')).toBeInTheDocument()
    })

    it('renders card without footer', () => {
      render(
        <Card data-testid="card">
          <CardHeader>
            <CardTitle>Title</CardTitle>
          </CardHeader>
          <CardContent>Content</CardContent>
        </Card>
      )

      expect(screen.getByTestId('card')).toBeInTheDocument()
      expect(screen.getByText('Title')).toBeInTheDocument()
      expect(screen.getByText('Content')).toBeInTheDocument()
    })
  })
})

import React from 'react'
import { render } from '@testing-library/react'
import { axe } from 'jest-axe'
import { Spinner } from '../spinner'

describe('Spinner Component', () => {
  it('should not have accessibility violations', async () => {
    const { container } = render(<Spinner aria-label="Loading" />)
    const results = await axe(container)
    expect(results).toHaveNoViolations()
  })

  it('should render spinner', () => {
    const { container } = render(<Spinner />)
    expect(container.firstChild).toBeTruthy()
  })

  it('should render all size variants', () => {
    const sizes = ['sm', 'md', 'lg'] as const
    sizes.forEach(size => {
      const { container } = render(<Spinner size={size} />)
      expect(container.firstChild).toBeTruthy()
    })
  })

  it('should accept custom className', () => {
    const { container } = render(<Spinner className="custom-spinner" />)
    expect(container.firstChild).toHaveClass('custom-spinner')
  })

  it('should have proper role and aria-label', () => {
    const { container } = render(<Spinner />)
    const spinner = container.firstChild as HTMLElement
    expect(spinner).toHaveAttribute('role', 'status')
    expect(spinner).toHaveAttribute('aria-label', 'Loading')
  })
})

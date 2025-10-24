import React from 'react'
import { render } from '@testing-library/react'
import { FadeIn } from '../fade-in'

// Mock IntersectionObserver
beforeAll(() => {
  global.IntersectionObserver = class IntersectionObserver {
    constructor() {}
    disconnect() {}
    observe() {}
    takeRecords() {
      return []
    }
    unobserve() {}
  } as any
})

describe('FadeIn Component', () => {
  it('should render children', () => {
    const { getByText } = render(
      <FadeIn>
        <div>Test content</div>
      </FadeIn>
    )
    expect(getByText('Test content')).toBeTruthy()
  })

  it('should render with delay', () => {
    const { getByText } = render(
      <FadeIn delay={0.5}>
        <div>Delayed content</div>
      </FadeIn>
    )
    expect(getByText('Delayed content')).toBeTruthy()
  })

  it('should render with custom duration', () => {
    const { getByText } = render(
      <FadeIn duration={1.5}>
        <div>Custom duration</div>
      </FadeIn>
    )
    expect(getByText('Custom duration')).toBeTruthy()
  })

  it('should render with all direction variants', () => {
    const directions = ['up', 'down', 'left', 'right'] as const
    directions.forEach(direction => {
      const { getByText } = render(
        <FadeIn direction={direction}>
          <div>{direction} content</div>
        </FadeIn>
      )
      expect(getByText(`${direction} content`)).toBeTruthy()
    })
  })

  it('should accept custom className', () => {
    const { container } = render(
      <FadeIn className="custom-fade">
        <div>Content</div>
      </FadeIn>
    )
    expect(container.firstChild).toHaveClass('custom-fade')
  })

  it('should render multiple children', () => {
    const { getByText } = render(
      <FadeIn>
        <div>Child 1</div>
        <div>Child 2</div>
        <div>Child 3</div>
      </FadeIn>
    )
    expect(getByText('Child 1')).toBeTruthy()
    expect(getByText('Child 2')).toBeTruthy()
    expect(getByText('Child 3')).toBeTruthy()
  })
})

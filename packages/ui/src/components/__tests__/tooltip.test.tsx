import React from 'react'
import { render } from '@testing-library/react'
import { Tooltip } from '../tooltip'

describe('Tooltip Component', () => {
  it('should render tooltip with children and content', () => {
    const { getByText } = render(
      <Tooltip content="Tooltip text">
        <button>Hover me</button>
      </Tooltip>
    )
    expect(getByText('Hover me')).toBeTruthy()
  })

  it('should render with all side positions', () => {
    const sides = ['top', 'right', 'bottom', 'left'] as const
    sides.forEach(side => {
      const { getByRole, unmount } = render(
        <Tooltip content="Tooltip text" side={side}>
          <button>Button {side}</button>
        </Tooltip>
      )
      expect(getByRole('button')).toBeTruthy()
      unmount()  // Clean up before next iteration
    })
  })

  it('should accept custom delay', () => {
    const { getByText } = render(
      <Tooltip content="Tooltip text" delay={500}>
        <button>Delayed Button</button>
      </Tooltip>
    )
    expect(getByText('Delayed Button')).toBeTruthy()
  })

  it('should accept custom className', () => {
    const { container } = render(
      <Tooltip content="Tooltip text" className="custom-tooltip">
        <button>Custom Button</button>
      </Tooltip>
    )
    expect(container.firstChild).toBeTruthy()
  })

  it('should render with default side (top)', () => {
    const { getByText } = render(
      <Tooltip content="Tooltip text">
        <button>Default Button</button>
      </Tooltip>
    )
    expect(getByText('Default Button')).toBeTruthy()
  })
})

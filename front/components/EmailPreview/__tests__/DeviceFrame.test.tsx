import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { DeviceFrame } from '../DeviceFrame';

describe('DeviceFrame', () => {
  const TestContent = () => (
    <div data-testid="test-content">Test Content</div>
  );

  it('renders children correctly', () => {
    render(
      <DeviceFrame device="desktop">
        <TestContent />
      </DeviceFrame>
    );

    expect(screen.getByTestId('test-content')).toBeInTheDocument();
  });

  it('applies desktop frame styles', () => {
    const { container } = render(
      <DeviceFrame device="desktop">
        <TestContent />
      </DeviceFrame>
    );

    const frameElement = container.firstChild as HTMLElement;
    expect(frameElement).toHaveClass('max-w-4xl', 'mx-auto', 'bg-white', 'shadow-lg', 'rounded-lg', 'overflow-hidden');
  });

  it('applies mobile frame styles', () => {
    const { container } = render(
      <DeviceFrame device="mobile">
        <TestContent />
      </DeviceFrame>
    );

    const frameElement = container.firstChild as HTMLElement;
    expect(frameElement).toHaveClass(
      'max-w-sm',
      'mx-auto',
      'bg-white',
      'shadow-lg',
      'rounded-[2.5rem]',
      'overflow-hidden',
      'border-8',
      'border-gray-800',
      'relative'
    );
  });

  it('renders mobile frame decorations', () => {
    const { container } = render(
      <DeviceFrame device="mobile">
        <TestContent />
      </DeviceFrame>
    );

    // Check for top decoration (notch)
    const topDecoration = container.querySelector('.absolute.top-0');
    expect(topDecoration).toBeInTheDocument();
    expect(topDecoration).toHaveClass('w-1/3', 'h-1', 'bg-gray-600', 'rounded-b-lg');

    // Check for bottom decoration (home indicator)
    const bottomDecoration = container.querySelector('.absolute.bottom-1');
    expect(bottomDecoration).toBeInTheDocument();
    expect(bottomDecoration).toHaveClass('w-1/3', 'h-1', 'bg-gray-600', 'rounded-full');
  });

  it('does not render mobile decorations for desktop', () => {
    const { container } = render(
      <DeviceFrame device="desktop">
        <TestContent />
      </DeviceFrame>
    );

    const decorations = container.querySelectorAll('.absolute');
    expect(decorations).toHaveLength(0);
  });

  it('applies correct content padding for desktop', () => {
    const { container } = render(
      <DeviceFrame device="desktop">
        <TestContent />
      </DeviceFrame>
    );

    const contentElement = container.querySelector('div > div');
    expect(contentElement).toHaveClass('p-0');
  });

  it('applies correct content padding for mobile', () => {
    const { container } = render(
      <DeviceFrame device="mobile">
        <TestContent />
      </DeviceFrame>
    );

    const contentElement = container.querySelector('div > div:last-child');
    expect(contentElement).toHaveClass('p-2', 'min-h-[600px]', 'bg-gray-50');
  });

  it('applies custom className', () => {
    const { container } = render(
      <DeviceFrame device="desktop" className="custom-class">
        <TestContent />
      </DeviceFrame>
    );

    expect(container.firstChild).toHaveClass('custom-class');
  });

  it('combines device styles with custom className', () => {
    const { container } = render(
      <DeviceFrame device="mobile" className="my-custom-class">
        <TestContent />
      </DeviceFrame>
    );

    const frameElement = container.firstChild as HTMLElement;
    expect(frameElement).toHaveClass('my-custom-class');
    expect(frameElement).toHaveClass('max-w-sm', 'rounded-[2.5rem]'); // Mobile styles should still be applied
  });

  it('handles complex children structure', () => {
    render(
      <DeviceFrame device="desktop">
        <div>
          <h1>Title</h1>
          <p>Paragraph</p>
          <button>Button</button>
        </div>
      </DeviceFrame>
    );

    expect(screen.getByText('Title')).toBeInTheDocument();
    expect(screen.getByText('Paragraph')).toBeInTheDocument();
    expect(screen.getByText('Button')).toBeInTheDocument();
  });

  it('positions mobile decorations correctly', () => {
    const { container } = render(
      <DeviceFrame device="mobile">
        <TestContent />
      </DeviceFrame>
    );

    const topDecoration = container.querySelector('.absolute.top-0.left-1\\/2');
    expect(topDecoration).toBeInTheDocument();
    expect(topDecoration).toHaveClass('transform', '-translate-x-1/2');

    const bottomDecoration = container.querySelector('.absolute.bottom-1.left-1\\/2');
    expect(bottomDecoration).toBeInTheDocument();
    expect(bottomDecoration).toHaveClass('transform', '-translate-x-1/2');
  });

  it('sets correct z-index for mobile decorations', () => {
    const { container } = render(
      <DeviceFrame device="mobile">
        <TestContent />
      </DeviceFrame>
    );

    const decorations = container.querySelectorAll('.absolute');
    decorations.forEach(decoration => {
      expect(decoration).toHaveClass('z-10');
    });
  });

  it('renders without children', () => {
    const { container } = render(
      <DeviceFrame device="desktop" />
    );

    expect(container.firstChild).toBeInTheDocument();
  });

  it('preserves content layout in desktop mode', () => {
    render(
      <DeviceFrame device="desktop">
        <div style={{ width: '100%', height: '500px', background: 'red' }}>
          Wide Content
        </div>
      </DeviceFrame>
    );

    expect(screen.getByText('Wide Content')).toBeInTheDocument();
  });

  it('constrains content in mobile mode', () => {
    const { container } = render(
      <DeviceFrame device="mobile">
        <div style={{ width: '100%', height: '500px', background: 'red' }}>
          Wide Content
        </div>
      </DeviceFrame>
    );

    const frameElement = container.firstChild as HTMLElement;
    expect(frameElement).toHaveClass('max-w-sm'); // Mobile frame should constrain width
    expect(screen.getByText('Wide Content')).toBeInTheDocument();
  });
});
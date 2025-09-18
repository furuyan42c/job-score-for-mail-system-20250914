import React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import ErrorBoundary, { withErrorBoundary } from './index';

const meta: Meta<typeof ErrorBoundary> = {
  title: 'Components/ErrorBoundary',
  component: ErrorBoundary,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: 'A comprehensive error boundary component that catches JavaScript errors in the component tree and displays a fallback UI.',
      },
    },
  },
  argTypes: {
    children: {
      control: false,
      description: 'The components to wrap with error boundary protection',
    },
    level: {
      control: 'select',
      options: ['page', 'component', 'global'],
      description: 'The level of the error boundary (affects messaging and styling)',
    },
    showDetails: {
      control: 'boolean',
      description: 'Whether to show technical error details (usually only in development)',
    },
    onError: {
      action: 'error-occurred',
      description: 'Callback function called when an error is caught',
    },
  },
};

export default meta;
type Story = StoryObj<typeof ErrorBoundary>;

// Component that throws different types of errors
const ErrorComponent: React.FC<{ errorType: string }> = ({ errorType }) => {
  React.useEffect(() => {
    switch (errorType) {
      case 'chunk':
        const chunkError = new Error('Loading chunk 2 failed');
        chunkError.name = 'ChunkLoadError';
        throw chunkError;
      case 'network':
        throw new Error('Network Error: Failed to fetch data');
      case 'auth':
        const authError = new Error('User authentication failed');
        authError.message = 'Authentication required';
        throw authError;
      case 'validation':
        const validationError = new Error('Invalid form data provided');
        validationError.name = 'ValidationError';
        throw validationError;
      case 'generic':
      default:
        throw new Error('Something unexpected happened in the component');
    }
  }, [errorType]);

  return null;
};

// Success component for contrast
const SuccessComponent: React.FC = () => (
  <div className="p-8 text-center">
    <div className="max-w-md mx-auto">
      <div className="w-16 h-16 mx-auto mb-4 bg-green-100 rounded-full flex items-center justify-center">
        <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">Everything is working!</h3>
      <p className="text-gray-600">This component rendered successfully without any errors.</p>
    </div>
  </div>
);

export const Default: Story = {
  args: {
    children: <ErrorComponent errorType="generic" />,
    level: 'component',
    showDetails: false,
  },
};

export const WithSuccessfulComponent: Story = {
  args: {
    children: <SuccessComponent />,
    level: 'component',
  },
  parameters: {
    docs: {
      description: {
        story: 'Shows how the ErrorBoundary renders children normally when no errors occur.',
      },
    },
  },
};

export const ChunkLoadError: Story = {
  args: {
    children: <ErrorComponent errorType="chunk" />,
    level: 'component',
    showDetails: false,
  },
  parameters: {
    docs: {
      description: {
        story: 'Simulates a chunk loading error, which commonly occurs when JavaScript bundles fail to load.',
      },
    },
  },
};

export const NetworkError: Story = {
  args: {
    children: <ErrorComponent errorType="network" />,
    level: 'component',
    showDetails: false,
  },
  parameters: {
    docs: {
      description: {
        story: 'Simulates a network error, providing appropriate messaging for connectivity issues.',
      },
    },
  },
};

export const AuthenticationError: Story = {
  args: {
    children: <ErrorComponent errorType="auth" />,
    level: 'component',
    showDetails: false,
  },
  parameters: {
    docs: {
      description: {
        story: 'Simulates an authentication error, suggesting the user needs to sign in again.',
      },
    },
  },
};

export const ValidationError: Story = {
  args: {
    children: <ErrorComponent errorType="validation" />,
    level: 'component',
    showDetails: false,
  },
  parameters: {
    docs: {
      description: {
        story: 'Simulates a validation error, indicating invalid data was detected.',
      },
    },
  },
};

export const GlobalLevel: Story = {
  args: {
    children: <ErrorComponent errorType="generic" />,
    level: 'global',
    showDetails: false,
  },
  parameters: {
    docs: {
      description: {
        story: 'Shows the error boundary at the global level with "Application Error" messaging.',
      },
    },
  },
};

export const PageLevel: Story = {
  args: {
    children: <ErrorComponent errorType="generic" />,
    level: 'page',
    showDetails: false,
  },
  parameters: {
    docs: {
      description: {
        story: 'Shows the error boundary at the page level.',
      },
    },
  },
};

export const WithErrorDetails: Story = {
  args: {
    children: <ErrorComponent errorType="generic" />,
    level: 'component',
    showDetails: true,
  },
  parameters: {
    docs: {
      description: {
        story: 'Shows technical error details (typically only shown in development mode).',
      },
    },
  },
};

export const CustomFallback: Story = {
  args: {
    children: <ErrorComponent errorType="generic" />,
    fallback: (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-400 to-pink-400">
        <div className="text-center text-white">
          <h1 className="text-4xl font-bold mb-4">Oops! 🎨</h1>
          <p className="text-xl mb-6">Our custom error page</p>
          <button className="bg-white text-purple-600 px-6 py-3 rounded-full font-semibold hover:bg-gray-100 transition-colors">
            Custom Action
          </button>
        </div>
      </div>
    ),
  },
  parameters: {
    docs: {
      description: {
        story: 'Shows how to provide a completely custom fallback UI instead of the default error boundary interface.',
      },
    },
  },
};

export const DarkMode: Story = {
  args: {
    children: <ErrorComponent errorType="generic" />,
    level: 'component',
    showDetails: true,
  },
  decorators: [
    (Story) => (
      <div className="dark min-h-screen bg-gray-900">
        <Story />
      </div>
    ),
  ],
  parameters: {
    docs: {
      description: {
        story: 'Shows the error boundary in dark mode with proper contrast and styling.',
      },
    },
  },
};

// HOC Example
const ProblematicComponent: React.FC<{ shouldError?: boolean }> = ({ shouldError = false }) => {
  if (shouldError) {
    throw new Error('Component wrapped with HOC failed');
  }
  return (
    <div className="p-4 bg-blue-50 rounded-lg">
      <h3 className="font-semibold text-blue-900">HOC Wrapped Component</h3>
      <p className="text-blue-700">This component is wrapped with the withErrorBoundary HOC.</p>
    </div>
  );
};

const WrappedComponent = withErrorBoundary(ProblematicComponent, {
  level: 'component',
  showDetails: true,
});

export const WithHOC: Story = {
  render: () => <WrappedComponent shouldError={true} />,
  parameters: {
    docs: {
      description: {
        story: 'Shows how to use the withErrorBoundary Higher-Order Component to automatically wrap components with error boundary protection.',
      },
    },
  },
};

export const WithHOCSuccess: Story = {
  render: () => <WrappedComponent shouldError={false} />,
  parameters: {
    docs: {
      description: {
        story: 'Shows the HOC-wrapped component rendering successfully when no errors occur.',
      },
    },
  },
};

// Interactive example with multiple states
export const Interactive: Story = {
  render: () => {
    const [errorType, setErrorType] = React.useState<string | null>(null);
    const [showDetails, setShowDetails] = React.useState(false);

    const triggerError = (type: string) => {
      setErrorType(type);
      // Reset after a short delay to allow re-triggering
      setTimeout(() => setErrorType(null), 100);
    };

    return (
      <div className="p-6">
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-4">Interactive Error Boundary Demo</h3>
          <div className="flex flex-wrap gap-2 mb-4">
            <button
              onClick={() => triggerError('generic')}
              className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600"
            >
              Generic Error
            </button>
            <button
              onClick={() => triggerError('chunk')}
              className="px-3 py-1 bg-orange-500 text-white rounded hover:bg-orange-600"
            >
              Chunk Error
            </button>
            <button
              onClick={() => triggerError('network')}
              className="px-3 py-1 bg-yellow-500 text-white rounded hover:bg-yellow-600"
            >
              Network Error
            </button>
            <button
              onClick={() => triggerError('auth')}
              className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Auth Error
            </button>
            <button
              onClick={() => triggerError('validation')}
              className="px-3 py-1 bg-purple-500 text-white rounded hover:bg-purple-600"
            >
              Validation Error
            </button>
          </div>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={showDetails}
              onChange={(e) => setShowDetails(e.target.checked)}
            />
            Show error details
          </label>
        </div>

        <ErrorBoundary key={errorType} level="component" showDetails={showDetails}>
          {errorType ? (
            <ErrorComponent errorType={errorType} />
          ) : (
            <SuccessComponent />
          )}
        </ErrorBoundary>
      </div>
    );
  },
  parameters: {
    docs: {
      description: {
        story: 'Interactive demo allowing you to trigger different types of errors and toggle error details visibility.',
      },
    },
  },
};
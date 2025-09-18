# EmailPreview Component

A comprehensive React component for previewing and managing job matching system emails with multiple preview modes and interactive features.

## Features

### Preview Modes
- **Desktop View**: Full desktop email layout with responsive design
- **Mobile View**: Mobile-optimized email display with device frame
- **Plain Text View**: Text-only version for accessibility and email clients without HTML support
- **HTML Source View**: Raw HTML source code for debugging and development

### Email Sections
The component displays emails with the following sections:
- **Editorial Picks**: 5 hand-curated jobs by the editorial team
- **Top 5 Recommendations**: Highest-scoring personalized matches
- **Personalized Picks**: 10 jobs based on user preferences and history
- **New Arrivals**: 10 recently added jobs
- **Popular Jobs**: 5 trending jobs with high application rates
- **You Might Also Like**: 5 jobs based on collaborative filtering

### Interactive Features
- User selector dropdown to preview emails for different users
- Regenerate email functionality with loading states
- Send test email capability
- Editable subject line with live preview
- Device frame toggle for mobile/desktop comparison
- Fullscreen mode for detailed review

### Job Card Display
Each job is displayed with:
- Company logo or fallback icon
- Job title and company name
- Location and salary information
- Match score visualization with color coding
- Tags and badges (new, popular, etc.)
- Apply button with external link handling

### Email Metadata
- Subject line with variable substitution
- From address configuration
- Generated timestamp
- GPT-5 nano usage indicators
- Fallback template indicators
- Template version tracking

## Usage

### Basic Usage

```tsx
import { EmailPreview } from '@/components/EmailPreview';

function EmailPreviewPage() {
  return (
    <EmailPreview />
  );
}
```

### With Custom Props

```tsx
import { EmailPreview } from '@/components/EmailPreview';
import { EmailTemplate, User } from '@/components/EmailPreview/types';

function EmailPreviewPage() {
  const [emailTemplate, setEmailTemplate] = useState<EmailTemplate | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<string>('');

  const handleUserChange = (userId: string) => {
    setSelectedUserId(userId);
    // Fetch new email template for user
  };

  const handleRegenerateEmail = async () => {
    // Regenerate email logic
  };

  const handleSendTestEmail = async () => {
    // Send test email logic
  };

  const handleSubjectChange = (subject: string) => {
    // Update subject line logic
  };

  return (
    <EmailPreview
      emailTemplate={emailTemplate}
      users={users}
      selectedUserId={selectedUserId}
      onUserChange={handleUserChange}
      onRegenerateEmail={handleRegenerateEmail}
      onSendTestEmail={handleSendTestEmail}
      onSubjectChange={handleSubjectChange}
      isLoading={false}
      error={null}
    />
  );
}
```

## Component Architecture

### Main Components

- **EmailPreview**: Main container component with sidebar and preview area
- **EmailSection**: Renders individual email sections with jobs
- **JobCard**: Displays individual job information with interactive elements
- **DeviceFrame**: Provides device-specific styling for mobile/desktop preview

### Supporting Files

- **types.ts**: TypeScript type definitions for all components
- **utils.ts**: Utility functions for data generation and email conversion
- **hooks.ts**: Custom React hooks for state management and side effects

### Custom Hooks

- **useEmailPreview**: Main hook for email preview state management
- **useDeviceFrame**: Hook for device frame and fullscreen functionality
- **useEmailContent**: Hook for subject line editing and content management
- **useEmailAnalytics**: Hook for calculating email analytics and metadata

## Props API

### EmailPreview Props

| Prop | Type | Description |
|------|------|-------------|
| `emailTemplate` | `EmailTemplate \| undefined` | Email template to preview |
| `users` | `User[] \| undefined` | List of users for selection |
| `selectedUserId` | `string \| undefined` | Currently selected user ID |
| `onUserChange` | `(userId: string) => void \| undefined` | Callback when user changes |
| `onRegenerateEmail` | `() => void \| undefined` | Callback to regenerate email |
| `onSendTestEmail` | `() => void \| undefined` | Callback to send test email |
| `onSubjectChange` | `(subject: string) => void \| undefined` | Callback when subject changes |
| `isLoading` | `boolean \| undefined` | Loading state override |
| `error` | `string \| undefined` | Error message override |

### JobCard Props

| Prop | Type | Description |
|------|------|-------------|
| `job` | `Job` | Job data to display |
| `previewMode` | `PreviewMode` | Current preview mode |
| `showMatchScore` | `boolean \| undefined` | Whether to show match score |
| `compact` | `boolean \| undefined` | Use compact layout |
| `className` | `string \| undefined` | Additional CSS classes |

### EmailSection Props

| Prop | Type | Description |
|------|------|-------------|
| `section` | `EmailSection` | Section data to display |
| `previewMode` | `PreviewMode` | Current preview mode |
| `className` | `string \| undefined` | Additional CSS classes |

## Testing

The component includes comprehensive test suites:

```bash
# Run all tests
npm test

# Run tests with coverage
npm test -- --coverage

# Run tests in watch mode
npm test -- --watch

# Run specific test file
npm test EmailPreview.test.tsx
```

### Test Coverage

- **EmailPreview.test.tsx**: Main component functionality and interactions
- **JobCard.test.tsx**: Job card rendering and user interactions
- **EmailSection.test.tsx**: Section rendering and styling
- **DeviceFrame.test.tsx**: Device frame functionality
- **utils.test.ts**: Utility functions and data generation
- **hooks.test.ts**: Custom hook behavior and state management

## Styling

The component uses Tailwind CSS with a custom design system:

### Color Scheme
- **Editorial Picks**: Purple theme (`purple-600`, `purple-50`)
- **Top Recommendations**: Blue theme (`blue-600`, `blue-50`)
- **Personalized Picks**: Red theme (`red-600`, `red-50`)
- **New Arrivals**: Green theme (`green-600`, `green-50`)
- **Popular Jobs**: Orange theme (`orange-600`, `orange-50`)
- **You Might Like**: Indigo theme (`indigo-600`, `indigo-50`)

### Responsive Design
- Mobile-first approach with responsive breakpoints
- Adaptive grid layouts for different screen sizes
- Touch-friendly interactive elements for mobile devices

## Performance Considerations

### Optimization Features
- Lazy loading of email content
- Memoized calculations for analytics
- Debounced subject line editing
- Efficient re-rendering with React hooks

### Memory Management
- Cleanup of timers and subscriptions
- Optimized mock data generation
- Minimal re-renders with proper dependency arrays

## Accessibility

### Features
- Semantic HTML structure
- ARIA labels and descriptions
- Keyboard navigation support
- Screen reader compatibility
- High contrast mode support

### Plain Text Mode
- Accessible alternative to HTML preview
- Proper heading hierarchy
- Clear content structure
- Screen reader optimized

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Dependencies

### Required Dependencies
- React 18+
- Next.js 13+
- Tailwind CSS 3+
- Lucide React (icons)
- class-variance-authority
- clsx

### UI Components
- Radix UI components (Button, Card, Tabs, etc.)
- Custom UI component library

## Contributing

### Development Setup

1. Install dependencies:
```bash
npm install
```

2. Run development server:
```bash
npm run dev
```

3. Run tests:
```bash
npm test
```

### Code Standards
- TypeScript strict mode
- ESLint configuration
- Prettier formatting
- Jest testing framework

### Adding New Features
1. Create feature branch
2. Implement functionality with types
3. Add comprehensive tests
4. Update documentation
5. Submit pull request

## License

MIT License - see LICENSE file for details.
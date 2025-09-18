# Job Matching System Frontend

A comprehensive frontend application for the AI-powered job matching system built with Next.js 14, TypeScript, and Atomic Design principles.

## 🏗️ Architecture

This project follows the Atomic Design methodology for component organization:

### Component Structure

```
src/components/
├── atoms/          # Basic building blocks
│   ├── Button/
│   ├── Input/
│   ├── Select/
│   ├── Badge/
│   ├── Avatar/
│   ├── Typography/
│   └── Loader/
├── molecules/      # Combinations of atoms
│   ├── FormField/
│   ├── SearchBar/
│   ├── JobCard/
│   ├── ScoreDisplay/
│   └── Pagination/
├── organisms/      # Complex UI sections
│   ├── JobListItem/
│   ├── JobFilterPanel/
│   └── Navigation/
└── templates/      # Page layouts
    ├── MainLayout/
    ├── DashboardLayout/
    └── AuthLayout/
```

### Pages (App Router)

```
src/app/
├── jobs/
│   ├── page.tsx           # Job listing page
│   └── [id]/page.tsx      # Job detail page
├── dashboard/
│   └── page.tsx           # User dashboard
└── profile/
    └── page.tsx           # User profile
```

## 🚀 Features

### UI Components
- **Atoms**: Reusable basic elements (buttons, inputs, badges, etc.)
- **Molecules**: Composite components (search bars, job cards, etc.)
- **Organisms**: Complex sections (navigation, filter panels, etc.)
- **Templates**: Page layouts with responsive design

### Design System
- **Tailwind CSS** with custom design tokens
- **Consistent color palette** with semantic naming
- **Typography scale** with responsive sizing
- **Spacing system** for consistent layouts
- **Animation utilities** for smooth interactions

### Accessibility
- **ARIA labels** and semantic HTML
- **Keyboard navigation** support
- **Screen reader** compatibility
- **Focus management** for interactive elements
- **Color contrast** compliance

### TypeScript
- **Comprehensive type definitions** for all data models
- **Strict typing** for component props
- **API response types** with validation
- **Utility type helpers** for common patterns

## 🛠️ Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide React** - Icon library
- **Zustand** - State management
- **React Query** - Server state management
- **Zod** - Schema validation
- **Storybook** - Component documentation

## 📦 Installation

1. **Install dependencies**:
```bash
npm install
```

2. **Set up environment variables**:
```bash
cp .env.example .env.local
```

3. **Start development server**:
```bash
npm run dev
```

4. **Start Storybook** (optional):
```bash
npm run storybook
```

## 🎨 Design Tokens

### Colors
- **Primary**: Blue color palette for main actions
- **Secondary**: Gray color palette for text and backgrounds
- **Success**: Green for positive states
- **Warning**: Orange for cautionary states
- **Danger**: Red for error states

### Typography
- **Font Family**: Inter (sans-serif), Fira Code (monospace)
- **Font Sizes**: xs, sm, base, lg, xl, 2xl, 3xl, 4xl, 5xl, 6xl
- **Font Weights**: light, normal, medium, semibold, bold

### Spacing
- **Scale**: 0.25rem increments from 1 to 96
- **Custom**: 18 (4.5rem), 88 (22rem), 128 (32rem)

## 📚 Component Usage

### Button
```tsx
import { Button } from '@/components/atoms';

<Button variant="primary" size="md" onClick={handleClick}>
  Click me
</Button>
```

### Job Card
```tsx
import { JobCard } from '@/components/molecules';

<JobCard
  job={jobData}
  variant="default"
  onApply={handleApply}
  onSave={handleSave}
/>
```

### Layout
```tsx
import { MainLayout } from '@/components/templates';

<MainLayout title="Page Title" user={user}>
  <div>Page content</div>
</MainLayout>
```

## 🧪 Testing

### Unit Tests
```bash
npm run test
npm run test:watch
npm run test:coverage
```

### E2E Tests
```bash
npm run test:e2e
```

### Type Checking
```bash
npm run type-check
```

## 📖 Documentation

### Storybook
Access component documentation and interactive examples:
```bash
npm run storybook
```

Navigate to `http://localhost:6006` to view:
- Component API documentation
- Interactive examples
- Design system guidelines
- Accessibility features

### Component Stories
Each component includes comprehensive Storybook stories showing:
- All variants and states
- Props documentation
- Usage examples
- Accessibility notes

## 🎯 Key Features

### Job Matching
- **Smart filtering** with multiple criteria
- **Match score visualization** with detailed breakdowns
- **Personalized recommendations** based on user profile
- **Real-time search** with debounced input

### User Experience
- **Responsive design** for all screen sizes
- **Dark mode support** (configurable)
- **Loading states** and error handling
- **Optimistic updates** for better perceived performance

### Performance
- **Code splitting** with Next.js App Router
- **Image optimization** with Next.js Image
- **Bundle analysis** tools
- **Lazy loading** for non-critical components

## 📱 Responsive Design

### Breakpoints
- **Mobile**: 640px and below
- **Tablet**: 641px - 1024px
- **Desktop**: 1025px and above

### Mobile-First Approach
- Components designed for mobile first
- Progressive enhancement for larger screens
- Touch-friendly interactive elements
- Optimized for performance on mobile devices

## 🔧 Build & Deployment

### Development
```bash
npm run dev          # Start development server
npm run lint         # Run ESLint
npm run type-check   # TypeScript type checking
```

### Production
```bash
npm run build        # Build for production
npm run start        # Start production server
```

### Storybook
```bash
npm run storybook           # Start Storybook dev server
npm run build-storybook     # Build static Storybook
```

## 📄 File Structure

```
frontend/
├── .storybook/              # Storybook configuration
├── public/                  # Static assets
├── src/
│   ├── app/                 # Next.js App Router pages
│   ├── components/          # UI components (Atomic Design)
│   ├── lib/                 # Utility functions and constants
│   ├── types/               # TypeScript type definitions
│   ├── stories/             # Storybook stories
│   └── styles/              # Global styles
├── tailwind.config.js       # Tailwind CSS configuration
├── next.config.js          # Next.js configuration
└── package.json            # Dependencies and scripts
```

## 🎨 Customization

### Extending the Design System
1. **Colors**: Add new color tokens in `tailwind.config.js`
2. **Components**: Create new atoms/molecules following the pattern
3. **Types**: Extend type definitions in `src/types/`
4. **Utilities**: Add helper functions in `src/lib/`

### Theme Customization
- Modify color palettes in Tailwind config
- Adjust typography scales and font families
- Customize spacing and sizing scales
- Add new animation utilities

## 🤝 Contributing

1. Follow the Atomic Design methodology
2. Include TypeScript types for all props
3. Add Storybook stories for new components
4. Write unit tests for component logic
5. Ensure accessibility compliance
6. Document component APIs

## 📝 License

This project is licensed under the ISC License.
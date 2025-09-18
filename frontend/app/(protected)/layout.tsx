import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'SQL Console - Job Matching System',
  description: 'Database query console for the job matching system with advanced analytics and reporting capabilities.',
  keywords: 'SQL, database, analytics, job matching, console, query',
  robots: 'noindex, nofollow', // Protected area shouldn't be indexed
}

// This would typically include authentication checks
export default function ProtectedLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-background">
      {/* Authentication check would go here */}
      {/* For now, we'll just render the children */}
      {children}
    </div>
  )
}
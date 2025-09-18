// Header component
// Basic implementation to resolve import errors

interface HeaderProps {
  variant?: 'public' | 'dashboard';
}

export function Header({ variant = 'public' }: HeaderProps) {
  return (
    <header className="bg-white border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <h1 className="text-xl font-semibold">JobMatch Pro</h1>
          </div>
          <nav className="flex space-x-8">
            <a href="/jobs" className="text-gray-600 hover:text-gray-900">Jobs</a>
            <a href="/companies" className="text-gray-600 hover:text-gray-900">Companies</a>
            <a href="/login" className="text-gray-600 hover:text-gray-900">Login</a>
          </nav>
        </div>
      </div>
    </header>
  );
}
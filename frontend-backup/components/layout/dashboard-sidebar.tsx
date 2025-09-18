// Dashboard sidebar component
// Basic implementation to resolve import errors

"use client";

export interface DashboardSidebarProps {
  className?: string;
}

export function DashboardSidebar({ className }: DashboardSidebarProps) {
  const navigation = [
    { name: 'Dashboard', href: '/dashboard', current: true },
    { name: 'Jobs', href: '/jobs', current: false },
    { name: 'Applications', href: '/applications', current: false },
    { name: 'Profile', href: '/profile', current: false },
    { name: 'Settings', href: '/settings', current: false },
  ];

  return (
    <aside className={`bg-gray-50 w-64 min-h-screen border-r border-gray-200 ${className}`}>
      <nav className="p-6">
        <ul className="space-y-2">
          {navigation.map((item) => (
            <li key={item.name}>
              <a
                href={item.href}
                className={`block px-4 py-2 rounded-md text-sm font-medium ${
                  item.current
                    ? 'bg-blue-100 text-blue-900'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                {item.name}
              </a>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}
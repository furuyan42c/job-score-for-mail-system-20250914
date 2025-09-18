// Dashboard footer component
// Basic implementation to resolve import errors

export interface DashboardFooterProps {
  className?: string;
}

export function DashboardFooter({ className }: DashboardFooterProps) {
  return (
    <footer className={`bg-white border-t border-gray-200 ${className}`}>
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-500">
            © 2024 JobMatch Pro. All rights reserved.
          </div>
          <div className="flex items-center space-x-4 text-sm text-gray-500">
            <a href="/privacy" className="hover:text-gray-700">Privacy</a>
            <a href="/terms" className="hover:text-gray-700">Terms</a>
            <a href="/support" className="hover:text-gray-700">Support</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
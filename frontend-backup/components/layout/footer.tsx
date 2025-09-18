// Footer component
// Basic implementation to resolve import errors

export function Footer() {
  return (
    <footer className="bg-gray-50 border-t">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-4">Company</h3>
            <ul className="space-y-2">
              <li><a href="/about" className="text-gray-600 hover:text-gray-900">About</a></li>
              <li><a href="/careers" className="text-gray-600 hover:text-gray-900">Careers</a></li>
              <li><a href="/contact" className="text-gray-600 hover:text-gray-900">Contact</a></li>
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-4">Resources</h3>
            <ul className="space-y-2">
              <li><a href="/help" className="text-gray-600 hover:text-gray-900">Help</a></li>
              <li><a href="/blog" className="text-gray-600 hover:text-gray-900">Blog</a></li>
              <li><a href="/api" className="text-gray-600 hover:text-gray-900">API</a></li>
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-4">Legal</h3>
            <ul className="space-y-2">
              <li><a href="/privacy" className="text-gray-600 hover:text-gray-900">Privacy</a></li>
              <li><a href="/terms" className="text-gray-600 hover:text-gray-900">Terms</a></li>
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-4">Connect</h3>
            <p className="text-gray-600">Follow us for updates</p>
          </div>
        </div>
        <div className="mt-8 pt-8 border-t text-center text-gray-500">
          <p>&copy; 2024 JobMatch Pro. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}
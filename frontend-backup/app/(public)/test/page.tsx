export default function TestPage() {
  return (
    <div className="p-8">
      <h1 className="text-4xl font-bold text-blue-600 mb-4">Test Page</h1>
      <p className="text-lg text-gray-600 mb-8">
        This is a simple test page to verify the app is working correctly.
      </p>

      <div className="space-y-4">
        <div className="bg-blue-100 p-4 rounded-lg">
          <h2 className="text-xl font-semibold text-blue-800">✅ Layout Loading</h2>
          <p className="text-blue-600">If you can see this, the layout is working properly.</p>
        </div>

        <div className="bg-green-100 p-4 rounded-lg">
          <h2 className="text-xl font-semibold text-green-800">✅ Styling Working</h2>
          <p className="text-green-600">Tailwind CSS classes are being applied correctly.</p>
        </div>

        <div className="bg-purple-100 p-4 rounded-lg">
          <h2 className="text-xl font-semibold text-purple-800">✅ Components Loading</h2>
          <p className="text-purple-600">React components are rendering without errors.</p>
        </div>
      </div>

      <div className="mt-8">
        <a
          href="/"
          className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Back to Home
        </a>
      </div>
    </div>
  );
}
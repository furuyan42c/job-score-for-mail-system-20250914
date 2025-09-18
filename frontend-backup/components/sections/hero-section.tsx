// Hero section component
// Basic implementation to resolve import errors

export function HeroSection() {
  return (
    <section className="bg-gradient-to-r from-blue-600 to-purple-600 text-white py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h1 className="text-4xl md:text-6xl font-bold mb-6">
          Find Your Dream Job
        </h1>
        <p className="text-xl md:text-2xl mb-8 opacity-90">
          Connect with top companies and discover opportunities that match your skills
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <a href="/jobs" className="bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100">
            Browse Jobs
          </a>
          <a href="/signup" className="border border-white px-8 py-3 rounded-lg font-semibold hover:bg-white hover:bg-opacity-10">
            Get Started
          </a>
        </div>
      </div>
    </section>
  );
}
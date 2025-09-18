// Features section component
// Basic implementation to resolve import errors

export function FeaturesSection() {
  const features = [
    {
      title: "AI-Powered Matching",
      description: "Our advanced algorithms match you with jobs that fit your skills and preferences.",
      icon: "🤖"
    },
    {
      title: "Real-time Updates",
      description: "Get notified instantly when new opportunities that match your profile become available.",
      icon: "🔔"
    },
    {
      title: "Comprehensive Profiles",
      description: "Build detailed profiles that showcase your skills, experience, and career aspirations.",
      icon: "👤"
    },
    {
      title: "Company Insights",
      description: "Access detailed information about company culture, benefits, and employee reviews.",
      icon: "🏢"
    }
  ];

  return (
    <section className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            Why Choose JobMatch Pro?
          </h2>
          <p className="text-xl text-gray-600">
            Discover the features that make us the preferred choice for job seekers
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => (
            <div key={index} className="text-center">
              <div className="text-4xl mb-4">{feature.icon}</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">{feature.title}</h3>
              <p className="text-gray-600">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
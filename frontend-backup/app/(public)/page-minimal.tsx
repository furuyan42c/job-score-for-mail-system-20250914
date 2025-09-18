/**
 * Minimal Landing Page for debugging
 */

import { HeroSection } from '@/components/sections/hero-section';

export default function MinimalLandingPage() {
  return (
    <div className="flex flex-col">
      {/* Test basic div first */}
      <div className="p-8 bg-green-100">
        <h1 className="text-3xl font-bold text-green-800">✅ Page Loading Successfully</h1>
        <p className="text-green-600">Basic page structure is working.</p>
      </div>

      {/* Test Hero Section */}
      <section className="relative">
        <HeroSection />
      </section>

      {/* Simple content */}
      <section className="py-12 bg-blue-50">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <h2 className="text-2xl font-bold text-blue-800 mb-4">✅ Components Loading</h2>
          <p className="text-blue-600">If you can see the hero section above, components are working.</p>
        </div>
      </section>
    </div>
  );
}
const path = require('path');

module.exports = {
  plugins: {
    'tailwindcss': {},
    'autoprefixer': {},
    // CSS optimization for production
    ...(process.env.NODE_ENV === 'production' && {
      '@fullhuman/postcss-purgecss': {
        content: [
          './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
          './src/components/**/*.{js,ts,jsx,tsx,mdx}',
          './src/app/**/*.{js,ts,jsx,tsx,mdx}',
          './src/stories/**/*.{js,ts,jsx,tsx,mdx}',
          './src/lib/**/*.{js,ts,jsx,tsx,mdx}',
          './app/**/*.{js,ts,jsx,tsx,mdx}',
          './lib/**/*.{js,ts,jsx,tsx,mdx}',
        ],
        defaultExtractor: content => content.match(/[\w-/:]+(?<!:)/g) || [],
        safelist: {
          standard: [
            // Preserve dynamic classes
            /^animate-/,
            /^duration-/,
            /^ease-/,
            /^transition-/,
            /^transform/,
            /^scale-/,
            /^rotate-/,
            /^translate-/,
            /^skew-/,
            // Preserve state-based classes
            /^hover:/,
            /^focus:/,
            /^active:/,
            /^disabled:/,
            /^group-hover:/,
            /^group-focus:/,
            // Preserve responsive classes
            /^sm:/,
            /^md:/,
            /^lg:/,
            /^xl:/,
            /^2xl:/,
            // Preserve dark mode classes
            /^dark:/,
            // Preserve error boundary and loading states
            /error/,
            /loading/,
            /spinner/,
            // Preserve component-specific classes
            /btn/,
            /card/,
            /badge/,
            /input/,
          ],
          deep: [
            // Preserve classes that might be added dynamically
            /data-/,
            /aria-/,
            /role-/,
          ],
          greedy: [
            // Preserve color variations
            /^bg-(primary|secondary|success|warning|danger|muted|accent|card|popover)-/,
            /^text-(primary|secondary|success|warning|danger|muted|accent|card|popover)-/,
            /^border-(primary|secondary|success|warning|danger|muted|accent|card|popover)-/,
            /^ring-(primary|secondary|success|warning|danger|muted|accent|card|popover)-/,
            // Preserve spacing variations
            /^(m|p)(t|r|b|l|x|y)?-/,
            /^space-(x|y)-/,
            /^gap-/,
            // Preserve sizing variations
            /^(w|h|min-w|min-h|max-w|max-h)-/,
            // Preserve positioning
            /^(top|right|bottom|left|inset)-/,
            // Preserve z-index
            /^z-/,
          ],
        },
        // Don't remove CSS custom properties
        variables: true,
        // Don't remove keyframes
        keyframes: true,
      },
      'cssnano': {
        preset: [
          'default',
          {
            // Preserve CSS custom properties
            cssDeclarationSorter: false,
            // Don't merge rules to preserve cascade
            mergeRules: false,
            // Don't remove comments that might be important
            discardComments: {
              removeAll: false,
            },
            // Don't normalize whitespace in CSS custom properties
            normalizeWhitespace: false,
          },
        ],
      },
    }),
  },
};
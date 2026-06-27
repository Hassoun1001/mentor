/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        mentor: {
          bg: '#0b1614',
          panel: '#102420',
          panelLight: '#173430',
          fg: '#e6efe9',
          muted: '#8aa098',
          accent: '#1f8a70',
          accentSoft: '#2faa8e',
          warn: '#d4a14a',
          danger: '#d75f5f',
          border: '#1d3a33',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'Segoe UI', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'monospace'],
        serif: ['Source Serif Pro', 'Georgia', 'serif'],
      },
      boxShadow: {
        panel: '0 1px 2px rgba(0,0,0,0.3), 0 4px 14px rgba(0,0,0,0.25)',
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
};

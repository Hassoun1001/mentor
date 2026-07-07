/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Values are CSS variables (RGB channels) so the whole palette can
        // switch between dark and light at runtime, while keeping Tailwind's
        // /opacity modifiers working. Channels are defined in index.css.
        mentor: {
          bg: 'rgb(var(--mentor-bg) / <alpha-value>)',
          panel: 'rgb(var(--mentor-panel) / <alpha-value>)',
          panelLight: 'rgb(var(--mentor-panelLight) / <alpha-value>)',
          fg: 'rgb(var(--mentor-fg) / <alpha-value>)',
          muted: 'rgb(var(--mentor-muted) / <alpha-value>)',
          accent: 'rgb(var(--mentor-accent) / <alpha-value>)',
          accentHover: 'rgb(var(--mentor-accentHover) / <alpha-value>)',
          accentSoft: 'rgb(var(--mentor-accentSoft) / <alpha-value>)',
          warn: 'rgb(var(--mentor-warn) / <alpha-value>)',
          danger: 'rgb(var(--mentor-danger) / <alpha-value>)',
          border: 'rgb(var(--mentor-border) / <alpha-value>)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'Segoe UI', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'monospace'],
        serif: ['Source Serif Pro', 'Georgia', 'serif'],
      },
      boxShadow: {
        panel: '0 1px 2px rgba(0,0,0,0.4)',
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
};

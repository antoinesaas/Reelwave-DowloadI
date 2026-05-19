/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        rw: {
          bg:      '#FFFFFF',
          ink:     '#0A0A0A',
          muted:   '#6E6E73',
          border:  '#E0E0E0',
          surface: 'rgba(255,255,255,0.72)',
          success: '#22C55E',
          error:   '#EF4444',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"IBM Plex Mono"', 'monospace'],
      },
      backdropBlur: { glass: '24px' },
      keyframes: {
        'float': {
          '0%,100%': { transform: 'translateY(0px)' },
          '50%':     { transform: 'translateY(-10px)' },
        },
        'glow-pulse': {
          '0%,100%': { boxShadow: '0 0 0 0 rgba(10,10,10,0)' },
          '50%':     { boxShadow: '0 0 20px 4px rgba(10,10,10,0.08)' },
        },
        'shake': {
          '0%,100%': { transform: 'translateX(0)' },
          '20%':     { transform: 'translateX(-8px)' },
          '40%':     { transform: 'translateX(8px)' },
          '60%':     { transform: 'translateX(-5px)' },
          '80%':     { transform: 'translateX(5px)' },
        },
        'spin-slow': {
          '0%':   { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
      },
      animation: {
        'float':       'float 4s ease-in-out infinite',
        'glow-pulse':  'glow-pulse 2s ease-in-out infinite',
        'shake':       'shake 0.4s ease-in-out',
        'spin-slow':   'spin-slow 8s linear infinite',
      },
    },
  },
  plugins: [],
}

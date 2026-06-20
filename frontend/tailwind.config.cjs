/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        ml: {
          500: '#2563EB',
          600: '#2563EB',
          700: '#1D4ED8',
        },
        primary: '#2563EB',
        secondary: '#7C3AED',
        success: '#10B981',
        warning: '#F59E0B',
        danger: '#EF4444',
        canvas: '#F8FAFC',
        card: '#FFFFFF',
        stroke: '#E2E8F0',
      },
      fontFamily: {
        display: ['Sora', 'Segoe UI', 'sans-serif'],
        body: ['Manrope', 'Segoe UI', 'sans-serif'],
      },
      boxShadow: {
        premium: '0 20px 50px rgba(15, 23, 42, 0.12)',
        float: '0 10px 30px rgba(37, 99, 235, 0.2)',
      },
      animation: {
        'fade-in': 'fadeIn 500ms ease-out',
        'slide-up': 'slideUp 450ms ease-out',
        pulseGlow: 'pulseGlow 1.6s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseGlow: {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(37, 99, 235, 0.2)' },
          '50%': { boxShadow: '0 0 0 10px rgba(37, 99, 235, 0.02)' },
        },
      },
    },
  },
  plugins: [],
}

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Hakkast brand color palette
        hakkast: {
          navy: '#0E2148',      // Primary dark blue
          purple: '#483AA0',    // Primary purple  
          lavender: '#7965C1',  // Light purple
          gold: '#E3D095',      // Gold accent
        },
        primary: {
          50: '#f4f3ff',
          100: '#ebe9fe',
          200: '#d9d6fe',
          300: '#beb7fd',
          400: '#a090fa',
          500: '#7965C1',       // Hakkast lavender
          600: '#483AA0',       // Hakkast purple
          700: '#3a2f80',
          800: '#2f2563',
          900: '#0E2148',       // Hakkast navy
        },
        accent: {
          50: '#fefce8',
          100: '#fef9c3',
          200: '#fef08a',
          300: '#fde047',
          400: '#facc15',
          500: '#E3D095',       // Hakkast gold
          600: '#ca8a04',
          700: '#a16207',
          800: '#854d0e',
          900: '#713f12',
        },
      },
      fontFamily: {
        'sans': ['Inter', 'system-ui', 'sans-serif'],
        'display': ['Poppins', 'system-ui', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.6s ease-out',
        'float': 'float 3s ease-in-out infinite',
        'pulse-slow': 'pulse 3s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'hakkast-gradient': 'linear-gradient(135deg, #0E2148 0%, #483AA0 50%, #7965C1 100%)',
        'hakkast-gold-gradient': 'linear-gradient(135deg, #E3D095 0%, #f6e8c1 100%)',
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
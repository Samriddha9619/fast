import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#2563eb',
        secondary: '#4b5563',
        background: '#f9fafb',
        'chat-sent': '#3b82f6',
        'chat-received': '#e5e7eb',
      },
    },
  },
  plugins: [],
}

export default config
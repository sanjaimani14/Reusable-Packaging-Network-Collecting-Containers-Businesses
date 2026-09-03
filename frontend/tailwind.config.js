/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          green: '#10B981', // green for positive recovery
          red: '#EF4444',   // red for safety/high-risk
          amber: '#F59E0B', // amber for warnings
          blue: '#3B82F6',  // blue for information
          dark: '#1E293B',  // slate-800
          light: '#F8FAFC', // slate-50
        }
      }
    },
  },
  plugins: [],
}

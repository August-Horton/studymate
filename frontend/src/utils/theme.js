const THEME_KEY = 'studymate_theme'
const LIGHT_THEME = 'light'
const DARK_THEME = 'dark'

const lightTheme = {
  '--bg-primary': '#f5f5f5',
  '--bg-secondary': '#ffffff',
  '--bg-tertiary': '#f9fafb',
  '--text-primary': '#1f2937',
  '--text-secondary': '#4b5563',
  '--text-tertiary': '#9ca3af',
  '--border-color': '#e5e7eb',
  '--accent-color': '#4f46e5',
  '--accent-light': '#eef2ff',
  '--shadow-color': 'rgba(0, 0, 0, 0.1)',
  '--nav-bg': '#ffffff',
  '--nav-text': '#1f2937',
  '--card-bg': '#ffffff',
  '--card-border': '#e5e7eb'
}

const darkTheme = {
  '--bg-primary': '#0f172a',
  '--bg-secondary': '#1e293b',
  '--bg-tertiary': '#334155',
  '--text-primary': '#f1f5f9',
  '--text-secondary': '#cbd5e1',
  '--text-tertiary': '#64748b',
  '--border-color': '#334155',
  '--accent-color': '#818cf8',
  '--accent-light': '#312e81',
  '--shadow-color': 'rgba(0, 0, 0, 0.3)',
  '--nav-bg': '#1e293b',
  '--nav-text': '#f1f5f9',
  '--card-bg': '#1e293b',
  '--card-border': '#334155'
}

export const getCurrentTheme = () => {
  return localStorage.getItem(THEME_KEY) || LIGHT_THEME
}

export const applyTheme = (theme) => {
  const themeVars = theme === DARK_THEME ? darkTheme : lightTheme
  const root = document.documentElement

  Object.entries(themeVars).forEach(([key, value]) => {
    root.style.setProperty(key, value)
  })

  root.setAttribute('data-theme', theme)
  localStorage.setItem(THEME_KEY, theme)
}

export const toggleTheme = () => {
  const current = getCurrentTheme()
  const next = current === LIGHT_THEME ? DARK_THEME : LIGHT_THEME
  applyTheme(next)
  return next
}

export const initTheme = () => {
  const saved = getCurrentTheme()
  applyTheme(saved)
  return saved
}

export { LIGHT_THEME, DARK_THEME }

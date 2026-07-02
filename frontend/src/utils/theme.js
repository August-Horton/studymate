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
  '--text-muted': '#d1d5db',
  '--border-color': '#e5e7eb',
  '--accent-color': '#4f46e5',
  '--accent-light': '#eef2ff',
  '--shadow-color': 'rgba(0, 0, 0, 0.08)',
  '--nav-bg': '#ffffff',
  '--nav-text': '#1f2937',
  '--card-bg': '#ffffff',
  '--card-border': '#e5e7eb',
  '--danger-light': '#fef2f2',
  '--hover-bg': '#f3f4f6'
}

const darkTheme = {
  '--bg-primary': '#0f172a',
  '--bg-secondary': '#1e293b',
  '--bg-tertiary': '#334155',
  '--text-primary': '#f1f5f9',
  '--text-secondary': '#cbd5e1',
  '--text-tertiary': '#64748b',
  '--text-muted': '#475569',
  '--border-color': '#334155',
  '--accent-color': '#818cf8',
  '--accent-light': '#1e1b4b',
  '--shadow-color': 'rgba(0, 0, 0, 0.4)',
  '--nav-bg': '#1e293b',
  '--nav-text': '#f1f5f9',
  '--card-bg': '#1e293b',
  '--card-border': '#334155',
  '--danger-light': 'rgba(239, 68, 68, 0.12)',
  '--hover-bg': '#334155'
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

  document.body.style.setProperty('color-scheme', theme === DARK_THEME ? 'dark' : 'light')
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

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type Theme = 'light' | 'dark' | 'system'

interface ThemeState {
  theme: Theme
  resolvedTheme: 'light' | 'dark'
  setTheme: (theme: Theme) => void
  toggleTheme: () => void
  initializeTheme: () => void
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: 'system',
      resolvedTheme: 'dark',

      setTheme: (theme: Theme) => {
        set({ theme })
        get().initializeTheme()
      },

      toggleTheme: () => {
        const { theme } = get()
        const themes: Theme[] = ['light', 'dark', 'system']
        const currentIndex = themes.indexOf(theme)
        const nextTheme = themes[(currentIndex + 1) % themes.length]
        set({ theme: nextTheme })
        get().initializeTheme()
      },

      initializeTheme: () => {
        const { theme } = get()
        let resolved: 'light' | 'dark'
        
        if (theme === 'system') {
          resolved = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
        } else {
          resolved = theme
        }
        
        set({ resolvedTheme: resolved })
        
        if (resolved === 'dark') {
          document.documentElement.classList.add('dark')
        } else {
          document.documentElement.classList.remove('dark')
        }
      },
    }),
    {
      name: 'miniclaw-theme',
    }
  )
)

export const useTheme = () => useThemeStore((state) => ({
  theme: state.theme,
  resolvedTheme: state.resolvedTheme,
  setTheme: state.setTheme,
  toggleTheme: state.toggleTheme,
}))
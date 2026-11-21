// Choix du thème visuel (design seulement). Le choix est mémorisé dans le navigateur.
import { ref } from 'vue'

const CLE = 'gestquinca_theme'
const THEMES = ['pro', 'doux']

function lire() {
  try {
    const t = localStorage.getItem(CLE)
    return THEMES.includes(t) ? t : 'pro'
  } catch {
    return 'pro'
  }
}

export const theme = ref(lire())

function appliquer() {
  document.documentElement.setAttribute('data-theme', theme.value)
}
appliquer()

export function changerTheme() {
  theme.value = theme.value === 'pro' ? 'doux' : 'pro'
  appliquer()
  try {
    localStorage.setItem(CLE, theme.value)
  } catch {
    /* stockage indisponible : le choix vaut jusqu'au rechargement */
  }
}

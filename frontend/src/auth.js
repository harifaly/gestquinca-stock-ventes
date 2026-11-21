// État de connexion partagé par toute l'application (sans bibliothèque supplémentaire).
import { reactive } from 'vue'
import { api } from './api'

const CLE = 'gestquinca_session'

function lireSession() {
  try {
    return JSON.parse(localStorage.getItem(CLE)) || {}
  } catch {
    return {}
  }
}

const enregistree = lireSession()
export const session = reactive({
  token: enregistree.token || null,
  nom: enregistree.nom || '',
  role: enregistree.role || '',
})

export const estAdmin = () => session.role === 'admin'

export async function connexion(identifiant, motDePasse) {
  const r = await api.post('/auth/login', {
    formulaire: { username: identifiant, password: motDePasse },
  })
  session.token = r.access_token
  session.nom = r.nom_complet
  session.role = r.role
  try {
    localStorage.setItem(CLE, JSON.stringify({ token: r.access_token, nom: r.nom_complet, role: r.role }))
  } catch {
    /* stockage indisponible : la session durera jusqu'au rechargement de la page */
  }
}

export function deconnexion() {
  session.token = null
  session.nom = ''
  session.role = ''
  try {
    localStorage.removeItem(CLE)
  } catch {
    /* rien à faire */
  }
}

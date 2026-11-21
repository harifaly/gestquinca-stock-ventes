// Appels à l'API FastAPI. Un seul endroit pour : l'adresse de l'API, le jeton de connexion
// et la traduction des erreurs en messages lisibles.
const BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')

let config = { token: () => null, surNonAutorise: () => {} }

// main.js branche ici le jeton courant et ce qu'il faut faire quand la session expire
export function configurerApi(options) {
  config = { ...config, ...options }
}

export class ApiError extends Error {
  constructor(statut, message) {
    super(message)
    this.statut = statut
  }
}

function formaterDetail(detail) {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    // erreurs de validation (422) : [{ loc: ['body', 'prix_vente'], msg: '...' }]
    return detail.map((e) => `${(e.loc || []).slice(1).join('.')} : ${e.msg}`).join(' ; ')
  }
  return 'Erreur inattendue'
}

async function requete(methode, chemin, { corps, params, formulaire } = {}) {
  const url = new URL(BASE + chemin)
  if (params) {
    for (const [cle, valeur] of Object.entries(params)) {
      if (valeur !== '' && valeur !== null && valeur !== undefined && valeur !== false) {
        url.searchParams.set(cle, valeur)
      }
    }
  }
  const entetes = {}
  const token = config.token()
  if (token) entetes.Authorization = `Bearer ${token}`

  let body
  if (formulaire) {
    body = new URLSearchParams(formulaire)
  } else if (corps !== undefined) {
    entetes['Content-Type'] = 'application/json'
    body = JSON.stringify(corps)
  }

  let reponse
  try {
    reponse = await fetch(url, { method: methode, headers: entetes, body })
  } catch {
    throw new ApiError(0, "Impossible de joindre l'API. Vérifiez qu'elle est démarrée (uvicorn).")
  }

  if (reponse.status === 401 && token) config.surNonAutorise()
  if (!reponse.ok) {
    let detail = `Erreur ${reponse.status}`
    try {
      detail = formaterDetail((await reponse.json()).detail)
    } catch {
      /* réponse sans JSON : on garde le message par défaut */
    }
    throw new ApiError(reponse.status, detail)
  }
  return reponse.status === 204 ? null : reponse.json()
}

export const api = {
  get: (chemin, options) => requete('GET', chemin, options),
  post: (chemin, options) => requete('POST', chemin, options),
  put: (chemin, options) => requete('PUT', chemin, options),
  patch: (chemin, options) => requete('PATCH', chemin, options),
  delete: (chemin, options) => requete('DELETE', chemin, options),
}

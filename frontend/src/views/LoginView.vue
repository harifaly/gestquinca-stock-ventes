<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { connexion } from '../auth'

const router = useRouter()
const identifiant = ref('')
const motDePasse = ref('')
const erreur = ref('')
const envoiEnCours = ref(false)

async function seConnecter() {
  erreur.value = ''
  envoiEnCours.value = true
  try {
    await connexion(identifiant.value, motDePasse.value)
    router.push({ name: 'produits' })
  } catch (e) {
    erreur.value = e.message
  } finally {
    envoiEnCours.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <section class="login-art" aria-hidden="false">
      <div class="login-art-texte">
        <span class="login-badge">Quincaillerie</span>
        <h2>Votre quincaillerie, simplement sous contrôle.</h2>
        <p>Achats, stock, ventes et crédits clients réunis au même endroit, sans calculs à refaire.</p>
        <ul class="login-points">
          <li>Un stock toujours juste</li>
          <li>Des ventes et des paiements suivis</li>
          <li>Des alertes avant la rupture</li>
        </ul>
      </div>
      <svg class="login-dessin" viewBox="0 0 360 220" role="img" aria-label="Cartons empilés">
        <ellipse cx="180" cy="204" rx="150" ry="10" fill="#27363d" opacity=".07" />
        <rect x="30" y="118" width="110" height="84" rx="12" fill="#fbefc9" stroke="#e0b84e" stroke-width="3" />
        <rect x="76" y="118" width="18" height="30" fill="#f4d97a" />
        <rect x="150" y="96" width="130" height="106" rx="12" fill="#dff0ec" stroke="#2a7f7a" stroke-width="3" />
        <rect x="204" y="96" width="22" height="38" fill="#9ccfc7" />
        <rect x="100" y="42" width="104" height="62" rx="12" fill="#fde5dd" stroke="#e8836a" stroke-width="3" />
        <rect x="143" y="42" width="18" height="24" fill="#f3b8a4" />
        <rect x="258" y="150" width="76" height="52" rx="10" fill="#ebe7f8" stroke="#8d82cf" stroke-width="3" />
        <circle cx="312" cy="62" r="22" fill="#fff" opacity=".7" />
        <circle cx="312" cy="62" r="9" fill="#fbefc9" />
      </svg>
    </section>

    <section class="login-form-side">
      <form class="login-carte" @submit.prevent="seConnecter">
        <h1 class="h3">Bon retour !</h1>
        <p class="text-muted mb-4">Connectez-vous pour gérer votre magasin.</p>

        <div class="mb-3">
          <label for="identifiant" class="form-label">Identifiant</label>
          <input id="identifiant" v-model.trim="identifiant" class="form-control form-control-lg" autocomplete="username" required autofocus />
        </div>
        <div class="mb-3">
          <label for="mot-de-passe" class="form-label">Mot de passe</label>
          <input id="mot-de-passe" v-model="motDePasse" type="password" class="form-control form-control-lg" autocomplete="current-password" required />
        </div>
        <div v-if="erreur" class="alert alert-danger py-2" role="alert">{{ erreur }}</div>
        <button class="btn btn-primary btn-lg w-100" :disabled="envoiEnCours">
          {{ envoiEnCours ? 'Connexion…' : 'Se connecter' }}
        </button>
        <p class="small text-muted mt-4 mb-0 demo-note">Démonstration : admin / admin123 ou vendeur / vendeur123</p>
      </form>
    </section>
  </div>
</template>

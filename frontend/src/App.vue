<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { session, deconnexion } from './auth'
import Icone from './components/Icone.vue'
import { theme, changerTheme } from './theme'

const router = useRouter()
const estAdmin = computed(() => session.role === 'admin')
const prenom = computed(() => (session.nom || '').split(' ')[0])
const initiales = computed(() => (session.nom || '?').split(' ').map((m) => m[0]).slice(0, 2).join('').toUpperCase())
const dateLongue = new Date().toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' })
const dateDuJour = dateLongue.charAt(0).toUpperCase() + dateLongue.slice(1)

function seDeconnecter() {
  deconnexion()
  router.push({ name: 'connexion' })
}
</script>

<template>
  <div v-if="session.token" class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand-mark"><Icone nom="produits" :taille="22" /></span>
        <span>
          <span class="brand-name">GestQuinca</span>
          <small class="brand-sub">Quincaillerie</small>
        </span>
      </div>

      <nav class="side-nav" aria-label="Navigation principale">
        <div v-if="estAdmin" class="nav-section">
          <router-link class="side-link" to="/tableau-de-bord"><Icone nom="tableau" />Tableau de bord</router-link>
        </div>

        <div class="nav-section">
          <div class="nav-section-title">Vendre</div>
          <router-link class="side-link" to="/ventes"><Icone nom="ventes" />Ventes</router-link>
          <router-link class="side-link" to="/clients"><Icone nom="clients" />Clients</router-link>
        </div>

        <div class="nav-section">
          <div class="nav-section-title">Mon stock</div>
          <router-link class="side-link" to="/produits"><Icone nom="produits" />Produits</router-link>
          <router-link class="side-link" to="/stock"><Icone nom="stock" />Stock</router-link>
          <router-link v-if="estAdmin" class="side-link" to="/categories"><Icone nom="categories" />Catégories</router-link>
        </div>

        <div v-if="estAdmin" class="nav-section">
          <div class="nav-section-title">Achats</div>
          <router-link class="side-link" to="/fournisseurs"><Icone nom="fournisseurs" />Fournisseurs</router-link>
          <router-link class="side-link" to="/commandes"><Icone nom="commandes" />Commandes</router-link>
        </div>

        <div v-if="estAdmin" class="nav-section">
          <div class="nav-section-title">Équipe</div>
          <router-link class="side-link" to="/utilisateurs"><Icone nom="utilisateurs" />Utilisateurs</router-link>
        </div>
      </nav>

      <div class="side-footer">
        <div class="d-flex align-items-center gap-2">
          <span class="avatar" aria-hidden="true">{{ initiales }}</span>
          <span class="lh-sm">
            <span class="d-block fw-bold small">{{ session.nom }}</span>
            <span class="role-pill" :class="estAdmin ? 'role-admin' : 'role-vendeur'">{{ estAdmin ? 'Administrateur' : 'Vendeur' }}</span>
          </span>
        </div>
        <button class="btn btn-outline-secondary btn-sm btn-deconnexion" @click="changerTheme">
          <Icone nom="palette" :taille="16" /> Thème {{ theme === 'pro' ? 'doux' : 'sobre' }}
        </button>
        <button class="btn btn-outline-secondary btn-sm btn-deconnexion" @click="seDeconnecter">
          <Icone nom="sortie" :taille="16" /> Déconnexion
        </button>
      </div>
    </aside>

    <div class="app-main">
      <header class="topbar">
        <div>
          <div class="greeting">Bonjour, {{ prenom }}</div>
          <div class="date-du-jour">{{ dateDuJour }}</div>
        </div>
      </header>
      <main class="content">
        <router-view />
      </main>
    </div>
  </div>

  <router-view v-else />
</template>

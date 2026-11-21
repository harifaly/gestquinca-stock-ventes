<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { api } from '../api'
import FournisseurForm from '../components/FournisseurForm.vue'

const TAILLE = 10
const q = ref('')
const page = ref(1)
const resultat = ref({ total: 0, items: [] })
const erreur = ref('')
const formulaire = reactive({ ouvert: false, fournisseur: null })
const nbPages = computed(() => Math.max(1, Math.ceil(resultat.value.total / TAILLE)))

async function supprimer(f) {
  if (!confirm(`Supprimer le fournisseur « ${f.nom} » ?`)) return
  erreur.value = ''
  try {
    await api.delete(`/fournisseurs/${f.id_fournisseur}`)
    charger()
  } catch (e) {
    erreur.value = e.message
  }
}

async function charger() {
  erreur.value = ''
  try {
    resultat.value = await api.get('/fournisseurs', { params: { q: q.value, page: page.value, taille: TAILLE } })
  } catch (e) {
    erreur.value = e.message
  }
}
onMounted(charger)
let minuteur = null
watch(q, () => { clearTimeout(minuteur); minuteur = setTimeout(() => { page.value = 1; charger() }, 300) })
function allerA(n) { page.value = n; charger() }
function ouvrir(f = null) { formulaire.fournisseur = f; formulaire.ouvert = true }
function apres() { formulaire.ouvert = false; charger() }
</script>

<template>
  <div class="d-flex justify-content-between align-items-center mb-3">
    <h1 class="h3 mb-0">Fournisseurs</h1>
    <button class="btn btn-primary" @click="ouvrir()">+ Nouveau fournisseur</button>
  </div>
  <div class="card shadow-sm mb-3">
    <div class="card-body">
      <label for="recherche" class="form-label mb-1">Recherche</label>
      <input id="recherche" v-model="q" class="form-control" placeholder="Nom, contact ou téléphone" />
    </div>
  </div>
  <div v-if="erreur" class="alert alert-danger" role="alert">{{ erreur }}</div>
  <div class="card shadow-sm">
    <div class="table-responsive">
      <table class="table table-hover mb-0">
        <thead><tr><th>Nom</th><th>Contact</th><th>Téléphone</th><th>Email</th><th class="text-end">Actions</th></tr></thead>
        <tbody>
          <tr v-if="resultat.items.length === 0"><td colspan="5" class="text-center text-muted py-4">Aucun fournisseur.</td></tr>
          <tr v-for="f in resultat.items" :key="f.id_fournisseur">
            <td>{{ f.nom }}</td><td>{{ f.contact }}</td><td>{{ f.telephone }}</td><td>{{ f.email }}</td>
            <td class="text-end text-nowrap">
              <router-link class="btn btn-sm btn-outline-secondary me-1" :to="{ name: 'commandes', query: { fournisseur: f.id_fournisseur } }">Commandes</router-link>
              <button class="btn btn-sm btn-outline-primary me-1" @click="ouvrir(f)">Modifier</button>
              <button class="btn btn-sm btn-outline-danger" @click="supprimer(f)">Supprimer</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="card-footer d-flex justify-content-between align-items-center">
      <span class="text-muted small">{{ resultat.total }} fournisseur(s)</span>
      <div class="btn-group btn-group-sm">
        <button class="btn btn-outline-secondary" :disabled="page <= 1" @click="allerA(page - 1)">Précédent</button>
        <span class="btn btn-outline-secondary disabled">Page {{ page }} sur {{ nbPages }}</span>
        <button class="btn btn-outline-secondary" :disabled="page >= nbPages" @click="allerA(page + 1)">Suivant</button>
      </div>
    </div>
  </div>
  <FournisseurForm v-if="formulaire.ouvert" :fournisseur="formulaire.fournisseur" @enregistre="apres" @ferme="formulaire.ouvert = false" />
</template>

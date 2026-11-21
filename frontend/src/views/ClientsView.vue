<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { api } from '../api'
import { estAdmin } from '../auth'
import { ariary } from '../utils/format'
import ClientForm from '../components/ClientForm.vue'

const TAILLE = 10
const filtres = reactive({ q: '', avec_creance: false })
const page = ref(1)
const resultat = ref({ total: 0, items: [] })
const erreur = ref('')
const formulaire = reactive({ ouvert: false, client: null })
const nbPages = computed(() => Math.max(1, Math.ceil(resultat.value.total / TAILLE)))

async function supprimer(c) {
  if (!confirm(`Supprimer le client « ${c.nom} » ?`)) return
  erreur.value = ''
  try {
    await api.delete(`/clients/${c.id_client}`)
    charger()
  } catch (e) {
    erreur.value = e.message
  }
}

async function charger() {
  erreur.value = ''
  try {
    resultat.value = await api.get('/clients', { params: { ...filtres, page: page.value, taille: TAILLE } })
  } catch (e) {
    erreur.value = e.message
  }
}
onMounted(charger)

let minuteur = null
watch(() => filtres.q, () => {
  clearTimeout(minuteur)
  minuteur = setTimeout(() => { page.value = 1; charger() }, 300)
})
watch(() => filtres.avec_creance, () => { page.value = 1; charger() })

function allerA(n) { page.value = n; charger() }
function ouvrir(client = null) { formulaire.client = client; formulaire.ouvert = true }
function apres() { formulaire.ouvert = false; charger() }
</script>

<template>
  <div class="d-flex justify-content-between align-items-center mb-3">
    <h1 class="h3 mb-0">Clients</h1>
    <button class="btn btn-primary" @click="ouvrir()">+ Nouveau client</button>
  </div>

  <div class="card shadow-sm mb-3">
    <div class="card-body row g-3 align-items-end">
      <div class="col-md-6">
        <label for="recherche" class="form-label mb-1">Recherche</label>
        <input id="recherche" v-model="filtres.q" class="form-control" placeholder="Nom ou téléphone" />
      </div>
      <div class="col-md-6">
        <div class="form-check">
          <input id="creance" v-model="filtres.avec_creance" type="checkbox" class="form-check-input" />
          <label for="creance" class="form-check-label">Clients qui doivent de l'argent</label>
        </div>
      </div>
    </div>
  </div>

  <div v-if="erreur" class="alert alert-danger" role="alert">{{ erreur }}</div>

  <div class="card shadow-sm">
    <div class="table-responsive">
      <table class="table table-hover mb-0">
        <thead>
          <tr>
            <th>Nom</th><th>Téléphone</th><th>Adresse</th><th class="text-end">Créance</th>
            <th class="text-end">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="resultat.items.length === 0">
            <td colspan="5" class="text-center text-muted py-4">Aucun client.</td>
          </tr>
          <tr v-for="c in resultat.items" :key="c.id_client">
            <td>{{ c.nom }}</td>
            <td>{{ c.telephone }}</td>
            <td>{{ c.adresse }}</td>
            <td class="text-end">
              <span v-if="c.creance > 0" class="text-danger fw-semibold">{{ ariary(c.creance) }}</span>
              <span v-else class="text-muted">—</span>
            </td>
            <td class="text-end text-nowrap">
              <router-link class="btn btn-sm btn-outline-secondary me-1" :to="{ name: 'ventes', query: { client: c.id_client } }">Ventes</router-link>
              <button v-if="estAdmin()" class="btn btn-sm btn-outline-primary me-1" @click="ouvrir(c)">Modifier</button>
              <button v-if="estAdmin()" class="btn btn-sm btn-outline-danger" @click="supprimer(c)">Supprimer</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="card-footer d-flex justify-content-between align-items-center">
      <span class="text-muted small">{{ resultat.total }} client(s)</span>
      <div class="btn-group btn-group-sm">
        <button class="btn btn-outline-secondary" :disabled="page <= 1" @click="allerA(page - 1)">Précédent</button>
        <span class="btn btn-outline-secondary disabled">Page {{ page }} sur {{ nbPages }}</span>
        <button class="btn btn-outline-secondary" :disabled="page >= nbPages" @click="allerA(page + 1)">Suivant</button>
      </div>
    </div>
  </div>

  <ClientForm v-if="formulaire.ouvert" :client="formulaire.client" @enregistre="apres" @ferme="formulaire.ouvert = false" />
</template>

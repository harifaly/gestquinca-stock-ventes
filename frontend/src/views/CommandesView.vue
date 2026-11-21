<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'
import { ariary, STATUTS_COMMANDE } from '../utils/format'

const TAILLE = 10
const route = useRoute()
const filtres = reactive({ statut: '', id_fournisseur: route.query.fournisseur ? Number(route.query.fournisseur) : '' })
const page = ref(1)
const resultat = ref({ total: 0, items: [] })
const erreur = ref('')
const nbPages = computed(() => Math.max(1, Math.ceil(resultat.value.total / TAILLE)))

async function charger() {
  erreur.value = ''
  try {
    resultat.value = await api.get('/commandes', { params: { ...filtres, page: page.value, taille: TAILLE } })
  } catch (e) {
    erreur.value = e.message
  }
}
onMounted(charger)
watch(filtres, () => { page.value = 1; charger() })
function allerA(n) { page.value = n; charger() }
</script>

<template>
  <div class="d-flex justify-content-between align-items-center mb-3">
    <h1 class="h3 mb-0">Commandes fournisseurs</h1>
    <router-link class="btn btn-primary" :to="{ name: 'nouvelle-commande' }">+ Nouvelle commande</router-link>
  </div>
  <div class="card shadow-sm mb-3">
    <div class="card-body row g-3 align-items-end">
      <div class="col-md-4">
        <label for="statut" class="form-label mb-1">Statut</label>
        <select id="statut" v-model="filtres.statut" class="form-select">
          <option value="">Tous</option>
          <option v-for="(s, cle) in STATUTS_COMMANDE" :key="cle" :value="cle">{{ s.libelle }}</option>
        </select>
      </div>
      <div v-if="filtres.id_fournisseur" class="col-md-8">
        <span class="badge bg-secondary me-2">Filtré sur un fournisseur</span>
        <button class="btn btn-sm btn-outline-secondary" @click="filtres.id_fournisseur = ''">Retirer le filtre</button>
      </div>
    </div>
  </div>
  <div v-if="erreur" class="alert alert-danger" role="alert">{{ erreur }}</div>
  <div class="card shadow-sm">
    <div class="table-responsive">
      <table class="table table-hover mb-0">
        <thead><tr><th>N°</th><th>Date</th><th>Fournisseur</th><th class="text-end">Total prévu</th><th>Statut</th><th></th></tr></thead>
        <tbody>
          <tr v-if="resultat.items.length === 0"><td colspan="6" class="text-center text-muted py-4">Aucune commande.</td></tr>
          <tr v-for="c in resultat.items" :key="c.id_commande">
            <td>#{{ c.id_commande }}</td><td>{{ c.date_commande }}</td><td>{{ c.fournisseur }}</td>
            <td class="text-end">{{ ariary(c.total_prevu) }}</td>
            <td><span class="badge" :class="STATUTS_COMMANDE[c.statut].classe">{{ STATUTS_COMMANDE[c.statut].libelle }}</span></td>
            <td class="text-end"><router-link class="btn btn-sm btn-outline-primary" :to="{ name: 'commande', params: { id: c.id_commande } }">Détail</router-link></td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="card-footer d-flex justify-content-between align-items-center">
      <span class="text-muted small">{{ resultat.total }} commande(s)</span>
      <div class="btn-group btn-group-sm">
        <button class="btn btn-outline-secondary" :disabled="page <= 1" @click="allerA(page - 1)">Précédent</button>
        <span class="btn btn-outline-secondary disabled">Page {{ page }} sur {{ nbPages }}</span>
        <button class="btn btn-outline-secondary" :disabled="page >= nbPages" @click="allerA(page + 1)">Suivant</button>
      </div>
    </div>
  </div>
</template>

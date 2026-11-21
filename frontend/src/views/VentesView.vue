<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'
import { ariary, dateFr, STATUTS } from '../utils/format'

const TAILLE = 10
const route = useRoute()
const filtres = reactive({ statut: '', id_client: route.query.client ? Number(route.query.client) : '' })
const page = ref(1)
const resultat = ref({ total: 0, items: [] })
const erreur = ref('')
const nbPages = computed(() => Math.max(1, Math.ceil(resultat.value.total / TAILLE)))

async function charger() {
  erreur.value = ''
  try {
    resultat.value = await api.get('/ventes', { params: { ...filtres, page: page.value, taille: TAILLE } })
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
    <h1 class="h3 mb-0">Ventes</h1>
    <router-link class="btn btn-primary" :to="{ name: 'nouvelle-vente' }">+ Nouvelle vente</router-link>
  </div>

  <div class="card shadow-sm mb-3">
    <div class="card-body row g-3 align-items-end">
      <div class="col-md-4">
        <label for="statut" class="form-label mb-1">Paiement</label>
        <select id="statut" v-model="filtres.statut" class="form-select">
          <option value="">Toutes</option>
          <option v-for="(s, cle) in STATUTS" :key="cle" :value="cle">{{ s.libelle }}</option>
        </select>
      </div>
      <div v-if="filtres.id_client" class="col-md-8">
        <span class="badge bg-secondary me-2">Filtré sur un client</span>
        <button class="btn btn-sm btn-outline-secondary" @click="filtres.id_client = ''">Retirer le filtre</button>
      </div>
    </div>
  </div>

  <div v-if="erreur" class="alert alert-danger" role="alert">{{ erreur }}</div>

  <div class="card shadow-sm">
    <div class="table-responsive">
      <table class="table table-hover mb-0">
        <thead>
          <tr>
            <th>N°</th><th>Date</th><th>Client</th><th>Vendeur</th>
            <th class="text-end">Total</th><th class="text-end">Reste à payer</th><th>Paiement</th><th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="resultat.items.length === 0">
            <td colspan="8" class="text-center text-muted py-4">Aucune vente.</td>
          </tr>
          <tr v-for="v in resultat.items" :key="v.id_vente">
            <td>#{{ v.id_vente }}</td>
            <td>{{ dateFr(v.date_vente) }}</td>
            <td>{{ v.client || 'Comptant' }}</td>
            <td>{{ v.vendeur }}</td>
            <td class="text-end">{{ ariary(v.total) }}</td>
            <td class="text-end">{{ v.solde > 0 ? ariary(v.solde) : '—' }}</td>
            <td><span class="badge" :class="STATUTS[v.statut_paiement].classe">{{ STATUTS[v.statut_paiement].libelle }}</span></td>
            <td class="text-end">
              <router-link class="btn btn-sm btn-outline-primary" :to="{ name: 'vente', params: { id: v.id_vente } }">Détail</router-link>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="card-footer d-flex justify-content-between align-items-center">
      <span class="text-muted small">{{ resultat.total }} vente(s)</span>
      <div class="btn-group btn-group-sm">
        <button class="btn btn-outline-secondary" :disabled="page <= 1" @click="allerA(page - 1)">Précédent</button>
        <span class="btn btn-outline-secondary disabled">Page {{ page }} sur {{ nbPages }}</span>
        <button class="btn btn-outline-secondary" :disabled="page >= nbPages" @click="allerA(page + 1)">Suivant</button>
      </div>
    </div>
  </div>
</template>

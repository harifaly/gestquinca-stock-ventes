<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { api } from '../api'
import { estAdmin } from '../auth'
import { dateFr, MOTIFS, nombre, TYPES_MOUVEMENT } from '../utils/format'
import AjustementForm from '../components/AjustementForm.vue'

const TAILLE = 15
const filtres = reactive({ id_produit: '', type_mouvement: '' })
const page = ref(1)
const resultat = ref({ total: 0, items: [] })
const produits = ref([])
const erreur = ref('')
const ouvert = ref(false)
const nbPages = computed(() => Math.max(1, Math.ceil(resultat.value.total / TAILLE)))

async function charger() {
  erreur.value = ''
  try {
    resultat.value = await api.get('/stock/mouvements', { params: { ...filtres, page: page.value, taille: TAILLE } })
  } catch (e) {
    erreur.value = e.message
  }
}
async function chargerProduits() {
  produits.value = (await api.get('/produits', { params: { taille: 100 } })).items
}
onMounted(async () => {
  try { await chargerProduits() } catch (e) { erreur.value = e.message }
  charger()
})
watch(filtres, () => { page.value = 1; charger() })
function allerA(n) { page.value = n; charger() }
async function apres() { ouvert.value = false; await chargerProduits(); charger() }
const origine = (m) => m.id_vente ? `Vente #${m.id_vente}` : m.id_reception ? `Réception #${m.id_reception}` : MOTIFS[m.motif]
</script>

<template>
  <div class="d-flex justify-content-between align-items-center mb-3">
    <h1 class="h3 mb-0">Stock</h1>
    <button v-if="estAdmin()" class="btn btn-primary" @click="ouvert = true">+ Ajustement</button>
  </div>
  <p class="text-muted">Historique de tous les mouvements. Le stock d'un produit est la somme de ses mouvements.</p>

  <div class="card shadow-sm mb-3">
    <div class="card-body row g-3">
      <div class="col-md-6">
        <label for="f-produit" class="form-label mb-1">Produit</label>
        <select id="f-produit" v-model="filtres.id_produit" class="form-select">
          <option value="">Tous</option>
          <option v-for="p in produits" :key="p.id_produit" :value="p.id_produit">{{ p.nom }} ({{ p.sku }})</option>
        </select>
      </div>
      <div class="col-md-6">
        <label for="f-type" class="form-label mb-1">Type</label>
        <select id="f-type" v-model="filtres.type_mouvement" class="form-select">
          <option value="">Tous</option>
          <option v-for="(t, cle) in TYPES_MOUVEMENT" :key="cle" :value="cle">{{ t.libelle }}</option>
        </select>
      </div>
    </div>
  </div>
  <div v-if="erreur" class="alert alert-danger" role="alert">{{ erreur }}</div>

  <div class="card shadow-sm">
    <div class="table-responsive">
      <table class="table table-hover mb-0">
        <thead><tr><th>Date</th><th>Produit</th><th>Type</th><th>Origine</th><th class="text-end">Quantité</th><th>Auteur</th></tr></thead>
        <tbody>
          <tr v-if="resultat.items.length === 0"><td colspan="6" class="text-center text-muted py-4">Aucun mouvement.</td></tr>
          <tr v-for="m in resultat.items" :key="m.id_mouvement">
            <td>{{ dateFr(m.date_mouvement) }}</td>
            <td>{{ m.produit }} <code class="ms-1">{{ m.sku }}</code></td>
            <td><span class="badge" :class="TYPES_MOUVEMENT[m.type_mouvement].classe">{{ TYPES_MOUVEMENT[m.type_mouvement].libelle }}</span></td>
            <td>{{ origine(m) }}</td>
            <td class="text-end fw-semibold" :class="m.quantite < 0 ? 'text-danger' : 'text-success'">{{ m.quantite > 0 ? '+' : '' }}{{ nombre(m.quantite) }} {{ m.unite }}</td>
            <td>{{ m.utilisateur }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="card-footer d-flex justify-content-between align-items-center">
      <span class="text-muted small">{{ resultat.total }} mouvement(s)</span>
      <div class="btn-group btn-group-sm">
        <button class="btn btn-outline-secondary" :disabled="page <= 1" @click="allerA(page - 1)">Précédent</button>
        <span class="btn btn-outline-secondary disabled">Page {{ page }} sur {{ nbPages }}</span>
        <button class="btn btn-outline-secondary" :disabled="page >= nbPages" @click="allerA(page + 1)">Suivant</button>
      </div>
    </div>
  </div>
  <AjustementForm v-if="ouvert" :produits="produits" @enregistre="apres" @ferme="ouvert = false" />
</template>

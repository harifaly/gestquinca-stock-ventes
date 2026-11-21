<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'
import { ariary, dateFr, MODES, nombre, STATUTS } from '../utils/format'

const route = useRoute()
const vente = ref(null)
const erreur = ref('')
const paiement = reactive({ montant: '', mode_paiement: 'especes' })
const envoiEnCours = ref(false)

async function charger() {
  try {
    vente.value = await api.get(`/ventes/${route.params.id}`)
    paiement.montant = vente.value.solde > 0 ? vente.value.solde : ''
  } catch (e) {
    erreur.value = e.message
  }
}
onMounted(charger)

async function payer() {
  erreur.value = ''
  envoiEnCours.value = true
  try {
    vente.value = await api.post(`/ventes/${vente.value.id_vente}/paiements`, { corps: { ...paiement } })
    paiement.montant = vente.value.solde > 0 ? vente.value.solde : ''
  } catch (e) {
    erreur.value = e.message
  } finally {
    envoiEnCours.value = false
  }
}
</script>

<template>
  <router-link :to="{ name: 'ventes' }" class="small">&larr; Retour aux ventes</router-link>
  <div v-if="erreur" class="alert alert-danger mt-3" role="alert">{{ erreur }}</div>

  <template v-if="vente">
    <div class="d-flex justify-content-between align-items-center my-3">
      <h1 class="h3 mb-0">Vente #{{ vente.id_vente }}</h1>
      <span class="badge fs-6" :class="STATUTS[vente.statut_paiement].classe">{{ STATUTS[vente.statut_paiement].libelle }}</span>
    </div>
    <p class="text-muted">
      {{ dateFr(vente.date_vente) }} · Client : <strong>{{ vente.client || 'Comptant (anonyme)' }}</strong> · Vendeur : {{ vente.vendeur }}
    </p>

    <div class="card shadow-sm mb-3">
      <table class="table mb-0">
        <thead><tr><th>Produit</th><th class="text-end">Quantité</th><th class="text-end">Prix unitaire</th><th class="text-end">Total</th></tr></thead>
        <tbody>
          <tr v-for="l in vente.lignes" :key="l.id_produit">
            <td>{{ l.nom }} <code class="ms-1">{{ l.sku }}</code></td>
            <td class="text-end">{{ nombre(l.quantite) }} {{ l.unite }}</td>
            <td class="text-end">{{ ariary(l.prix_unitaire) }}</td>
            <td class="text-end">{{ ariary(l.total_ligne) }}</td>
          </tr>
        </tbody>
        <tfoot>
          <tr><th colspan="3" class="text-end">Total</th><th class="text-end">{{ ariary(vente.total) }}</th></tr>
          <tr><td colspan="3" class="text-end">Déjà payé</td><td class="text-end">{{ ariary(vente.total_paye) }}</td></tr>
          <tr><th colspan="3" class="text-end">Reste à payer</th><th class="text-end" :class="vente.solde > 0 ? 'text-danger' : ''">{{ ariary(vente.solde) }}</th></tr>
        </tfoot>
      </table>
    </div>

    <div class="row g-3">
      <div class="col-md-6">
        <div class="card shadow-sm h-100">
          <div class="card-header">Paiements</div>
          <ul class="list-group list-group-flush">
            <li v-if="vente.paiements.length === 0" class="list-group-item text-muted">Aucun paiement.</li>
            <li v-for="p in vente.paiements" :key="p.id_paiement" class="list-group-item d-flex justify-content-between">
              <span>{{ dateFr(p.date_paiement) }} · {{ MODES[p.mode_paiement] }}</span>
              <strong>{{ ariary(p.montant) }}</strong>
            </li>
          </ul>
        </div>
      </div>
      <div v-if="vente.solde > 0" class="col-md-6">
        <form class="card shadow-sm h-100" @submit.prevent="payer">
          <div class="card-header">Enregistrer un paiement</div>
          <div class="card-body">
            <div class="mb-3">
              <label for="montant" class="form-label">Montant (Ar)</label>
              <input id="montant" v-model.number="paiement.montant" type="number" min="0.01" step="0.01" class="form-control" required />
            </div>
            <div class="mb-3">
              <label for="mode" class="form-label">Mode de paiement</label>
              <select id="mode" v-model="paiement.mode_paiement" class="form-select">
                <option v-for="(libelle, cle) in MODES" :key="cle" :value="cle">{{ libelle }}</option>
              </select>
            </div>
            <button class="btn btn-success" :disabled="envoiEnCours">Encaisser</button>
          </div>
        </form>
      </div>
    </div>
  </template>
</template>

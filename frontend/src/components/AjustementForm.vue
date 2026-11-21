<script setup>
import { ref } from 'vue'
import { api } from '../api'
import { MOTIFS } from '../utils/format'

const props = defineProps({ produits: { type: Array, required: true } })
const emit = defineEmits(['enregistre', 'ferme'])

const form = ref({ id_produit: '', sens: 'retrait', quantite: 1, motif: 'casse' })
const erreur = ref('')
const envoiEnCours = ref(false)

async function enregistrer() {
  erreur.value = ''
  envoiEnCours.value = true
  const signe = form.value.sens === 'retrait' ? -1 : 1
  try {
    await api.post('/stock/ajustements', {
      corps: { id_produit: form.value.id_produit, quantite: signe * form.value.quantite, motif: form.value.motif },
    })
    emit('enregistre')
  } catch (e) {
    erreur.value = e.message
  } finally {
    envoiEnCours.value = false
  }
}
</script>

<template>
  <div class="modal fade show d-block" tabindex="-1" role="dialog" aria-modal="true">
    <div class="modal-dialog">
      <form class="modal-content" @submit.prevent="enregistrer">
        <div class="modal-header">
          <h2 class="modal-title h5">Ajustement de stock</h2>
          <button type="button" class="btn-close" aria-label="Fermer" @click="emit('ferme')"></button>
        </div>
        <div class="modal-body">
          <div class="mb-3">
            <label for="aj-produit" class="form-label">Produit</label>
            <select id="aj-produit" v-model="form.id_produit" class="form-select" required>
              <option value="" disabled>Choisir…</option>
              <option v-for="p in produits" :key="p.id_produit" :value="p.id_produit">{{ p.nom }} ({{ p.sku }}) — stock {{ p.stock }} {{ p.unite }}</option>
            </select>
          </div>
          <div class="row">
            <div class="col-6 mb-3">
              <label for="aj-sens" class="form-label">Sens</label>
              <select id="aj-sens" v-model="form.sens" class="form-select">
                <option value="retrait">Retrait (perte, casse…)</option>
                <option value="ajout">Ajout (stock retrouvé)</option>
              </select>
            </div>
            <div class="col-6 mb-3">
              <label for="aj-qte" class="form-label">Quantité</label>
              <input id="aj-qte" v-model.number="form.quantite" type="number" min="0.001" step="any" class="form-control" required />
            </div>
          </div>
          <div class="mb-3">
            <label for="aj-motif" class="form-label">Motif (obligatoire)</label>
            <select id="aj-motif" v-model="form.motif" class="form-select" required>
              <option v-for="(libelle, cle) in MOTIFS" :key="cle" :value="cle">{{ libelle }}</option>
            </select>
          </div>
          <div class="form-text mb-2">L'ajustement crée un nouveau mouvement : l'historique n'est jamais modifié.</div>
          <div v-if="erreur" class="alert alert-danger py-2 mb-0" role="alert">{{ erreur }}</div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-outline-secondary" @click="emit('ferme')">Annuler</button>
          <button class="btn btn-primary" :disabled="envoiEnCours">Enregistrer</button>
        </div>
      </form>
    </div>
  </div>
  <div class="modal-backdrop fade show"></div>
</template>

<script setup>
import { ref } from 'vue'
import { api } from '../api'

// produit = null pour un ajout, sinon le produit à modifier
const props = defineProps({
  produit: { type: Object, default: null },
  categories: { type: Array, required: true },
})
const emit = defineEmits(['enregistre', 'ferme'])

const UNITES = [
  { valeur: 'sac', libelle: 'Sac' },
  { valeur: 'barre', libelle: 'Barre' },
  { valeur: 'metre', libelle: 'Mètre' },
  { valeur: 'kg', libelle: 'Kilogramme' },
  { valeur: 'litre', libelle: 'Litre' },
  { valeur: 'piece', libelle: 'Pièce' },
]

const p = props.produit
const form = ref({
  sku: p?.sku ?? '',
  nom: p?.nom ?? '',
  marque: p?.marque ?? '',
  description: p?.description ?? '',
  unite: p?.unite ?? 'piece',
  prix_achat: p?.prix_achat ?? 0,
  prix_vente: p?.prix_vente ?? 0,
  stock_minimum: p?.stock_minimum ?? 0,
  id_categorie: p?.id_categorie ?? props.categories[0]?.id_categorie ?? null,
})
const erreur = ref('')
const envoiEnCours = ref(false)

async function enregistrer() {
  erreur.value = ''
  envoiEnCours.value = true
  const corps = {
    ...form.value,
    marque: form.value.marque || null,
    description: form.value.description || null,
  }
  try {
    if (props.produit) {
      await api.put(`/produits/${props.produit.id_produit}`, { corps })
    } else {
      await api.post('/produits', { corps })
    }
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
    <div class="modal-dialog modal-lg modal-dialog-scrollable">
      <form class="modal-content" @submit.prevent="enregistrer">
        <div class="modal-header">
          <h2 class="modal-title h5">{{ produit ? 'Modifier le produit' : 'Nouveau produit' }}</h2>
          <button type="button" class="btn-close" aria-label="Fermer" @click="emit('ferme')"></button>
        </div>

        <div class="modal-body">
          <div class="row g-3">
            <div class="col-md-4">
              <label for="f-sku" class="form-label">Référence (SKU)</label>
              <input id="f-sku" v-model.trim="form.sku" class="form-control" maxlength="50" required />
            </div>
            <div class="col-md-8">
              <label for="f-nom" class="form-label">Nom du produit</label>
              <input id="f-nom" v-model.trim="form.nom" class="form-control" maxlength="200" required />
            </div>
            <div class="col-md-6">
              <label for="f-categorie" class="form-label">Catégorie</label>
              <select id="f-categorie" v-model="form.id_categorie" class="form-select" required>
                <option v-for="c in categories" :key="c.id_categorie" :value="c.id_categorie">{{ c.nom }}</option>
              </select>
            </div>
            <div class="col-md-3">
              <label for="f-unite" class="form-label">Unité</label>
              <select id="f-unite" v-model="form.unite" class="form-select" required>
                <option v-for="u in UNITES" :key="u.valeur" :value="u.valeur">{{ u.libelle }}</option>
              </select>
            </div>
            <div class="col-md-3">
              <label for="f-marque" class="form-label">Marque</label>
              <input id="f-marque" v-model.trim="form.marque" class="form-control" />
            </div>
            <div class="col-md-4">
              <label for="f-prix-achat" class="form-label">Prix d'achat (Ar)</label>
              <input id="f-prix-achat" v-model.number="form.prix_achat" type="number" min="0" step="0.01" class="form-control" required />
            </div>
            <div class="col-md-4">
              <label for="f-prix-vente" class="form-label">Prix de vente (Ar)</label>
              <input id="f-prix-vente" v-model.number="form.prix_vente" type="number" min="0" step="0.01" class="form-control" required />
            </div>
            <div class="col-md-4">
              <label for="f-stock-min" class="form-label">Stock minimum</label>
              <input id="f-stock-min" v-model.number="form.stock_minimum" type="number" min="0" step="0.001" class="form-control" required />
            </div>
            <div class="col-12">
              <label for="f-description" class="form-label">Description</label>
              <textarea id="f-description" v-model.trim="form.description" class="form-control" rows="2"></textarea>
            </div>
          </div>
          <div v-if="erreur" class="alert alert-danger mt-3 mb-0 py-2" role="alert">{{ erreur }}</div>
        </div>

        <div class="modal-footer">
          <button type="button" class="btn btn-outline-secondary" @click="emit('ferme')">Annuler</button>
          <button class="btn btn-primary" :disabled="envoiEnCours">
            {{ envoiEnCours ? 'Enregistrement…' : 'Enregistrer' }}
          </button>
        </div>
      </form>
    </div>
  </div>
  <div class="modal-backdrop fade show"></div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { ariary } from '../utils/format'

const router = useRouter()
const fournisseurs = ref([])
const produits = ref([])
const idFournisseur = ref('')
const produitChoisi = ref('')
const lignes = ref([])      // [{ produit, quantite, prix }]
const erreur = ref('')
const envoiEnCours = ref(false)

const total = computed(() => lignes.value.reduce((s, l) => s + l.quantite * l.prix, 0))
const disponibles = computed(() => produits.value.filter((p) => !lignes.value.some((l) => l.produit.id_produit === p.id_produit)))

onMounted(async () => {
  try {
    fournisseurs.value = (await api.get('/fournisseurs', { params: { taille: 100 } })).items
    produits.value = (await api.get('/produits', { params: { taille: 100 } })).items
  } catch (e) {
    erreur.value = e.message
  }
})

function ajouter() {
  const produit = produits.value.find((p) => p.id_produit === produitChoisi.value)
  if (!produit) return
  lignes.value.push({ produit, quantite: 1, prix: produit.prix_achat })
  produitChoisi.value = ''
}

async function valider() {
  erreur.value = ''
  envoiEnCours.value = true
  try {
    const commande = await api.post('/commandes', {
      corps: {
        id_fournisseur: idFournisseur.value,
        lignes: lignes.value.map((l) => ({ id_produit: l.produit.id_produit, quantite_commandee: l.quantite, prix_achat_prevu: l.prix })),
      },
    })
    router.push({ name: 'commande', params: { id: commande.id_commande } })
  } catch (e) {
    erreur.value = e.message
  } finally {
    envoiEnCours.value = false
  }
}
</script>

<template>
  <router-link :to="{ name: 'commandes' }" class="small">&larr; Retour aux commandes</router-link>
  <h1 class="h3 my-3">Nouvelle commande fournisseur</h1>
  <p class="text-muted">Une commande n'augmente pas le stock : seule la réception le fait.</p>
  <div v-if="erreur" class="alert alert-danger" role="alert">{{ erreur }}</div>

  <form class="card shadow-sm" @submit.prevent="valider">
    <div class="card-body">
      <div class="mb-3">
        <label for="fournisseur" class="form-label">Fournisseur</label>
        <select id="fournisseur" v-model="idFournisseur" class="form-select" required>
          <option value="" disabled>Choisir…</option>
          <option v-for="f in fournisseurs" :key="f.id_fournisseur" :value="f.id_fournisseur">{{ f.nom }}</option>
        </select>
      </div>
      <div class="input-group mb-3">
        <select id="ajout-produit" v-model="produitChoisi" class="form-select" aria-label="Produit à ajouter">
          <option value="">Choisir un produit…</option>
          <option v-for="p in disponibles" :key="p.id_produit" :value="p.id_produit">{{ p.nom }} ({{ p.sku }})</option>
        </select>
        <button type="button" class="btn btn-outline-primary" :disabled="!produitChoisi" @click="ajouter">Ajouter</button>
      </div>
      <table class="table align-middle">
        <thead><tr><th>Produit</th><th style="width:150px">Quantité</th><th style="width:180px">Prix d'achat prévu (Ar)</th><th class="text-end">Total</th><th></th></tr></thead>
        <tbody>
          <tr v-if="lignes.length === 0"><td colspan="5" class="text-center text-muted py-3">Aucun produit ajouté.</td></tr>
          <tr v-for="(l, i) in lignes" :key="l.produit.id_produit">
            <td>{{ l.produit.nom }}</td>
            <td><input v-model.number="l.quantite" type="number" min="0.001" step="any" class="form-control form-control-sm" :aria-label="'Quantité ' + l.produit.nom" required /></td>
            <td><input v-model.number="l.prix" type="number" min="0" step="0.01" class="form-control form-control-sm" :aria-label="'Prix ' + l.produit.nom" required /></td>
            <td class="text-end">{{ ariary(l.quantite * l.prix) }}</td>
            <td class="text-end"><button type="button" class="btn btn-sm btn-outline-danger" @click="lignes.splice(i, 1)">Retirer</button></td>
          </tr>
        </tbody>
        <tfoot><tr><th colspan="3" class="text-end">Total prévu</th><th class="text-end">{{ ariary(total) }}</th><th></th></tr></tfoot>
      </table>
      <button class="btn btn-success" :disabled="lignes.length === 0 || envoiEnCours">Créer la commande</button>
    </div>
  </form>
</template>

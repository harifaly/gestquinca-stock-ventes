<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { api } from '../api'
import { estAdmin } from '../auth'
import ProduitForm from '../components/ProduitForm.vue'

const TAILLE = 10
const filtres = reactive({ q: '', id_categorie: '', sous_seuil: false, inclure_inactifs: false })
const page = ref(1)
const resultat = ref({ total: 0, items: [] })
const categories = ref([])
const chargement = ref(false)
const erreur = ref('')
const formulaire = reactive({ ouvert: false, produit: null })

const nombre = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 3 })
const ariary = (valeur) => `${new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 2 }).format(valeur)} Ar`
const nbPages = computed(() => Math.max(1, Math.ceil(resultat.value.total / TAILLE)))

async function charger() {
  chargement.value = true
  erreur.value = ''
  try {
    resultat.value = await api.get('/produits', {
      params: { ...filtres, page: page.value, taille: TAILLE },
    })
  } catch (e) {
    erreur.value = e.message
  } finally {
    chargement.value = false
  }
}

onMounted(async () => {
  try {
    categories.value = await api.get('/categories')
  } catch (e) {
    erreur.value = e.message
  }
  charger()
})

// Une nouvelle recherche ou un nouveau filtre revient à la page 1.
// La saisie dans la zone de recherche est retardée de 300 ms pour ne pas interroger l'API à chaque lettre.
let minuteur = null
watch(() => filtres.q, () => {
  clearTimeout(minuteur)
  minuteur = setTimeout(() => { page.value = 1; charger() }, 300)
})
watch(() => [filtres.id_categorie, filtres.sous_seuil, filtres.inclure_inactifs], () => {
  page.value = 1
  charger()
})

function allerA(numero) {
  page.value = numero
  charger()
}

async function supprimer(produit) {
  if (!confirm(`Supprimer définitivement « ${produit.nom} » ? (Possible seulement s'il n'a jamais été commandé, vendu ni ajusté.)`)) return
  erreur.value = ''
  try {
    await api.delete(`/produits/${produit.id_produit}`)
    charger()
  } catch (e) {
    erreur.value = e.message
  }
}

function ouvrirFormulaire(produit = null) {
  formulaire.produit = produit
  formulaire.ouvert = true
}

function apresEnregistrement() {
  formulaire.ouvert = false
  charger()
}

async function changerActif(produit) {
  const verbe = produit.actif ? 'désactiver' : 'réactiver'
  if (!confirm(`Voulez-vous ${verbe} « ${produit.nom} » ?`)) return
  try {
    await api.patch(`/produits/${produit.id_produit}/actif`, { corps: { actif: !produit.actif } })
    charger()
  } catch (e) {
    erreur.value = e.message
  }
}
</script>

<template>
  <div class="d-flex justify-content-between align-items-center mb-3">
    <h1 class="h3 mb-0">Produits</h1>
    <button v-if="estAdmin()" class="btn btn-primary" @click="ouvrirFormulaire()">+ Nouveau produit</button>
  </div>

  <div class="card shadow-sm mb-3">
    <div class="card-body">
      <div class="row g-3 align-items-end">
        <div class="col-md-5">
          <label for="recherche" class="form-label mb-1">Recherche</label>
          <input id="recherche" v-model="filtres.q" class="form-control" placeholder="Nom, référence ou marque" />
        </div>
        <div class="col-md-3">
          <label for="filtre-categorie" class="form-label mb-1">Catégorie</label>
          <select id="filtre-categorie" v-model="filtres.id_categorie" class="form-select">
            <option value="">Toutes</option>
            <option v-for="c in categories" :key="c.id_categorie" :value="c.id_categorie">{{ c.nom }}</option>
          </select>
        </div>
        <div class="col-md-4">
          <div class="form-check">
            <input id="sous-seuil" v-model="filtres.sous_seuil" type="checkbox" class="form-check-input" />
            <label for="sous-seuil" class="form-check-label">À réapprovisionner seulement</label>
          </div>
          <div v-if="estAdmin()" class="form-check">
            <input id="inactifs" v-model="filtres.inclure_inactifs" type="checkbox" class="form-check-input" />
            <label for="inactifs" class="form-check-label">Afficher les produits désactivés</label>
          </div>
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
            <th>Référence</th>
            <th>Produit</th>
            <th>Catégorie</th>
            <th class="text-end">Prix de vente</th>
            <th class="text-end">Stock</th>
            <th v-if="estAdmin()" class="text-end">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!chargement && resultat.items.length === 0">
            <td :colspan="estAdmin() ? 6 : 5" class="text-center text-muted py-4">Aucun produit ne correspond.</td>
          </tr>
          <tr v-for="p in resultat.items" :key="p.id_produit" :class="{ 'ligne-inactive': !p.actif }">
            <td><code>{{ p.sku }}</code></td>
            <td>
              {{ p.nom }}
              <span v-if="!p.actif" class="badge bg-secondary ms-1">Désactivé</span>
              <div v-if="p.marque" class="small text-muted">{{ p.marque }}</div>
            </td>
            <td>{{ p.categorie }}</td>
            <td class="text-end">{{ ariary(p.prix_vente) }}</td>
            <td class="text-end">
              {{ nombre.format(p.stock) }} {{ p.unite }}
              <span v-if="p.sous_seuil" class="badge bg-danger ms-1" title="Stock inférieur ou égal au stock minimum">Faible</span>
            </td>
            <td v-if="estAdmin()" class="text-end text-nowrap">
              <button class="btn btn-sm btn-outline-primary me-1" @click="ouvrirFormulaire(p)">Modifier</button>
              <button class="btn btn-sm" :class="p.actif ? 'btn-outline-danger' : 'btn-outline-success'" @click="changerActif(p)">
                {{ p.actif ? 'Désactiver' : 'Réactiver' }}
              </button>
              <button class="btn btn-sm btn-outline-danger ms-1" @click="supprimer(p)">Supprimer</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="card-footer d-flex justify-content-between align-items-center">
      <span class="text-muted small">{{ resultat.total }} produit(s)</span>
      <div class="btn-group btn-group-sm">
        <button class="btn btn-outline-secondary" :disabled="page <= 1" @click="allerA(page - 1)">Précédent</button>
        <span class="btn btn-outline-secondary disabled">Page {{ page }} sur {{ nbPages }}</span>
        <button class="btn btn-outline-secondary" :disabled="page >= nbPages" @click="allerA(page + 1)">Suivant</button>
      </div>
    </div>
  </div>

  <ProduitForm
    v-if="formulaire.ouvert"
    :produit="formulaire.produit"
    :categories="categories"
    @enregistre="apresEnregistrement"
    @ferme="formulaire.ouvert = false"
  />
</template>

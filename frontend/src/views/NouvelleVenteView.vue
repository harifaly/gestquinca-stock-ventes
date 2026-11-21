<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { ariary, MODES, nombre } from '../utils/format'
import ClientForm from '../components/ClientForm.vue'

const router = useRouter()
const produits = ref([])
const clients = ref([])
const panier = ref([])          // [{ produit, quantite }]
const idClient = ref('')
const produitChoisi = ref('')
const paiement = reactive({ montant: 0, mode_paiement: 'especes' })
const erreur = ref('')
const envoiEnCours = ref(false)
const nouveauClient = ref(false)

const total = computed(() => panier.value.reduce((s, l) => s + l.quantite * l.produit.prix_vente, 0))
const reste = computed(() => Math.max(0, total.value - (paiement.montant || 0)))
const disponibles = computed(() => produits.value.filter((p) => !panier.value.some((l) => l.produit.id_produit === p.id_produit)))

async function chargerClients() {
  clients.value = (await api.get('/clients', { params: { taille: 100 } })).items
}

onMounted(async () => {
  try {
    produits.value = (await api.get('/produits', { params: { taille: 100 } })).items
    await chargerClients()
  } catch (e) {
    erreur.value = e.message
  }
})

function ajouter() {
  const produit = produits.value.find((p) => p.id_produit === produitChoisi.value)
  if (!produit) return
  panier.value.push({ produit, quantite: 1 })
  produitChoisi.value = ''
  paiement.montant = total.value      // par défaut : paiement comptant complet
}
function retirer(i) {
  panier.value.splice(i, 1)
  paiement.montant = Math.min(paiement.montant, total.value)
}
function toutPayer() { paiement.montant = total.value }

async function clientCree(client) {
  nouveauClient.value = false
  await chargerClients()
  idClient.value = client.id_client
}

async function valider() {
  erreur.value = ''
  envoiEnCours.value = true
  const corps = {
    id_client: idClient.value || null,
    lignes: panier.value.map((l) => ({ id_produit: l.produit.id_produit, quantite: l.quantite })),
  }
  if (paiement.montant > 0) corps.paiement = { montant: paiement.montant, mode_paiement: paiement.mode_paiement }
  try {
    const vente = await api.post('/ventes', { corps })
    router.push({ name: 'vente', params: { id: vente.id_vente } })
  } catch (e) {
    erreur.value = e.message     // ex. « RG06 : stock insuffisant… »
  } finally {
    envoiEnCours.value = false
  }
}
</script>

<template>
  <router-link :to="{ name: 'ventes' }" class="small">&larr; Retour aux ventes</router-link>
  <h1 class="h3 my-3">Nouvelle vente</h1>

  <div v-if="erreur" class="alert alert-danger" role="alert">{{ erreur }}</div>

  <div class="row g-3">
    <div class="col-lg-8">
      <div class="card shadow-sm">
        <div class="card-header">Produits</div>
        <div class="card-body">
          <div class="input-group mb-3">
            <select id="ajout-produit" v-model="produitChoisi" class="form-select" aria-label="Produit à ajouter">
              <option value="">Choisir un produit…</option>
              <option v-for="p in disponibles" :key="p.id_produit" :value="p.id_produit">
                {{ p.nom }} ({{ p.sku }}) — {{ ariary(p.prix_vente) }} — stock {{ nombre(p.stock) }} {{ p.unite }}
              </option>
            </select>
            <button type="button" class="btn btn-outline-primary" :disabled="!produitChoisi" @click="ajouter">Ajouter</button>
          </div>
          <table class="table align-middle mb-0">
            <thead><tr><th>Produit</th><th class="text-end">Prix</th><th style="width:140px">Quantité</th><th class="text-end">Total</th><th></th></tr></thead>
            <tbody>
              <tr v-if="panier.length === 0"><td colspan="5" class="text-center text-muted py-3">Aucun produit ajouté.</td></tr>
              <tr v-for="(l, i) in panier" :key="l.produit.id_produit">
                <td>{{ l.produit.nom }}<div class="small text-muted">stock : {{ nombre(l.produit.stock) }} {{ l.produit.unite }}</div></td>
                <td class="text-end">{{ ariary(l.produit.prix_vente) }}</td>
                <td><input v-model.number="l.quantite" type="number" min="0.001" step="any" class="form-control form-control-sm" :aria-label="'Quantité ' + l.produit.nom" /></td>
                <td class="text-end">{{ ariary(l.quantite * l.produit.prix_vente) }}</td>
                <td class="text-end"><button type="button" class="btn btn-sm btn-outline-danger" @click="retirer(i)">Retirer</button></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="col-lg-4">
      <form class="card shadow-sm" @submit.prevent="valider">
        <div class="card-header">Client et paiement</div>
        <div class="card-body">
          <label for="client" class="form-label">Client</label>
          <div class="input-group mb-3">
            <select id="client" v-model="idClient" class="form-select">
              <option value="">Comptant (sans client)</option>
              <option v-for="c in clients" :key="c.id_client" :value="c.id_client">{{ c.nom }}</option>
            </select>
            <button type="button" class="btn btn-outline-secondary" title="Nouveau client" @click="nouveauClient = true">+</button>
          </div>

          <div class="d-flex justify-content-between fs-5 mb-3"><span>Total</span><strong>{{ ariary(total) }}</strong></div>

          <label for="paye" class="form-label">Payé maintenant (Ar)</label>
          <div class="input-group mb-1">
            <input id="paye" v-model.number="paiement.montant" type="number" min="0" step="0.01" class="form-control" />
            <button type="button" class="btn btn-outline-secondary" @click="toutPayer">Tout</button>
          </div>
          <div class="form-text mb-3">0 = vente à crédit (un client est alors obligatoire).</div>

          <label for="mode" class="form-label">Mode de paiement</label>
          <select id="mode" v-model="paiement.mode_paiement" class="form-select mb-3">
            <option v-for="(libelle, cle) in MODES" :key="cle" :value="cle">{{ libelle }}</option>
          </select>

          <div class="d-flex justify-content-between mb-3">
            <span>Reste à payer</span><strong :class="reste > 0 ? 'text-danger' : ''">{{ ariary(reste) }}</strong>
          </div>
          <button class="btn btn-success w-100" :disabled="panier.length === 0 || envoiEnCours">
            {{ envoiEnCours ? 'Validation…' : 'Valider la vente' }}
          </button>
        </div>
      </form>
    </div>
  </div>

  <ClientForm v-if="nouveauClient" @enregistre="clientCree" @ferme="nouveauClient = false" />
</template>

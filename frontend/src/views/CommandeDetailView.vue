<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'
import { ariary, nombre, STATUTS_COMMANDE } from '../utils/format'

const route = useRoute()
const commande = ref(null)
const saisie = ref([])          // une entrée par ligne à recevoir : { id_produit, quantite, prix }
const erreur = ref('')
const envoiEnCours = ref(false)

function preparerSaisie() {
  saisie.value = commande.value.lignes.map((l) => ({
    id_produit: l.id_produit, quantite: l.reste > 0 ? l.reste : 0, prix: l.prix_achat_prevu,
  }))
}

async function charger() {
  try {
    commande.value = await api.get(`/commandes/${route.params.id}`)
    preparerSaisie()
  } catch (e) {
    erreur.value = e.message
  }
}
onMounted(charger)

async function recevoir() {
  erreur.value = ''
  const lignes = saisie.value.filter((s) => s.quantite > 0)
    .map((s) => ({ id_produit: s.id_produit, quantite_recue: s.quantite, prix_achat_reel: s.prix }))
  if (lignes.length === 0) {
    erreur.value = 'Saisissez au moins une quantité reçue.'
    return
  }
  envoiEnCours.value = true
  try {
    commande.value = await api.post(`/commandes/${commande.value.id_commande}/receptions`, { corps: { lignes } })
    preparerSaisie()
  } catch (e) {
    erreur.value = e.message
  } finally {
    envoiEnCours.value = false
  }
}
</script>

<template>
  <router-link :to="{ name: 'commandes' }" class="small">&larr; Retour aux commandes</router-link>
  <div v-if="erreur" class="alert alert-danger mt-3" role="alert">{{ erreur }}</div>

  <template v-if="commande">
    <div class="d-flex justify-content-between align-items-center my-3">
      <h1 class="h3 mb-0">Commande #{{ commande.id_commande }}</h1>
      <span class="badge fs-6" :class="STATUTS_COMMANDE[commande.statut].classe">{{ STATUTS_COMMANDE[commande.statut].libelle }}</span>
    </div>
    <p class="text-muted">{{ commande.date_commande }} · Fournisseur : <strong>{{ commande.fournisseur }}</strong> · Total prévu : {{ ariary(commande.total_prevu) }}</p>

    <form class="card shadow-sm mb-3" @submit.prevent="recevoir">
      <div class="table-responsive">
        <table class="table align-middle mb-0">
          <thead>
            <tr><th>Produit</th><th class="text-end">Commandé</th><th class="text-end">Déjà reçu</th><th class="text-end">Reste</th>
              <th v-if="commande.statut !== 'recue'" style="width:140px">Reçu maintenant</th>
              <th v-if="commande.statut !== 'recue'" style="width:170px">Prix réel (Ar)</th></tr>
          </thead>
          <tbody>
            <tr v-for="(l, i) in commande.lignes" :key="l.id_produit">
              <td>{{ l.nom }} <code class="ms-1">{{ l.sku }}</code></td>
              <td class="text-end">{{ nombre(l.quantite_commandee) }} {{ l.unite }}</td>
              <td class="text-end">{{ nombre(l.quantite_recue) }}</td>
              <td class="text-end">{{ nombre(l.reste) }}</td>
              <template v-if="commande.statut !== 'recue'">
                <td><input v-model.number="saisie[i].quantite" type="number" min="0" step="any" class="form-control form-control-sm" :disabled="l.reste <= 0" :aria-label="'Reçu ' + l.nom" /></td>
                <td><input v-model.number="saisie[i].prix" type="number" min="0" step="0.01" class="form-control form-control-sm" :disabled="l.reste <= 0" :aria-label="'Prix réel ' + l.nom" /></td>
              </template>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="commande.statut !== 'recue'" class="card-footer text-end">
        <button class="btn btn-success" :disabled="envoiEnCours">Enregistrer la réception</button>
      </div>
    </form>

    <div class="card shadow-sm">
      <div class="card-header">Réceptions</div>
      <ul class="list-group list-group-flush">
        <li v-if="commande.receptions.length === 0" class="list-group-item text-muted">Aucune réception.</li>
        <li v-for="r in commande.receptions" :key="r.id_reception" class="list-group-item">
          <strong>Réception #{{ r.id_reception }}</strong> · {{ r.date_reception }} · {{ r.utilisateur }}
          <div v-for="l in r.lignes" :key="l.id_produit" class="small text-muted">
            {{ l.nom }} : {{ nombre(l.quantite_recue) }} {{ l.unite }} à {{ ariary(l.prix_achat_reel) }}
          </div>
        </li>
      </ul>
    </div>
  </template>
</template>

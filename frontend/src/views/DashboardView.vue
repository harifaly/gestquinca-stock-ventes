<script setup>
import { onMounted, ref, watch } from 'vue'
import { api } from '../api'
import { ariary, nombre } from '../utils/format'

const periode = ref('mois')
const d = ref(null)
const erreur = ref('')
const PERIODES = { jour: "Aujourd'hui", semaine: 'Cette semaine', mois: 'Ce mois' }

async function charger() {
  erreur.value = ''
  try {
    d.value = await api.get('/dashboard', { params: { periode: periode.value } })
  } catch (e) {
    erreur.value = e.message
  }
}
onMounted(charger)
watch(periode, charger)
</script>

<template>
  <div class="d-flex justify-content-between align-items-center mb-3">
    <h1 class="h3 mb-0">Tableau de bord</h1>
    <div class="btn-group" role="group" aria-label="Période">
      <button v-for="(libelle, cle) in PERIODES" :key="cle" class="btn btn-sm"
              :class="periode === cle ? 'btn-primary' : 'btn-outline-primary'" @click="periode = cle">{{ libelle }}</button>
    </div>
  </div>
  <div v-if="erreur" class="alert alert-danger" role="alert">{{ erreur }}</div>

  <template v-if="d">
    <p class="text-muted small">Période : depuis le {{ d.debut }}. Le chiffre d'affaires, les encaissements et les créances sont trois notions différentes.</p>
    <div class="row g-3 mb-4">
      <div class="col-6 col-lg-3"><div class="card stat-card stat-ca h-100"><div class="card-body">
        <div class="stat-label">Chiffre d'affaires</div><div class="fs-4 fw-semibold" data-test="ca">{{ ariary(d.chiffre_affaires) }}</div>
        <div class="small text-muted">{{ d.nombre_ventes }} vente(s)</div></div></div></div>
      <div class="col-6 col-lg-3"><div class="card stat-card stat-enc h-100"><div class="card-body">
        <div class="stat-label">Encaissements</div><div class="fs-4 fw-semibold text-success" data-test="encaissements">{{ ariary(d.encaissements) }}</div>
        <div class="small text-muted">paiements reçus</div></div></div></div>
      <div class="col-6 col-lg-3"><div class="card stat-card stat-cre h-100"><div class="card-body">
        <div class="stat-label">Créances clients</div><div class="fs-4 fw-semibold text-danger" data-test="creances">{{ ariary(d.creances_total) }}</div>
        <div class="small text-muted">restant dû, à ce jour</div></div></div></div>
      <div class="col-6 col-lg-3"><div class="card stat-card stat-marge h-100"><div class="card-body">
        <div class="stat-label">Marge brute estimée</div><div class="fs-4 fw-semibold" data-test="marge">{{ ariary(d.marge_brute) }}</div>
        <div class="small text-muted">valeur du stock : {{ ariary(d.valeur_stock) }}</div></div></div></div>
    </div>

    <div class="row g-3">
      <div class="col-lg-6">
        <div class="card shadow-sm h-100">
          <div class="card-header">Produits à réapprovisionner ({{ d.produits_a_reapprovisionner.length }})</div>
          <ul class="list-group list-group-flush">
            <li v-if="d.produits_a_reapprovisionner.length === 0" class="list-group-item text-muted">Aucun produit sous le seuil.</li>
            <li v-for="p in d.produits_a_reapprovisionner" :key="p.id_produit" class="list-group-item d-flex justify-content-between">
              <span>{{ p.nom }} <code class="ms-1">{{ p.sku }}</code></span>
              <span><strong class="text-danger">{{ nombre(p.stock) }}</strong> / min. {{ nombre(p.stock_minimum) }} {{ p.unite }}</span>
            </li>
          </ul>
        </div>
      </div>
      <div class="col-lg-6">
        <div class="card shadow-sm h-100">
          <div class="card-header">Meilleurs produits de la période</div>
          <ul class="list-group list-group-flush">
            <li v-if="d.meilleurs_produits.length === 0" class="list-group-item text-muted">Aucune vente sur la période.</li>
            <li v-for="(p, i) in d.meilleurs_produits" :key="p.id_produit" class="list-group-item d-flex justify-content-between">
              <span>{{ i + 1 }}. {{ p.nom }}</span>
              <span>{{ nombre(p.quantite_vendue) }} {{ p.unite }} · {{ ariary(p.chiffre_affaires) }}</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </template>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api'

const categories = ref([])
const erreur = ref('')
const formulaire = reactive({ ouvert: false, id: null, nom: '', description: '', erreur: '', envoi: false })

async function charger() {
  erreur.value = ''
  try {
    categories.value = await api.get('/categories')
  } catch (e) {
    erreur.value = e.message
  }
}
onMounted(charger)

async function supprimer(c) {
  if (!confirm(`Supprimer la catégorie « ${c.nom} » ?`)) return
  erreur.value = ''
  try {
    await api.delete(`/categories/${c.id_categorie}`)
    charger()
  } catch (e) {
    erreur.value = e.message
  }
}

function ouvrir(c = null) {
  Object.assign(formulaire, { ouvert: true, id: c?.id_categorie ?? null, nom: c?.nom ?? '', description: c?.description ?? '', erreur: '' })
}

async function enregistrer() {
  formulaire.erreur = ''
  formulaire.envoi = true
  const corps = { nom: formulaire.nom, description: formulaire.description || null }
  try {
    formulaire.id ? await api.put(`/categories/${formulaire.id}`, { corps }) : await api.post('/categories', { corps })
    formulaire.ouvert = false
    charger()
  } catch (e) {
    formulaire.erreur = e.message
  } finally {
    formulaire.envoi = false
  }
}
</script>

<template>
  <div class="d-flex justify-content-between align-items-center mb-3">
    <h1 class="h3 mb-0">Catégories</h1>
    <button class="btn btn-primary" @click="ouvrir()">+ Nouvelle catégorie</button>
  </div>
  <div v-if="erreur" class="alert alert-danger" role="alert">{{ erreur }}</div>
  <div class="card shadow-sm">
    <table class="table table-hover mb-0">
      <thead><tr><th>Nom</th><th>Description</th><th class="text-end">Actions</th></tr></thead>
      <tbody>
        <tr v-if="categories.length === 0"><td colspan="3" class="text-center text-muted py-4">Aucune catégorie.</td></tr>
        <tr v-for="c in categories" :key="c.id_categorie">
          <td>{{ c.nom }}</td><td>{{ c.description }}</td>
          <td class="text-end text-nowrap">
            <button class="btn btn-sm btn-outline-primary me-1" @click="ouvrir(c)">Modifier</button>
            <button class="btn btn-sm btn-outline-danger" @click="supprimer(c)">Supprimer</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>

  <template v-if="formulaire.ouvert">
    <div class="modal fade show d-block" tabindex="-1" role="dialog" aria-modal="true">
      <div class="modal-dialog">
        <form class="modal-content" @submit.prevent="enregistrer">
          <div class="modal-header">
            <h2 class="modal-title h5">{{ formulaire.id ? 'Modifier la catégorie' : 'Nouvelle catégorie' }}</h2>
            <button type="button" class="btn-close" aria-label="Fermer" @click="formulaire.ouvert = false"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3"><label for="cat-nom" class="form-label">Nom</label>
              <input id="cat-nom" v-model.trim="formulaire.nom" class="form-control" maxlength="100" required /></div>
            <div class="mb-3"><label for="cat-desc" class="form-label">Description</label>
              <input id="cat-desc" v-model.trim="formulaire.description" class="form-control" /></div>
            <div v-if="formulaire.erreur" class="alert alert-danger py-2 mb-0" role="alert">{{ formulaire.erreur }}</div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-outline-secondary" @click="formulaire.ouvert = false">Annuler</button>
            <button class="btn btn-primary" :disabled="formulaire.envoi">Enregistrer</button>
          </div>
        </form>
      </div>
    </div>
    <div class="modal-backdrop fade show"></div>
  </template>
</template>

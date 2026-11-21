<script setup>
import { ref } from 'vue'
import { api } from '../api'

const props = defineProps({ fournisseur: { type: Object, default: null } })
const emit = defineEmits(['enregistre', 'ferme'])

const f = props.fournisseur
const form = ref({
  nom: f?.nom ?? '', contact: f?.contact ?? '', telephone: f?.telephone ?? '',
  email: f?.email ?? '', adresse: f?.adresse ?? '',
})
const erreur = ref('')
const envoiEnCours = ref(false)

async function enregistrer() {
  erreur.value = ''
  envoiEnCours.value = true
  const corps = Object.fromEntries(Object.entries(form.value).map(([k, v]) => [k, v === '' ? null : v]))
  try {
    props.fournisseur
      ? await api.put(`/fournisseurs/${props.fournisseur.id_fournisseur}`, { corps })
      : await api.post('/fournisseurs', { corps })
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
          <h2 class="modal-title h5">{{ fournisseur ? 'Modifier le fournisseur' : 'Nouveau fournisseur' }}</h2>
          <button type="button" class="btn-close" aria-label="Fermer" @click="emit('ferme')"></button>
        </div>
        <div class="modal-body">
          <div class="mb-3"><label for="fo-nom" class="form-label">Nom</label>
            <input id="fo-nom" v-model.trim="form.nom" class="form-control" required /></div>
          <div class="mb-3"><label for="fo-contact" class="form-label">Personne à contacter</label>
            <input id="fo-contact" v-model.trim="form.contact" class="form-control" /></div>
          <div class="row">
            <div class="col-md-6 mb-3"><label for="fo-tel" class="form-label">Téléphone</label>
              <input id="fo-tel" v-model.trim="form.telephone" class="form-control" /></div>
            <div class="col-md-6 mb-3"><label for="fo-mail" class="form-label">Email</label>
              <input id="fo-mail" v-model.trim="form.email" type="email" class="form-control" /></div>
          </div>
          <div class="mb-3"><label for="fo-adr" class="form-label">Adresse</label>
            <input id="fo-adr" v-model.trim="form.adresse" class="form-control" /></div>
          <div v-if="erreur" class="alert alert-danger py-2 mb-0" role="alert">{{ erreur }}</div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-outline-secondary" @click="emit('ferme')">Annuler</button>
          <button class="btn btn-primary" :disabled="envoiEnCours">{{ envoiEnCours ? 'Enregistrement…' : 'Enregistrer' }}</button>
        </div>
      </form>
    </div>
  </div>
  <div class="modal-backdrop fade show"></div>
</template>

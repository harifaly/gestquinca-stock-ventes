<script setup>
import { ref } from 'vue'
import { api } from '../api'

const props = defineProps({ client: { type: Object, default: null } })
const emit = defineEmits(['enregistre', 'ferme'])

const form = ref({
  nom: props.client?.nom ?? '',
  telephone: props.client?.telephone ?? '',
  adresse: props.client?.adresse ?? '',
})
const erreur = ref('')
const envoiEnCours = ref(false)

async function enregistrer() {
  erreur.value = ''
  envoiEnCours.value = true
  const corps = { nom: form.value.nom, telephone: form.value.telephone || null, adresse: form.value.adresse || null }
  try {
    const resultat = props.client
      ? await api.put(`/clients/${props.client.id_client}`, { corps })
      : await api.post('/clients', { corps })
    emit('enregistre', resultat)
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
          <h2 class="modal-title h5">{{ client ? 'Modifier le client' : 'Nouveau client' }}</h2>
          <button type="button" class="btn-close" aria-label="Fermer" @click="emit('ferme')"></button>
        </div>
        <div class="modal-body">
          <div class="mb-3">
            <label for="c-nom" class="form-label">Nom</label>
            <input id="c-nom" v-model.trim="form.nom" class="form-control" required />
          </div>
          <div class="mb-3">
            <label for="c-tel" class="form-label">Téléphone</label>
            <input id="c-tel" v-model.trim="form.telephone" class="form-control" />
          </div>
          <div class="mb-3">
            <label for="c-adr" class="form-label">Adresse</label>
            <input id="c-adr" v-model.trim="form.adresse" class="form-control" />
          </div>
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

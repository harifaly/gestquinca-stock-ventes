<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api'

const utilisateurs = ref([])
const erreur = ref('')
const formulaire = reactive({ ouvert: false, id: null, nom_utilisateur: '', nom_complet: '', role: 'vendeur', mot_de_passe: '', erreur: '', envoi: false })

async function charger() {
  erreur.value = ''
  try {
    utilisateurs.value = await api.get('/utilisateurs')
  } catch (e) {
    erreur.value = e.message
  }
}
onMounted(charger)

function ouvrir(u = null) {
  Object.assign(formulaire, {
    ouvert: true, id: u?.id_utilisateur ?? null, nom_utilisateur: u?.nom_utilisateur ?? '',
    nom_complet: u?.nom_complet ?? '', role: u?.role ?? 'vendeur', mot_de_passe: '', erreur: '',
  })
}

async function enregistrer() {
  formulaire.erreur = ''
  formulaire.envoi = true
  try {
    if (formulaire.id) {
      await api.put(`/utilisateurs/${formulaire.id}`, {
        corps: { nom_complet: formulaire.nom_complet, role: formulaire.role, mot_de_passe: formulaire.mot_de_passe || null },
      })
    } else {
      await api.post('/utilisateurs', {
        corps: { nom_utilisateur: formulaire.nom_utilisateur, nom_complet: formulaire.nom_complet, role: formulaire.role, mot_de_passe: formulaire.mot_de_passe },
      })
    }
    formulaire.ouvert = false
    charger()
  } catch (e) {
    formulaire.erreur = e.message
  } finally {
    formulaire.envoi = false
  }
}

async function changerActif(u) {
  if (!confirm(`Voulez-vous ${u.actif ? 'désactiver' : 'réactiver'} le compte « ${u.nom_utilisateur} » ?`)) return
  erreur.value = ''
  try {
    await api.patch(`/utilisateurs/${u.id_utilisateur}/actif`, { corps: { actif: !u.actif } })
    charger()
  } catch (e) {
    erreur.value = e.message
  }
}
</script>

<template>
  <div class="d-flex justify-content-between align-items-center mb-3">
    <h1 class="h3 mb-0">Utilisateurs</h1>
    <button class="btn btn-primary" @click="ouvrir()">+ Nouvel utilisateur</button>
  </div>
  <div v-if="erreur" class="alert alert-danger" role="alert">{{ erreur }}</div>
  <div class="card shadow-sm">
    <table class="table table-hover mb-0">
      <thead><tr><th>Identifiant</th><th>Nom</th><th>Rôle</th><th>Compte</th><th class="text-end">Actions</th></tr></thead>
      <tbody>
        <tr v-for="u in utilisateurs" :key="u.id_utilisateur" :class="{ 'ligne-inactive': !u.actif }">
          <td><code>{{ u.nom_utilisateur }}</code></td>
          <td>{{ u.nom_complet }}</td>
          <td><span class="badge" :class="u.role === 'admin' ? 'bg-warning text-dark' : 'bg-info text-dark'">{{ u.role === 'admin' ? 'Administrateur' : 'Vendeur' }}</span></td>
          <td>{{ u.actif ? 'Actif' : 'Désactivé' }}</td>
          <td class="text-end text-nowrap">
            <button class="btn btn-sm btn-outline-primary me-1" @click="ouvrir(u)">Modifier</button>
            <button class="btn btn-sm" :class="u.actif ? 'btn-outline-danger' : 'btn-outline-success'" @click="changerActif(u)">
              {{ u.actif ? 'Désactiver' : 'Réactiver' }}
            </button>
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
            <h2 class="modal-title h5">{{ formulaire.id ? 'Modifier l\'utilisateur' : 'Nouvel utilisateur' }}</h2>
            <button type="button" class="btn-close" aria-label="Fermer" @click="formulaire.ouvert = false"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3"><label for="u-id" class="form-label">Identifiant</label>
              <input id="u-id" v-model.trim="formulaire.nom_utilisateur" class="form-control" :disabled="!!formulaire.id" minlength="3" required /></div>
            <div class="mb-3"><label for="u-nom" class="form-label">Nom complet</label>
              <input id="u-nom" v-model.trim="formulaire.nom_complet" class="form-control" required /></div>
            <div class="mb-3"><label for="u-role" class="form-label">Rôle</label>
              <select id="u-role" v-model="formulaire.role" class="form-select">
                <option value="vendeur">Vendeur</option><option value="admin">Administrateur</option>
              </select></div>
            <div class="mb-3"><label for="u-mdp" class="form-label">{{ formulaire.id ? 'Nouveau mot de passe (laisser vide pour ne pas changer)' : 'Mot de passe (8 caractères minimum)' }}</label>
              <input id="u-mdp" v-model="formulaire.mot_de_passe" type="password" class="form-control" minlength="8" autocomplete="new-password" :required="!formulaire.id" /></div>
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

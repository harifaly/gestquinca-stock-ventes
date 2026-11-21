import { createRouter, createWebHistory } from 'vue-router'
import { estAdmin, session } from './auth'
import LoginView from './views/LoginView.vue'
import ProduitsView from './views/ProduitsView.vue'
import ClientsView from './views/ClientsView.vue'
import VentesView from './views/VentesView.vue'
import NouvelleVenteView from './views/NouvelleVenteView.vue'
import VenteDetailView from './views/VenteDetailView.vue'
import DashboardView from './views/DashboardView.vue'
import StockView from './views/StockView.vue'
import FournisseursView from './views/FournisseursView.vue'
import CategoriesView from './views/CategoriesView.vue'
import UtilisateursView from './views/UtilisateursView.vue'
import CommandesView from './views/CommandesView.vue'
import NouvelleCommandeView from './views/NouvelleCommandeView.vue'
import CommandeDetailView from './views/CommandeDetailView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: () => (estAdmin() ? '/tableau-de-bord' : '/produits') },
    { path: '/connexion', name: 'connexion', component: LoginView },
    { path: '/produits', name: 'produits', component: ProduitsView, meta: { connexionRequise: true } },
    { path: '/clients', name: 'clients', component: ClientsView, meta: { connexionRequise: true } },
    { path: '/ventes', name: 'ventes', component: VentesView, meta: { connexionRequise: true } },
    { path: '/ventes/nouvelle', name: 'nouvelle-vente', component: NouvelleVenteView, meta: { connexionRequise: true } },
    { path: '/ventes/:id(\\d+)', name: 'vente', component: VenteDetailView, meta: { connexionRequise: true } },
    { path: '/stock', name: 'stock', component: StockView, meta: { connexionRequise: true } },
    { path: '/tableau-de-bord', name: 'tableau-de-bord', component: DashboardView, meta: { connexionRequise: true, admin: true } },
    // Achats : réservés à l'administrateur (meta.admin)
    { path: '/categories', name: 'categories', component: CategoriesView, meta: { connexionRequise: true, admin: true } },
    { path: '/utilisateurs', name: 'utilisateurs', component: UtilisateursView, meta: { connexionRequise: true, admin: true } },
    { path: '/fournisseurs', name: 'fournisseurs', component: FournisseursView, meta: { connexionRequise: true, admin: true } },
    { path: '/commandes', name: 'commandes', component: CommandesView, meta: { connexionRequise: true, admin: true } },
    { path: '/commandes/nouvelle', name: 'nouvelle-commande', component: NouvelleCommandeView, meta: { connexionRequise: true, admin: true } },
    { path: '/commandes/:id(\\d+)', name: 'commande', component: CommandeDetailView, meta: { connexionRequise: true, admin: true } },
  ],
})

// Protection des pages : sans connexion, on est renvoyé vers la page de connexion
router.beforeEach((vers) => {
  if (vers.meta.connexionRequise && !session.token) return { name: 'connexion' }
  if (vers.meta.admin && !estAdmin()) return { name: 'produits' }
  if (vers.name === 'connexion' && session.token) return '/'
})

export default router

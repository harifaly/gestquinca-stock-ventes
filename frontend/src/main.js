import { createApp } from 'vue'
import '@fontsource-variable/nunito'
import '@fontsource-variable/inter'
import 'bootstrap/dist/css/bootstrap.min.css'
import './style.css'
import './theme-pro.css'
import './theme'
import App from './App.vue'
import router from './router'
import { configurerApi } from './api'
import { session, deconnexion } from './auth'

// Quand l'API répond « non connecté » (jeton expiré), on revient à la page de connexion
configurerApi({
  token: () => session.token,
  surNonAutorise: () => {
    deconnexion()
    router.push({ name: 'connexion' })
  },
})

createApp(App).use(router).mount('#app')

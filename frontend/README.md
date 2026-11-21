# GestQuinca – Frontend (Vue 3)

## Lancer
```
cd frontend
npm install
copy .env.example .env      (Windows ; cp sous Linux/Mac)
npm run dev
```
Ouvrir http://localhost:5173 (l'API doit tourner sur http://localhost:8000).
Comptes de démonstration : `admin / admin123`, `vendeur / vendeur123`.

## Contenu
- `src/api.js` : appels HTTP + gestion des erreurs
- `src/auth.js` : session (token JWT, rôle)
- `src/router.js` : routes protégées
- `src/views/` : pages (connexion, produits, clients, ventes, paiements, fournisseurs, commandes, réceptions, stock et tableau de bord)
- `src/components/ProduitForm.vue` : formulaire d'ajout/modification

`npm run build` produit le dossier `dist/`.

## Design
Deux thèmes au choix, avec un bouton **« Thème doux / sobre »** dans la barre latérale (le choix est mémorisé dans le navigateur) :
- **Sobre** (par défaut) : fond gris clair, barre latérale bleu nuit, un seul bleu d'accent. Fichier `src/theme-pro.css`, police Inter.
- **Doux** : tons pastel chauds. Fichier `src/style.css`, police Nunito.

Les couleurs se changent en modifiant les variables au début de chaque fichier (`--c-primaire`, `--c-fond`, `--sb-bg`…).
Les polices sont installées avec `npm install` (elles fonctionnent hors connexion). Le changement de thème est géré par `src/theme.js`
(attribut `data-theme` sur `<html>`). La barre latérale et les icônes sont dans `src/App.vue` et `src/components/Icone.vue`.

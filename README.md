# GestQuinca - Gestion de stock et de commandes d'une quincaillerie

Application web (Vue.js + FastAPI + PostgreSQL) pour gérer le catalogue, le stock, les ventes (comptant ou à crédit)
et les paiements d'une quincaillerie. Projet final du cours « Application web et base de données relationnelle ».

**Auteur(s) :** ANDRIAMIRINDRAMANANA Harifaly Lunard

## 1. Ce que fait l'application

| Module | Administrateur | Vendeur |
|---|---|---|
| Authentification (JWT), rôles | oui | oui |
| Produits : ajouter, modifier, désactiver, supprimer (si jamais utilisé), rechercher, filtrer | tout | consultation |
| Catégories : ajouter, modifier, supprimer (si vide) | tout | consultation (via les produits) |
| Utilisateurs : créer un compte, rôle, mot de passe haché, désactiver | tout | aucun accès |
| Clients : ajouter, modifier, supprimer (si aucune vente), rechercher, créance | tout | consulter, créer |
| Ventes : panier, prix copié, sortie de stock automatique | oui | oui |
| Paiements : acomptes, solde, statut (non payée, partielle, payée) | oui | oui |
| Stock : quantités, alerte sous le seuil, historique des mouvements | oui | consultation |
| Ajustement de stock justifié (perte, casse, erreur de comptage, autre) | oui | aucun accès |
| Tableau de bord : chiffre d'affaires, encaissements, créances, marge estimée, ruptures, meilleurs produits | oui | aucun accès |
| Fournisseurs : fiche, recherche, supprimer (si aucune commande) | tout | aucun accès |
| Commandes fournisseurs à plusieurs lignes, réceptions partielles, entrée en stock, CMP | tout | aucun accès |

**Politique de suppression.** Ce qui n'a jamais servi se supprime vraiment (produit créé par erreur, catégorie vide, client sans vente,
fournisseur sans commande). Dès qu'il existe un historique (ventes, commandes, mouvements de stock), la base **refuse** la suppression
(clés étrangères `ON DELETE RESTRICT`) et l'application propose de **désactiver** le produit ou le compte à la place : on ne perd
jamais l'historique comptable.

Le cycle complet **achat, stock, vente, paiement** fonctionne : une commande n'a aucun effet sur le stock, chaque réception
l'augmente et recalcule le coût moyen pondéré, chaque vente le diminue, et un ajustement justifié corrige les écarts.
Aucun mouvement n'est jamais modifié ni supprimé : l'historique est complet. Le tableau de bord distingue le chiffre d'affaires
(ventes de la période), les encaissements (paiements reçus) et les créances (restant dû à ce jour).

## 2. Technologies

- **Base de données** : PostgreSQL 16 (clés, contraintes CHECK, vues, triggers PL/pgSQL)
- **API** : Python 3.10+, FastAPI, psycopg 3 (SQL écrit à la main, sans ORM), JWT, bcrypt
- **Interface** : Vue.js 3, Vue Router, Bootstrap 5, Vite
- **Tests** : 23 tests SQL (`db/tests/tests.sql`) et 42 tests d'API (pytest)

### Pourquoi ces choix

- **PostgreSQL** : le sujet porte sur l'intégrité d'une base relationnelle. PostgreSQL applique les clés étrangères composées, les contraintes `CHECK`,
  les index uniques partiels, les vues et les triggers qui garantissent les règles de gestion (stock jamais négatif, paiement limité au reste à payer...)
  **dans la base**, donc quel que soit le client qui l'utilise.
- **FastAPI + psycopg sans ORM** : le SQL est écrit à la main et reste visible, ce qui montre le lien entre l'interface et les tables.
  FastAPI valide les données (Pydantic), gère l'authentification JWT et documente l'API automatiquement (`/docs`).
- **Vue.js 3 + Bootstrap** : une interface réactive avec peu de code, sans bibliothèque lourde ; Bootstrap donne un rendu propre et adapté au mobile.
- **Pas d'ORM, pas de logique métier dupliquée** : l'API ne fait que transmettre ; ce sont les contraintes de la base qui décident.

## 3. Organisation du dépôt

```
db/                 scripts SQL (schéma, vues, triggers, données d'exemple) et tests SQL
backend/            API FastAPI (app/routers, schemas, sécurité) et tests pytest
frontend/           interface Vue 3
docs/screenshots/   captures d'écran
docker-compose.yml  PostgreSQL prêt à l'emploi (facultatif)
```

## 4. Modèle de données

13 tables : `utilisateur`, `categorie`, `produit`, `fournisseur`, `client`, `commande_fournisseur`, `ligne_commande`,
`reception`, `ligne_reception`, `vente`, `ligne_vente`, `paiement`, `mouvement_stock`.

```mermaid
erDiagram
  CATEGORIE ||--o{ PRODUIT : classe
  FOURNISSEUR ||--o{ COMMANDE_FOURNISSEUR : recoit
  UTILISATEUR ||--o{ COMMANDE_FOURNISSEUR : passe
  COMMANDE_FOURNISSEUR ||--|{ LIGNE_COMMANDE : contient
  PRODUIT ||--o{ LIGNE_COMMANDE : "est commande"
  COMMANDE_FOURNISSEUR ||--o{ RECEPTION : "est livree par"
  RECEPTION ||--|{ LIGNE_RECEPTION : comprend
  PRODUIT ||--o{ LIGNE_RECEPTION : "est recu"
  CLIENT |o--o{ VENTE : achete
  UTILISATEUR ||--o{ VENTE : enregistre
  VENTE ||--|{ LIGNE_VENTE : contient
  PRODUIT ||--o{ LIGNE_VENTE : "est vendu"
  VENTE ||--o{ PAIEMENT : "est reglee par"
  PRODUIT ||--o{ MOUVEMENT_STOCK : "fait varier"
  LIGNE_VENTE |o--o| MOUVEMENT_STOCK : "sortie de stock"
  LIGNE_RECEPTION |o--o| MOUVEMENT_STOCK : "entree de stock"
```

Schéma entité-association complet (10 entités, 3 associations qui portent des données) :

![Modèle entité-association](docs/modelisation/mea.png)

**Schéma relationnel** (clé primaire = première colonne, deux premières colonnes pour les tables de lignes ; `#` = clé étrangère) :

```
utilisateur          (id_utilisateur, nom_utilisateur UNIQUE, mot_de_passe_hash, nom_complet, role, actif)
categorie            (id_categorie, nom UNIQUE, description)
produit              (id_produit, sku UNIQUE, nom, marque, description, unite, prix_achat, prix_vente, stock_minimum, cmp, actif, #id_categorie)
fournisseur          (id_fournisseur, nom, telephone, adresse, email, contact)
client               (id_client, nom, telephone, adresse)
commande_fournisseur (id_commande, date_commande, #id_fournisseur, #id_utilisateur)
ligne_commande       (#id_commande, #id_produit, quantite_commandee, prix_achat_prevu)
reception            (id_reception, date_reception, #id_commande, #id_utilisateur)
ligne_reception      (#id_reception, #id_produit, quantite_recue, prix_achat_reel)
vente                (id_vente, date_vente, #id_client (NULL possible), #id_utilisateur)
ligne_vente          (#id_vente, #id_produit, quantite, prix_unitaire)
paiement             (id_paiement, #id_vente, date_paiement, montant, mode_paiement, #id_utilisateur)
mouvement_stock      (id_mouvement, #id_produit, type_mouvement, quantite, date_mouvement, #id_utilisateur,
                      #(id_vente, id_produit) NULL possible, #(id_reception, id_produit) NULL possible, motif)
```

Le dossier complet (cardinalités, passage au relationnel, dépendances fonctionnelles table par table, preuve de la BCNF, vues)
est dans **[docs/modelisation.md](docs/modelisation.md)**.

Choix de conception principaux :
- Le **stock n'est jamais stocké** : c'est la somme des mouvements signés de `mouvement_stock` (vue `v_stock`).
- Les **totaux, soldes et statuts** (vente, commande, créance client) sont calculés par des vues, jamais enregistrés,
  pour éviter les dépendances fonctionnelles transitives et les incohérences.
- Les tables de lignes ont une **clé primaire composée** (ex. `ligne_vente(id_vente, id_produit)`).
- Toutes les tables sont en **BCNF** : chaque dépendance fonctionnelle non triviale a pour déterminant une clé candidate.
  La démonstration (dépendances fonctionnelles de chaque table) est dans [docs/modelisation.md](docs/modelisation.md).

### Règles de gestion appliquées par la base

| Règle | Contenu | Mécanisme |
|---|---|---|
| RG01 | Référence (SKU) unique | `UNIQUE` |
| RG02 | Statut d'une commande déduit des réceptions | vue `v_statut_commande` |
| RG03 | Réception limitée au reste à recevoir | trigger |
| RG04 | Prix d'achat réel enregistré à la réception | colonne `prix_achat_reel` |
| RG05 | Coût moyen pondéré recalculé à chaque entrée | trigger |
| RG06 | Stock jamais négatif | trigger (avec verrou du produit) |
| RG07 | Prix de vente copié dans la ligne de vente | colonne `prix_unitaire` |
| RG08 | Un paiement ne dépasse pas le reste à payer | trigger |
| RG09 | Total, solde et statut de vente calculés | vues |
| RG10 | Vente non soldée : client obligatoire | trigger différé |
| RG11 | Mouvements de stock non modifiables | trigger |
| RG12 | Une opération est atomique | une transaction par requête |
| RG13 | Rôles admin / vendeur contrôlés côté serveur | dépendances FastAPI |
| RG14 | Mots de passe hachés (bcrypt) | `pgcrypto` / `bcrypt` |

## 5. Installation et lancement

Prérequis : **PostgreSQL 16** (ou Docker), **Python 3.10+**, **Node.js 20+** (npm).

### 5.1 Créer la base de données

**Option A – PostgreSQL installé sur l'ordinateur.** Ouvrir `psql` (ou pgAdmin) avec l'utilisateur `postgres` :

```sql
CREATE USER gestquinca WITH PASSWORD 'gestquinca_dev';
CREATE DATABASE gestquinca OWNER gestquinca;
```

Puis, depuis la racine du projet, exécuter les scripts dans l'ordre :

```
psql -U gestquinca -d gestquinca -f db/01_schema.sql
psql -U gestquinca -d gestquinca -f db/02_vues.sql
psql -U gestquinca -d gestquinca -f db/03_triggers.sql
psql -U gestquinca -d gestquinca -f db/04_seed.sql
```

Sous Windows, si les accents s'affichent mal dans la console, taper d'abord `chcp 65001` (c'est seulement l'affichage).

**Option B – Docker.** `docker compose up -d` crée la base et exécute automatiquement les 4 scripts.

Les données d'exemple contiennent 2 utilisateurs, 6 catégories, 14 produits, 3 fournisseurs, 4 clients, 4 commandes,
4 réceptions, 7 ventes et leurs paiements.

### 5.2 Lancer l'API

```
cd backend
python -m venv .venv
.venv\Scripts\activate          (Mac/Linux : source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env          (Mac/Linux : cp .env.example .env)
uvicorn app.main:app --reload
```

L'API répond sur http://localhost:8000. Documentation interactive : http://localhost:8000/docs.
Si PostgreSQL n'utilise pas le port 5432 ou un autre mot de passe, modifier `DATABASE_URL` dans `backend/.env`.

### 5.3 Lancer l'interface

Dans un second terminal :

```
cd frontend
npm install
copy .env.example .env          (Mac/Linux : cp .env.example .env)
npm run dev
```

Ouvrir http://localhost:5173.

### 5.4 Comptes de démonstration

| Rôle | Identifiant | Mot de passe |
|---|---|---|
| Administrateur | `admin` | `admin123` |
| Vendeur | `vendeur` | `vendeur123` |



## 6. Tester et reproduire la démonstration

Pour **essayer** l'application, il suffit d'avoir fait l'installation (section 5) et de se connecter : les tests automatiques
ne sont pas obligatoires, ils servent à vérifier que tout fonctionne.

> **Ordre conseillé.** Les tests automatiques supposent les données d'exemple d'origine (par exemple 14 produits). Lancez-les **avant** de jouer
> avec l'interface. Si vous avez déjà enregistré des ventes, recréez d'abord la base (section 5.1).

### 6.1 Démonstration rapide dans l'interface (5 minutes)

1. Se connecter en `vendeur`. Aller dans **Ventes** puis **Nouvelle vente**, ajouter un produit, payer en partie : la vente apparaît « Partielle ».
2. Ouvrir la vente et encaisser plus que le reste : l'erreur **RG08** s'affiche.
3. Demander une quantité supérieure au stock : l'erreur **RG06** s'affiche et rien n'est enregistré.
4. Valider une vente à crédit sans client : l'erreur **RG10** s'affiche.
5. Se connecter en `admin` : les boutons de création, modification, désactivation et suppression des produits apparaissent, ainsi que les menus **Fournisseurs**, **Commandes** et **Utilisateurs** (absents pour le vendeur).
6. En `admin`, supprimer le produit « Ciment CPJ 45 » : la suppression est **refusée** (il a un historique) et l'application propose de le désactiver.

### 6.2 Scénario de recette du cahier des charges (en `admin`, puis en `vendeur`)

1. Créer un produit « Ciment » (unité : sac), un fournisseur, puis une commande de 100 sacs : le stock reste à 0.
2. Dans la commande, réceptionner 101 sacs : l'erreur **RG03** s'affiche. Réceptionner 60 puis 40 : le statut passe à « Partiellement reçue » puis « Reçue », et le stock à 100.
3. Se connecter en `vendeur` et vendre 10 sacs à crédit à un client ; encaisser deux paiements successifs : le statut devient « Partielle » et le solde reste exact.
4. Vérifier que le stock est à 90, qu'une vente au-delà du stock est refusée, et que le **Tableau de bord** (en `admin`) affiche des chiffres cohérents.
5. Dans **Stock**, faire un ajustement de retrait pour cause de casse : un nouveau mouvement apparaît dans l'historique. Un retrait supérieur au stock est refusé (**RG06**).

### 6.3 Tests automatiques (facultatif)

**Base de données** (23 tests des règles de gestion, annulés à la fin par un `ROLLBACK`) :
```
psql -U gestquinca -d gestquinca -f db/tests/tests.sql
```
Résultat attendu : `23 OK, 0 échec`.

**API** (depuis `backend`, environnement virtuel activé) :
```
pytest -v
```
Résultat attendu : `42 passed`. Les tests de vente et d'achat suppriment à la fin ce qu'ils ont créé (le propriétaire de la base est requis pour ce nettoyage).

## 7. Captures d'écran

| | |
|---|---|
| ![Connexion](docs/screenshots/connexion.png) Connexion | ![Produits](docs/screenshots/produits.png) Liste et recherche des produits |
| ![Sous le seuil](docs/screenshots/produits-sous-seuil.png) Produits à réapprovisionner | ![Formulaire](docs/screenshots/formulaire-produit.png) Ajout d'un produit (admin) |
| ![Erreur SKU](docs/screenshots/erreur-sku.png) Contrainte d'unicité du SKU | ![Vendeur](docs/screenshots/vue-vendeur.png) Vue du vendeur (lecture seule) |
| ![Ventes](docs/screenshots/ventes.png) Liste des ventes | ![Nouvelle vente](docs/screenshots/nouvelle-vente.png) Nouvelle vente et règle RG10 |
| ![Détail](docs/screenshots/detail-vente.png) Détail d'une vente et paiements | ![Clients](docs/screenshots/clients.png) Clients et créances |
| ![Fournisseur](docs/screenshots/fournisseur-formulaire.png) Fiche fournisseur (admin) | ![Commande](docs/screenshots/nouvelle-commande.png) Nouvelle commande fournisseur |
| ![Réception](docs/screenshots/commande-recue.png) Commande reçue en deux réceptions | ![Tableau de bord](docs/screenshots/tableau-de-bord.png) Tableau de bord (admin) |
| ![Stock](docs/screenshots/stock.png) Historique des mouvements de stock | ![Ajustement](docs/screenshots/ajustement.png) Ajustement justifié (admin) |
| ![Catégories](docs/screenshots/categories.png) Catégories (admin) | ![Utilisateurs](docs/screenshots/utilisateurs.png) Gestion des utilisateurs (admin) |

| | |
|---|---|
| ![Suppression refusée](docs/screenshots/suppression-refusee.png) Suppression refusée : le produit a un historique | |

## 8. Documentation complémentaire

- `backend/README.md` : détail de l'API et organisation du code
- `frontend/README.md` : organisation de l'interface
- [`docs/modelisation.md`](docs/modelisation.md) : modèle entité-association, schéma relationnel, dépendances fonctionnelles et justification BCNF

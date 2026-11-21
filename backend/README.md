# API GestQuinca (FastAPI)

Prérequis : la base de données `gestquinca` est créée et remplie (voir `db/`), et Python 3.10 ou plus récent est installé.

## Lancer l'API (Windows, invite de commandes dans le dossier `backend`)

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

- Sur Mac ou Linux : `source .venv/bin/activate` au lieu de `.venv\Scripts\activate`, et `cp` au lieu de `copy`.
- Si votre base n'utilise pas le port 5432 ou un autre mot de passe, modifiez `DATABASE_URL` dans `.env`.
- L'API répond sur http://localhost:8000. Vérification : http://localhost:8000/sante doit afficher `{"statut":"ok"}`.

## Essayer l'API sans interface

Ouvrez http://localhost:8000/docs (documentation interactive générée automatiquement) :

1. Cliquez sur le bouton **Authorize** et connectez-vous avec `admin` / `admin123` (ou `vendeur` / `vendeur123`).
2. Ouvrez `GET /produits`, cliquez sur **Try it out** puis **Execute**.
3. Testez la recherche : paramètre `q` = `ciment`. Testez aussi `sous_seuil` = `true`.
4. Avec `admin`, essayez `POST /produits` ; avec `vendeur`, la même requête est refusée (403).

## Lancer les tests

```
pytest -v
```

Les 42 tests utilisent la vraie base (données de `db/04_seed.sql`) et nettoient leurs ajouts. Ils échouent si les données d'exemple ont été modifiées (par exemple après des ventes réelles) : lancez-les **avant** de jouer avec l'interface, ou recréez la base.

Résultat attendu : `42 passed`.

## Organisation du code

| Fichier | Rôle |
|---|---|
| `app/main.py` | Démarrage, CORS, traduction des erreurs de la base en messages clairs |
| `app/config.py` | Paramètres (`.env`) |
| `app/db.py` | Connexion PostgreSQL : une transaction par requête (COMMIT ou ROLLBACK) |
| `app/security.py` | Jeton JWT, vérification du mot de passe bcrypt, rôles admin et vendeur |
| `app/schemas.py` | Validation des données (Pydantic) |
| `app/routers/` | Un fichier par module (voir ci-dessous) |
| `tests/` | Tests pytest |

## Les modules de l'API

| Module | Routes principales | Accès |
|---|---|---|
| `auth` | `POST /auth/login`, `GET /auth/me` | tous |
| `produits` | `GET` (recherche, filtres, pagination), `POST`, `PUT`, `PATCH /{id}/actif`, `DELETE` | lecture : tous ; écriture : admin |
| `categories` | `GET`, `POST`, `PUT`, `DELETE` | lecture : tous ; écriture : admin |
| `clients` | `GET`, `POST`, `PUT`, `DELETE` | lecture et création : tous ; modification et suppression : admin |
| `ventes` | `GET`, `POST` (panier), `GET /{id}`, `POST /{id}/paiements` | tous |
| `fournisseurs` | `GET`, `POST`, `PUT`, `DELETE` | admin |
| `commandes` | `GET`, `POST`, `GET /{id}`, `POST /{id}/receptions` | admin |
| `stock` | `GET /stock/mouvements`, `POST /stock/ajustements` | lecture : tous ; ajustement : admin |
| `dashboard` | `GET /dashboard` | admin |
| `utilisateurs` | `GET`, `POST`, `PUT`, `PATCH /{id}/actif` | admin |

La liste complète et à jour, avec un bouton d'essai, est dans http://localhost:8000/docs.

**Suppression.** Les routes `DELETE` ne suppriment que ce qui n'a jamais servi. S'il existe un historique, elles répondent `409` avec un message clair
(les clés étrangères sont en `ON DELETE RESTRICT`) ; il faut alors désactiver l'élément.

## Ajouter un module

Copier `app/routers/produits.py` (ou `clients.py`, plus court), adapter le SQL et les schémas, puis ajouter une ligne `app.include_router(...)` dans `main.py`.

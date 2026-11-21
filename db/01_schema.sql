-- =====================================================================
-- GestQuinca : création des tables (13 tables, toutes en BCNF)
-- Exécuté en premier (voir docker-compose.yml). Ordre : 01 -> 02 -> 03 -> 04
-- =====================================================================

-- ---------- Référentiels ----------
CREATE TABLE utilisateur (
  id_utilisateur    INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  nom_utilisateur   TEXT NOT NULL UNIQUE,
  mot_de_passe_hash TEXT NOT NULL,                     -- RG14 : jamais en clair
  nom_complet       TEXT NOT NULL,
  role              TEXT NOT NULL CHECK (role IN ('admin', 'vendeur')),
  actif             BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE categorie (
  id_categorie INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  nom          TEXT NOT NULL UNIQUE,
  description  TEXT
);

CREATE TABLE produit (
  id_produit    INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  sku           TEXT NOT NULL UNIQUE,                  -- RG01
  nom           TEXT NOT NULL,
  marque        TEXT,
  description   TEXT,
  unite         TEXT NOT NULL CHECK (unite IN ('sac','barre','metre','kg','litre','piece')),
  prix_achat    NUMERIC(14,2) NOT NULL CHECK (prix_achat >= 0),   -- prix d'achat indicatif
  prix_vente    NUMERIC(14,2) NOT NULL CHECK (prix_vente >= 0),   -- prix de vente courant
  stock_minimum NUMERIC(12,3) NOT NULL DEFAULT 0 CHECK (stock_minimum >= 0),
  cmp           NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (cmp >= 0),-- maintenu par trigger (RG05)
  actif         BOOLEAN NOT NULL DEFAULT TRUE,         -- un produit utilisé est désactivé, pas supprimé
  id_categorie  INT NOT NULL REFERENCES categorie ON DELETE RESTRICT
);

CREATE TABLE fournisseur (
  id_fournisseur INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  nom            TEXT NOT NULL,
  telephone      TEXT,
  adresse        TEXT,
  email          TEXT,
  contact        TEXT
);

CREATE TABLE client (
  id_client INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  nom       TEXT NOT NULL,
  telephone TEXT,
  adresse   TEXT
);

-- ---------- Approvisionnement ----------
CREATE TABLE commande_fournisseur (
  id_commande    INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  date_commande  DATE NOT NULL DEFAULT CURRENT_DATE,
  id_fournisseur INT NOT NULL REFERENCES fournisseur ON DELETE RESTRICT,
  id_utilisateur INT NOT NULL REFERENCES utilisateur ON DELETE RESTRICT
);

CREATE TABLE ligne_commande (
  id_commande        INT REFERENCES commande_fournisseur ON DELETE RESTRICT,
  id_produit         INT REFERENCES produit ON DELETE RESTRICT,
  quantite_commandee NUMERIC(12,3) NOT NULL CHECK (quantite_commandee > 0),
  prix_achat_prevu   NUMERIC(14,2) NOT NULL CHECK (prix_achat_prevu >= 0),
  PRIMARY KEY (id_commande, id_produit)
);

CREATE TABLE reception (
  id_reception   INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  date_reception DATE NOT NULL DEFAULT CURRENT_DATE,
  id_commande    INT NOT NULL REFERENCES commande_fournisseur ON DELETE RESTRICT,
  id_utilisateur INT NOT NULL REFERENCES utilisateur ON DELETE RESTRICT
);

CREATE TABLE ligne_reception (
  id_reception    INT REFERENCES reception ON DELETE RESTRICT,
  id_produit      INT REFERENCES produit ON DELETE RESTRICT,
  quantite_recue  NUMERIC(12,3) NOT NULL CHECK (quantite_recue > 0),
  prix_achat_reel NUMERIC(14,2) NOT NULL CHECK (prix_achat_reel >= 0),   -- RG04
  PRIMARY KEY (id_reception, id_produit)
);

-- ---------- Ventes et paiements ----------
CREATE TABLE vente (
  id_vente       INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  date_vente     TIMESTAMP NOT NULL DEFAULT now(),
  id_client      INT REFERENCES client ON DELETE RESTRICT,   -- NULL = vente comptant anonyme (RG10)
  id_utilisateur INT NOT NULL REFERENCES utilisateur ON DELETE RESTRICT
);

CREATE TABLE ligne_vente (
  id_vente      INT REFERENCES vente ON DELETE RESTRICT,
  id_produit    INT REFERENCES produit ON DELETE RESTRICT,
  quantite      NUMERIC(12,3) NOT NULL CHECK (quantite > 0),
  prix_unitaire NUMERIC(14,2) NOT NULL CHECK (prix_unitaire >= 0),     -- copie du prix du jour (RG07)
  PRIMARY KEY (id_vente, id_produit)
);

CREATE TABLE paiement (
  id_paiement    INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  id_vente       INT NOT NULL REFERENCES vente ON DELETE RESTRICT,
  date_paiement  TIMESTAMP NOT NULL DEFAULT now(),
  montant        NUMERIC(14,2) NOT NULL CHECK (montant > 0),
  mode_paiement  TEXT NOT NULL CHECK (mode_paiement IN ('especes','mobile_money','virement','carte')),
  id_utilisateur INT NOT NULL REFERENCES utilisateur ON DELETE RESTRICT
);

-- ---------- Journal de stock (quantité signée : + entrée, - sortie) ----------
CREATE TABLE mouvement_stock (
  id_mouvement   INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  id_produit     INT NOT NULL REFERENCES produit ON DELETE RESTRICT,
  type_mouvement TEXT NOT NULL CHECK (type_mouvement IN ('ENTREE_RECEPTION','SORTIE_VENTE','AJUSTEMENT')),
  quantite       NUMERIC(12,3) NOT NULL,
  date_mouvement TIMESTAMP NOT NULL DEFAULT now(),
  id_utilisateur INT NOT NULL REFERENCES utilisateur ON DELETE RESTRICT,
  id_vente       INT,
  id_reception   INT,
  motif          TEXT CHECK (motif IN ('perte','casse','erreur_comptage','autre')),
  -- clés étrangères composées : ignorées par PostgreSQL si une colonne est NULL (MATCH SIMPLE)
  FOREIGN KEY (id_vente, id_produit)     REFERENCES ligne_vente     ON DELETE RESTRICT,
  FOREIGN KEY (id_reception, id_produit) REFERENCES ligne_reception ON DELETE RESTRICT,
  -- cohérence du mouvement selon son type
  CHECK (
       (type_mouvement = 'ENTREE_RECEPTION' AND quantite > 0 AND id_reception IS NOT NULL AND id_vente IS NULL     AND motif IS NULL)
    OR (type_mouvement = 'SORTIE_VENTE'     AND quantite < 0 AND id_vente     IS NOT NULL AND id_reception IS NULL AND motif IS NULL)
    OR (type_mouvement = 'AJUSTEMENT'       AND quantite <> 0 AND id_vente IS NULL AND id_reception IS NULL AND motif IS NOT NULL)
  )
);

-- Une ligne de vente (ou de réception) ne génère qu'un seul mouvement
CREATE UNIQUE INDEX ux_mouvement_vente     ON mouvement_stock (id_vente, id_produit)     WHERE type_mouvement = 'SORTIE_VENTE';
CREATE UNIQUE INDEX ux_mouvement_reception ON mouvement_stock (id_reception, id_produit) WHERE type_mouvement = 'ENTREE_RECEPTION';

-- ---------- Index de performance (clés étrangères et recherches) ----------
CREATE INDEX ix_produit_categorie   ON produit (id_categorie);
CREATE INDEX ix_produit_nom         ON produit (lower(nom));
CREATE INDEX ix_commande_fourn      ON commande_fournisseur (id_fournisseur);
CREATE INDEX ix_reception_commande  ON reception (id_commande);
CREATE INDEX ix_vente_client        ON vente (id_client);
CREATE INDEX ix_vente_date          ON vente (date_vente);
CREATE INDEX ix_paiement_vente      ON paiement (id_vente);
CREATE INDEX ix_paiement_date       ON paiement (date_paiement);
CREATE INDEX ix_mouvement_produit   ON mouvement_stock (id_produit);
CREATE INDEX ix_mouvement_date      ON mouvement_stock (date_mouvement);

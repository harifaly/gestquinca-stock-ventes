-- =====================================================================
-- GestQuinca : vues calculées (aucun total, solde, statut ni stock n'est stocké)
-- =====================================================================

-- Stock courant = somme des mouvements ; sous_seuil = alerte de réapprovisionnement
CREATE VIEW v_stock AS
SELECT p.id_produit, p.sku, p.nom, p.unite, p.stock_minimum,
       COALESCE(SUM(m.quantite), 0)                         AS stock,
       COALESCE(SUM(m.quantite), 0) <= p.stock_minimum      AS sous_seuil
FROM produit p
LEFT JOIN mouvement_stock m ON m.id_produit = p.id_produit
GROUP BY p.id_produit;

-- Total d'une vente (RG09)
CREATE VIEW v_total_vente AS
SELECT id_vente, ROUND(SUM(quantite * prix_unitaire), 2) AS total
FROM ligne_vente
GROUP BY id_vente;

-- Solde et statut de paiement d'une vente (RG09)
CREATE VIEW v_solde_vente AS
WITH pay AS (
  SELECT id_vente, SUM(montant) AS total_paye FROM paiement GROUP BY id_vente
)
SELECT v.id_vente,
       COALESCE(t.total, 0)                                  AS total,
       COALESCE(pay.total_paye, 0)                           AS total_paye,
       COALESCE(t.total, 0) - COALESCE(pay.total_paye, 0)    AS solde,
       CASE WHEN COALESCE(pay.total_paye, 0) = 0                          THEN 'non_payee'
            WHEN COALESCE(pay.total_paye, 0) < COALESCE(t.total, 0)       THEN 'partiellement_payee'
            ELSE 'payee' END                                  AS statut_paiement
FROM vente v
LEFT JOIN v_total_vente t ON t.id_vente = v.id_vente
LEFT JOIN pay             ON pay.id_vente = v.id_vente;

-- Statut d'une commande fournisseur, déduit des réceptions (RG02, RG03)
CREATE VIEW v_statut_commande AS
WITH recu AS (
  SELECT lc.id_commande, lc.id_produit, lc.quantite_commandee,
         COALESCE(SUM(lr.quantite_recue), 0) AS recu
  FROM ligne_commande lc
  LEFT JOIN reception r        ON r.id_commande = lc.id_commande
  LEFT JOIN ligne_reception lr ON lr.id_reception = r.id_reception AND lr.id_produit = lc.id_produit
  GROUP BY lc.id_commande, lc.id_produit, lc.quantite_commandee
)
SELECT id_commande,
       CASE WHEN SUM(recu) = 0                       THEN 'en_cours'
            WHEN bool_and(recu >= quantite_commandee) THEN 'recue'
            ELSE 'partiellement_recue' END            AS statut
FROM recu
GROUP BY id_commande;

-- Créance (reste dû) de chaque client, pour le tableau de bord
CREATE VIEW v_creance_client AS
SELECT c.id_client, c.nom, COALESCE(SUM(s.solde), 0) AS creance
FROM client c
LEFT JOIN vente v ON v.id_client = c.id_client
LEFT JOIN v_solde_vente s ON s.id_vente = v.id_vente
GROUP BY c.id_client;

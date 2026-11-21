-- =====================================================================
-- GestQuinca : données d'exemple (démonstration et tests)
-- Toutes les valeurs sont inventées. Les identifiants numériques supposent
-- une base neuve (les séquences démarrent à 1).
-- Comptes de démonstration : admin / admin123 et vendeur / vendeur123
-- =====================================================================
CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- hachage bcrypt des mots de passe (RG14)

BEGIN;

-- ---------- Utilisateurs (1 = admin, 2 = vendeur) ----------
INSERT INTO utilisateur (nom_utilisateur, mot_de_passe_hash, nom_complet, role) VALUES
  ('admin',   crypt('admin123',   gen_salt('bf')), 'Administrateur GestQuinca', 'admin'),
  ('vendeur', crypt('vendeur123', gen_salt('bf')), 'Vendeur de démonstration',  'vendeur');

-- ---------- Catégories (1 à 6) ----------
INSERT INTO categorie (nom, description) VALUES
  ('Ciment et liants',       'Ciment, chaux, mortier'),
  ('Fer et acier',           'Fer à béton, fil de fer'),
  ('Plomberie',              'Tuyaux, robinetterie'),
  ('Outillage',              'Outils à main, quincaillerie'),
  ('Peinture',               'Peintures et accessoires'),
  ('Électricité',            'Câbles et protections');

-- ---------- Produits (1 à 14) ----------
INSERT INTO produit (sku, nom, unite, prix_achat, prix_vente, stock_minimum, id_categorie) VALUES
  ('CIM-001', 'Ciment CPJ 45, sac de 50 kg',        'sac',    24000,  27000,  20, 1),
  ('CIM-002', 'Chaux hydratée, sac de 25 kg',       'sac',    12000,  14500,  10, 1),
  ('FER-008', 'Fer à béton Ø8 mm, barre de 12 m',   'barre',   9000,  10500,  50, 2),
  ('FER-010', 'Fer à béton Ø10 mm, barre de 12 m',  'barre',  14000,  16000,  40, 2),
  ('FER-FIL', 'Fil de fer recuit',                  'kg',      4500,   5500,  25, 2),
  ('PLB-PVC', 'Tuyau PVC Ø32 mm, barre de 6 m',     'barre',   8000,   9800,  30, 3),
  ('PLB-ROB', 'Robinet laiton 1/2 pouce',           'piece',   6000,   8000,  15, 3),
  ('OUT-MAR', 'Marteau 500 g',                      'piece',   9000,  12000,   8, 4),
  ('OUT-SCI', 'Scie à métaux',                      'piece',   7000,   9500,   5, 4),
  ('PEI-BLC', 'Peinture acrylique blanche, seau 20 L','piece',85000,  98000,   6, 5),
  ('PEI-PIN', 'Pinceau plat 50 mm',                 'piece',   2000,   3000,  20, 5),
  ('ELE-CAB', 'Câble électrique 2,5 mm²',           'metre',   1200,   1700, 200, 6),
  ('ELE-DIS', 'Disjoncteur 16 A',                   'piece',   9000,  12500,  10, 6),
  ('OUT-CLO', 'Clous 100 mm',                       'kg',      6000,   7500,  15, 4);

-- ---------- Fournisseurs (1 à 3) et clients (1 à 4) ----------
INSERT INTO fournisseur (nom, telephone, adresse, email, contact) VALUES
  ('Comptoir du Ciment',          '034 00 000 01', 'Antananarivo', 'contact@comptoir-ciment.example', 'Mme Ravao'),
  ('Métal Distribution',          '034 00 000 02', 'Antananarivo', 'ventes@metal-distribution.example', 'M. Andry'),
  ('Outillage et Électricité OI', '034 00 000 03', 'Antsirabe',    'commandes@outillage-oi.example',    'M. Faly');

INSERT INTO client (nom, telephone, adresse) VALUES
  ('Rakoto Jean',          '032 00 000 11', 'Antananarivo'),
  ('Rabe Maçonnerie',      '032 00 000 12', 'Ambohimanarina'),
  ('Entreprise BTP Mada',  '032 00 000 13', 'Antananarivo'),
  ('Randria Hery',         '032 00 000 14', 'Antsirabe');

-- ---------- Commandes fournisseurs (1 à 4) ----------
INSERT INTO commande_fournisseur (date_commande, id_fournisseur, id_utilisateur) VALUES
  (CURRENT_DATE - 15, 1, 1),   -- 1 : ciment, reçue en 2 fois
  (CURRENT_DATE - 14, 2, 1),   -- 2 : fer et plomberie, reçue en une fois
  (CURRENT_DATE - 13, 3, 1),   -- 3 : outillage, peinture, électricité : partiellement reçue
  (CURRENT_DATE - 1,  1, 1);   -- 4 : ciment, en cours (aucune réception)

INSERT INTO ligne_commande (id_commande, id_produit, quantite_commandee, prix_achat_prevu) VALUES
  (1, 1, 100, 24000),
  (2, 3, 200,  9000), (2, 4, 100, 14000), (2, 5, 50, 4500), (2, 6, 80, 8000), (2, 7, 40, 6000),
  (3, 2,  30, 12000), (3, 8,  20,  9000), (3, 9, 10, 7000), (3, 10, 12, 85000),
  (3, 11, 40,  2000), (3, 12, 500, 1200), (3, 13, 30, 9000), (3, 14, 40, 6000),
  (4, 1, 200, 24000);

-- ---------- Réceptions (1 à 4) ----------
INSERT INTO reception (date_reception, id_commande, id_utilisateur) VALUES
  (CURRENT_DATE - 12, 1, 1),
  (CURRENT_DATE - 10, 1, 1),
  (CURRENT_DATE - 9,  2, 1),
  (CURRENT_DATE - 8,  3, 1);

INSERT INTO ligne_reception (id_reception, id_produit, quantite_recue, prix_achat_reel) VALUES
  (1, 1, 60, 24000),
  (2, 1, 40, 24500),                                   -- prix différent : le CMP du ciment devient 24 200
  (3, 3, 200, 9000), (3, 4, 100, 14000), (3, 5, 50, 4500), (3, 6, 80, 8000), (3, 7, 40, 6000),
  (4, 2, 30, 12000), (4, 8, 20, 9000), (4, 9, 10, 7000), (4, 10, 12, 85000), (4, 11, 40, 2000),
  (4, 12, 300, 1200), (4, 13, 30, 9000), (4, 14, 20, 6000);   -- 300 sur 500 câbles, 20 sur 40 clous

-- Entrées de stock correspondantes (dans l'ordre des dates, pour le calcul du CMP)
INSERT INTO mouvement_stock (id_produit, type_mouvement, quantite, date_mouvement, id_utilisateur, id_reception)
SELECT lr.id_produit, 'ENTREE_RECEPTION', lr.quantite_recue, r.date_reception + TIME '09:00', r.id_utilisateur, lr.id_reception
FROM ligne_reception lr
JOIN reception r ON r.id_reception = lr.id_reception
ORDER BY r.date_reception, lr.id_reception, lr.id_produit;

-- ---------- Ventes (1 à 7) : vendeur = utilisateur 2 ----------
INSERT INTO vente (date_vente, id_client, id_utilisateur) VALUES
  (now() - INTERVAL '5 days', 1,    2),   -- 1 : scénario de recette, vente à crédit
  (now() - INTERVAL '4 days', NULL, 2),   -- 2 : comptant anonyme
  (now() - INTERVAL '3 days', 2,    2),   -- 3 : artisan, paiement partiel
  (now() - INTERVAL '2 days', NULL, 2),   -- 4 : comptant anonyme
  (now() - INTERVAL '2 days', 3,    2),   -- 5 : entreprise, payée en 2 fois
  (now() - INTERVAL '1 day',  4,    2),   -- 6 : à crédit, aucun paiement
  (now(),                     NULL, 2);   -- 7 : comptant anonyme

INSERT INTO ligne_vente (id_vente, id_produit, quantite, prix_unitaire) VALUES
  (1, 1, 10, 27000),
  (2, 3, 10, 10500), (2, 5, 5, 5500),
  (3, 4, 20, 16000), (3, 3, 30, 10500), (3, 14, 5, 7500),
  (4, 8, 1, 12000),  (4, 11, 4, 3000),
  (5, 10, 6, 98000), (5, 12, 150, 1700),
  (6, 6, 30, 9800),  (6, 7, 10, 8000),
  (7, 13, 3, 12500);

-- Sorties de stock correspondantes
INSERT INTO mouvement_stock (id_produit, type_mouvement, quantite, date_mouvement, id_utilisateur, id_vente)
SELECT lv.id_produit, 'SORTIE_VENTE', -lv.quantite, v.date_vente, v.id_utilisateur, lv.id_vente
FROM ligne_vente lv
JOIN vente v ON v.id_vente = lv.id_vente
ORDER BY v.date_vente, lv.id_vente, lv.id_produit;

-- Un ajustement justifié : 2 pinceaux cassés
INSERT INTO mouvement_stock (id_produit, type_mouvement, quantite, date_mouvement, id_utilisateur, motif)
VALUES (11, 'AJUSTEMENT', -2, now() - INTERVAL '1 day', 1, 'casse');

-- ---------- Paiements ----------
INSERT INTO paiement (id_vente, date_paiement, montant, mode_paiement, id_utilisateur) VALUES
  (1, now() - INTERVAL '5 days', 100000, 'especes',      2),
  (1, now() - INTERVAL '2 days',  80000, 'mobile_money', 2),
  (2, now() - INTERVAL '4 days', 132500, 'especes',      2),
  (3, now() - INTERVAL '3 days', 400000, 'virement',     2),
  (4, now() - INTERVAL '2 days',  24000, 'especes',      2),
  (5, now() - INTERVAL '2 days', 500000, 'mobile_money', 2),
  (5, now() - INTERVAL '1 day',  343000, 'virement',     2),
  (7, now(),                      37500, 'especes',      2);

COMMIT;

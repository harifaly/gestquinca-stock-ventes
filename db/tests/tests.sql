-- =====================================================================
-- GestQuinca : tests automatiques de la base (à lancer APRÈS 04_seed.sql)
--   psql -U gestquinca -d gestquinca -v ON_ERROR_STOP=1 -f db/tests/tests.sql
-- Tout est exécuté dans une transaction annulée à la fin : la base reste intacte.
-- =====================================================================
BEGIN;
CREATE TEMP TABLE resultats (ordre SERIAL, test TEXT, ok BOOLEAN);

-- ---------- Valeurs attendues après le seed (scénario de recette) ----------
INSERT INTO resultats (test, ok)
SELECT 'Stock du ciment = 90 (100 reçus - 10 vendus)', stock = 90 FROM v_stock WHERE sku = 'CIM-001';
INSERT INTO resultats (test, ok)
SELECT 'Vente 1 : total 270 000, payé 180 000, reste 90 000, partiellement payée',
       total = 270000 AND total_paye = 180000 AND solde = 90000 AND statut_paiement = 'partiellement_payee'
FROM v_solde_vente WHERE id_vente = 1;
INSERT INTO resultats (test, ok)
SELECT 'CMP du ciment = 24 200 (60 à 24 000 puis 40 à 24 500)', cmp = 24200 FROM produit WHERE sku = 'CIM-001';
INSERT INTO resultats (test, ok)
SELECT 'Statuts des commandes : recue, recue, partiellement_recue, en_cours',
       (SELECT array_agg(statut ORDER BY id_commande) FROM v_statut_commande) = ARRAY['recue','recue','partiellement_recue','en_cours'];
INSERT INTO resultats (test, ok)
SELECT 'Statuts de paiement : 1 non payée, 2 partielles, 4 payées',
       (SELECT count(*) FROM v_solde_vente WHERE statut_paiement = 'non_payee') = 1
   AND (SELECT count(*) FROM v_solde_vente WHERE statut_paiement = 'partiellement_payee') = 2
   AND (SELECT count(*) FROM v_solde_vente WHERE statut_paiement = 'payee') = 4;
INSERT INTO resultats (test, ok)
SELECT 'Alertes de stock : câble (150 pour 200), clous (15 pour 15), peinture (6 pour 6)',
       (SELECT array_agg(sku ORDER BY sku) FROM v_stock WHERE sous_seuil) = ARRAY['ELE-CAB','OUT-CLO','PEI-BLC'];
INSERT INTO resultats (test, ok)
SELECT 'Créance totale des clients = 90 000 + 272 500 + 374 000', SUM(creance) = 736500 FROM v_creance_client;

-- ---------- Règles refusées par la base ----------
-- Chaque bloc doit échouer avec le bon code ; les erreurs sont absorbées par un sous-bloc.

-- RG03 : réception supérieure au reste à recevoir (câble : reste 200)
DO $$ BEGIN
  BEGIN
    INSERT INTO reception (id_commande, id_utilisateur) VALUES (3, 1);
    INSERT INTO ligne_reception VALUES (currval(pg_get_serial_sequence('reception','id_reception')), 12, 201, 1200);
    INSERT INTO resultats (test, ok) VALUES ('RG03 : réception de 201 pour un reste de 200 refusée', FALSE);
  EXCEPTION WHEN OTHERS THEN
    INSERT INTO resultats (test, ok) VALUES ('RG03 : réception de 201 pour un reste de 200 refusée', SQLERRM LIKE 'RG03%');
  END;
END $$;

-- RG03 : produit absent de la commande
DO $$ BEGIN
  BEGIN
    INSERT INTO reception (id_commande, id_utilisateur) VALUES (3, 1);
    INSERT INTO ligne_reception VALUES (currval(pg_get_serial_sequence('reception','id_reception')), 1, 5, 24000);
    INSERT INTO resultats (test, ok) VALUES ('RG03 : produit absent de la commande refusé', FALSE);
  EXCEPTION WHEN OTHERS THEN
    INSERT INTO resultats (test, ok) VALUES ('RG03 : produit absent de la commande refusé', SQLERRM LIKE 'RG03%');
  END;
END $$;

-- RG03 : le reste exact est accepté (200 câbles), puis la commande devient « recue » pour cette ligne
DO $$ BEGIN
  BEGIN
    INSERT INTO reception (id_commande, id_utilisateur) VALUES (3, 1);
    INSERT INTO ligne_reception VALUES (currval(pg_get_serial_sequence('reception','id_reception')), 12, 200, 1200);
    INSERT INTO resultats (test, ok) VALUES ('RG03 : réception du reste exact (200) acceptée', TRUE);
  EXCEPTION WHEN OTHERS THEN
    INSERT INTO resultats (test, ok) VALUES ('RG03 : réception du reste exact (200) acceptée', FALSE);
  END;
END $$;

-- RG06 : vente supérieure au stock (peinture : stock 6)
DO $$ BEGIN
  BEGIN
    INSERT INTO vente (id_client, id_utilisateur) VALUES (1, 2);
    INSERT INTO ligne_vente VALUES (currval(pg_get_serial_sequence('vente','id_vente')), 10, 7, 98000);
    INSERT INTO mouvement_stock (id_produit, type_mouvement, quantite, id_utilisateur, id_vente)
      VALUES (10, 'SORTIE_VENTE', -7, 2, currval(pg_get_serial_sequence('vente','id_vente')));
    INSERT INTO resultats (test, ok) VALUES ('RG06 : vente de 7 pour un stock de 6 refusée', FALSE);
  EXCEPTION WHEN OTHERS THEN
    INSERT INTO resultats (test, ok) VALUES ('RG06 : vente de 7 pour un stock de 6 refusée', SQLERRM LIKE 'RG06%');
  END;
END $$;

-- RG06 : un ajustement négatif ne peut pas rendre le stock négatif
DO $$ BEGIN
  BEGIN
    INSERT INTO mouvement_stock (id_produit, type_mouvement, quantite, id_utilisateur, motif)
      VALUES (10, 'AJUSTEMENT', -7, 1, 'perte');
    INSERT INTO resultats (test, ok) VALUES ('RG06 : ajustement de -7 pour un stock de 6 refusé', FALSE);
  EXCEPTION WHEN OTHERS THEN
    INSERT INTO resultats (test, ok) VALUES ('RG06 : ajustement de -7 pour un stock de 6 refusé', SQLERRM LIKE 'RG06%');
  END;
END $$;

-- Sortie de stock différente de la quantité vendue
DO $$ BEGIN
  BEGIN
    INSERT INTO vente (id_client, id_utilisateur) VALUES (1, 2);
    INSERT INTO ligne_vente VALUES (currval(pg_get_serial_sequence('vente','id_vente')), 10, 2, 98000);
    INSERT INTO mouvement_stock (id_produit, type_mouvement, quantite, id_utilisateur, id_vente)
      VALUES (10, 'SORTIE_VENTE', -1, 2, currval(pg_get_serial_sequence('vente','id_vente')));
    INSERT INTO resultats (test, ok) VALUES ('Sortie de stock différente de la quantité vendue refusée', FALSE);
  EXCEPTION WHEN OTHERS THEN
    INSERT INTO resultats (test, ok) VALUES ('Sortie de stock différente de la quantité vendue refusée', SQLERRM LIKE '%doit être égale%');
  END;
END $$;

-- RG08 : paiement supérieur au reste à payer (vente 1 : reste 90 000)
DO $$ BEGIN
  BEGIN
    INSERT INTO paiement (id_vente, montant, mode_paiement, id_utilisateur) VALUES (1, 90001, 'especes', 2);
    INSERT INTO resultats (test, ok) VALUES ('RG08 : paiement de 90 001 pour un reste de 90 000 refusé', FALSE);
  EXCEPTION WHEN OTHERS THEN
    INSERT INTO resultats (test, ok) VALUES ('RG08 : paiement de 90 001 pour un reste de 90 000 refusé', SQLERRM LIKE 'RG08%');
  END;
END $$;

-- RG08 : le solde exact est accepté et la vente devient payée
DO $$ BEGIN
  INSERT INTO paiement (id_vente, montant, mode_paiement, id_utilisateur) VALUES (1, 90000, 'especes', 2);
  INSERT INTO resultats (test, ok)
    SELECT 'RG08 : paiement du solde exact (90 000) accepté, vente payée', statut_paiement = 'payee' AND solde = 0
    FROM v_solde_vente WHERE id_vente = 1;
END $$;

-- RG10 : vente anonyme non soldée refusée à la fin de la transaction
DO $$ BEGIN
  BEGIN
    INSERT INTO vente (id_client, id_utilisateur) VALUES (NULL, 2);
    INSERT INTO ligne_vente VALUES (currval(pg_get_serial_sequence('vente','id_vente')), 13, 1, 12500);
    SET CONSTRAINTS ALL IMMEDIATE;
    INSERT INTO resultats (test, ok) VALUES ('RG10 : vente anonyme non soldée refusée', FALSE);
  EXCEPTION WHEN OTHERS THEN
    INSERT INTO resultats (test, ok) VALUES ('RG10 : vente anonyme non soldée refusée', SQLERRM LIKE 'RG10%');
  END;
END $$;

-- RG11 : mouvements immuables (modification, suppression, vidage)
DO $$ BEGIN
  BEGIN UPDATE mouvement_stock SET quantite = 1 WHERE id_mouvement = 1;
    INSERT INTO resultats (test, ok) VALUES ('RG11 : modification d''un mouvement refusée', FALSE);
  EXCEPTION WHEN OTHERS THEN
    INSERT INTO resultats (test, ok) VALUES ('RG11 : modification d''un mouvement refusée', SQLERRM LIKE 'RG11%');
  END;
  BEGIN DELETE FROM mouvement_stock WHERE id_mouvement = 1;
    INSERT INTO resultats (test, ok) VALUES ('RG11 : suppression d''un mouvement refusée', FALSE);
  EXCEPTION WHEN OTHERS THEN
    INSERT INTO resultats (test, ok) VALUES ('RG11 : suppression d''un mouvement refusée', SQLERRM LIKE 'RG11%');
  END;
  BEGIN TRUNCATE mouvement_stock;
    INSERT INTO resultats (test, ok) VALUES ('RG11 : vidage du journal de stock refusé', FALSE);
  EXCEPTION WHEN OTHERS THEN
    INSERT INTO resultats (test, ok) VALUES ('RG11 : vidage du journal de stock refusé', SQLERRM LIKE 'RG11%');
  END;
END $$;

-- RG01 : SKU unique
DO $$ BEGIN
  BEGIN
    INSERT INTO produit (sku, nom, unite, prix_achat, prix_vente, id_categorie) VALUES ('CIM-001', 'Doublon', 'sac', 1, 1, 1);
    INSERT INTO resultats (test, ok) VALUES ('RG01 : SKU en double refusé', FALSE);
  EXCEPTION WHEN unique_violation THEN
    INSERT INTO resultats (test, ok) VALUES ('RG01 : SKU en double refusé', TRUE);
  END;
END $$;

-- Intégrité référentielle : un produit utilisé ne peut pas être supprimé
DO $$ BEGIN
  BEGIN
    DELETE FROM produit WHERE sku = 'CIM-001';
    INSERT INTO resultats (test, ok) VALUES ('Suppression d''un produit utilisé refusée (désactivation seulement)', FALSE);
  EXCEPTION WHEN foreign_key_violation OR restrict_violation THEN   -- le code d'erreur dépend de la version de PostgreSQL
    INSERT INTO resultats (test, ok) VALUES ('Suppression d''un produit utilisé refusée (désactivation seulement)', TRUE);
  END;
END $$;

-- Mouvement pointant vers une ligne de vente inexistante
DO $$ BEGIN
  BEGIN
    INSERT INTO mouvement_stock (id_produit, type_mouvement, quantite, id_utilisateur, id_vente)
      VALUES (1, 'SORTIE_VENTE', -1, 2, 999);
    INSERT INTO resultats (test, ok) VALUES ('Mouvement vers une ligne de vente inexistante refusé', FALSE);
  EXCEPTION WHEN foreign_key_violation THEN
    INSERT INTO resultats (test, ok) VALUES ('Mouvement vers une ligne de vente inexistante refusé', TRUE);
  END;
END $$;

-- Mouvement incohérent avec son type
DO $$ BEGIN
  BEGIN
    INSERT INTO mouvement_stock (id_produit, type_mouvement, quantite, id_utilisateur, motif)
      VALUES (1, 'SORTIE_VENTE', -1, 2, 'casse');
    INSERT INTO resultats (test, ok) VALUES ('Mouvement de vente avec un motif refusé (CHECK)', FALSE);
  EXCEPTION WHEN check_violation THEN
    INSERT INTO resultats (test, ok) VALUES ('Mouvement de vente avec un motif refusé (CHECK)', TRUE);
  END;
END $$;

-- ---------- Bilan ----------
SELECT ordre, CASE WHEN ok THEN 'OK    ' ELSE 'ÉCHEC ' END AS statut, test FROM resultats ORDER BY ordre;

DO $$
DECLARE v_echecs INT; v_total INT;
BEGIN
  SELECT count(*) FILTER (WHERE NOT ok), count(*) INTO v_echecs, v_total FROM resultats;
  RAISE NOTICE '% tests, % échec(s)', v_total, v_echecs;
  IF v_echecs > 0 THEN RAISE EXCEPTION '% test(s) en échec', v_echecs; END IF;
END $$;

ROLLBACK;

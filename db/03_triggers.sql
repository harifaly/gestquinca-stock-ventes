-- =====================================================================
-- GestQuinca : règles de gestion garanties par la base (triggers)
-- Les messages commencent par le code de la règle (RGxx) pour que l'API
-- puisse les reconnaître et afficher une erreur compréhensible.
-- =====================================================================

-- ---------------------------------------------------------------------
-- RG03 : une réception ne dépasse pas le reste à recevoir, et le produit
--        reçu doit figurer dans la commande de la réception.
-- ---------------------------------------------------------------------
CREATE FUNCTION fn_verifier_ligne_reception() RETURNS trigger AS $$
DECLARE
  v_commande INT;
  v_commande_qte NUMERIC;
  v_deja_recu NUMERIC;
BEGIN
  SELECT id_commande INTO v_commande FROM reception WHERE id_reception = NEW.id_reception;
  IF NOT FOUND THEN
    RETURN NEW;                      -- la clé étrangère signalera l'erreur
  END IF;

  -- verrou sur la ligne de commande pour éviter deux réceptions simultanées
  SELECT quantite_commandee INTO v_commande_qte
  FROM ligne_commande
  WHERE id_commande = v_commande AND id_produit = NEW.id_produit
  FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'RG03 : le produit % ne figure pas dans la commande %', NEW.id_produit, v_commande;
  END IF;

  SELECT COALESCE(SUM(lr.quantite_recue), 0) INTO v_deja_recu
  FROM ligne_reception lr
  JOIN reception r ON r.id_reception = lr.id_reception
  WHERE r.id_commande = v_commande
    AND lr.id_produit = NEW.id_produit
    AND NOT (lr.id_reception = NEW.id_reception);

  IF v_deja_recu + NEW.quantite_recue > v_commande_qte THEN
    RAISE EXCEPTION 'RG03 : quantité reçue (%) supérieure au reste à recevoir (%) pour le produit % de la commande %',
      NEW.quantite_recue, v_commande_qte - v_deja_recu, NEW.id_produit, v_commande;
  END IF;
  RETURN NEW;
END $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_ligne_reception_verif
  BEFORE INSERT OR UPDATE ON ligne_reception
  FOR EACH ROW EXECUTE FUNCTION fn_verifier_ligne_reception();

-- ---------------------------------------------------------------------
-- Mouvements de stock : une seule fonction pour
--   RG06  stock jamais négatif (le produit est verrouillé pendant la vérification)
--   RG04/RG05  entrée de réception : quantité identique à la ligne reçue,
--              et recalcul du coût moyen pondéré (CMP)
--   cohérence d'une sortie de vente avec sa ligne de vente
-- ---------------------------------------------------------------------
CREATE FUNCTION fn_mouvement_avant_insertion() RETURNS trigger AS $$
DECLARE
  v_stock NUMERIC;
  v_cmp   NUMERIC;
  v_qte   NUMERIC;
  v_prix  NUMERIC;
BEGIN
  SELECT cmp INTO v_cmp FROM produit WHERE id_produit = NEW.id_produit FOR UPDATE;
  IF NOT FOUND THEN
    RETURN NEW;                      -- la clé étrangère signalera l'erreur
  END IF;

  SELECT COALESCE(SUM(quantite), 0) INTO v_stock
  FROM mouvement_stock WHERE id_produit = NEW.id_produit;

  IF v_stock + NEW.quantite < 0 THEN
    RAISE EXCEPTION 'RG06 : stock insuffisant pour le produit % (disponible : %, demandé : %)',
      NEW.id_produit, v_stock, -NEW.quantite;
  END IF;

  IF NEW.type_mouvement = 'SORTIE_VENTE' THEN
    SELECT quantite INTO v_qte FROM ligne_vente
    WHERE id_vente = NEW.id_vente AND id_produit = NEW.id_produit;
    IF FOUND AND NEW.quantite <> -v_qte THEN
      RAISE EXCEPTION 'La sortie de stock (%) doit être égale à la quantité vendue (%)', -NEW.quantite, v_qte;
    END IF;

  ELSIF NEW.type_mouvement = 'ENTREE_RECEPTION' THEN
    SELECT quantite_recue, prix_achat_reel INTO v_qte, v_prix FROM ligne_reception
    WHERE id_reception = NEW.id_reception AND id_produit = NEW.id_produit;
    IF FOUND THEN
      IF NEW.quantite <> v_qte THEN
        RAISE EXCEPTION 'L''entrée de stock (%) doit être égale à la quantité reçue (%)', NEW.quantite, v_qte;
      END IF;
      -- RG05 : CMP = (stock x CMP actuel + quantité reçue x prix reçu) / (stock + quantité reçue)
      UPDATE produit
      SET cmp = ROUND((v_stock * v_cmp + NEW.quantite * v_prix) / (v_stock + NEW.quantite), 2)
      WHERE id_produit = NEW.id_produit;
    END IF;
  END IF;
  RETURN NEW;
END $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_mouvement_avant_insertion
  BEFORE INSERT ON mouvement_stock
  FOR EACH ROW EXECUTE FUNCTION fn_mouvement_avant_insertion();

-- ---------------------------------------------------------------------
-- RG11 : les mouvements de stock ne sont jamais modifiés ni supprimés
-- ---------------------------------------------------------------------
CREATE FUNCTION fn_mouvement_immuable() RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'RG11 : les mouvements de stock sont immuables ; une correction crée un nouveau mouvement (ajustement)';
END $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_mouvement_immuable
  BEFORE UPDATE OR DELETE ON mouvement_stock
  FOR EACH ROW EXECUTE FUNCTION fn_mouvement_immuable();
CREATE TRIGGER trg_mouvement_non_vide
  BEFORE TRUNCATE ON mouvement_stock
  FOR EACH STATEMENT EXECUTE FUNCTION fn_mouvement_immuable();

-- ---------------------------------------------------------------------
-- RG08 : le total payé ne dépasse pas le total de la vente
-- ---------------------------------------------------------------------
CREATE FUNCTION fn_paiement_avant_insertion() RETURNS trigger AS $$
DECLARE
  v_total NUMERIC;
  v_paye  NUMERIC;
BEGIN
  PERFORM 1 FROM vente WHERE id_vente = NEW.id_vente FOR UPDATE;   -- sérialise les paiements d'une même vente
  IF NOT FOUND THEN
    RETURN NEW;                      -- la clé étrangère signalera l'erreur
  END IF;

  SELECT COALESCE(ROUND(SUM(quantite * prix_unitaire), 2), 0) INTO v_total
  FROM ligne_vente WHERE id_vente = NEW.id_vente;
  SELECT COALESCE(SUM(montant), 0) INTO v_paye
  FROM paiement WHERE id_vente = NEW.id_vente;

  IF v_paye + NEW.montant > v_total THEN
    RAISE EXCEPTION 'RG08 : le paiement (%) dépasse le reste à payer de la vente %, soit %',
      NEW.montant, NEW.id_vente, v_total - v_paye;
  END IF;
  RETURN NEW;
END $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_paiement_avant_insertion
  BEFORE INSERT ON paiement
  FOR EACH ROW EXECUTE FUNCTION fn_paiement_avant_insertion();

-- ---------------------------------------------------------------------
-- RG10 : une vente non soldée doit être rattachée à un client enregistré.
-- Vérifié en fin de transaction (le trigger est différé) : l'API crée la
-- vente, ses lignes et ses paiements dans la même transaction.
-- ---------------------------------------------------------------------
CREATE FUNCTION fn_vente_credit_exige_client() RETURNS trigger AS $$
DECLARE
  v_client INT;
  v_solde  NUMERIC;
BEGIN
  SELECT id_client INTO v_client FROM vente WHERE id_vente = NEW.id_vente;
  IF FOUND AND v_client IS NULL THEN
    SELECT solde INTO v_solde FROM v_solde_vente WHERE id_vente = NEW.id_vente;
    IF COALESCE(v_solde, 0) > 0 THEN
      RAISE EXCEPTION 'RG10 : la vente % n''est pas soldée (reste %) : un client enregistré est obligatoire',
        NEW.id_vente, v_solde;
    END IF;
  END IF;
  RETURN NULL;
END $$ LANGUAGE plpgsql;

CREATE CONSTRAINT TRIGGER trg_vente_client_credit
  AFTER INSERT OR UPDATE ON vente
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION fn_vente_credit_exige_client();
CREATE CONSTRAINT TRIGGER trg_ligne_vente_client_credit
  AFTER INSERT OR UPDATE ON ligne_vente
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION fn_vente_credit_exige_client();
CREATE CONSTRAINT TRIGGER trg_paiement_client_credit
  AFTER INSERT ON paiement
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION fn_vente_credit_exige_client();

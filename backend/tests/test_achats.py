"""Tests fournisseurs, commandes, réceptions : scénario de recette du cahier des charges."""
import pytest

from app.db import pool


def _produit(client, headers, sku):
    return client.get("/produits", params={"q": sku}, headers=headers).json()["items"][0]


def test_achats_reserves_a_ladministrateur(client, vendeur):
    assert client.get("/fournisseurs", headers=vendeur).status_code == 403
    assert client.get("/commandes", headers=vendeur).status_code == 403
    assert client.post("/commandes", headers=vendeur, json={}).status_code in (403, 422)


def test_fournisseur_crud(client, admin):
    r = client.post("/fournisseurs", headers=admin, json={"nom": "TEST fournisseur", "contact": "M. Test"})
    assert r.status_code == 201
    idf = r.json()["id_fournisseur"]
    assert client.put(f"/fournisseurs/{idf}", headers=admin, json={"nom": "TEST fournisseur 2"}).json()["nom"] == "TEST fournisseur 2"
    assert client.get("/fournisseurs", params={"q": "TEST fournisseur"}, headers=admin).json()["total"] >= 1
    with pool.connection() as conn:
        conn.execute("DELETE FROM fournisseur WHERE nom LIKE 'TEST fournisseur%'")


def test_commande_n_a_aucun_effet_sur_le_stock_puis_receptions(client, admin):
    p = _produit(client, admin, "CIM-001")
    fournisseur = client.get("/fournisseurs", headers=admin).json()["items"][0]
    stock0 = p["stock"]
    r = client.post("/commandes", headers=admin, json={
        "id_fournisseur": fournisseur["id_fournisseur"],
        "lignes": [{"id_produit": p["id_produit"], "quantite_commandee": "100", "prix_achat_prevu": "24000"}]})
    assert r.status_code == 201, r.text
    cmd = r.json()
    assert cmd["statut"] == "en_cours"
    assert _produit(client, admin, "CIM-001")["stock"] == stock0            # RG02

    url = f"/commandes/{cmd['id_commande']}/receptions"
    # plus que la commande : refusé (RG03) et rien n'est enregistré
    r = client.post(url, headers=admin, json={"lignes": [
        {"id_produit": p["id_produit"], "quantite_recue": "101", "prix_achat_reel": "24000"}]})
    assert r.status_code == 409 and "RG03" in r.json()["detail"]
    assert _produit(client, admin, "CIM-001")["stock"] == stock0

    r = client.post(url, headers=admin, json={"lignes": [
        {"id_produit": p["id_produit"], "quantite_recue": "60", "prix_achat_reel": "24000"}]})
    assert r.status_code == 201 and r.json()["statut"] == "partiellement_recue"
    assert _produit(client, admin, "CIM-001")["stock"] == stock0 + 60

    r = client.post(url, headers=admin, json={"lignes": [
        {"id_produit": p["id_produit"], "quantite_recue": "40", "prix_achat_reel": "26000"}]})
    assert r.status_code == 201 and r.json()["statut"] == "recue"
    assert r.json()["lignes"][0]["reste"] == 0 and len(r.json()["receptions"]) == 2
    nouveau = _produit(client, admin, "CIM-001")
    assert nouveau["stock"] == stock0 + 100
    assert nouveau["cmp"] != p["cmp"]                                       # RG05

    # une commande entièrement reçue n'accepte plus rien
    r = client.post(url, headers=admin, json={"lignes": [
        {"id_produit": p["id_produit"], "quantite_recue": "1", "prix_achat_reel": "24000"}]})
    assert r.status_code == 409


def test_produit_hors_commande_et_doublons(client, admin):
    p, q = _produit(client, admin, "CIM-001"), _produit(client, admin, "CIM-002")
    f = client.get("/fournisseurs", headers=admin).json()["items"][0]["id_fournisseur"]
    ligne = {"id_produit": p["id_produit"], "quantite_commandee": "5", "prix_achat_prevu": "100"}
    assert client.post("/commandes", headers=admin, json={"id_fournisseur": f, "lignes": [ligne, ligne]}).status_code == 422
    assert client.post("/commandes", headers=admin, json={"id_fournisseur": 99999, "lignes": [ligne]}).status_code == 409
    cmd = client.post("/commandes", headers=admin, json={"id_fournisseur": f, "lignes": [ligne]}).json()
    r = client.post(f"/commandes/{cmd['id_commande']}/receptions", headers=admin, json={"lignes": [
        {"id_produit": q["id_produit"], "quantite_recue": "1", "prix_achat_reel": "100"}]})
    assert r.status_code == 409 and "RG03" in r.json()["detail"]
    assert client.get("/commandes/999999", headers=admin).status_code == 404

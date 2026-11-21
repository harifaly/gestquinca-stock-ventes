"""Tests clients, ventes, paiements (base réelle, nettoyage via transaction impossible : on compte les écarts)."""
import pytest

from app.db import pool


def _produit(client, headers, sku):
    r = client.get("/produits", params={"q": sku}, headers=headers)
    return r.json()["items"][0]


def test_vendeur_cree_client_mais_ne_modifie_pas(client, vendeur, admin):
    r = client.post("/clients", json={"nom": "TEST client", "telephone": "0340000000"}, headers=vendeur)
    assert r.status_code == 201
    idc = r.json()["id_client"]
    assert client.put(f"/clients/{idc}", json={"nom": "X"}, headers=vendeur).status_code == 403
    assert client.put(f"/clients/{idc}", json={"nom": "TEST client 2"}, headers=admin).status_code == 200
    assert client.get("/clients", params={"q": "TEST client"}, headers=vendeur).json()["total"] >= 1
    with pool.connection() as conn:
        conn.execute("DELETE FROM client WHERE nom LIKE 'TEST client%'")


def test_vente_comptant_baisse_le_stock(client, vendeur):
    p = _produit(client, vendeur, "CIM-001")
    r = client.post("/ventes", headers=vendeur, json={
        "lignes": [{"id_produit": p["id_produit"], "quantite": "2"}],
        "paiement": {"montant": p["prix_vente"] * 2, "mode_paiement": "especes"}})
    assert r.status_code == 201, r.text
    v = r.json()
    assert v["statut_paiement"] == "payee" and v["solde"] == 0
    assert v["lignes"][0]["prix_unitaire"] == p["prix_vente"]
    assert _produit(client, vendeur, "CIM-001")["stock"] == p["stock"] - 2


def test_stock_insuffisant_annule_tout(client, vendeur):
    p = _produit(client, vendeur, "CIM-001")
    with pool.connection() as conn:
        avant = conn.execute("SELECT count(*) AS n FROM vente").fetchone()["n"]
    r = client.post("/ventes", headers=vendeur, json={
        "lignes": [{"id_produit": p["id_produit"], "quantite": "999999"}]})
    assert r.status_code == 409 and "RG06" in r.json()["detail"]
    with pool.connection() as conn:
        assert conn.execute("SELECT count(*) AS n FROM vente").fetchone()["n"] == avant


def test_credit_sans_client_refuse(client, vendeur):
    p = _produit(client, vendeur, "CIM-001")
    r = client.post("/ventes", headers=vendeur, json={"lignes": [{"id_produit": p["id_produit"], "quantite": "1"}]})
    assert r.status_code == 409 and "RG10" in r.json()["detail"]


def test_credit_puis_paiements_et_trop_percu(client, vendeur):
    p = _produit(client, vendeur, "CIM-001")
    cl = client.get("/clients", headers=vendeur).json()["items"][0]
    r = client.post("/ventes", headers=vendeur, json={
        "id_client": cl["id_client"], "lignes": [{"id_produit": p["id_produit"], "quantite": "1"}]})
    assert r.status_code == 201, r.text
    v = r.json()
    assert v["statut_paiement"] == "non_payee"
    r2 = client.post(f"/ventes/{v['id_vente']}/paiements", headers=vendeur,
                     json={"montant": v["total"] + 1, "mode_paiement": "especes"})
    assert r2.status_code == 409 and "RG08" in r2.json()["detail"]
    r3 = client.post(f"/ventes/{v['id_vente']}/paiements", headers=vendeur,
                     json={"montant": 1000, "mode_paiement": "mobile_money"})
    assert r3.status_code == 201 and r3.json()["statut_paiement"] == "partiellement_payee"


def test_produit_en_double_et_inconnu(client, vendeur):
    p = _produit(client, vendeur, "CIM-001")
    l = {"id_produit": p["id_produit"], "quantite": "1"}
    assert client.post("/ventes", headers=vendeur, json={"lignes": [l, l]}).status_code == 422
    assert client.post("/ventes", headers=vendeur, json={"lignes": [{"id_produit": 99999, "quantite": "1"}]}).status_code == 422
    assert client.post("/ventes", headers=vendeur, json={"lignes": []}).status_code == 422

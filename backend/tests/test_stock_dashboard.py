"""Tests stock (mouvements, ajustements) et tableau de bord."""
from app.db import pool


def _produit(client, headers, sku):
    return client.get("/produits", params={"q": sku}, headers=headers).json()["items"][0]


def test_tableau_de_bord_reserve_a_ladmin(client, vendeur):
    assert client.get("/dashboard", headers=vendeur).status_code == 403


def test_tableau_de_bord_coherent_avec_la_base(client, admin):
    r = client.get("/dashboard", params={"periode": "mois"}, headers=admin)
    assert r.status_code == 200
    d = r.json()
    with pool.connection() as conn:
        attendu = conn.execute("SELECT COALESCE(SUM(creance),0)::float8 AS s FROM v_creance_client").fetchone()["s"]
        sous_seuil = conn.execute(
            "SELECT count(*) AS n FROM v_stock s JOIN produit p USING (id_produit) WHERE s.sous_seuil AND p.actif"
        ).fetchone()["n"]
    assert d["creances_total"] == attendu
    assert len(d["produits_a_reapprovisionner"]) == sous_seuil
    assert len(d["meilleurs_produits"]) <= 5
    assert d["valeur_stock"] > 0 and d["marge_brute"] is not None
    assert client.get("/dashboard", params={"periode": "annee"}, headers=admin).status_code == 422


def test_ajustement_justifie_et_historique(client, admin, vendeur):
    p = _produit(client, admin, "CIM-001")
    corps = {"id_produit": p["id_produit"], "quantite": "-3", "motif": "perte"}
    assert client.post("/stock/ajustements", headers=vendeur, json=corps).status_code == 403
    r = client.post("/stock/ajustements", headers=admin, json=corps)
    assert r.status_code == 201 and r.json()["motif"] == "perte" and r.json()["quantite"] == -3
    assert _produit(client, admin, "CIM-001")["stock"] == p["stock"] - 3
    h = client.get("/stock/mouvements", params={"id_produit": p["id_produit"], "type_mouvement": "AJUSTEMENT"}, headers=vendeur)
    assert h.status_code == 200 and h.json()["items"][0]["id_mouvement"] == r.json()["id_mouvement"]
    # correction = nouveau mouvement (RG11)
    client.post("/stock/ajustements", headers=admin, json={**corps, "quantite": "3", "motif": "erreur_comptage"})
    assert _produit(client, admin, "CIM-001")["stock"] == p["stock"]


def test_ajustement_invalide(client, admin):
    p = _produit(client, admin, "CIM-001")
    base = {"id_produit": p["id_produit"], "motif": "casse"}
    assert client.post("/stock/ajustements", headers=admin, json={**base, "quantite": "0"}).status_code == 422
    assert client.post("/stock/ajustements", headers=admin, json={**base, "quantite": "1", "motif": "vol"}).status_code == 422
    r = client.post("/stock/ajustements", headers=admin, json={**base, "quantite": "-999999"})
    assert r.status_code == 409 and "RG06" in r.json()["detail"]

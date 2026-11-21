"""Suppression : possible pour ce qui n'a jamais servi, refusée (409) dès qu'il existe un historique."""
from app.db import pool

from .conftest import NOUVEAU_PRODUIT


def _un(requete):
    with pool.connection() as conn:
        return conn.execute(requete).fetchone()["n"]


def test_categorie_vide_supprimable_et_categorie_utilisee_refusee(client, admin, vendeur):
    cree = client.post("/categories", json={"nom": "Catégorie de test", "description": None}, headers=admin).json()
    url = f"/categories/{cree['id_categorie']}"
    assert client.delete(url, headers=vendeur).status_code == 403
    assert client.delete(url, headers=admin).status_code == 204
    assert client.delete(url, headers=admin).status_code == 404
    r = client.delete("/categories/1", headers=admin)                 # catégorie utilisée par des produits
    assert r.status_code == 409 and "produit" in r.json()["detail"]


def test_client_sans_vente_supprimable_et_client_avec_ventes_refuse(client, admin, vendeur):
    cree = client.post("/clients", json={"nom": "Client de test", "telephone": None, "adresse": None}, headers=admin).json()
    url = f"/clients/{cree['id_client']}"
    assert client.delete(url, headers=vendeur).status_code == 403
    assert client.delete(url, headers=admin).status_code == 204
    assert client.delete(url, headers=admin).status_code == 404
    avec_ventes = _un("SELECT min(id_client) AS n FROM vente WHERE id_client IS NOT NULL")
    r = client.delete(f"/clients/{avec_ventes}", headers=admin)
    assert r.status_code == 409 and "vente" in r.json()["detail"]


def test_fournisseur_sans_commande_supprimable_et_fournisseur_avec_commandes_refuse(client, admin, vendeur):
    cree = client.post("/fournisseurs", json={"nom": "Fournisseur de test"}, headers=admin).json()
    url = f"/fournisseurs/{cree['id_fournisseur']}"
    assert client.delete(url, headers=vendeur).status_code == 403
    assert client.delete(url, headers=admin).status_code == 204
    assert client.delete(url, headers=admin).status_code == 404
    avec_commandes = _un("SELECT min(id_fournisseur) AS n FROM commande_fournisseur")
    r = client.delete(f"/fournisseurs/{avec_commandes}", headers=admin)
    assert r.status_code == 409 and "commande" in r.json()["detail"]


def test_produit_jamais_utilise_supprimable_et_produit_avec_historique_refuse(client, admin, vendeur, produit_a_nettoyer):
    cree = client.post("/produits", json=NOUVEAU_PRODUIT, headers=admin).json()
    url = f"/produits/{cree['id_produit']}"
    assert client.delete(url, headers=vendeur).status_code == 403
    assert client.delete(url, headers=admin).status_code == 204
    assert client.get(url, headers=admin).status_code == 404
    assert client.delete(url, headers=admin).status_code == 404

    ciment = client.get("/produits", params={"q": "CIM-001"}, headers=admin).json()["items"][0]
    r = client.delete(f"/produits/{ciment['id_produit']}", headers=admin)
    assert r.status_code == 409 and "Désactivez" in r.json()["detail"]
    assert client.get(f"/produits/{ciment['id_produit']}", headers=admin).status_code == 200     # toujours là

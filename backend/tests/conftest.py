"""Tests de l'API sur la vraie base PostgreSQL (celle de DATABASE_URL, avec les données de 04_seed.sql).

Ils ne modifient pas les données d'exemple : les produits créés par les tests sont supprimés ensuite.
Lancer depuis le dossier backend :  pytest -v
"""
import pytest
from fastapi.testclient import TestClient

from app.db import pool
from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:      # démarre l'application (ouvre la connexion à la base)
        yield c


def _entetes(client, identifiant, mot_de_passe):
    reponse = client.post("/auth/login", data={"username": identifiant, "password": mot_de_passe})
    assert reponse.status_code == 200, reponse.text
    return {"Authorization": f"Bearer {reponse.json()['access_token']}"}


@pytest.fixture(scope="session")
def admin(client):
    return _entetes(client, "admin", "admin123")


@pytest.fixture(scope="session")
def vendeur(client):
    return _entetes(client, "vendeur", "vendeur123")


NOUVEAU_PRODUIT = {
    "sku": "TEST-001", "nom": "Produit de test", "marque": "Test", "unite": "piece",
    "prix_achat": "1000", "prix_vente": "1500", "stock_minimum": "5", "id_categorie": 1,
}


@pytest.fixture
def produit_a_nettoyer():
    """Supprime après le test les produits de test (jamais utilisés, donc supprimables)."""
    yield
    with pool.connection() as conn:
        conn.execute("DELETE FROM produit WHERE sku LIKE 'TEST-%'")


@pytest.fixture(scope="module", autouse=True)
def nettoyer_ventes_de_test(client):
    """Les tests de vente et d achat modifient le stock : à la fin de chaque fichier de tests, on supprime ce qu ils ont créé.
    Les mouvements sont normalement immuables (RG11) ; ce nettoyage de test désactive
    temporairement ce trigger (réservé au propriétaire de la base)."""
    with pool.connection() as conn:
        base = conn.execute("SELECT COALESCE(max(id_vente), 0) AS m FROM vente").fetchone()["m"]
        base_cmd = conn.execute("SELECT COALESCE(max(id_commande), 0) AS m FROM commande_fournisseur").fetchone()["m"]
        base_rec = conn.execute("SELECT COALESCE(max(id_reception), 0) AS m FROM reception").fetchone()["m"]
        base_mvt = conn.execute("SELECT COALESCE(max(id_mouvement), 0) AS m FROM mouvement_stock").fetchone()["m"]
        base_mvt = conn.execute("SELECT COALESCE(max(id_mouvement), 0) AS m FROM mouvement_stock").fetchone()["m"]
        cmp_avant = conn.execute("SELECT id_produit, cmp FROM produit").fetchall()
    yield
    with pool.connection() as conn:
        conn.execute("ALTER TABLE mouvement_stock DISABLE TRIGGER trg_mouvement_immuable")
        conn.execute("DELETE FROM mouvement_stock WHERE id_mouvement > %s", (base_mvt,))
        conn.execute("ALTER TABLE mouvement_stock ENABLE TRIGGER trg_mouvement_immuable")
        conn.execute("DELETE FROM paiement WHERE id_vente > %s", (base,))
        conn.execute("DELETE FROM ligne_vente WHERE id_vente > %s", (base,))
        conn.execute("DELETE FROM vente WHERE id_vente > %s", (base,))
        # achats de test : réceptions, mouvements d'entrée, commandes, puis CMP remis à sa valeur d'origine
        conn.execute("ALTER TABLE mouvement_stock DISABLE TRIGGER trg_mouvement_immuable")
        conn.execute("ALTER TABLE mouvement_stock ENABLE TRIGGER trg_mouvement_immuable")
        conn.execute("DELETE FROM ligne_reception WHERE id_reception > %s", (base_rec,))
        conn.execute("DELETE FROM reception WHERE id_reception > %s", (base_rec,))
        conn.execute("DELETE FROM ligne_commande WHERE id_commande > %s", (base_cmd,))
        conn.execute("DELETE FROM commande_fournisseur WHERE id_commande > %s", (base_cmd,))
        for ligne in cmp_avant:
            conn.execute("UPDATE produit SET cmp = %s WHERE id_produit = %s", (ligne["cmp"], ligne["id_produit"]))

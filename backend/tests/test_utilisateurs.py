"""Tests utilisateurs et catégories (administrateur)."""
from app.db import pool


def _nettoyer():
    with pool.connection() as conn:
        conn.execute("DELETE FROM utilisateur WHERE nom_utilisateur LIKE 'test.%'")
        conn.execute("DELETE FROM categorie WHERE nom LIKE 'TEST cat%'")


def test_gestion_utilisateurs_reservee_a_ladmin(client, vendeur):
    assert client.get("/utilisateurs", headers=vendeur).status_code == 403
    assert client.post("/categories", headers=vendeur, json={"nom": "X"}).status_code == 403
    assert client.put("/categories/1", headers=vendeur, json={"nom": "X"}).status_code == 403


def test_creer_utilisateur_connexion_et_desactivation(client, admin):
    _nettoyer()
    r = client.post("/utilisateurs", headers=admin, json={
        "nom_utilisateur": "test.caissier", "nom_complet": "Test Caissier", "role": "vendeur",
        "mot_de_passe": "motdepasse1"})
    assert r.status_code == 201 and "mot_de_passe" not in r.json()
    uid = r.json()["id_utilisateur"]
    with pool.connection() as conn:     # RG14 : jamais en clair
        h = conn.execute("SELECT mot_de_passe_hash FROM utilisateur WHERE id_utilisateur=%s", (uid,)).fetchone()
    assert h["mot_de_passe_hash"].startswith("$2") and "motdepasse1" not in h["mot_de_passe_hash"]
    assert client.post("/auth/login", data={"username": "test.caissier", "password": "motdepasse1"}).status_code == 200
    # doublon, mot de passe trop court
    assert client.post("/utilisateurs", headers=admin, json={
        "nom_utilisateur": "test.caissier", "nom_complet": "Autre", "role": "vendeur",
        "mot_de_passe": "motdepasse1"}).status_code == 409
    assert client.post("/utilisateurs", headers=admin, json={
        "nom_utilisateur": "test.court", "nom_complet": "X", "role": "vendeur", "mot_de_passe": "abc"}).status_code == 422
    # changement de mot de passe puis désactivation : l'accès disparaît
    assert client.put(f"/utilisateurs/{uid}", headers=admin, json={
        "nom_complet": "Test Caissier", "role": "vendeur", "mot_de_passe": "nouveaumdp1"}).status_code == 200
    assert client.post("/auth/login", data={"username": "test.caissier", "password": "motdepasse1"}).status_code == 401
    assert client.post("/auth/login", data={"username": "test.caissier", "password": "nouveaumdp1"}).status_code == 200
    assert client.patch(f"/utilisateurs/{uid}/actif", headers=admin, json={"actif": False}).status_code == 200
    assert client.post("/auth/login", data={"username": "test.caissier", "password": "nouveaumdp1"}).status_code == 401
    _nettoyer()


def test_admin_ne_peut_pas_se_bloquer_lui_meme(client, admin):
    moi = client.get("/auth/me", headers=admin).json()
    assert client.patch(f"/utilisateurs/{moi['id_utilisateur']}/actif", headers=admin, json={"actif": False}).status_code == 409
    assert client.put(f"/utilisateurs/{moi['id_utilisateur']}", headers=admin, json={
        "nom_complet": moi["nom_complet"], "role": "vendeur"}).status_code == 409


def test_modifier_categorie(client, admin):
    _nettoyer()
    c = client.post("/categories", headers=admin, json={"nom": "TEST cat"}).json()
    r = client.put(f"/categories/{c['id_categorie']}", headers=admin, json={"nom": "TEST cat 2", "description": "d"})
    assert r.status_code == 200 and r.json()["nom"] == "TEST cat 2"
    assert client.put("/categories/999999", headers=admin, json={"nom": "Z"}).status_code == 404
    _nettoyer()

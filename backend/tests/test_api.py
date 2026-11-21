from .conftest import NOUVEAU_PRODUIT


# ---------- Authentification (RG13, RG14) ----------
def test_sante(client):
    assert client.get("/sante").json() == {"statut": "ok"}


def test_connexion_refusee_avec_mauvais_mot_de_passe(client):
    r = client.post("/auth/login", data={"username": "admin", "password": "faux"})
    assert r.status_code == 401


def test_connexion_refusee_avec_identifiant_inconnu(client):
    r = client.post("/auth/login", data={"username": "inconnu", "password": "admin123"})
    assert r.status_code == 401


def test_page_protegee_sans_jeton(client):
    assert client.get("/produits").status_code == 401


def test_jeton_invalide(client):
    r = client.get("/produits", headers={"Authorization": "Bearer nimportequoi"})
    assert r.status_code == 401


def test_utilisateur_connecte(client, vendeur):
    r = client.get("/auth/me", headers=vendeur)
    assert r.json()["role"] == "vendeur"


# ---------- Consultation et recherche ----------
def test_liste_des_produits_avec_stock(client, vendeur):
    r = client.get("/produits", headers=vendeur, params={"taille": 100})
    assert r.status_code == 200
    assert r.json()["total"] == 14
    ciment = next(p for p in r.json()["items"] if p["sku"] == "CIM-001")
    assert ciment["stock"] == 90          # scénario de recette : 100 reçus, 10 vendus
    assert ciment["cmp"] == 24200         # coût moyen pondéré calculé par la base
    assert ciment["categorie"] == "Ciment et liants"


def test_recherche_par_nom(client, vendeur):
    r = client.get("/produits", headers=vendeur, params={"q": "ciment"})
    assert [p["sku"] for p in r.json()["items"]] == ["CIM-001"]


def test_recherche_par_sku(client, vendeur):
    r = client.get("/produits", headers=vendeur, params={"q": "fer-0"})
    assert sorted(p["sku"] for p in r.json()["items"]) == ["FER-008", "FER-010"]


def test_produits_sous_le_seuil(client, vendeur):
    r = client.get("/produits", headers=vendeur, params={"sous_seuil": True})
    assert sorted(p["sku"] for p in r.json()["items"]) == ["ELE-CAB", "OUT-CLO", "PEI-BLC"]


def test_pagination(client, vendeur):
    r = client.get("/produits", headers=vendeur, params={"taille": 5, "page": 3})
    assert r.json()["total"] == 14 and len(r.json()["items"]) == 4


def test_produit_introuvable(client, vendeur):
    assert client.get("/produits/99999", headers=vendeur).status_code == 404


def test_liste_des_categories(client, vendeur):
    r = client.get("/categories", headers=vendeur)
    assert len(r.json()) == 6


# ---------- Droits : le vendeur ne peut pas modifier le catalogue (RG13) ----------
def test_vendeur_ne_peut_pas_creer_un_produit(client, vendeur):
    assert client.post("/produits", json=NOUVEAU_PRODUIT, headers=vendeur).status_code == 403


def test_vendeur_ne_peut_pas_desactiver_un_produit(client, vendeur):
    r = client.patch("/produits/1/actif", json={"actif": False}, headers=vendeur)
    assert r.status_code == 403


# ---------- Ajout, modification, désactivation ----------
def test_cycle_complet_d_un_produit(client, admin, produit_a_nettoyer):
    r = client.post("/produits", json=NOUVEAU_PRODUIT, headers=admin)
    assert r.status_code == 201, r.text
    produit = r.json()
    assert produit["stock"] == 0 and produit["cmp"] == 0 and produit["actif"] is True

    modif = dict(NOUVEAU_PRODUIT, prix_vente="1800", nom="Produit de test modifié")
    r = client.put(f"/produits/{produit['id_produit']}", json=modif, headers=admin)
    assert r.status_code == 200 and r.json()["prix_vente"] == 1800

    r = client.patch(f"/produits/{produit['id_produit']}/actif", json={"actif": False}, headers=admin)
    assert r.json()["actif"] is False
    # un produit désactivé disparaît de la liste par défaut, mais reste consultable
    liste = client.get("/produits", headers=admin, params={"q": "TEST-001"}).json()
    assert liste["total"] == 0
    liste = client.get("/produits", headers=admin, params={"q": "TEST-001", "inclure_inactifs": True}).json()
    assert liste["total"] == 1


# ---------- Contraintes de la base transformées en messages clairs ----------
def test_sku_en_double_refuse(client, admin):
    r = client.post("/produits", json=dict(NOUVEAU_PRODUIT, sku="CIM-001"), headers=admin)   # RG01
    assert r.status_code == 409 and "SKU" in r.json()["detail"]


def test_categorie_inexistante_refusee(client, admin):
    r = client.post("/produits", json=dict(NOUVEAU_PRODUIT, id_categorie=999), headers=admin)
    assert r.status_code == 409


def test_prix_negatif_refuse_par_la_validation(client, admin):
    r = client.post("/produits", json=dict(NOUVEAU_PRODUIT, prix_vente="-5"), headers=admin)
    assert r.status_code == 422


def test_unite_inconnue_refusee(client, admin):
    r = client.post("/produits", json=dict(NOUVEAU_PRODUIT, unite="tonne"), headers=admin)
    assert r.status_code == 422

"""Module Produits : ajouter, consulter, modifier, désactiver, rechercher.

Modèle à suivre pour les autres modules (fournisseurs, clients, ventes...) :
  1. un schéma Pydantic d'entrée et de sortie (schemas.py)
  2. des routes qui exécutent du SQL explicite
  3. la base se charge des contraintes (unicité, clés étrangères, CHECK) ;
     main.py transforme ses erreurs en messages compréhensibles.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..db import get_conn
from ..schemas import ActifIn, ProduitIn, ProduitOut, ProduitPage
from ..security import exiger_admin, utilisateur_courant

router = APIRouter(prefix="/produits", tags=["Produits"])

# Le stock vient de la vue v_stock (somme des mouvements) : on ne le stocke jamais.
SELECT_PRODUIT = """
    SELECT p.id_produit, p.sku, p.nom, p.marque, p.description, p.unite,
           p.prix_achat::float8 AS prix_achat, p.prix_vente::float8 AS prix_vente,
           p.stock_minimum::float8 AS stock_minimum, p.cmp::float8 AS cmp,
           p.actif, p.id_categorie, c.nom AS categorie,
           s.stock::float8 AS stock, s.sous_seuil
    FROM produit p
    JOIN categorie c ON c.id_categorie = p.id_categorie
    JOIN v_stock   s ON s.id_produit   = p.id_produit
"""


def lire_produit(conn, id_produit: int) -> dict:
    produit = conn.execute(SELECT_PRODUIT + " WHERE p.id_produit = %s", (id_produit,)).fetchone()
    if produit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Produit introuvable")
    return produit


@router.get("", response_model=ProduitPage)
def rechercher_produits(
    q: Optional[str] = Query(None, description="Recherche dans le nom, le SKU ou la marque"),
    id_categorie: Optional[int] = None,
    sous_seuil: bool = Query(False, description="Seulement les produits à réapprovisionner"),
    inclure_inactifs: bool = False,
    page: int = Query(1, ge=1),
    taille: int = Query(20, ge=1, le=100),
    conn=Depends(get_conn),
    _=Depends(utilisateur_courant),
):
    conditions, parametres = [], []
    if q:
        conditions.append("(p.nom ILIKE %s OR p.sku ILIKE %s OR p.marque ILIKE %s)")
        parametres += [f"%{q}%"] * 3
    if id_categorie is not None:
        conditions.append("p.id_categorie = %s")
        parametres.append(id_categorie)
    if sous_seuil:
        conditions.append("s.sous_seuil")
    if not inclure_inactifs:
        conditions.append("p.actif")
    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""

    total = conn.execute(
        "SELECT count(*) AS n FROM produit p JOIN v_stock s ON s.id_produit = p.id_produit" + where,
        parametres,
    ).fetchone()["n"]
    items = conn.execute(
        SELECT_PRODUIT + where + " ORDER BY p.nom LIMIT %s OFFSET %s",
        parametres + [taille, (page - 1) * taille],
    ).fetchall()
    return {"total": total, "page": page, "taille": taille, "items": items}


@router.get("/{id_produit}", response_model=ProduitOut)
def consulter_produit(id_produit: int, conn=Depends(get_conn), _=Depends(utilisateur_courant)):
    return lire_produit(conn, id_produit)


@router.post("", response_model=ProduitOut, status_code=status.HTTP_201_CREATED)
def creer_produit(donnees: ProduitIn, conn=Depends(get_conn), _=Depends(exiger_admin)):
    # le CMP démarre à 0 : il est calculé par la base à chaque réception (RG05)
    ligne = conn.execute(
        "INSERT INTO produit (sku, nom, marque, description, unite, prix_achat, prix_vente, "
        "                     stock_minimum, id_categorie) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id_produit",
        (donnees.sku, donnees.nom, donnees.marque, donnees.description, donnees.unite,
         donnees.prix_achat, donnees.prix_vente, donnees.stock_minimum, donnees.id_categorie),
    ).fetchone()
    return lire_produit(conn, ligne["id_produit"])


@router.put("/{id_produit}", response_model=ProduitOut)
def modifier_produit(id_produit: int, donnees: ProduitIn, conn=Depends(get_conn), _=Depends(exiger_admin)):
    # Modifier le prix de vente ne change pas les anciennes ventes : leur prix est copié dans ligne_vente (RG07)
    ligne = conn.execute(
        "UPDATE produit SET sku = %s, nom = %s, marque = %s, description = %s, unite = %s, "
        "       prix_achat = %s, prix_vente = %s, stock_minimum = %s, id_categorie = %s "
        "WHERE id_produit = %s RETURNING id_produit",
        (donnees.sku, donnees.nom, donnees.marque, donnees.description, donnees.unite,
         donnees.prix_achat, donnees.prix_vente, donnees.stock_minimum, donnees.id_categorie, id_produit),
    ).fetchone()
    if ligne is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Produit introuvable")
    return lire_produit(conn, id_produit)


@router.patch("/{id_produit}/actif", response_model=ProduitOut)
def activer_ou_desactiver_produit(id_produit: int, donnees: ActifIn, conn=Depends(get_conn),
                                  _=Depends(exiger_admin)):
    """Un produit déjà utilisé n'est jamais supprimé : on le désactive (il disparaît des listes)."""
    ligne = conn.execute(
        "UPDATE produit SET actif = %s WHERE id_produit = %s RETURNING id_produit",
        (donnees.actif, id_produit),
    ).fetchone()
    if ligne is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Produit introuvable")
    return lire_produit(conn, id_produit)


@router.delete("/{id_produit}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_produit(id_produit: int, conn=Depends(get_conn), _=Depends(exiger_admin)):
    """Supprime un produit créé par erreur, c'est-à-dire jamais commandé, reçu, vendu ni ajusté.
    Un produit qui a un historique ne peut qu'être désactivé : l'historique des stocks et des ventes est conservé."""
    lire_produit(conn, id_produit)                       # 404 si inconnu
    n = conn.execute(
        "SELECT (SELECT count(*) FROM ligne_commande   WHERE id_produit = %(p)s) "
        "     + (SELECT count(*) FROM ligne_reception  WHERE id_produit = %(p)s) "
        "     + (SELECT count(*) FROM ligne_vente      WHERE id_produit = %(p)s) "
        "     + (SELECT count(*) FROM mouvement_stock  WHERE id_produit = %(p)s) AS n", {"p": id_produit}).fetchone()["n"]
    if n:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "Suppression impossible : ce produit a un historique (commandes, ventes ou stock). "
                            "Désactivez-le à la place.")
    conn.execute("DELETE FROM produit WHERE id_produit = %s", (id_produit,))

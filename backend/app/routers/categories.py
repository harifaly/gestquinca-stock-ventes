from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from ..db import get_conn
from ..schemas import CategorieIn, CategorieOut
from ..security import exiger_admin, utilisateur_courant

router = APIRouter(prefix="/categories", tags=["Catégories"])


@router.get("", response_model=List[CategorieOut])
def lister_categories(conn=Depends(get_conn), _=Depends(utilisateur_courant)):
    return conn.execute(
        "SELECT id_categorie, nom, description FROM categorie ORDER BY nom"
    ).fetchall()


@router.post("", response_model=CategorieOut, status_code=status.HTTP_201_CREATED)
def creer_categorie(donnees: CategorieIn, conn=Depends(get_conn), _=Depends(exiger_admin)):
    return conn.execute(
        "INSERT INTO categorie (nom, description) VALUES (%s, %s) "
        "RETURNING id_categorie, nom, description",
        (donnees.nom, donnees.description),
    ).fetchone()


@router.put("/{id_categorie}", response_model=CategorieOut)
def modifier_categorie(id_categorie: int, donnees: CategorieIn, conn=Depends(get_conn), _=Depends(exiger_admin)):
    ligne = conn.execute(
        "UPDATE categorie SET nom = %s, description = %s WHERE id_categorie = %s "
        "RETURNING id_categorie, nom, description",
        (donnees.nom, donnees.description, id_categorie),
    ).fetchone()
    if ligne is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Catégorie introuvable")
    return ligne


@router.delete("/{id_categorie}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_categorie(id_categorie: int, conn=Depends(get_conn), _=Depends(exiger_admin)):
    """Supprime une catégorie vide. Si des produits l'utilisent, la suppression est refusée."""
    existe = conn.execute("SELECT 1 FROM categorie WHERE id_categorie = %s", (id_categorie,)).fetchone()
    if existe is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Catégorie introuvable")
    n = conn.execute("SELECT count(*) AS n FROM produit WHERE id_categorie = %s", (id_categorie,)).fetchone()["n"]
    if n:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            f"Suppression impossible : {n} produit(s) utilisent cette catégorie. Déplacez-les d'abord.")
    conn.execute("DELETE FROM categorie WHERE id_categorie = %s", (id_categorie,))

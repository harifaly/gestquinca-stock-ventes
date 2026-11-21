"""Module Fournisseurs (administrateur uniquement, RG13)."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..db import get_conn
from ..schemas import FournisseurIn, FournisseurOut, FournisseurPage
from ..security import exiger_admin

router = APIRouter(prefix="/fournisseurs", tags=["Fournisseurs"], dependencies=[Depends(exiger_admin)])

COLONNES = "id_fournisseur, nom, telephone, adresse, email, contact"


@router.get("", response_model=FournisseurPage)
def rechercher_fournisseurs(
    q: Optional[str] = Query(None, description="Recherche dans le nom, le contact ou le téléphone"),
    page: int = Query(1, ge=1),
    taille: int = Query(20, ge=1, le=100),
    conn=Depends(get_conn),
):
    where, parametres = "", []
    if q:
        where = " WHERE nom ILIKE %s OR contact ILIKE %s OR telephone ILIKE %s"
        parametres = [f"%{q}%"] * 3
    total = conn.execute("SELECT count(*) AS n FROM fournisseur" + where, parametres).fetchone()["n"]
    items = conn.execute(
        f"SELECT {COLONNES} FROM fournisseur{where} ORDER BY nom LIMIT %s OFFSET %s",
        parametres + [taille, (page - 1) * taille]).fetchall()
    return {"total": total, "page": page, "taille": taille, "items": items}


@router.get("/{id_fournisseur}", response_model=FournisseurOut)
def consulter_fournisseur(id_fournisseur: int, conn=Depends(get_conn)):
    ligne = conn.execute(f"SELECT {COLONNES} FROM fournisseur WHERE id_fournisseur = %s",
                         (id_fournisseur,)).fetchone()
    if ligne is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fournisseur introuvable")
    return ligne


@router.post("", response_model=FournisseurOut, status_code=status.HTTP_201_CREATED)
def creer_fournisseur(d: FournisseurIn, conn=Depends(get_conn)):
    return conn.execute(
        f"INSERT INTO fournisseur (nom, telephone, adresse, email, contact) VALUES (%s,%s,%s,%s,%s) "
        f"RETURNING {COLONNES}", (d.nom, d.telephone, d.adresse, d.email, d.contact)).fetchone()


@router.put("/{id_fournisseur}", response_model=FournisseurOut)
def modifier_fournisseur(id_fournisseur: int, d: FournisseurIn, conn=Depends(get_conn)):
    ligne = conn.execute(
        f"UPDATE fournisseur SET nom=%s, telephone=%s, adresse=%s, email=%s, contact=%s "
        f"WHERE id_fournisseur=%s RETURNING {COLONNES}",
        (d.nom, d.telephone, d.adresse, d.email, d.contact, id_fournisseur)).fetchone()
    if ligne is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fournisseur introuvable")
    return ligne


@router.delete("/{id_fournisseur}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_fournisseur(id_fournisseur: int, conn=Depends(get_conn)):
    """Supprime un fournisseur qui n'a aucune commande. Sinon l'historique des achats serait perdu : refusé."""
    existe = conn.execute("SELECT 1 FROM fournisseur WHERE id_fournisseur = %s", (id_fournisseur,)).fetchone()
    if existe is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fournisseur introuvable")
    n = conn.execute("SELECT count(*) AS n FROM commande_fournisseur WHERE id_fournisseur = %s", (id_fournisseur,)).fetchone()["n"]
    if n:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            f"Suppression impossible : ce fournisseur a {n} commande(s) enregistrée(s).")
    conn.execute("DELETE FROM fournisseur WHERE id_fournisseur = %s", (id_fournisseur,))

"""Stock : historique des mouvements (lecture pour tous) et ajustements justifiés (administrateur).

RG06 : un ajustement négatif ne peut pas rendre le stock négatif (trigger de la base).
RG11 : on ne modifie jamais un mouvement, une correction crée un nouveau mouvement.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from ..db import get_conn
from ..schemas import AjustementIn, MouvementOut, MouvementPage
from ..security import exiger_admin, utilisateur_courant

router = APIRouter(prefix="/stock", tags=["Stock"])

SELECT_MOUVEMENT = """
    SELECT m.id_mouvement, to_char(m.date_mouvement, 'YYYY-MM-DD"T"HH24:MI:SS') AS date_mouvement,
           m.id_produit, p.sku, p.nom AS produit, p.unite, m.type_mouvement, m.quantite::float8 AS quantite,
           m.motif, m.id_vente, m.id_reception, u.nom_complet AS utilisateur
    FROM mouvement_stock m
    JOIN produit p     ON p.id_produit = m.id_produit
    JOIN utilisateur u ON u.id_utilisateur = m.id_utilisateur
"""


@router.get("/mouvements", response_model=MouvementPage)
def lister_mouvements(
    id_produit: Optional[int] = None,
    type_mouvement: Optional[str] = Query(None, pattern="^(ENTREE_RECEPTION|SORTIE_VENTE|AJUSTEMENT)$"),
    page: int = Query(1, ge=1),
    taille: int = Query(20, ge=1, le=100),
    conn=Depends(get_conn),
    _=Depends(utilisateur_courant),
):
    conditions, parametres = [], []
    if id_produit is not None:
        conditions.append("m.id_produit = %s")
        parametres.append(id_produit)
    if type_mouvement:
        conditions.append("m.type_mouvement = %s")
        parametres.append(type_mouvement)
    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    total = conn.execute("SELECT count(*) AS n FROM mouvement_stock m" + where, parametres).fetchone()["n"]
    items = conn.execute(
        SELECT_MOUVEMENT + where + " ORDER BY m.date_mouvement DESC, m.id_mouvement DESC LIMIT %s OFFSET %s",
        parametres + [taille, (page - 1) * taille]).fetchall()
    return {"total": total, "page": page, "taille": taille, "items": items}


@router.post("/ajustements", response_model=MouvementOut, status_code=status.HTTP_201_CREATED)
def creer_ajustement(d: AjustementIn, conn=Depends(get_conn), admin=Depends(exiger_admin)):
    ligne = conn.execute(
        "INSERT INTO mouvement_stock (id_produit, type_mouvement, quantite, id_utilisateur, motif) "
        "VALUES (%s, 'AJUSTEMENT', %s, %s, %s) RETURNING id_mouvement",
        (d.id_produit, d.quantite, admin["id_utilisateur"], d.motif)).fetchone()
    return conn.execute(SELECT_MOUVEMENT + " WHERE m.id_mouvement = %s", (ligne["id_mouvement"],)).fetchone()

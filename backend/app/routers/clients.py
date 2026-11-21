"""Module Clients : le vendeur consulte et crée, l'administrateur modifie."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..db import get_conn
from ..schemas import ClientIn, ClientOut, ClientPage
from ..security import exiger_admin, utilisateur_courant

router = APIRouter(prefix="/clients", tags=["Clients"])

# La créance (ce que le client doit encore) vient de la vue v_creance_client.
SELECT_CLIENT = """
    SELECT c.id_client, c.nom, c.telephone, c.adresse, r.creance::float8 AS creance
    FROM client c JOIN v_creance_client r ON r.id_client = c.id_client
"""


def lire_client(conn, id_client: int) -> dict:
    client = conn.execute(SELECT_CLIENT + " WHERE c.id_client = %s", (id_client,)).fetchone()
    if client is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Client introuvable")
    return client


@router.get("", response_model=ClientPage)
def rechercher_clients(
    q: Optional[str] = Query(None, description="Recherche dans le nom ou le téléphone"),
    avec_creance: bool = Query(False, description="Seulement les clients qui doivent de l'argent"),
    page: int = Query(1, ge=1),
    taille: int = Query(20, ge=1, le=100),
    conn=Depends(get_conn),
    _=Depends(utilisateur_courant),
):
    conditions, parametres = [], []
    if q:
        conditions.append("(c.nom ILIKE %s OR c.telephone ILIKE %s)")
        parametres += [f"%{q}%"] * 2
    if avec_creance:
        conditions.append("r.creance > 0")
    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    total = conn.execute(
        "SELECT count(*) AS n FROM client c JOIN v_creance_client r ON r.id_client = c.id_client" + where,
        parametres,
    ).fetchone()["n"]
    items = conn.execute(
        SELECT_CLIENT + where + " ORDER BY c.nom LIMIT %s OFFSET %s",
        parametres + [taille, (page - 1) * taille],
    ).fetchall()
    return {"total": total, "page": page, "taille": taille, "items": items}


@router.get("/{id_client}", response_model=ClientOut)
def consulter_client(id_client: int, conn=Depends(get_conn), _=Depends(utilisateur_courant)):
    return lire_client(conn, id_client)


@router.post("", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
def creer_client(donnees: ClientIn, conn=Depends(get_conn), _=Depends(utilisateur_courant)):
    ligne = conn.execute(
        "INSERT INTO client (nom, telephone, adresse) VALUES (%s, %s, %s) RETURNING id_client",
        (donnees.nom, donnees.telephone, donnees.adresse),
    ).fetchone()
    return lire_client(conn, ligne["id_client"])


@router.put("/{id_client}", response_model=ClientOut)
def modifier_client(id_client: int, donnees: ClientIn, conn=Depends(get_conn), _=Depends(exiger_admin)):
    ligne = conn.execute(
        "UPDATE client SET nom = %s, telephone = %s, adresse = %s WHERE id_client = %s RETURNING id_client",
        (donnees.nom, donnees.telephone, donnees.adresse, id_client),
    ).fetchone()
    if ligne is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Client introuvable")
    return lire_client(conn, id_client)


@router.delete("/{id_client}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_client(id_client: int, conn=Depends(get_conn), _=Depends(exiger_admin)):
    """Supprime un client qui n'a aucune vente. Sinon l'historique des ventes serait perdu : refusé."""
    lire_client(conn, id_client)                         # 404 si inconnu
    n = conn.execute("SELECT count(*) AS n FROM vente WHERE id_client = %s", (id_client,)).fetchone()["n"]
    if n:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            f"Suppression impossible : ce client a {n} vente(s) enregistrée(s).")
    conn.execute("DELETE FROM client WHERE id_client = %s", (id_client,))

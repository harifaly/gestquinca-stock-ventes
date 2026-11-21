"""Commandes fournisseurs et réceptions (administrateur uniquement, RG13).

RG02 : une commande n'a aucun effet sur le stock.
RG03/RG04 : seule une réception augmente le stock (mouvement d'entrée) et conserve le prix réel.
RG05 : le trigger de la base recalcule le coût moyen pondéré à chaque entrée.
RG12 : une réception est créée en une seule transaction.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..db import get_conn
from ..schemas import CommandeDetail, CommandeIn, CommandePage, ReceptionIn
from ..security import exiger_admin

router = APIRouter(prefix="/commandes", tags=["Commandes fournisseurs"])

SELECT_COMMANDE = """
    SELECT c.id_commande, to_char(c.date_commande, 'YYYY-MM-DD') AS date_commande,
           c.id_fournisseur, f.nom AS fournisseur, s.statut,
           COALESCE((SELECT SUM(quantite_commandee * prix_achat_prevu) FROM ligne_commande lc
                     WHERE lc.id_commande = c.id_commande), 0)::float8 AS total_prevu
    FROM commande_fournisseur c
    JOIN fournisseur f ON f.id_fournisseur = c.id_fournisseur
    JOIN v_statut_commande s ON s.id_commande = c.id_commande
"""


def lire_commande(conn, id_commande: int) -> dict:
    commande = conn.execute(SELECT_COMMANDE + " WHERE c.id_commande = %s", (id_commande,)).fetchone()
    if commande is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Commande introuvable")
    commande["lignes"] = conn.execute(
        "SELECT lc.id_produit, p.sku, p.nom, p.unite, lc.quantite_commandee::float8 AS quantite_commandee, "
        "       COALESCE(SUM(lr.quantite_recue), 0)::float8 AS quantite_recue, "
        "       (lc.quantite_commandee - COALESCE(SUM(lr.quantite_recue), 0))::float8 AS reste, "
        "       lc.prix_achat_prevu::float8 AS prix_achat_prevu "
        "FROM ligne_commande lc JOIN produit p ON p.id_produit = lc.id_produit "
        "LEFT JOIN reception r ON r.id_commande = lc.id_commande "
        "LEFT JOIN ligne_reception lr ON lr.id_reception = r.id_reception AND lr.id_produit = lc.id_produit "
        "WHERE lc.id_commande = %s "
        "GROUP BY lc.id_produit, p.sku, p.nom, p.unite, lc.quantite_commandee, lc.prix_achat_prevu "
        "ORDER BY p.nom", (id_commande,)).fetchall()
    receptions = conn.execute(
        "SELECT r.id_reception, to_char(r.date_reception, 'YYYY-MM-DD') AS date_reception, "
        "       u.nom_complet AS utilisateur "
        "FROM reception r JOIN utilisateur u ON u.id_utilisateur = r.id_utilisateur "
        "WHERE r.id_commande = %s ORDER BY r.id_reception", (id_commande,)).fetchall()
    for r in receptions:
        r["lignes"] = conn.execute(
            "SELECT lr.id_produit, p.nom, p.unite, lr.quantite_recue::float8 AS quantite_recue, "
            "       lr.prix_achat_reel::float8 AS prix_achat_reel "
            "FROM ligne_reception lr JOIN produit p ON p.id_produit = lr.id_produit "
            "WHERE lr.id_reception = %s ORDER BY p.nom", (r["id_reception"],)).fetchall()
    commande["receptions"] = receptions
    return commande


@router.get("", response_model=CommandePage)
def lister_commandes(
    id_fournisseur: Optional[int] = None,
    statut: Optional[str] = Query(None, pattern="^(en_cours|partiellement_recue|recue)$"),
    page: int = Query(1, ge=1),
    taille: int = Query(20, ge=1, le=100),
    conn=Depends(get_conn),
    _=Depends(exiger_admin),
):
    conditions, parametres = [], []
    if id_fournisseur is not None:
        conditions.append("c.id_fournisseur = %s")
        parametres.append(id_fournisseur)
    if statut:
        conditions.append("s.statut = %s")
        parametres.append(statut)
    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    total = conn.execute(
        "SELECT count(*) AS n FROM commande_fournisseur c JOIN v_statut_commande s "
        "ON s.id_commande = c.id_commande" + where, parametres).fetchone()["n"]
    items = conn.execute(
        SELECT_COMMANDE + where + " ORDER BY c.date_commande DESC, c.id_commande DESC LIMIT %s OFFSET %s",
        parametres + [taille, (page - 1) * taille]).fetchall()
    return {"total": total, "page": page, "taille": taille, "items": items}


@router.get("/{id_commande}", response_model=CommandeDetail)
def consulter_commande(id_commande: int, conn=Depends(get_conn), _=Depends(exiger_admin)):
    return lire_commande(conn, id_commande)


@router.post("", response_model=CommandeDetail, status_code=status.HTTP_201_CREATED)
def creer_commande(d: CommandeIn, conn=Depends(get_conn), admin=Depends(exiger_admin)):
    ids = [l.id_produit for l in d.lignes]
    if len(ids) != len(set(ids)):
        raise HTTPException(422, "Un même produit ne peut apparaître qu'une fois dans la commande")
    id_commande = conn.execute(
        "INSERT INTO commande_fournisseur (id_fournisseur, id_utilisateur) VALUES (%s, %s) RETURNING id_commande",
        (d.id_fournisseur, admin["id_utilisateur"])).fetchone()["id_commande"]
    for l in d.lignes:
        conn.execute(
            "INSERT INTO ligne_commande (id_commande, id_produit, quantite_commandee, prix_achat_prevu) "
            "VALUES (%s, %s, %s, %s)", (id_commande, l.id_produit, l.quantite_commandee, l.prix_achat_prevu))
    return lire_commande(conn, id_commande)


@router.post("/{id_commande}/receptions", response_model=CommandeDetail, status_code=status.HTTP_201_CREATED)
def enregistrer_reception(id_commande: int, d: ReceptionIn, conn=Depends(get_conn), admin=Depends(exiger_admin)):
    lire_commande(conn, id_commande)                      # 404 si la commande n'existe pas
    ids = [l.id_produit for l in d.lignes]
    if len(ids) != len(set(ids)):
        raise HTTPException(422, "Un même produit ne peut apparaître qu'une fois dans la réception")
    id_reception = conn.execute(
        "INSERT INTO reception (id_commande, id_utilisateur) VALUES (%s, %s) RETURNING id_reception",
        (id_commande, admin["id_utilisateur"])).fetchone()["id_reception"]
    for l in sorted(d.lignes, key=lambda x: x.id_produit):
        conn.execute(                                      # RG03 vérifié par le trigger de la base
            "INSERT INTO ligne_reception (id_reception, id_produit, quantite_recue, prix_achat_reel) "
            "VALUES (%s, %s, %s, %s)", (id_reception, l.id_produit, l.quantite_recue, l.prix_achat_reel))
        conn.execute(                                      # entrée de stock ; le trigger recalcule le CMP (RG05)
            "INSERT INTO mouvement_stock (id_produit, type_mouvement, quantite, id_utilisateur, id_reception) "
            "VALUES (%s, 'ENTREE_RECEPTION', %s, %s, %s)",
            (l.id_produit, l.quantite_recue, admin["id_utilisateur"], id_reception))
    return lire_commande(conn, id_commande)

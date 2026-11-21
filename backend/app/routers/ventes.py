"""Module Ventes et paiements.

Une vente = une transaction : la vente, ses lignes, les mouvements de stock et le
paiement éventuel sont créés ensemble. Si une règle de la base est violée
(RG06 stock insuffisant, RG08 paiement trop élevé, RG10 crédit sans client),
TOUT est annulé.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..db import get_conn
from ..schemas import PaiementIn, VenteDetail, VenteIn, VentePage
from ..security import utilisateur_courant

router = APIRouter(prefix="/ventes", tags=["Ventes"])

SELECT_VENTE = """
    SELECT v.id_vente, to_char(v.date_vente, 'YYYY-MM-DD"T"HH24:MI:SS') AS date_vente,
           v.id_client, c.nom AS client, u.nom_complet AS vendeur,
           s.total::float8 AS total, s.total_paye::float8 AS total_paye,
           s.solde::float8 AS solde, s.statut_paiement
    FROM vente v
    JOIN utilisateur u   ON u.id_utilisateur = v.id_utilisateur
    JOIN v_solde_vente s ON s.id_vente = v.id_vente
    LEFT JOIN client c   ON c.id_client = v.id_client
"""


def lire_vente(conn, id_vente: int) -> dict:
    vente = conn.execute(SELECT_VENTE + " WHERE v.id_vente = %s", (id_vente,)).fetchone()
    if vente is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vente introuvable")
    vente["lignes"] = conn.execute(
        "SELECT lv.id_produit, p.sku, p.nom, p.unite, lv.quantite::float8 AS quantite, "
        "       lv.prix_unitaire::float8 AS prix_unitaire, "
        "       ROUND(lv.quantite * lv.prix_unitaire, 2)::float8 AS total_ligne "
        "FROM ligne_vente lv JOIN produit p ON p.id_produit = lv.id_produit "
        "WHERE lv.id_vente = %s ORDER BY p.nom", (id_vente,)).fetchall()
    vente["paiements"] = conn.execute(
        "SELECT pa.id_paiement, to_char(pa.date_paiement, 'YYYY-MM-DD\"T\"HH24:MI:SS') AS date_paiement, "
        "       pa.montant::float8 AS montant, pa.mode_paiement, u.nom_complet AS vendeur "
        "FROM paiement pa JOIN utilisateur u ON u.id_utilisateur = pa.id_utilisateur "
        "WHERE pa.id_vente = %s ORDER BY pa.date_paiement, pa.id_paiement", (id_vente,)).fetchall()
    return vente


@router.get("", response_model=VentePage)
def lister_ventes(
    id_client: Optional[int] = None,
    statut: Optional[str] = Query(None, pattern="^(non_payee|partiellement_payee|payee)$"),
    page: int = Query(1, ge=1),
    taille: int = Query(20, ge=1, le=100),
    conn=Depends(get_conn),
    _=Depends(utilisateur_courant),
):
    conditions, parametres = [], []
    if id_client is not None:
        conditions.append("v.id_client = %s")
        parametres.append(id_client)
    if statut:
        conditions.append("s.statut_paiement = %s")
        parametres.append(statut)
    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    total = conn.execute(
        "SELECT count(*) AS n FROM vente v JOIN v_solde_vente s ON s.id_vente = v.id_vente" + where,
        parametres).fetchone()["n"]
    items = conn.execute(
        SELECT_VENTE + where + " ORDER BY v.date_vente DESC, v.id_vente DESC LIMIT %s OFFSET %s",
        parametres + [taille, (page - 1) * taille]).fetchall()
    return {"total": total, "page": page, "taille": taille, "items": items}


@router.get("/{id_vente}", response_model=VenteDetail)
def consulter_vente(id_vente: int, conn=Depends(get_conn), _=Depends(utilisateur_courant)):
    return lire_vente(conn, id_vente)


@router.post("", response_model=VenteDetail, status_code=status.HTTP_201_CREATED)
def creer_vente(donnees: VenteIn, conn=Depends(get_conn), utilisateur=Depends(utilisateur_courant)):
    ids = [l.id_produit for l in donnees.lignes]
    if len(ids) != len(set(ids)):
        raise HTTPException(422, "Un même produit ne peut apparaître qu'une fois : regroupez les quantités")

    id_vente = conn.execute(
        "INSERT INTO vente (id_client, id_utilisateur) VALUES (%s, %s) RETURNING id_vente",
        (donnees.id_client, utilisateur["id_utilisateur"]),
    ).fetchone()["id_vente"]

    # lignes triées par produit : évite les blocages entre deux ventes simultanées
    for ligne in sorted(donnees.lignes, key=lambda l: l.id_produit):
        # RG07 : le prix de vente du jour est COPIÉ dans la ligne
        copie = conn.execute(
            "INSERT INTO ligne_vente (id_vente, id_produit, quantite, prix_unitaire) "
            "SELECT %s, id_produit, %s, prix_vente FROM produit WHERE id_produit = %s AND actif "
            "RETURNING id_produit",
            (id_vente, ligne.quantite, ligne.id_produit),
        ).fetchone()
        if copie is None:
            raise HTTPException(422, f"Produit {ligne.id_produit} introuvable ou désactivé")
        # la sortie de stock est un mouvement négatif ; le trigger vérifie RG06 (stock suffisant)
        conn.execute(
            "INSERT INTO mouvement_stock (id_produit, type_mouvement, quantite, id_utilisateur, id_vente) "
            "VALUES (%s, 'SORTIE_VENTE', %s, %s, %s)",
            (ligne.id_produit, -ligne.quantite, utilisateur["id_utilisateur"], id_vente),
        )

    if donnees.paiement:
        conn.execute(
            "INSERT INTO paiement (id_vente, montant, mode_paiement, id_utilisateur) VALUES (%s, %s, %s, %s)",
            (id_vente, donnees.paiement.montant, donnees.paiement.mode_paiement, utilisateur["id_utilisateur"]),
        )

    # RG10 est vérifié en fin de transaction : on le déclenche ici pour que l'erreur
    # soit renvoyée proprement et que tout soit annulé.
    conn.execute("SET CONSTRAINTS ALL IMMEDIATE")
    return lire_vente(conn, id_vente)


@router.post("/{id_vente}/paiements", response_model=VenteDetail, status_code=status.HTTP_201_CREATED)
def enregistrer_paiement(id_vente: int, donnees: PaiementIn, conn=Depends(get_conn),
                         utilisateur=Depends(utilisateur_courant)):
    lire_vente(conn, id_vente)                        # 404 si la vente n'existe pas
    conn.execute(
        "INSERT INTO paiement (id_vente, montant, mode_paiement, id_utilisateur) VALUES (%s, %s, %s, %s)",
        (id_vente, donnees.montant, donnees.mode_paiement, utilisateur["id_utilisateur"]),
    )                                                 # RG08 : le trigger refuse un trop-perçu
    return lire_vente(conn, id_vente)

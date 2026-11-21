"""Tableau de bord (administrateur).

Trois notions distinctes (cahier des charges 4.5) :
  - chiffre d'affaires = ventes de la période (qu'elles soient payées ou non)
  - encaissements      = paiements reçus pendant la période
  - créances           = total restant dû par les clients, à ce jour
"""
from fastapi import APIRouter, Depends, Query

from ..db import get_conn
from ..schemas import Dashboard
from ..security import exiger_admin

router = APIRouter(prefix="/dashboard", tags=["Tableau de bord"])

DEBUT = {
    "jour": "date_trunc('day', now())",
    "semaine": "date_trunc('week', now())",
    "mois": "date_trunc('month', now())",
}


@router.get("", response_model=Dashboard)
def tableau_de_bord(periode: str = Query("mois", pattern="^(jour|semaine|mois)$"),
                    conn=Depends(get_conn), _=Depends(exiger_admin)):
    debut = DEBUT[periode]          # valeur issue d'une liste fermée : pas d'injection possible
    ventes = conn.execute(
        f"SELECT to_char({debut}, 'YYYY-MM-DD') AS debut, "
        f"  COALESCE(ROUND(SUM(lv.quantite * lv.prix_unitaire), 2), 0)::float8 AS ca, "
        f"  COUNT(DISTINCT v.id_vente) AS nb, "
        # marge brute estimée = CA - coût des marchandises vendues (au CMP actuel du produit)
        f"  COALESCE(ROUND(SUM(lv.quantite * (lv.prix_unitaire - p.cmp)), 2), 0)::float8 AS marge "
        f"FROM vente v JOIN ligne_vente lv ON lv.id_vente = v.id_vente "
        f"JOIN produit p ON p.id_produit = lv.id_produit "
        f"WHERE v.date_vente >= {debut}").fetchone()
    debut_txt = conn.execute(f"SELECT to_char({debut}, 'YYYY-MM-DD') AS d").fetchone()["d"]
    encaissements = conn.execute(
        f"SELECT COALESCE(SUM(montant), 0)::float8 AS n FROM paiement WHERE date_paiement >= {debut}"
    ).fetchone()["n"]
    creances = conn.execute("SELECT COALESCE(SUM(creance), 0)::float8 AS n FROM v_creance_client").fetchone()["n"]
    valeur_stock = conn.execute(
        "SELECT COALESCE(ROUND(SUM(s.stock * p.cmp), 2), 0)::float8 AS n "
        "FROM v_stock s JOIN produit p ON p.id_produit = s.id_produit WHERE p.actif").fetchone()["n"]
    alertes = conn.execute(
        "SELECT p.id_produit, p.sku, p.nom, p.unite, s.stock::float8 AS stock, p.stock_minimum::float8 AS stock_minimum "
        "FROM produit p JOIN v_stock s ON s.id_produit = p.id_produit "
        "WHERE p.actif AND s.sous_seuil ORDER BY s.stock - p.stock_minimum, p.nom").fetchall()
    meilleurs = conn.execute(
        f"SELECT p.id_produit, p.nom, p.unite, SUM(lv.quantite)::float8 AS quantite_vendue, "
        f"       ROUND(SUM(lv.quantite * lv.prix_unitaire), 2)::float8 AS chiffre_affaires "
        f"FROM ligne_vente lv JOIN vente v ON v.id_vente = lv.id_vente "
        f"JOIN produit p ON p.id_produit = lv.id_produit WHERE v.date_vente >= {debut} "
        f"GROUP BY p.id_produit, p.nom, p.unite ORDER BY SUM(lv.quantite) DESC, p.nom LIMIT 5").fetchall()
    return {"periode": periode, "debut": debut_txt, "chiffre_affaires": ventes["ca"], "nombre_ventes": ventes["nb"],
            "encaissements": encaissements, "creances_total": creances, "marge_brute": ventes["marge"],
            "valeur_stock": valeur_stock, "produits_a_reapprovisionner": alertes, "meilleurs_produits": meilleurs}

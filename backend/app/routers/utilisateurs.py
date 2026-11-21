"""Gestion des comptes (administrateur uniquement, RG13). Mots de passe hachés avec bcrypt (RG14)."""
from typing import List

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status

from ..db import get_conn
from ..schemas import ActifIn, UtilisateurIn, UtilisateurListe, UtilisateurModif
from ..security import exiger_admin

router = APIRouter(prefix="/utilisateurs", tags=["Utilisateurs"])

COLONNES = "id_utilisateur, nom_utilisateur, nom_complet, role, actif"


def hacher(mot_de_passe: str) -> str:
    return bcrypt.hashpw(mot_de_passe.encode(), bcrypt.gensalt()).decode()


@router.get("", response_model=List[UtilisateurListe])
def lister_utilisateurs(conn=Depends(get_conn), _=Depends(exiger_admin)):
    return conn.execute(f"SELECT {COLONNES} FROM utilisateur ORDER BY nom_complet").fetchall()


@router.post("", response_model=UtilisateurListe, status_code=status.HTTP_201_CREATED)
def creer_utilisateur(d: UtilisateurIn, conn=Depends(get_conn), _=Depends(exiger_admin)):
    return conn.execute(
        f"INSERT INTO utilisateur (nom_utilisateur, mot_de_passe_hash, nom_complet, role) "
        f"VALUES (%s, %s, %s, %s) RETURNING {COLONNES}",
        (d.nom_utilisateur, hacher(d.mot_de_passe), d.nom_complet, d.role)).fetchone()


@router.put("/{id_utilisateur}", response_model=UtilisateurListe)
def modifier_utilisateur(id_utilisateur: int, d: UtilisateurModif, conn=Depends(get_conn),
                         admin=Depends(exiger_admin)):
    if id_utilisateur == admin["id_utilisateur"] and d.role != "admin":
        raise HTTPException(409, "Vous ne pouvez pas retirer votre propre rôle d'administrateur")
    ligne = conn.execute(
        f"UPDATE utilisateur SET nom_complet = %s, role = %s WHERE id_utilisateur = %s RETURNING {COLONNES}",
        (d.nom_complet, d.role, id_utilisateur)).fetchone()
    if ligne is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Utilisateur introuvable")
    if d.mot_de_passe:
        conn.execute("UPDATE utilisateur SET mot_de_passe_hash = %s WHERE id_utilisateur = %s",
                     (hacher(d.mot_de_passe), id_utilisateur))
    return ligne


@router.patch("/{id_utilisateur}/actif", response_model=UtilisateurListe)
def changer_actif(id_utilisateur: int, d: ActifIn, conn=Depends(get_conn), admin=Depends(exiger_admin)):
    """On désactive un compte au lieu de le supprimer : il reste l'auteur de ses anciennes opérations."""
    if id_utilisateur == admin["id_utilisateur"] and not d.actif:
        raise HTTPException(409, "Vous ne pouvez pas désactiver votre propre compte")
    ligne = conn.execute(
        f"UPDATE utilisateur SET actif = %s WHERE id_utilisateur = %s RETURNING {COLONNES}",
        (d.actif, id_utilisateur)).fetchone()
    if ligne is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Utilisateur introuvable")
    return ligne

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ..db import get_conn
from ..schemas import Token, Utilisateur
from ..security import creer_token, utilisateur_courant, verifier_mot_de_passe

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post("/login", response_model=Token)
def connexion(formulaire: OAuth2PasswordRequestForm = Depends(), conn=Depends(get_conn)):
    """Connexion : renvoie un jeton à envoyer ensuite dans l'en-tête Authorization: Bearer <jeton>."""
    utilisateur = conn.execute(
        "SELECT id_utilisateur, nom_utilisateur, mot_de_passe_hash, nom_complet, role "
        "FROM utilisateur WHERE nom_utilisateur = %s AND actif",
        (formulaire.username,),
    ).fetchone()
    # même message si l'identifiant ou le mot de passe est faux (on ne révèle pas lequel)
    if utilisateur is None or not verifier_mot_de_passe(formulaire.password, utilisateur["mot_de_passe_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Identifiant ou mot de passe incorrect")
    return Token(access_token=creer_token(utilisateur), role=utilisateur["role"],
                 nom_complet=utilisateur["nom_complet"])


@router.get("/me", response_model=Utilisateur)
def moi(utilisateur: dict = Depends(utilisateur_courant)):
    """Utilisateur connecté (sert à l'interface pour afficher le nom et adapter les menus)."""
    return utilisateur

"""Authentification (jeton JWT) et contrôle des rôles (RG13, RG14)."""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from .config import settings
from .db import get_conn

oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")
ALGORITHME = "HS256"


def verifier_mot_de_passe(mot_de_passe: str, hash_enregistre: str) -> bool:
    """Compare un mot de passe saisi avec le hash bcrypt de la base (RG14)."""
    try:
        return bcrypt.checkpw(mot_de_passe.encode(), hash_enregistre.encode())
    except ValueError:
        return False


def creer_token(utilisateur: dict) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    charge = {"sub": str(utilisateur["id_utilisateur"]), "role": utilisateur["role"], "exp": expiration}
    return jwt.encode(charge, settings.jwt_secret, algorithm=ALGORITHME)


def utilisateur_courant(token: str = Depends(oauth2), conn=Depends(get_conn)) -> dict:
    """Retrouve l'utilisateur à partir du jeton. Relit la base à chaque requête :
    un compte désactivé perd son accès immédiatement."""
    erreur = HTTPException(status.HTTP_401_UNAUTHORIZED, "Session invalide ou expirée",
                           headers={"WWW-Authenticate": "Bearer"})
    try:
        charge = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHME])
        id_utilisateur = int(charge["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise erreur
    utilisateur = conn.execute(
        "SELECT id_utilisateur, nom_utilisateur, nom_complet, role FROM utilisateur "
        "WHERE id_utilisateur = %s AND actif",
        (id_utilisateur,),
    ).fetchone()
    if utilisateur is None:
        raise erreur
    return utilisateur


def exiger_admin(utilisateur: dict = Depends(utilisateur_courant)) -> dict:
    """RG13 : réservé à l'administrateur (vérifié côté serveur, jamais seulement dans l'interface)."""
    if utilisateur["role"] != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Action réservée à l'administrateur")
    return utilisateur

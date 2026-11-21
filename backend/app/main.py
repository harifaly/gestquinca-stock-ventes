"""Point d'entrée de l'API GestQuinca.

Lancer :  uvicorn app.main:app --reload
Documentation interactive :  http://localhost:8000/docs
"""
from contextlib import asynccontextmanager

import psycopg.errors as pg
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .db import pool
from .routers import auth, categories, clients, commandes, dashboard, fournisseurs, produits, stock, utilisateurs, ventes


@asynccontextmanager
async def cycle_de_vie(_: FastAPI):
    pool.open()          # ouvre les connexions à PostgreSQL au démarrage
    yield
    pool.close()


app = FastAPI(title="GestQuinca API", version="1.0.0", lifespan=cycle_de_vie,
              description="Gestion de stock et de commandes pour une quincaillerie")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origine.strip() for origine in settings.cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(produits.router)
app.include_router(clients.router)
app.include_router(ventes.router)
app.include_router(fournisseurs.router)
app.include_router(commandes.router)
app.include_router(stock.router)
app.include_router(dashboard.router)
app.include_router(utilisateurs.router)


@app.get("/sante", tags=["Technique"])
def sante():
    """Vérifie que l'API et la base répondent."""
    with pool.connection() as conn:
        conn.execute("SELECT 1")
    return {"statut": "ok"}


# ---------- Erreurs de la base transformées en messages compréhensibles ----------
# Les contraintes (unicité, clés étrangères, CHECK) et les triggers RGxx sont dans PostgreSQL :
# l'API n'a qu'à traduire leurs erreurs pour l'interface.

def _reponse(code: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=code, content={"detail": message})


@app.exception_handler(pg.UniqueViolation)
async def erreur_unicite(_: Request, e: pg.UniqueViolation):
    contrainte = e.diag.constraint_name or ""
    if contrainte == "produit_sku_key":
        return _reponse(409, "Cette référence (SKU) est déjà utilisée par un autre produit")
    return _reponse(409, "Cette valeur existe déjà")


@app.exception_handler(pg.ForeignKeyViolation)
@app.exception_handler(pg.RestrictViolation)
async def erreur_reference(_: Request, e: Exception):
    return _reponse(409, "Opération impossible : référence inexistante, ou donnée utilisée ailleurs")


@app.exception_handler(pg.CheckViolation)
async def erreur_contrainte(_: Request, e: pg.CheckViolation):
    return _reponse(422, f"Valeur refusée par une règle de la base ({e.diag.constraint_name})")


@app.exception_handler(pg.RaiseException)
async def erreur_regle_de_gestion(_: Request, e: pg.RaiseException):
    # messages des triggers : "RG06 : stock insuffisant ...", "RG08 : ...", etc.
    return _reponse(409, e.diag.message_primary or "Règle de gestion non respectée")

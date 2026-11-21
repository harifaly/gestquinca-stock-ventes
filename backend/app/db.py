"""Connexion à PostgreSQL.

On écrit le SQL à la main (pas d'ORM) pour que les tables, jointures et
contraintes de la base restent visibles dans le code.

Chaque requête HTTP reçoit une connexion et UNE transaction : tout est validé
(COMMIT) si la route se termine bien, tout est annulé (ROLLBACK) si une erreur
survient (règle RG12 : une opération est atomique).
"""
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .config import settings

pool = ConnectionPool(
    settings.database_url,
    min_size=1,
    max_size=10,
    open=False,                      # ouvert au démarrage de l'application (voir main.py)
    kwargs={"row_factory": dict_row},  # chaque ligne est un dictionnaire {colonne: valeur}
)


def get_conn():
    """Dépendance FastAPI : une connexion par requête, avec COMMIT ou ROLLBACK automatique."""
    with pool.connection() as conn:
        yield conn

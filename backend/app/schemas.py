"""Formes des données échangées avec l'interface (validation avec Pydantic)."""
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

Unite = Literal["sac", "barre", "metre", "kg", "litre", "piece"]


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    nom_complet: str


class Utilisateur(BaseModel):
    id_utilisateur: int
    nom_utilisateur: str
    nom_complet: str
    role: str


class CategorieIn(BaseModel):
    nom: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None


class CategorieOut(CategorieIn):
    id_categorie: int


class ProduitIn(BaseModel):
    sku: str = Field(min_length=1, max_length=50)
    nom: str = Field(min_length=1, max_length=200)
    marque: Optional[str] = None
    description: Optional[str] = None
    unite: Unite
    prix_achat: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    prix_vente: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    stock_minimum: Decimal = Field(default=Decimal(0), ge=0, max_digits=12, decimal_places=3)
    id_categorie: int


class ProduitOut(BaseModel):
    id_produit: int
    sku: str
    nom: str
    marque: Optional[str]
    description: Optional[str]
    unite: str
    prix_achat: float
    prix_vente: float
    stock_minimum: float
    cmp: float
    actif: bool
    id_categorie: int
    categorie: str
    stock: float
    sous_seuil: bool


class ProduitPage(BaseModel):
    total: int
    page: int
    taille: int
    items: List[ProduitOut]


class ActifIn(BaseModel):
    actif: bool


# ---------- Clients, ventes, paiements ----------
Mode = Literal["especes", "mobile_money", "virement", "carte"]


class ClientIn(BaseModel):
    nom: str = Field(min_length=1, max_length=200)
    telephone: Optional[str] = None
    adresse: Optional[str] = None


class ClientOut(ClientIn):
    id_client: int
    creance: float = 0


class ClientPage(BaseModel):
    total: int
    page: int
    taille: int
    items: List[ClientOut]


class LigneVenteIn(BaseModel):
    id_produit: int
    quantite: Decimal = Field(gt=0, max_digits=12, decimal_places=3)


class PaiementIn(BaseModel):
    montant: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    mode_paiement: Mode


class VenteIn(BaseModel):
    id_client: Optional[int] = None          # vide = vente comptant anonyme (RG10)
    lignes: List[LigneVenteIn] = Field(min_length=1)
    paiement: Optional[PaiementIn] = None    # acompte ou paiement complet à la vente


class LigneVenteOut(BaseModel):
    id_produit: int
    sku: str
    nom: str
    unite: str
    quantite: float
    prix_unitaire: float
    total_ligne: float


class PaiementOut(BaseModel):
    id_paiement: int
    date_paiement: str
    montant: float
    mode_paiement: str
    vendeur: str


class VenteResume(BaseModel):
    id_vente: int
    date_vente: str
    id_client: Optional[int]
    client: Optional[str]
    vendeur: str
    total: float
    total_paye: float
    solde: float
    statut_paiement: str


class VentePage(BaseModel):
    total: int
    page: int
    taille: int
    items: List[VenteResume]


class VenteDetail(VenteResume):
    lignes: List[LigneVenteOut]
    paiements: List[PaiementOut]


# ---------- Fournisseurs, commandes fournisseurs, réceptions ----------
class FournisseurIn(BaseModel):
    nom: str = Field(min_length=1, max_length=200)
    telephone: Optional[str] = None
    adresse: Optional[str] = None
    email: Optional[str] = None
    contact: Optional[str] = None


class FournisseurOut(FournisseurIn):
    id_fournisseur: int


class FournisseurPage(BaseModel):
    total: int
    page: int
    taille: int
    items: List[FournisseurOut]


class LigneCommandeIn(BaseModel):
    id_produit: int
    quantite_commandee: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    prix_achat_prevu: Decimal = Field(ge=0, max_digits=14, decimal_places=2)


class CommandeIn(BaseModel):
    id_fournisseur: int
    lignes: List[LigneCommandeIn] = Field(min_length=1)


class LigneReceptionIn(BaseModel):
    id_produit: int
    quantite_recue: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    prix_achat_reel: Decimal = Field(ge=0, max_digits=14, decimal_places=2)


class ReceptionIn(BaseModel):
    lignes: List[LigneReceptionIn] = Field(min_length=1)


class CommandeResume(BaseModel):
    id_commande: int
    date_commande: str
    id_fournisseur: int
    fournisseur: str
    statut: str
    total_prevu: float


class CommandePage(BaseModel):
    total: int
    page: int
    taille: int
    items: List[CommandeResume]


class LigneCommandeOut(BaseModel):
    id_produit: int
    sku: str
    nom: str
    unite: str
    quantite_commandee: float
    quantite_recue: float
    reste: float
    prix_achat_prevu: float


class LigneReceptionOut(BaseModel):
    id_produit: int
    nom: str
    unite: str
    quantite_recue: float
    prix_achat_reel: float


class ReceptionOut(BaseModel):
    id_reception: int
    date_reception: str
    utilisateur: str
    lignes: List[LigneReceptionOut]


class CommandeDetail(CommandeResume):
    lignes: List[LigneCommandeOut]
    receptions: List[ReceptionOut]


# ---------- Stock et tableau de bord ----------
Motif = Literal["perte", "casse", "erreur_comptage", "autre"]


class AjustementIn(BaseModel):
    id_produit: int
    quantite: Decimal = Field(max_digits=12, decimal_places=3, description="positive = ajout, négative = retrait")
    motif: Motif


class MouvementOut(BaseModel):
    id_mouvement: int
    date_mouvement: str
    id_produit: int
    sku: str
    produit: str
    unite: str
    type_mouvement: str
    quantite: float
    motif: Optional[str]
    id_vente: Optional[int]
    id_reception: Optional[int]
    utilisateur: str


class MouvementPage(BaseModel):
    total: int
    page: int
    taille: int
    items: List[MouvementOut]


class ProduitAlerte(BaseModel):
    id_produit: int
    sku: str
    nom: str
    unite: str
    stock: float
    stock_minimum: float


class MeilleurProduit(BaseModel):
    id_produit: int
    nom: str
    unite: str
    quantite_vendue: float
    chiffre_affaires: float


class Dashboard(BaseModel):
    periode: str
    debut: str
    chiffre_affaires: float
    nombre_ventes: int
    encaissements: float
    creances_total: float
    marge_brute: float
    valeur_stock: float
    produits_a_reapprovisionner: List[ProduitAlerte]
    meilleurs_produits: List[MeilleurProduit]


# ---------- Utilisateurs (administrateur) ----------
class UtilisateurIn(BaseModel):
    nom_utilisateur: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9._-]+$")
    nom_complet: str = Field(min_length=1, max_length=200)
    role: Literal["admin", "vendeur"]
    mot_de_passe: str = Field(min_length=8, max_length=72)


class UtilisateurModif(BaseModel):
    nom_complet: str = Field(min_length=1, max_length=200)
    role: Literal["admin", "vendeur"]
    mot_de_passe: Optional[str] = Field(None, min_length=8, max_length=72,
                                        description="Laisser vide pour ne pas changer le mot de passe")


class UtilisateurListe(Utilisateur):
    actif: bool

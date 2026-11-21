// Formats d'affichage partagés (français, ariary)
const montant = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 2 })
const quantite = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 3 })

export const ariary = (v) => `${montant.format(v)} Ar`
export const nombre = (v) => quantite.format(v)
export const dateFr = (iso) => new Date(iso).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' })

export const STATUTS = {
  non_payee: { libelle: 'Non payée', classe: 'bg-danger' },
  partiellement_payee: { libelle: 'Partielle', classe: 'bg-warning text-dark' },
  payee: { libelle: 'Payée', classe: 'bg-success' },
}
export const MODES = {
  especes: 'Espèces',
  mobile_money: 'Mobile money',
  virement: 'Virement',
  carte: 'Carte',
}

export const STATUTS_COMMANDE = {
  en_cours: { libelle: 'En cours', classe: 'bg-secondary' },
  partiellement_recue: { libelle: 'Partiellement reçue', classe: 'bg-warning text-dark' },
  recue: { libelle: 'Reçue', classe: 'bg-success' },
}

export const TYPES_MOUVEMENT = {
  ENTREE_RECEPTION: { libelle: 'Entrée (réception)', classe: 'bg-success' },
  SORTIE_VENTE: { libelle: 'Sortie (vente)', classe: 'bg-primary' },
  AJUSTEMENT: { libelle: 'Ajustement', classe: 'bg-warning text-dark' },
}
export const MOTIFS = { perte: 'Perte', casse: 'Casse', erreur_comptage: 'Erreur de comptage', autre: 'Autre' }

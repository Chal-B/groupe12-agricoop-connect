"""
========================================================================
  LOGIC.PY  —  COMPLÉTÉ PAR L'ÉQUIPE DATA SCIENCE
========================================================================
AgriCoop Connect — Coopérative COMAKI, Kintélé
========================================================================
"""

PRIX_ACHAT_KG = {
    "Manioc": 150,
    "Maïs": 200,
    "Arachide": 400,
}

PRIX_VENTE_KG = {
    "Manioc": 220,
    "Maïs": 280,
    "Arachide": 500,
}

# Ce que chaque rôle a le droit de faire (module Authentification).
ACTIONS_PAR_ROLE = {
    "Secrétaire": ["gerer_comptes", "gerer_membres", "tableau_de_bord", "consulter_rapport_partenaire"],
    "Président": ["enregistrer_vente", "tableau_de_bord", "generer_rapport_partenaire"],
    "Trésorière": ["enregistrer_paiement", "tableau_de_bord"],
    "Responsable dépôt": ["enregistrer_livraison", "tableau_de_bord"],
    "Membre": ["consulter_fiche_membre"],
}


# ========================================================================
# ZONE A — Tableau de bord & Statistiques
# ========================================================================

def calculer_indicateurs_globaux(livraisons, ventes, paiements):
    """Calcule les indicateurs principaux du tableau de bord."""
    stock_total = sum(l["quantite"] for l in livraisons) - sum(v["quantite"] for v in ventes)

    valeur_livraisons = sum(
        l["quantite"] * PRIX_ACHAT_KG.get(l["culture"], 0)
        for l in livraisons
    )
    total_paiements = sum(p["montant"] for p in paiements)
    montant_du_total = valeur_livraisons - total_paiements

    membres_actifs = set(l["membre_id"] for l in livraisons)

    return {
        "stock_total": stock_total,
        "montant_du_total": montant_du_total,
        "nb_membres_actifs": len(membres_actifs),
        "nb_livraisons_mois": len(livraisons),
    }


def calculer_livraisons_par_jour_semaine(livraisons):
    """Regroupe le volume total livré par date."""
    resultat = {}
    for l in livraisons:
        date = l["date"]
        resultat[date] = resultat.get(date, 0) + l["quantite"]
    return resultat


def classer_membres_par_production(livraisons):
    """Trie les membres par volume total livré, décroissant."""
    totaux = {}
    for l in livraisons:
        totaux[l["membre_id"]] = totaux.get(l["membre_id"], 0) + l["quantite"]

    resultat = [
        {"membre_id": membre_id, "volume_total": volume}
        for membre_id, volume in totaux.items()
    ]
    resultat.sort(key=lambda x: x["volume_total"], reverse=True)
    return resultat


def calculer_statistiques_globales(livraisons, ventes):
    """Calcule, pour chaque culture, le volume livré et la valeur des ventes."""
    resultat = {}

    for l in livraisons:
        culture = l["culture"]
        if culture not in resultat:
            resultat[culture] = {"volume_total": 0, "valeur_totale": 0}
        resultat[culture]["volume_total"] += l["quantite"]

    for v in ventes:
        culture = v["culture"]
        if culture not in resultat:
            resultat[culture] = {"volume_total": 0, "valeur_totale": 0}
        resultat[culture]["valeur_totale"] += v["quantite"] * v["prix_kg"]

    return resultat


def generer_indicateurs_rapport_bailleur(livraisons, ventes, paiements):
    """Calcule les indicateurs agrégés (sans donnée nominative) du rapport bailleur."""
    volume_total_periode = sum(l["quantite"] for l in livraisons)
    montant_ventes_periode = sum(v["quantite"] * v["prix_kg"] for v in ventes)

    membres_actifs = set(l["membre_id"] for l in livraisons)
    nb_membres_actifs = len(membres_actifs)

    if nb_membres_actifs == 0:
        taux_regularite_paiements = 0
    else:
        membres_payes = set(
            p["membre_id"] for p in paiements if p["membre_id"] in membres_actifs
        )
        taux_regularite_paiements = round(len(membres_payes) / nb_membres_actifs * 100)

    return {
        "volume_total_periode": volume_total_periode,
        "montant_ventes_periode": montant_ventes_periode,
        "taux_regularite_paiements": taux_regularite_paiements,
        "nb_membres_actifs": nb_membres_actifs,
    }


def identifier_top_acheteur(ventes, acheteurs):
    """Identifie l'acheteur ayant le plus gros volume cumulé."""
    if not ventes:
        return {"acheteur_nom": None, "volume_total": 0}

    totaux = {}
    for v in ventes:
        totaux[v["acheteur_id"]] = totaux.get(v["acheteur_id"], 0) + v["quantite"]

    top_id = max(totaux, key=totaux.get)
    top_volume = totaux[top_id]

    nom = None
    for a in acheteurs:
        if a["id"] == top_id:
            nom = a["nom"]
            break

    return {"acheteur_nom": nom, "volume_total": top_volume}


# ========================================================================
# ZONE B — Membres & Livraisons
# ========================================================================

def calculer_solde_membre(membre_id, livraisons, paiements):
    """Calcule le solde dû à un membre (valeur de ses livraisons moins ses paiements reçus)."""
    valeur_livraisons = sum(
        l["quantite"] * PRIX_ACHAT_KG.get(l["culture"], 0)
        for l in livraisons
        if l["membre_id"] == membre_id
    )
    total_paiements = sum(
        p["montant"] for p in paiements if p["membre_id"] == membre_id
    )
    return valeur_livraisons - total_paiements


def detecter_membres_inactifs(membres, livraisons, jours_seuil=90):
    """Identifie les membres n'ayant fait aucune livraison."""
    membres_ayant_livre = set(l["membre_id"] for l in livraisons)
    return [
        {"membre_id": m["id"], "nom": m["nom"]}
        for m in membres
        if m["id"] not in membres_ayant_livre
    ]


def detecter_anomalie_livraison(livraison):
    """Vérifie qu'une livraison respecte les règles métier de base."""
    anomalies = []

    quantite = livraison.get("quantite")
    if not isinstance(quantite, (int, float)) or quantite <= 0:
        anomalies.append("Quantité invalide : doit être strictement positive.")

    culture = livraison.get("culture")
    if culture not in PRIX_ACHAT_KG:
        anomalies.append(f"Culture inconnue : {culture}.")

    membre_id = livraison.get("membre_id")
    if not membre_id:
        anomalies.append("Aucun membre rattaché à cette livraison.")

    return anomalies


def generer_recu(membre_nom, montant):
    """Formate un texte de reçu pour un paiement."""
    if montant <= 0:
        return f"Aucun montant à verser pour {membre_nom}."
    return f"Reçu - {membre_nom} : paiement de {montant} FCFA effectué."


def calculer_historique_paiements_membre(membre_id, paiements):
    """Extrait l'historique des paiements d'un membre, du plus récent au plus ancien."""
    historique = [p for p in paiements if p["membre_id"] == membre_id]
    historique.sort(key=lambda p: p["date"], reverse=True)
    return historique


def rechercher_membre_similaire(nom_complet, membres):
    """Recherche un membre existant au nom quasi identique (détection de doublon)."""
    nom_normalise = " ".join(nom_complet.split()).lower()

    for m in membres:
        if " ".join(m["nom"].split()).lower() == nom_normalise:
            return m

    return None


def valider_nouveau_membre(donnees):
    """Vérifie que le formulaire de création d'un nouveau membre est complet."""
    anomalies = []

    if not donnees.get("nom", "").strip():
        anomalies.append("Le nom est obligatoire.")
    if not donnees.get("prenom", "").strip():
        anomalies.append("Le prénom est obligatoire.")
    if not donnees.get("village", "").strip():
        anomalies.append("Le village est obligatoire.")
    if not donnees.get("contact", "").strip():
        anomalies.append("Le contact est obligatoire.")

    return anomalies


# ========================================================================
# ZONE C — Ventes, Stock & Paiements
# ========================================================================

def calculer_stock_disponible(livraisons, ventes):
    """Calcule la quantité disponible à la vente, par culture."""
    resultat = {culture: 0 for culture in PRIX_ACHAT_KG}

    for l in livraisons:
        if l["culture"] in resultat:
            resultat[l["culture"]] += l["quantite"]

    for v in ventes:
        if v["culture"] in resultat:
            resultat[v["culture"]] -= v["quantite"]

    return resultat


def verifier_stock_avant_vente(vente, stock_disponible):
    """Vérifie qu'une vente demandée ne dépasse pas le stock disponible."""
    return vente["quantite"] <= stock_disponible.get(vente["culture"], 0)


def calculer_marge_vente(vente):
    """Calcule la marge générée par une vente."""
    prix_achat_reference = PRIX_ACHAT_KG[vente["culture"]]
    return (vente["prix_kg"] - prix_achat_reference) * vente["quantite"]


def verifier_paiement_valide(paiement, solde_du):
    """Vérifie qu'un paiement est positif et ne dépasse pas le solde dû."""
    anomalies = []

    montant = paiement.get("montant")
    if not isinstance(montant, (int, float)) or montant <= 0:
        anomalies.append("Le montant doit être strictement positif.")
    if isinstance(montant, (int, float)) and montant > solde_du:
        anomalies.append(f"Le montant dépasse le solde dû ({solde_du} FCFA).")

    return anomalies


def calculer_moyenne_prix_vente(ventes, culture):
    """Calcule le prix de vente moyen pondéré par quantité pour une culture donnée."""
    ventes_culture = [v for v in ventes if v["culture"] == culture]

    if not ventes_culture:
        return 0

    total_quantite = sum(v["quantite"] for v in ventes_culture)
    total_valeur = sum(v["quantite"] * v["prix_kg"] for v in ventes_culture)

    if total_quantite == 0:
        return 0

    return round(total_valeur / total_quantite)


# ========================================================================
# ZONE D — Authentification (nouveau module)
# ========================================================================

def authentifier_utilisateur(nom_utilisateur, mot_de_passe, utilisateurs):
    """Vérifie les identifiants et retourne le profil (sans le mot de passe) si valides."""
    for u in utilisateurs:
        if u["nom_utilisateur"] == nom_utilisateur and u["mot_de_passe"] == mot_de_passe:
            return {
                "nom_utilisateur": u["nom_utilisateur"],
                "role": u["role"],
                "nom_complet": u["nom_complet"],
                "membre_id": u["membre_id"],
            }
    return None


def verifier_acces_role(role, action):
    """Vérifie qu'un rôle a le droit d'effectuer une action donnée."""
    return action in ACTIONS_PAR_ROLE.get(role, [])

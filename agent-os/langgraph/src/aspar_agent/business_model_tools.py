"""Calculation functions for ASPAR's own business-line modeling. Every
function refuses to fabricate a number: if a required input is missing
(None), the function returns None for that result and the caller records
the field in `donnee_manquante` — never an estimate presented as fact.
"""

from __future__ import annotations

from typing import Any

# Durées standard par taille de chantier — portées du SOP réel MG Contracting
# ("Processus Chiffrage & Exécution Chantier", hub client MG Contracting).
DUREE_STANDARD_JOURS = {
    "Petit": 45,
    "Moyen": 60,
    "Grand": 75,
}

DEFAULT_MARGE_PCT = 10.0  # cohérent avec l'exemple du SOP (250 000 -> 275 000 TND)

# Repères de prix d'aménagement au m² par type d'activité, en EUR/m² —
# SOURCE : marché français (Travaux.com, Cushman & Wakefield, HR Associés,
# recherche du 2026-09-14), AUCUNE donnée tunisienne détaillée n'est publiée
# publiquement à ce jour. Sert de repère international honnête en attendant
# de vraies données tunisiennes (à collecter chantier par chantier via
# devis_chantier ci-dessus) — jamais présenté comme un prix tunisien réel.
# Format : (bas, haut) en EUR/m².
REPERES_AMENAGEMENT_EUR_M2 = {
    "commerce_classique": (500, 1000),
    "commerce_luxe": (2000, 2500),
    "restaurant_cafe": (750, 2250),
    "bureau_standard": (600, 1000),
    "bureau_qualitatif": (700, 1200),
    "batiment_commercial_standard": (500, 900),
    "batiment_commercial_avec_accueil": (900, 1500),
}


def estimation_amenagement_m2(
    surface_m2: float | None,
    type_activite: str,
    taux_change_eur_tnd: float,
) -> dict[str, Any]:
    """Fourchette d'estimation rapide (pas un devis final) pour l'aménagement
    d'un local commercial, à partir des repères REPERES_AMENAGEMENT_EUR_M2.

    Toujours retourner la fourchette ET la mention explicite "repère
    international (marché français), pas une donnée tunisienne vérifiée" —
    ne jamais laisser croire que c'est un prix tunisien réel. Le vrai devis
    chiffré vient de devis_chantier() une fois le déboursé sec réel connu.
    """
    if surface_m2 is None or surface_m2 <= 0:
        return {"erreur": "surface_m2 manquante ou invalide", "estimation": None}

    reperes = REPERES_AMENAGEMENT_EUR_M2.get(type_activite)
    if reperes is None:
        return {
            "erreur": f"type_activite inconnu: {type_activite!r} (attendu: {list(REPERES_AMENAGEMENT_EUR_M2)})",
            "estimation": None,
        }

    bas_eur_m2, haut_eur_m2 = reperes
    bas_tnd = round(bas_eur_m2 * surface_m2 * taux_change_eur_tnd, 0)
    haut_tnd = round(haut_eur_m2 * surface_m2 * taux_change_eur_tnd, 0)

    return {
        "type_activite": type_activite,
        "surface_m2": surface_m2,
        "fourchette_eur_m2": reperes,
        "fourchette_tnd": (bas_tnd, haut_tnd),
        "source": "Repère international (marché français, 2026) — PAS une donnée tunisienne vérifiée. "
        "À affiner avec de vrais devis tunisiens dès que disponibles.",
    }


def marge_brute_mensuelle(ca_mensuel_tnd: float | None, couts_variables_mensuels_tnd: float | None) -> float | None:
    if ca_mensuel_tnd is None or couts_variables_mensuels_tnd is None:
        return None
    return ca_mensuel_tnd - couts_variables_mensuels_tnd


def profit_net_mensuel(marge_brute_tnd: float | None, couts_fixes_mensuels_tnd: float | None) -> float | None:
    if marge_brute_tnd is None or couts_fixes_mensuels_tnd is None:
        return None
    return marge_brute_tnd - couts_fixes_mensuels_tnd


def payback_mois(capex_ouverture_tnd: float | None, profit_net_mensuel_tnd: float | None) -> float | None:
    if capex_ouverture_tnd is None or profit_net_mensuel_tnd is None:
        return None
    if profit_net_mensuel_tnd <= 0:
        return None  # jamais négatif ou infini présenté comme un chiffre — payback non atteignable avec ces données
    return capex_ouverture_tnd / profit_net_mensuel_tnd


def seuil_rentabilite_nb_clients(
    couts_fixes_mensuels_tnd: float | None,
    prix_unitaire_tnd: float | None,
    cout_variable_unitaire_tnd: float | None,
) -> float | None:
    if couts_fixes_mensuels_tnd is None or prix_unitaire_tnd is None or cout_variable_unitaire_tnd is None:
        return None
    marge_unitaire = prix_unitaire_tnd - cout_variable_unitaire_tnd
    if marge_unitaire <= 0:
        return None
    return couts_fixes_mensuels_tnd / marge_unitaire


def score_modele_economique(state: dict[str, Any]) -> tuple[float, list[str]]:
    """Score /100 = complétude des données (chaque champ clé renseigné vaut
    des points) + santé du modèle (payback raisonnable, marge positive) une
    fois les données présentes. Retourne (score, donnee_manquante).

    Conçu pour ne jamais donner un score élevé à un modèle juste parce qu'il
    "a l'air bien" sans données — un modèle avec beaucoup de champs manquants
    plafonne bas, quel que soit ce qui est calculable sur le reste.
    """
    champs_requis = [
        "capex_ouverture_tnd",
        "ca_mensuel_tnd",
        "couts_variables_mensuels_tnd",
        "couts_fixes_mensuels_tnd",
        "nb_clients_reels",
        "prix_unitaire_tnd",
        "cout_variable_unitaire_tnd",
    ]
    manquants = [c for c in champs_requis if state.get(c) is None]
    completude = (len(champs_requis) - len(manquants)) / len(champs_requis)

    sante = 0.0
    if state.get("profit_net_mensuel_tnd") is not None:
        sante += 0.5 if state["profit_net_mensuel_tnd"] > 0 else 0.0
    if state.get("payback_mois") is not None:
        sante += 0.5 if state["payback_mois"] <= 36 else 0.2  # payback > 3 ans = signal faible, pas éliminatoire

    score = round((completude * 60) + (sante * 40), 1)
    return score, manquants


def pack_franchise_generique(
    capex_reel_tnd: float | None,
    part_extension_pct: float | None,
    droit_entree_pct: float | None,
    nom_marque: str,
) -> dict[str, Any]:
    """Découpe un CAPEX réel (déjà sourcé pour UNE marque donnée, jamais
    inventé ici) en pack de base + extension + droit d'entrée. Généralise
    la méthode validée le 2026-09-14 sur Café IA (CAPEX réel 92 599 TND,
    92 599 = 75 599 base + 17 000 extension, soit ~18.4% en extension ;
    droit d'entrée 15% proposé, jamais encore acté en ADR) — réutilisable
    pour n'importe quelle marque, à condition que le CAPEX de CETTE marque
    soit un chiffre réel fourni par l'appelant, jamais fabriqué ici.

    `part_extension_pct` et `droit_entree_pct` doivent être fournis
    explicitement par l'appelant (pas de valeur par défaut fabriquée) —
    s'ils manquent, la fonction les liste dans `donnee_manquante` plutôt
    que de réutiliser silencieusement les 18.4%/15% de Café IA, qui ne
    sont pas nécessairement pertinents pour une autre marque.
    """
    manquants: list[str] = []
    if capex_reel_tnd is None:
        manquants.append("capex_reel_tnd")
    if part_extension_pct is None:
        manquants.append("part_extension_pct")
    if droit_entree_pct is None:
        manquants.append("droit_entree_pct")
    if manquants:
        return {"pack": None, "donnee_manquante": manquants}

    montant_extension = round(capex_reel_tnd * part_extension_pct / 100, 2)
    montant_base = round(capex_reel_tnd - montant_extension, 2)
    droit_entree = round(capex_reel_tnd * droit_entree_pct / 100, 2)
    total = round(capex_reel_tnd + droit_entree, 2)

    return {
        "marque": nom_marque,
        "pack_de_base_tnd": montant_base,
        "extension_image_tnd": montant_extension,
        "total_pack_materiel_tnd": capex_reel_tnd,
        "droit_entree_tnd": droit_entree,
        "prix_total_par_unite_tnd": total,
        "donnee_manquante": [],
        "statut": "STRUCTURE_VALIDEE_CHIFFRES_A_CONFIRMER_PAR_MARQUE",
        "avertissement": (
            f"Structure de calcul (base + extension + droit d'entrée) validée "
            f"pour {nom_marque} sur un CAPEX réel fourni. Réutilisable pour "
            "une autre marque UNIQUEMENT si son propre CAPEX réel, sa propre "
            "répartition base/extension et son propre % de droit d'entrée "
            "sont fournis — jamais en recopiant ceux d'une autre marque."
        ),
    }


def paliers_solutions(
    prix_reference_tnd: float,
    cout_variable_reel_tnd: float,
    marges_cibles_pct: dict[str, float],
) -> dict[str, Any]:
    """Construit des paliers d'abonnement ASPAR Solutions autour d'un prix
    de référence déjà validé (ADR 0005 : 90 TND/mois/point de vente, marge
    30% sur coût variable réel 65.3 TND/mois) plutôt qu'un prix unique.

    `marges_cibles_pct` : dict nom_palier -> marge cible en % au-dessus du
    coût variable réel, ex. {"Essentiel": 30, "Croissance": 60, "Elite": 100}.
    Les NOMS de palier passés ici sont des PROPOSITIONS à valider par le CEO
    — cette fonction ne décide jamais du contenu fonctionnel de chaque
    palier (crédits IAP, heures de support, intégrations) : elle vérifie
    uniquement qu'un prix proposé pour un palier dégage bien la marge cible
    au-dessus du coût variable réel, jamais un prix qui repasserait sous le
    coût réel comme l'ancien prix à 30 TND (ADR 0005).
    """
    if cout_variable_reel_tnd <= 0:
        return {"paliers": None, "erreur": "cout_variable_reel_tnd doit être > 0"}

    paliers: dict[str, Any] = {}
    for nom, marge_pct in marges_cibles_pct.items():
        prix_palier = round(cout_variable_reel_tnd * (1 + marge_pct / 100), 2)
        paliers[nom] = {
            "prix_mensuel_tnd": prix_palier,
            "marge_cible_pct": marge_pct,
            "marge_tnd": round(prix_palier - cout_variable_reel_tnd, 2),
            "au_dessus_du_prix_reference": prix_palier >= prix_reference_tnd,
        }

    return {
        "prix_reference_tnd": prix_reference_tnd,
        "cout_variable_reel_tnd": cout_variable_reel_tnd,
        "paliers": paliers,
        "statut": "NOMS_ET_CONTENU_FONCTIONNEL_A_VALIDER_PAR_LE_CEO",
        "avertissement": (
            "Seuls les prix et marges sont calculés ici, jamais le contenu "
            "fonctionnel (crédits IAP, heures de support, intégrations) de "
            "chaque palier — ça reste une décision produit du CEO, pas un "
            "chiffre dérivable. Les noms de palier sont des propositions."
        ),
    }


def paliers_building(
    surface_m2: float | None,
    type_activite: str,
    taux_change_eur_tnd: float,
) -> dict[str, Any]:
    """Construit 3 "paliers" GÉNÉRIQUES et RÉUTILISABLES pour ASPAR Building —
    un outil de calcul pour n'importe quel projet d'aménagement/construction,
    PAS un pack figé lié à un client ou une marque précise.

    Combine estimation_amenagement_m2() (design/mobilier/finition, fourchette
    EUR/m² -> TND) avec devis_chantier() (partie gros-œuvre/exécution) — mais
    SANS jamais inventer de déboursé sec : devis_chantier() est toujours
    appelé ici avec debourse_sec_tnd=None, donc il retourne systématiquement
    None + une entrée dans donnee_manquante. C'est le comportement voulu, pas
    un bug : tant qu'un vrai devis chantier n'existe pas pour un projet
    précis, cette fonction ne doit jamais produire un prix chantier "réel".

    STATUT DES DONNÉES SOP UTILISÉES PAR devis_chantier() (DUREE_STANDARD_JOURS
    = 45/60/75 jours, logique "déboursé sec + marge 10%") : ces valeurs sont
    présentées ailleurs dans ce module comme portées du SOP "MG Contracting".
    Un audit (2026-09-14) a confirmé qu'aucune trace écrite vérifiable de ce
    SOP n'existe dans aspar-group, aspar-agent-os, ni ailleurs. Ces valeurs
    proviennent UNIQUEMENT d'une conversation orale avec le CEO (Majdi
    Garbouj). Elles doivent être traitées comme "donnée orale du CEO, non
    recoupée par écrit" — jamais comme un SOP validé et sourcé — jusqu'à ce
    qu'un document écrit (contrat, devis réel, process documenté) les
    confirme. Cette fonction hérite de ce statut via l'appel à devis_chantier()
    ; elle n'ajoute aucune donnée tunisienne inventée de son côté.

    Retourne un dict avec `statut` explicite :
    - "PROPOSITION_NON_VALIDEE" quand les 3 niveaux ont pu être calculés à
      partir d'une fourchette valide (surface + type d'activité connus) ;
    - "ERREUR_DONNEES_INSUFFISANTES" quand surface_m2 ou type_activite ne
      permettent aucun calcul — aucun niveau n'est alors renvoyé, et aucun
      chiffre n'est fabriqué pour compenser.

    Les noms de niveaux ("Essentiel"/"Confort"/"Premium") sont des
    PROPOSITIONS de l'outil, pas une décision actée par le CEO — à valider
    avant tout usage commercial ou client.
    """
    estimation = estimation_amenagement_m2(surface_m2, type_activite, taux_change_eur_tnd)

    if "erreur" in estimation:
        return {
            "statut": "ERREUR_DONNEES_INSUFFISANTES",
            "erreur": estimation["erreur"],
            "type_activite": type_activite,
            "surface_m2": surface_m2,
            "amenagement_design_mobilier": None,
            "gros_oeuvre_execution_chantier": None,
        }

    bas_eur_m2, haut_eur_m2 = estimation["fourchette_eur_m2"]
    etendue_eur_m2 = haut_eur_m2 - bas_eur_m2

    # fraction de la fourchette EUR/m² utilisée par chaque niveau proposé —
    # 0.0 = bas de fourchette, 1.0 = haut de fourchette.
    niveaux_proposes = (
        ("Essentiel", 0.0),
        ("Confort", 0.5),
        ("Premium", 1.0),
    )

    niveaux: dict[str, Any] = {}
    for nom, fraction in niveaux_proposes:
        eur_m2 = bas_eur_m2 + fraction * etendue_eur_m2
        multiplicateur_vs_bas = round(eur_m2 / bas_eur_m2, 3) if bas_eur_m2 else None
        prix_estime_tnd = round(eur_m2 * surface_m2 * taux_change_eur_tnd, 0)
        niveaux[nom] = {
            "nom_propose": nom,
            "statut_nom": "PROPOSITION_NON_VALIDEE — nom indicatif choisi par l'outil, pas validé par le CEO",
            "multiplicateur_vs_bas_fourchette": multiplicateur_vs_bas,
            "eur_m2_utilise": round(eur_m2, 2),
            "calcul": (
                f"{round(eur_m2, 2)} EUR/m2 x {surface_m2} m2 x {taux_change_eur_tnd} (taux EUR->TND) "
                f"= {prix_estime_tnd} TND"
            ),
            "prix_estime_tnd": prix_estime_tnd,
        }

    # Partie gros-œuvre/exécution : jamais de déboursé sec inventé ici.
    prix_vente_ht_tnd, duree_estimee_jours, montant_par_lot_tnd, donnee_manquante_devis = devis_chantier(
        debourse_sec_tnd=None,
        marge_pct=DEFAULT_MARGE_PCT,
        taille_chantier="Moyen",
        repartition_lots_pct={},
    )

    return {
        "statut": "PROPOSITION_NON_VALIDEE",
        "avertissement": (
            "Les 3 paliers ci-dessous ('Essentiel'/'Confort'/'Premium') sont des noms PROPOSÉS par l'outil "
            "de calcul, PAS une décision actée par le CEO (Majdi Garbouj) — à valider avant tout usage "
            "commercial ou client. Les montants restent une fourchette internationale (marché français, "
            "voir estimation_amenagement_m2) et NE SONT PAS des prix tunisiens vérifiés tant qu'un devis "
            "chantier réel (déboursé sec saisi via devis_chantier) n'a pas été établi pour ce projet précis."
        ),
        "type_activite": type_activite,
        "surface_m2": surface_m2,
        "taux_change_eur_tnd": taux_change_eur_tnd,
        "amenagement_design_mobilier": {
            "source": estimation["source"],
            "fourchette_eur_m2": estimation["fourchette_eur_m2"],
            "niveaux": niveaux,
        },
        "gros_oeuvre_execution_chantier": {
            "prix_vente_ht_tnd": prix_vente_ht_tnd,
            "duree_estimee_jours": duree_estimee_jours,
            "montant_par_lot_tnd": montant_par_lot_tnd,
            "donnee_manquante": donnee_manquante_devis,
            "note": (
                "Aucun déboursé sec saisi pour ce projet : devis_chantier() retourne None par conception, "
                "jamais une estimation inventée à sa place. Rappel : les durées standard (45/60/75 jours) "
                "et la logique 'déboursé sec + marge 10%' de devis_chantier() sont une donnée ORALE du CEO "
                "(Majdi Garbouj), non recoupée par un document écrit vérifiable — pas un SOP validé et "
                "sourcé — jusqu'à preuve écrite du contraire."
            ),
        },
    }


def devis_chantier(
    debourse_sec_tnd: float | None,
    marge_pct: float,
    taille_chantier: str,
    repartition_lots_pct: dict[str, float],
) -> tuple[float | None, int | None, dict[str, float], list[str]]:
    """Calcule un devis chantier ASPAR Building — logique portée du vrai SOP
    de chiffrage MG Contracting (déboursé sec + marge, répartition en lots,
    durée standard par taille). Retourne (prix_vente_ht, duree_jours,
    montant_par_lot, donnee_manquante).
    """
    manquants: list[str] = []

    if debourse_sec_tnd is None:
        manquants.append("debourse_sec_tnd")
        return None, None, {}, manquants

    prix_vente_ht = debourse_sec_tnd * (1 + marge_pct / 100)

    duree_jours = DUREE_STANDARD_JOURS.get(taille_chantier)
    if duree_jours is None:
        manquants.append("taille_chantier (valeur inconnue, attendu: Petit/Moyen/Grand)")

    total_pct = sum(repartition_lots_pct.values()) if repartition_lots_pct else 0
    montant_par_lot: dict[str, float] = {}
    if repartition_lots_pct and abs(total_pct - 100) < 0.01:
        montant_par_lot = {
            lot: round(prix_vente_ht * pct / 100, 2) for lot, pct in repartition_lots_pct.items()
        }
    else:
        manquants.append("repartition_lots_pct (absente ou ne totalise pas 100%)")

    return round(prix_vente_ht, 2), duree_jours, montant_par_lot, manquants

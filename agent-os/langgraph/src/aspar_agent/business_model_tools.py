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

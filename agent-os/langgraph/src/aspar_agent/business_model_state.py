"""State for ASPAR's own business-line modeling (Solutions, Cabinet, Building,
future lines) — distinct from study_state.py, which models a THIRD-PARTY
concept being studied (Café IA, Elionor). This models ASPAR's own economics.

Structure ported from the real Notion framework "Business models — ASPAR INC"
(ASPAR Business / Étude / Modèles): CAPEX d'ouverture, coûts, MRR/ARR net,
payback, profit net, score /100 — but reimplemented in tested Python, never
as a Notion formula/rollup (ADR 0004: Notion's formula engine is confirmed to
return opaque, unresolvable references through its MCP connector).

Hard rule enforced by this module and its nodes: a value that has no real
input is never estimated or invented — it is listed in `donnee_manquante`
and every computation depending on it is skipped, not guessed.
"""

from __future__ import annotations

from typing import Any

from typing_extensions import TypedDict


class BusinessModelState(TypedDict, total=False):
    entite: str  # "ASPAR Solutions" | "ASPAR Business — Cabinet" | "ASPAR Building" | ...

    # Investissement de lancement (réel, sourcé — jamais estimé)
    capex_ouverture_tnd: float | None

    # Économie mensuelle réelle
    ca_mensuel_tnd: float | None
    couts_variables_mensuels_tnd: float | None
    couts_fixes_mensuels_tnd: float | None

    # Unité économique (pour un seuil de rentabilité en nombre de clients/missions)
    nb_clients_reels: int | None
    prix_unitaire_tnd: float | None
    cout_variable_unitaire_tnd: float | None

    # Résultats calculés (jamais saisis à la main — toujours dérivés, ou absents)
    marge_brute_mensuelle_tnd: float | None
    profit_net_mensuel_tnd: float | None
    payback_mois: float | None
    seuil_rentabilite_nb_clients: float | None
    score_modele_economique: float | None  # /100, reflète aussi la complétude des données

    donnee_manquante: list[str]  # noms des champs sans valeur réelle disponible
    trace: list[str]


class DevisChantierState(TypedDict, total=False):
    """État pour le calcul de devis Building — logique de déboursé sec + marge,
    4 lots, durée standard par taille de chantier.

    STATUT DE LA SOURCE (corrigé le 2026-09-14) : cette logique a été présentée
    précédemment comme portée d'un "SOP réel MG Contracting" écrit et
    consultable. Un audit du 2026-09-14 (recherche exhaustive dans
    AsparGroup/aspar-group, AsparGroup/aspar-agent-os, et GitHub code search
    sur l'organisation) n'a trouvé AUCUN document écrit de ce SOP nulle part.
    Les valeurs (marge 10%, durées Petit 45j/Moyen 60j/Grand 75j, 4 lots) sont
    une donnée ORALE du CEO (Majdi Garbouj), non recoupée par écrit à ce jour
    — pas un SOP client validé et sourcé. À traiter comme telle tant qu'un
    document MG Contracting réel n'est pas localisé ou que ce SOP n'est pas
    formellement rédigé et validé comme référence ASPAR Building.
    """

    debourse_sec_tnd: float | None
    marge_pct: float  # défaut 10%, cohérent avec le SOP source
    taille_chantier: str  # "Petit" | "Moyen" | "Grand"
    repartition_lots_pct: dict[str, float]  # ex: {"Génie civil": 40, "Agencement": 35, ...}

    prix_vente_ht_tnd: float | None
    duree_estimee_jours: int | None
    montant_par_lot_tnd: dict[str, float]
    donnee_manquante: list[str]

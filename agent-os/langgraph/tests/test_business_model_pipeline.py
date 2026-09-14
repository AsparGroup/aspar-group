"""Tests for the ASPAR business-line modeling pipeline, using the real
data found in Notion on 2026-09-13 (ASPAR Solutions pricing, Cabinet's one
real invoice) plus a fully-empty ASPAR Building case — proving the pipeline
never fabricates a number when data is missing.
"""

from aspar_agent.business_model_graph import build_business_model_graph
from aspar_agent.business_model_tools import devis_chantier, estimation_amenagement_m2


def invoke(payload: dict, thread_id: str):
    graph = build_business_model_graph()
    return graph.invoke(payload, {"configurable": {"thread_id": thread_id}})


def test_aspar_solutions_real_pricing_but_missing_cost_data():
    """Real: 30 TND/mois/point de vente (page produit ASPAR Solutions,
    Notion). CAPEX dev, coût support réel, nombre de clients réels : aucun
    trouvé — le score doit rester bas et lister ces champs comme manquants,
    pas les deviner à partir du seul prix public.
    """
    result = invoke(
        {
            "entite": "ASPAR Solutions",
            "prix_unitaire_tnd": 30,
        },
        "solutions-donnees-reelles",
    )
    assert "capex_ouverture_tnd" in result["donnee_manquante"]
    assert "ca_mensuel_tnd" in result["donnee_manquante"]
    assert "nb_clients_reels" in result["donnee_manquante"]
    assert result["score_modele_economique"] < 40  # forte incomplétude, score plafonné bas


def test_aspar_cabinet_real_single_invoice_no_consolidated_revenue():
    """Réel : une seule facture historique connue (FAC-2023-06, 7 800 TND,
    5% de 156 000 TND documentés) — pas un CA mensuel récurrent. On ne doit
    jamais transformer ce chiffre ponctuel en un faux "ca_mensuel_tnd".
    """
    result = invoke(
        {
            "entite": "ASPAR Business — Cabinet",
            # aucun ca_mensuel_tnd fourni : le seul chiffre réel (7800 TND) est
            # une facture historique ponctuelle, pas un revenu mensuel récurrent
        },
        "cabinet-donnees-reelles",
    )
    assert "ca_mensuel_tnd" in result["donnee_manquante"]
    assert result["profit_net_mensuel_tnd"] is None


def test_aspar_building_entirely_missing_data():
    """Réel : aucune donnée trouvée nulle part pour ASPAR Building en tant
    que ligne de business — le pipeline doit le refléter honnêtement (tous
    les champs manquants, score minimal), pas inventer une estimation.
    """
    result = invoke({"entite": "ASPAR Building"}, "building-aucune-donnee")
    assert len(result["donnee_manquante"]) == 7  # les 7 champs requis, tous absents
    assert result["score_modele_economique"] == 0.0


def test_devis_chantier_uses_real_mg_contracting_sop_formula():
    """Formule réelle du SOP MG Contracting : déboursé sec + marge 10%
    (exemple du SOP : 250 000 -> 275 000 TND)."""
    prix, duree, montants, manquants = devis_chantier(
        debourse_sec_tnd=250_000,
        marge_pct=10.0,
        taille_chantier="Grand",
        repartition_lots_pct={
            "Génie civil": 40,
            "Agencement": 35,
            "Ameublement": 15,
            "Signalétique": 10,
        },
    )
    assert prix == 275_000.0
    assert duree == 75  # durée standard "Grand" du SOP
    assert montants["Génie civil"] == 110_000.0
    assert manquants == []


def test_devis_chantier_missing_debourse_sec_never_guesses():
    prix, duree, montants, manquants = devis_chantier(
        debourse_sec_tnd=None,
        marge_pct=10.0,
        taille_chantier="Petit",
        repartition_lots_pct={},
    )
    assert prix is None
    assert "debourse_sec_tnd" in manquants


def test_estimation_amenagement_m2_never_claims_tunisian_data():
    """Aucune donnée tunisienne détaillée n'est publiée publiquement (recherche
    du 2026-09-14) — l'estimation doit toujours dire explicitement qu'elle
    utilise un repère français, jamais laisser croire à un prix tunisien vérifié.
    """
    result = estimation_amenagement_m2(surface_m2=80, type_activite="restaurant_cafe", taux_change_eur_tnd=3.4)
    assert "PAS une donnée tunisienne vérifiée" in result["source"]
    assert result["fourchette_tnd"] == (204000.0, 612000.0)


def test_estimation_amenagement_m2_missing_surface():
    result = estimation_amenagement_m2(surface_m2=None, type_activite="restaurant_cafe", taux_change_eur_tnd=3.4)
    assert result["estimation"] is None
    assert "erreur" in result


def test_estimation_amenagement_m2_unknown_activity():
    result = estimation_amenagement_m2(surface_m2=50, type_activite="usine_chimique", taux_change_eur_tnd=3.4)
    assert "erreur" in result

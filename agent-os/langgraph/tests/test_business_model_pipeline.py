"""Tests for the ASPAR business-line modeling pipeline, using the real
data found in Notion on 2026-09-13 (ASPAR Solutions pricing, Cabinet's one
real invoice) plus a fully-empty ASPAR Building case — proving the pipeline
never fabricates a number when data is missing.
"""

from aspar_agent.business_model_graph import build_business_model_graph
from aspar_agent.business_model_tools import (
    devis_chantier,
    estimation_amenagement_m2,
    pack_franchise_generique,
    paliers_building,
    paliers_solutions,
)


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


def test_pack_franchise_generique_reproduces_cafe_ia_real_numbers():
    """Vérifie que la fonction généralisée reproduit exactement le calcul
    Café IA déjà validé le 2026-09-14 (CAPEX réel 92 599 TND, extension
    17 000 TND soit ~18.36%, droit d'entrée 15%)."""
    result = pack_franchise_generique(
        capex_reel_tnd=92_599,
        part_extension_pct=17_000 / 92_599 * 100,
        droit_entree_pct=15.0,
        nom_marque="Café IA",
    )
    assert result["extension_image_tnd"] == 17_000.0
    assert result["pack_de_base_tnd"] == 75_599.0
    assert result["droit_entree_tnd"] == round(92_599 * 0.15, 2)
    assert result["donnee_manquante"] == []


def test_pack_franchise_generique_never_reuses_another_brand_split():
    """Sans CAPEX réel fourni pour la nouvelle marque, la fonction ne doit
    jamais réutiliser silencieusement les chiffres Café IA — tout doit
    ressortir en donnee_manquante."""
    result = pack_franchise_generique(
        capex_reel_tnd=None,
        part_extension_pct=None,
        droit_entree_pct=None,
        nom_marque="Nouvelle Marque X",
    )
    assert result["pack"] is None
    assert set(result["donnee_manquante"]) == {
        "capex_reel_tnd",
        "part_extension_pct",
        "droit_entree_pct",
    }


def test_paliers_solutions_never_prices_below_real_variable_cost():
    """Reproduit l'erreur ADR 0005 (30 TND < 65.3 TND coût réel = perte) :
    un palier dont le prix calculé descendrait sous le coût variable réel
    ne doit jamais pouvoir être généré silencieusement — la marge cible
    minimale doit toujours être > 0."""
    result = paliers_solutions(
        prix_reference_tnd=90.0,
        cout_variable_reel_tnd=65.3,
        marges_cibles_pct={"Essentiel": 30, "Croissance": 60, "Elite": 100},
    )
    prix = [p["prix_mensuel_tnd"] for p in result["paliers"].values()]
    assert all(p > 65.3 for p in prix)
    assert prix == sorted(prix)  # paliers strictement croissants
    assert result["paliers"]["Essentiel"]["prix_mensuel_tnd"] == 84.89


def test_paliers_solutions_invalid_cost_never_produces_tiers():
    result = paliers_solutions(
        prix_reference_tnd=90.0,
        cout_variable_reel_tnd=0,
        marges_cibles_pct={"Essentiel": 30},
    )
    assert result["paliers"] is None
    assert "erreur" in result


def test_paliers_building_nominal_case_produces_increasing_unvalidated_tiers():
    """Cas nominal : surface + type d'activité valides -> 3 niveaux calculés,
    strictement croissants (Essentiel < Confort < Premium), et le statut doit
    dire sans ambiguïté que ce sont des propositions, pas une décision actée."""
    result = paliers_building(surface_m2=100, type_activite="bureau_standard", taux_change_eur_tnd=3.4)

    assert result["statut"] == "PROPOSITION_NON_VALIDEE"
    niveaux = result["amenagement_design_mobilier"]["niveaux"]
    assert set(niveaux) == {"Essentiel", "Confort", "Premium"}

    prix = [niveaux["Essentiel"]["prix_estime_tnd"], niveaux["Confort"]["prix_estime_tnd"], niveaux["Premium"]["prix_estime_tnd"]]
    assert prix == sorted(prix)
    assert prix[0] < prix[1] < prix[2]  # strictement croissant, pas seulement non-décroissant

    # multiplicateurs explicites et croissants eux aussi
    mults = [niveaux[n]["multiplicateur_vs_bas_fourchette"] for n in ("Essentiel", "Confort", "Premium")]
    assert mults == sorted(mults)
    assert niveaux["Essentiel"]["multiplicateur_vs_bas_fourchette"] == 1.0

    # chaque niveau porte explicitement la mention "non validé"
    for n in niveaux.values():
        assert "PROPOSITION_NON_VALIDEE" in n["statut_nom"]


def test_paliers_building_missing_surface_raises_clean_error_no_fabricated_number():
    result = paliers_building(surface_m2=None, type_activite="bureau_standard", taux_change_eur_tnd=3.4)

    assert result["statut"] == "ERREUR_DONNEES_INSUFFISANTES"
    assert "erreur" in result
    assert result["amenagement_design_mobilier"] is None
    assert result["gros_oeuvre_execution_chantier"] is None


def test_paliers_building_unknown_type_activite_raises_clean_error():
    result = paliers_building(surface_m2=80, type_activite="usine_chimique", taux_change_eur_tnd=3.4)

    assert result["statut"] == "ERREUR_DONNEES_INSUFFISANTES"
    assert "erreur" in result
    assert result["amenagement_design_mobilier"] is None


def test_paliers_building_never_mixes_real_devis_chantier_without_debourse_sec():
    """Preuve que l'estimation indicative (design/mobilier) n'est jamais
    mélangée à un vrai devis chantier tant que debourse_sec_tnd n'est pas
    fourni : la partie gros-œuvre doit rester None + donnee_manquante, et
    aucun niveau proposé ne doit porter un champ de prix chantier réel."""
    result = paliers_building(surface_m2=100, type_activite="restaurant_cafe", taux_change_eur_tnd=3.4)

    gros_oeuvre = result["gros_oeuvre_execution_chantier"]
    assert gros_oeuvre["prix_vente_ht_tnd"] is None
    assert gros_oeuvre["duree_estimee_jours"] is None
    assert gros_oeuvre["montant_par_lot_tnd"] == {}
    assert "debourse_sec_tnd" in gros_oeuvre["donnee_manquante"]

    # aucun niveau d'aménagement ne doit contenir un champ de devis chantier réel
    for niveau in result["amenagement_design_mobilier"]["niveaux"].values():
        assert "prix_vente_ht_tnd" not in niveau
        assert "debourse_sec_tnd" not in niveau

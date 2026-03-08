"""
MCP Tool Bridge -- connects agent tool registries to MCP server functions.

Instead of running MCP servers as separate processes and connecting via the
MCP protocol (which requires stdio/SSE transport), we import the tool
functions directly and register them as callables in agent tool registries.

Each MCP server module defines async (or sync) functions decorated with
``@mcp.tool()``.  These are ordinary Python functions that we can import
and invoke directly -- no protocol overhead needed.

Usage::

    from src.mcp_bridge import wire_agent_tools
    agent = create_statistical_genetics_agent()
    wire_agent_tools(agent)
    # agent._tool_registry is now populated with callable implementations
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from src.agents.base_agent import BaseAgent

logger = logging.getLogger("lumi.mcp_bridge")

# ===================================================================
# Import all MCP server tool functions
# ===================================================================

# -- Genomics ----------------------------------------------------------
from src.mcp_servers.genomics.server import (
    query_target_disease,
    get_target_info,
    query_gwas_associations,
    query_gene_variants,
    query_clinvar_gene,
    get_gene_info,
    get_variant_consequences,
    query_rsid,
    query_pharmgkb_gene,
)

# -- Expression --------------------------------------------------------
from src.mcp_servers.expression.server import (
    get_gene_expression,
    get_protein_expression,
    get_pathology_data,
    query_gene_expression_single_cell,
    search_geo_datasets,
    get_eqtls,
    query_encode_experiments,
)

# -- Protein & Structure -----------------------------------------------
from src.mcp_servers.protein.server import (
    get_protein_info,
    search_proteins,
    get_protein_sequence,
    get_protein_features,
    search_structures,
    get_structure_info,
    get_binding_sites,
    get_predicted_structure,
    get_pae,
    get_protein_domains,
    search_domains_by_name,
    get_interactions,
    get_network,
    get_enrichment,
)

# -- Clinical & Drug ---------------------------------------------------
from src.mcp_servers.clinical.server import (
    search_trials,
    get_trial_details,
    search_trials_by_target,
    search_pubmed,
    get_article_details,
    get_target_compounds,
    get_compound_info,
    get_drug_info,
    search_adverse_events,
    get_drug_label,
    get_drug_label_sections,
)

# -- Literature --------------------------------------------------------
from src.mcp_servers.literature.server import (
    search_papers,
    get_paper_details,
    get_citations,
    get_references,
    get_author_papers,
    search_preprints,
    get_preprint_details,
    search_fulltext,
    get_article_citations,
)

# -- Safety & Toxicology -----------------------------------------------
from src.mcp_servers.safety.server import (
    query_gene_chemical_interactions,
    query_gene_disease_associations,
    query_chemical_diseases,
    query_toxicity_assays,
    get_side_effects,
    get_drug_indications,
    get_knockout_phenotypes,
    get_safety_summary,
)

# -- Protein Design ----------------------------------------------------
from src.mcp_servers.protein_design.server import (
    esm2_score_sequence,
    esm2_mutant_effect,
    esm2_embed,
    calculate_protein_properties,
    predict_solubility,
    predict_structure_alphafold,
    blast_sequence,
    calculate_cai,
    number_antibody,
    predict_developability,
)

# -- Pathways & Ontology -----------------------------------------------
from src.mcp_servers.pathways.server import (
    get_pathways_for_gene,
    get_pathway_details,
    pathway_enrichment,
    get_go_annotations,
    go_enrichment,
    get_kegg_pathways,
    get_pathway_genes,
    get_pathway_info,
    search_pathways,
)

# -- Biosecurity -------------------------------------------------------
from src.mcp_servers.biosecurity.server import (
    screen_against_select_agents,
    blast_protein,
    check_select_agent_list,
    scan_toxin_domains,
    screen_virulence_factors,
    check_bwc_compliance,
)

# -- Metabolic (requires COBRApy -- optional) --------------------------
_HAS_METABOLIC = False
try:
    from src.mcp_servers.metabolic.server import (
        run_fba,
        run_fva,
        simulate_gene_knockout,
        simulate_reaction_knockout,
        add_heterologous_pathway,
        list_available_models,
        get_model_info,
        get_model_reactions,
        optimize_codons,
        predict_expression_level,
    )
    _HAS_METABOLIC = True
except ImportError:
    logger.warning("Metabolic MCP server not available (missing cobra?)")

# -- BioRender / Figure Generation (requires mcp + Node.js -- optional) -
_HAS_BIORENDER = False
try:
    from src.mcp_servers.biorender.server import (
        generate_volcano_plot,
        generate_expression_heatmap,
        generate_pathway_diagram,
        generate_target_comparison_radar,
        generate_gene_expression_bar,
        generate_drug_target_sankey,
        generate_pipeline_flow,
        generate_moa_diagram,
        generate_literature_wordcloud,
        generate_confidence_distribution,
        generate_clinical_timeline,
        generate_category_pie,
        generate_venn_diagram,
        search_biorender_icons,
        search_biorender_templates,
        download_figure,
    )
    _HAS_BIORENDER = True
except ImportError:
    logger.warning("BioRender MCP server not available (missing mcp package or Node.js?)")

# -- Cheminformatics (requires RDKit -- optional) ----------------------
_HAS_CHEM = False
try:
    from src.mcp_servers.cheminformatics.server import (
        calculate_descriptors,
        check_drug_likeness,
        compute_fingerprint,
        compute_similarity,
        substructure_search,
        search_compound,
        get_compound_bioactivity,
        get_compound_safety,
        search_zinc,
        convert_molecule,
    )
    _HAS_CHEM = True
except ImportError:
    logger.warning("Cheminformatics MCP server not available (missing rdkit?)")


# ===================================================================
# Master tool registry: tool_name -> callable
# ===================================================================

TOOL_REGISTRY: dict[str, Callable] = {
    # --- Genomics ---
    "query_target_disease": query_target_disease,
    "get_target_info": get_target_info,
    "query_gwas_associations": query_gwas_associations,
    "query_gene_variants": query_gene_variants,
    "query_clinvar_gene": query_clinvar_gene,
    "get_gene_info": get_gene_info,
    "get_variant_consequences": get_variant_consequences,
    "query_rsid": query_rsid,
    "query_pharmgkb_gene": query_pharmgkb_gene,
    # --- Expression ---
    "get_gene_expression": get_gene_expression,
    "get_protein_expression": get_protein_expression,
    "get_pathology_data": get_pathology_data,
    "query_gene_expression_single_cell": query_gene_expression_single_cell,
    "search_geo_datasets": search_geo_datasets,
    "get_eqtls": get_eqtls,
    "query_encode_experiments": query_encode_experiments,
    # --- Protein & Structure ---
    "get_protein_info": get_protein_info,
    "search_proteins": search_proteins,
    "get_protein_sequence": get_protein_sequence,
    "get_protein_features": get_protein_features,
    "search_structures": search_structures,
    "get_structure_info": get_structure_info,
    "get_binding_sites": get_binding_sites,
    "get_predicted_structure": get_predicted_structure,
    "get_pae": get_pae,
    "get_protein_domains": get_protein_domains,
    "search_domains_by_name": search_domains_by_name,
    "get_interactions": get_interactions,
    "get_network": get_network,
    "get_enrichment": get_enrichment,
    # --- Clinical & Drug ---
    "search_trials": search_trials,
    "get_trial_details": get_trial_details,
    "search_trials_by_target": search_trials_by_target,
    "search_pubmed": search_pubmed,
    "get_article_details": get_article_details,
    "get_target_compounds": get_target_compounds,
    "get_compound_info": get_compound_info,
    "get_drug_info": get_drug_info,
    "search_adverse_events": search_adverse_events,
    "get_drug_label": get_drug_label,
    "get_drug_label_sections": get_drug_label_sections,
    # --- Literature ---
    "search_papers": search_papers,
    "get_paper_details": get_paper_details,
    "get_citations": get_citations,
    "get_references": get_references,
    "get_author_papers": get_author_papers,
    "search_preprints": search_preprints,
    "get_preprint_details": get_preprint_details,
    "search_fulltext": search_fulltext,
    "get_article_citations": get_article_citations,
    # --- Safety & Toxicology ---
    "query_gene_chemical_interactions": query_gene_chemical_interactions,
    "query_gene_disease_associations": query_gene_disease_associations,
    "query_chemical_diseases": query_chemical_diseases,
    "query_toxicity_assays": query_toxicity_assays,
    "get_side_effects": get_side_effects,
    "get_drug_indications": get_drug_indications,
    "get_knockout_phenotypes": get_knockout_phenotypes,
    "get_safety_summary": get_safety_summary,
    # --- Protein Design ---
    "esm2_score_sequence": esm2_score_sequence,
    "esm2_mutant_effect": esm2_mutant_effect,
    "esm2_embed": esm2_embed,
    "calculate_protein_properties": calculate_protein_properties,
    "predict_solubility": predict_solubility,
    "predict_structure_alphafold": predict_structure_alphafold,
    "blast_sequence": blast_sequence,
    "calculate_cai": calculate_cai,
    "number_antibody": number_antibody,
    "predict_developability": predict_developability,
    # --- Pathways & Ontology ---
    "get_pathways_for_gene": get_pathways_for_gene,
    "get_pathway_details": get_pathway_details,
    "pathway_enrichment": pathway_enrichment,
    "get_go_annotations": get_go_annotations,
    "go_enrichment": go_enrichment,
    "get_kegg_pathways": get_kegg_pathways,
    "get_pathway_genes": get_pathway_genes,
    "get_pathway_info": get_pathway_info,
    "search_pathways": search_pathways,
    # --- Biosecurity ---
    "screen_against_select_agents": screen_against_select_agents,
    "blast_protein": blast_protein,
    "check_select_agent_list": check_select_agent_list,
    "scan_toxin_domains": scan_toxin_domains,
    "screen_virulence_factors": screen_virulence_factors,
    "check_bwc_compliance": check_bwc_compliance,
}

# --- Metabolic (conditional) ---
if _HAS_METABOLIC:
    TOOL_REGISTRY.update({
        "run_fba": run_fba,
        "run_fva": run_fva,
        "simulate_gene_knockout": simulate_gene_knockout,
        "simulate_reaction_knockout": simulate_reaction_knockout,
        "add_heterologous_pathway": add_heterologous_pathway,
        "list_available_models": list_available_models,
        "get_model_info": get_model_info,
        "get_model_reactions": get_model_reactions,
        "optimize_codons": optimize_codons,
        "predict_expression_level": predict_expression_level,
    })

# --- BioRender / Figure Generation (conditional) ---
if _HAS_BIORENDER:
    TOOL_REGISTRY.update({
        "generate_volcano_plot": generate_volcano_plot,
        "generate_expression_heatmap": generate_expression_heatmap,
        "generate_pathway_diagram": generate_pathway_diagram,
        "generate_target_comparison_radar": generate_target_comparison_radar,
        "generate_gene_expression_bar": generate_gene_expression_bar,
        "generate_drug_target_sankey": generate_drug_target_sankey,
        "generate_pipeline_flow": generate_pipeline_flow,
        "generate_moa_diagram": generate_moa_diagram,
        "generate_literature_wordcloud": generate_literature_wordcloud,
        "generate_confidence_distribution": generate_confidence_distribution,
        "generate_clinical_timeline": generate_clinical_timeline,
        "generate_category_pie": generate_category_pie,
        "generate_venn_diagram": generate_venn_diagram,
        "search_biorender_icons": search_biorender_icons,
        "search_biorender_templates": search_biorender_templates,
        "download_figure": download_figure,
    })

# --- Cheminformatics (conditional) ---
if _HAS_CHEM:
    TOOL_REGISTRY.update({
        "calculate_descriptors": calculate_descriptors,
        "check_drug_likeness": check_drug_likeness,
        "compute_fingerprint": compute_fingerprint,
        "compute_similarity": compute_similarity,
        "substructure_search": substructure_search,
        "search_compound": search_compound,
        "get_compound_bioactivity": get_compound_bioactivity,
        "get_compound_safety": get_compound_safety,
        "search_zinc": search_zinc,
        "convert_molecule": convert_molecule,
    })


# ===================================================================
# Wiring function
# ===================================================================


def wire_agent_tools(agent: BaseAgent) -> None:
    """Register callable implementations for all tools defined in an agent's tool list.

    Iterates over ``agent.tools`` (the list of tool-definition dicts that
    are sent to the Anthropic API), looks up each tool name in the master
    :data:`TOOL_REGISTRY`, and registers the corresponding callable in
    ``agent._tool_registry`` so that :meth:`BaseAgent._call_tool` can
    invoke it.

    The built-in ``execute_code`` tool is skipped since it is handled
    directly by :class:`BaseAgent`.

    Args:
        agent: A specialist agent whose tools need callable implementations.
    """
    wired = 0
    skipped = 0
    missing: list[str] = []

    for tool_def in agent.tools:
        name = tool_def.get("name", "")
        if name == "execute_code":
            skipped += 1
            continue
        if name in TOOL_REGISTRY:
            agent._tool_registry[name] = TOOL_REGISTRY[name]
            wired += 1
        else:
            missing.append(name)

    tool_count = len(agent.tools) - skipped  # exclude execute_code
    if missing:
        logger.warning(
            "Agent '%s': %d/%d tools wired, %d missing: %s",
            agent.name,
            wired,
            tool_count,
            len(missing),
            ", ".join(missing),
        )
    else:
        logger.info(
            "Agent '%s': all %d tools wired successfully",
            agent.name,
            wired,
        )

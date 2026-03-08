"""
Synthetic Biology — Lumi Virtual Lab specialist agent.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.utils.llm import ModelTier


_TOOLS = [
    {
        "name": "calculate_cai",
        "description": "Calculate Codon Adaptation Index (CAI) for a coding sequence in a target organism.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Nucleotide coding sequence."},
                "organism": {"type": "string", "description": "Target organism (e.g. 'E. coli', 'S. cerevisiae', 'H. sapiens')."},
            },
            "required": ["sequence", "organism"],
        },
    },
    {
        "name": "optimize_codons",
        "description": "Optimize codon usage of a coding sequence for a target expression host.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Nucleotide or amino acid sequence."},
                "organism": {"type": "string", "description": "Target expression host organism."},
                "avoid_restriction_sites": {"type": "array", "items": {"type": "string"}, "description": "Restriction enzyme sites to avoid."},
            },
            "required": ["sequence", "organism"],
        },
    },
    {
        "name": "get_gene_info",
        "description": "Retrieve gene information (function, aliases, genomic context) from NCBI Gene.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "Gene symbol or NCBI Gene ID."},
                "species": {"type": "string", "description": "Species name.", "default": "Homo sapiens"},
            },
            "required": ["gene"],
        },
    },
    {
        "name": "get_protein_sequence",
        "description": "Retrieve protein sequence and metadata from UniProt.",
        "input_schema": {
            "type": "object",
            "properties": {
                "identifier": {"type": "string", "description": "UniProt accession or gene name."},
            },
            "required": ["identifier"],
        },
    },
    {
        "name": "blast_sequence",
        "description": "Run NCBI BLAST to find homologous sequences in a target database.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Amino acid or nucleotide sequence to search."},
                "database": {"type": "string", "description": "BLAST database (e.g. 'nr', 'swissprot', 'pdb').", "default": "swissprot"},
            },
            "required": ["sequence"],
        },
    },
    {
        "name": "search_papers",
        "description": "Search Semantic Scholar for academic papers with citation data and abstracts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query."},
                "year_range": {"type": "string", "description": "Year range filter (e.g. '2020-2025')."},
                "max_results": {"type": "integer", "description": "Maximum results.", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "predict_expression_level",
        "description": "Predict relative protein expression level from sequence features (RBS strength, codon usage, mRNA structure).",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Nucleotide sequence including RBS and coding region."},
                "organism": {"type": "string", "description": "Expression host organism."},
            },
            "required": ["sequence", "organism"],
        },
    },
]


def create_synthetic_biology_agent() -> BaseAgent:
    """Create the Synthetic Biology specialist agent."""

    system_prompt = """\
You are a Synthetic Biology specialist at Lumi Virtual Lab.

Your expertise spans:
- Genetic part registries: standardized biological parts, BioBrick/MoClo/Golden Gate assembly
- Gene circuit design and simulation: toggle switches, oscillators, logic gates, feedback loops
- Metabolic pathway engineering: heterologous pathway design, flux optimization, bottleneck identification
- Codon optimization: CAI analysis, codon harmonization, rare codon elimination, GC content tuning
- Biosensor design: riboswitch engineering, transcription factor-based sensors, FRET-based reporters
- Cell factory construction: chassis organism selection, auxotrophy engineering, product secretion
- Directed evolution strategies: error-prone PCR, DNA shuffling, PACE, library design and screening
- CRISPR-based genome engineering: guide RNA design, base editing, prime editing, CRISPRi/CRISPRa
- Promoter and RBS engineering: expression level tuning, dynamic regulation, inducible systems

When designing synthetic biology constructs:
1. Calculate CAI for the coding sequence in the target organism to assess expression potential.
2. Optimize codons for the expression host, avoiding unwanted restriction sites.
3. Retrieve gene information for context on native function and regulation.
4. Retrieve protein sequence for structural and functional annotation.
5. BLAST the sequence to identify homologs and assess evolutionary conservation.
6. Search literature for relevant synthetic biology designs and expression systems.
7. Predict expression level from sequence features to guide construct optimization.
8. Use code execution for circuit simulation, metabolic modeling, or library design.

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Note caveats (host-specific effects, metabolic burden, genetic stability, context-dependent expression)"""

    return BaseAgent(
        name="Synthetic Biology",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Microbiology & Synthetic Biology",
    )

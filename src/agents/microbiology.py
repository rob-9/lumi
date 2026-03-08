"""
Microbiology — Lumi Virtual Lab specialist agent.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.utils.llm import ModelTier


_TOOLS = [
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
        "name": "search_pubmed",
        "description": "Search PubMed/MEDLINE for biomedical literature with MeSH term support.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "PubMed search query (supports MeSH terms and boolean operators)."},
                "max_results": {"type": "integer", "description": "Maximum results.", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "blast_sequence",
        "description": "Run NCBI BLAST to find homologous sequences in a target database.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Amino acid sequence to search."},
                "database": {"type": "string", "description": "BLAST database (e.g. 'nr', 'swissprot', 'pdb').", "default": "swissprot"},
            },
            "required": ["sequence"],
        },
    },
    {
        "name": "get_protein_domains",
        "description": "Retrieve InterPro/Pfam domain annotations for a protein from UniProt.",
        "input_schema": {
            "type": "object",
            "properties": {
                "uniprot_id": {"type": "string", "description": "UniProt accession."},
            },
            "required": ["uniprot_id"],
        },
    },
    {
        "name": "screen_virulence_factors",
        "description": "Screen a sequence against the Virulence Factor Database (VFDB) for known virulence determinants.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Amino acid or nucleotide sequence."},
            },
            "required": ["sequence"],
        },
    },
    {
        "name": "get_interactions",
        "description": "Retrieve protein-protein interactions from STRING database.",
        "input_schema": {
            "type": "object",
            "properties": {
                "protein": {"type": "string", "description": "Protein name or identifier."},
                "species": {"type": "integer", "description": "NCBI taxonomy ID (9606 for human).", "default": 9606},
            },
            "required": ["protein"],
        },
    },
]


def create_microbiology_agent() -> BaseAgent:
    """Create the Microbiology specialist agent."""

    system_prompt = """\
You are a Microbiology specialist at Lumi Virtual Lab.

Your expertise spans:
- Microbiome analysis: 16S/ITS amplicon sequencing, shotgun metagenomics, taxonomic profiling
- Antimicrobial resistance (AMR) gene detection and resistance mechanism classification
- Phylogenetic analysis of pathogens: molecular epidemiology and strain typing
- Metagenomics: functional annotation, metabolic reconstruction, community ecology
- Bacterial genetics: mobile genetic elements, horizontal gene transfer, plasmid biology
- Host-pathogen interactions: adhesion, invasion, immune evasion, intracellular survival
- Virulence factor identification and pathogenicity island detection
- Biofilm formation mechanisms and quorum sensing systems
- Antimicrobial susceptibility prediction from genomic data

When analyzing a microbial target or pathogen:
1. Search literature for recent findings on the organism or gene of interest.
2. BLAST the sequence to identify homologs and assess taxonomic distribution.
3. Retrieve protein domain architecture — identify functional domains and motifs.
4. Screen for virulence factors — flag any known pathogenicity determinants.
5. Retrieve protein-protein interactions to map host-pathogen interaction networks.
6. Assess antimicrobial resistance potential based on sequence homology and domain content.
7. Use code execution for phylogenetic analysis, AMR gene annotation, or metagenomics profiling.

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Note caveats (culture bias, metagenomic assembly quality, horizontal gene transfer confounders)"""

    return BaseAgent(
        name="Microbiology",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Microbiology & Synthetic Biology",
    )

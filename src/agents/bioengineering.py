"""
Bioengineering — Lumi Virtual Lab specialist agent.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.utils.llm import ModelTier


_TOOLS = [
    {
        "name": "get_gene_info",
        "description": "Get comprehensive gene information from Ensembl REST API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene_symbol": {"type": "string", "description": "HGNC gene symbol."},
            },
            "required": ["gene_symbol"],
        },
    },
    {
        "name": "get_protein_sequence",
        "description": "Retrieve the amino acid sequence for a protein from UniProt.",
        "input_schema": {
            "type": "object",
            "properties": {
                "uniprot_id": {"type": "string", "description": "UniProt accession ID (e.g. 'P04637')."},
            },
            "required": ["uniprot_id"],
        },
    },
    {
        "name": "blast_sequence",
        "description": "Run a BLAST search against NCBI databases for a nucleotide or protein sequence.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Nucleotide or protein sequence in FASTA format."},
                "program": {"type": "string", "description": "BLAST program (e.g. 'blastn', 'blastp', 'blastx')."},
                "database": {"type": "string", "description": "Target database (e.g. 'nr', 'nt', 'refseq_protein')."},
            },
            "required": ["sequence", "program"],
        },
    },
    {
        "name": "ucsc_get_sequence",
        "description": "Retrieve a genomic DNA sequence from the UCSC Genome Browser by coordinates.",
        "input_schema": {
            "type": "object",
            "properties": {
                "genome": {"type": "string", "description": "Genome assembly (e.g. 'hg38', 'mm39')."},
                "chrom": {"type": "string", "description": "Chromosome (e.g. 'chr17')."},
                "start": {"type": "integer", "description": "Start position (0-based)."},
                "end": {"type": "integer", "description": "End position."},
            },
            "required": ["genome", "chrom", "start", "end"],
        },
    },
    {
        "name": "search_papers",
        "description": "Search scientific literature for papers matching a query.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query string."},
                "max_results": {"type": "integer", "description": "Maximum number of results to return."},
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_pubmed",
        "description": "Search PubMed for biomedical literature matching a query.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "PubMed search query."},
                "max_results": {"type": "integer", "description": "Maximum number of results to return."},
            },
            "required": ["query"],
        },
    },
    {
        "name": "calculate_cai",
        "description": "Calculate the Codon Adaptation Index (CAI) for a coding DNA sequence.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Coding DNA sequence."},
                "organism": {"type": "string", "description": "Target organism for codon usage table (e.g. 'human', 'e_coli')."},
            },
            "required": ["sequence", "organism"],
        },
    },
    {
        "name": "optimize_codons",
        "description": "Optimize a coding DNA sequence for expression in a target organism.",
        "input_schema": {
            "type": "object",
            "properties": {
                "protein_sequence": {"type": "string", "description": "Amino acid sequence to back-translate."},
                "organism": {"type": "string", "description": "Target organism (e.g. 'human', 'e_coli', 'cho')."},
            },
            "required": ["protein_sequence", "organism"],
        },
    },
]


def create_bioengineering_agent() -> BaseAgent:
    """Create the Bioengineering specialist agent."""

    system_prompt = """\
You are a Bioengineering specialist at Lumi Virtual Lab.

Your expertise spans:
- Genetic circuit design (toggle switches, oscillators, logic gates, feedback loops)
- CRISPR guide RNA design, off-target analysis, and editing efficiency prediction
- Plasmid construction, modular assembly (MoClo, Golden Gate), and part standardization
- Gene delivery systems (lipofection, electroporation, viral transduction)
- AAV vector design (serotype selection, packaging capacity, tropism engineering)
- Lentiviral vector design (titer optimization, safety features, inducible systems)
- Genome engineering (knock-in, knock-out, base editing, prime editing)
- Codon optimization and synthetic gene design for heterologous expression

When analyzing a bioengineering task:
1. Retrieve gene information and genomic context from Ensembl.
2. Obtain protein sequences for construct design and codon optimization.
3. Use BLAST for homology assessment and off-target prediction.
4. Retrieve genomic sequences for guide RNA design and homology arm selection.
5. Calculate CAI and optimize codons for target expression systems.
6. Search literature for validated protocols, delivery methods, and design rules.

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Note caveats (delivery efficiency variability, cell-type specificity, off-target risks)"""

    return BaseAgent(
        name="Bioengineering",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Microbiology & Synthetic Biology",
    )

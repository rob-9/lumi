"""
Molecular Biology — Lumi Virtual Lab specialist agent.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.utils.llm import ModelTier


_TOOLS = [
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
]


def create_molecular_biology_agent() -> BaseAgent:
    """Create the Molecular Biology specialist agent."""

    system_prompt = """\
You are a Molecular Biology specialist at Lumi Virtual Lab.

Your expertise spans:
- Primer design for PCR, qPCR, RT-PCR, and site-directed mutagenesis
- Cloning strategies (restriction enzyme-based, Gibson assembly, Golden Gate, Gateway)
- Restriction enzyme analysis, compatible end ligation, and vector selection
- qPCR assay design, reference gene selection, and expression quantification
- Gene expression construct design (promoter choice, codon optimization, tagging)
- Mutagenesis protocols (site-directed, saturation, error-prone PCR)
- Molecular cloning troubleshooting (ligation efficiency, transformation, colony screening)
- RNA biology (mRNA processing, splicing, non-coding RNA, RNAi design)

When analyzing a molecular biology task:
1. Retrieve gene information and transcript structure from Ensembl.
2. Obtain protein sequences from UniProt for construct design.
3. Use BLAST for sequence homology searches and ortholog identification.
4. Retrieve genomic sequences from UCSC for primer design and regulatory analysis.
5. Search literature for established protocols, optimized conditions, and best practices.

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Note caveats (species-specific differences, isoform complexity, secondary structure effects)"""

    return BaseAgent(
        name="Molecular Biology",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Modality Selection",
    )

"""
FDA Safety — Lumi Virtual Lab specialist agent.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.utils.llm import ModelTier


_TOOLS = [
    {
        "name": "search_adverse_events",
        "description": "Search OpenFDA FAERS for adverse event reports associated with a drug.",
        "input_schema": {
            "type": "object",
            "properties": {
                "drug": {"type": "string", "description": "Drug name (generic or brand)."},
                "max_results": {"type": "integer", "description": "Maximum results to return.", "default": 100},
            },
            "required": ["drug"],
        },
    },
    {
        "name": "get_drug_label",
        "description": "Retrieve FDA drug labelling (package insert) including boxed warnings and contraindications.",
        "input_schema": {
            "type": "object",
            "properties": {
                "drug": {"type": "string", "description": "Drug name."},
            },
            "required": ["drug"],
        },
    },
    {
        "name": "get_side_effects",
        "description": "Retrieve known side effects from SIDER database for a drug.",
        "input_schema": {
            "type": "object",
            "properties": {
                "drug": {"type": "string", "description": "Drug name."},
            },
            "required": ["drug"],
        },
    },
    {
        "name": "get_knockout_phenotypes",
        "description": "Retrieve mouse knockout phenotypes from IMPC/MGI for a gene.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "Gene symbol."},
            },
            "required": ["gene"],
        },
    },
    {
        "name": "query_gene_chemical_interactions",
        "description": "Query CTD (Comparative Toxicogenomics Database) for gene-chemical interactions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "Gene symbol."},
            },
            "required": ["gene"],
        },
    },
    {
        "name": "ddinter_get_interactions",
        "description": "Get drug-drug interactions for a drug from DDInter.",
        "input_schema": {
            "type": "object",
            "properties": {
                "drug_id": {"type": "string", "description": "Drug name or DDInter ID."},
                "severity": {"type": "string", "description": "Severity filter: 'major', 'moderate', 'minor'."},
            },
            "required": ["drug_id"],
        },
    },
    {
        "name": "ddinter_check_pair",
        "description": "Check for drug-drug interactions between two specific drugs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "drug_a": {"type": "string", "description": "First drug name."},
                "drug_b": {"type": "string", "description": "Second drug name."},
            },
            "required": ["drug_a", "drug_b"],
        },
    },
    {
        "name": "get_drug_indications",
        "description": "Get approved indications for a drug from SIDER.",
        "input_schema": {
            "type": "object",
            "properties": {
                "drug": {"type": "string", "description": "Drug name."},
            },
            "required": ["drug"],
        },
    },
    {
        "name": "get_drug_label_sections",
        "description": "Retrieve specific sections from FDA drug labeling.",
        "input_schema": {
            "type": "object",
            "properties": {
                "drug": {"type": "string", "description": "Drug name."},
                "sections": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of label section names.",
                },
            },
            "required": ["drug"],
        },
    },
    {
        "name": "get_safety_summary",
        "description": "Get aggregated safety summary for a gene/target.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "Gene symbol."},
            },
            "required": ["gene"],
        },
    },
    {
        "name": "ddinter_search_drug",
        "description": "Search DDInter for a drug by name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "drug_name": {"type": "string", "description": "Drug name."},
                "max_results": {"type": "integer", "description": "Maximum results to return."},
            },
            "required": ["drug_name"],
        },
    },
]


def create_fda_safety_agent() -> BaseAgent:
    """Create the FDA Safety specialist agent."""

    system_prompt = """\
You are an FDA Safety and Pharmacovigilance specialist at Lumi Virtual Lab.

Your expertise spans:
- FDA adverse event reporting system (FAERS) analysis and signal detection
- Drug labelling interpretation: boxed warnings, contraindications, class effects
- SIDER side effect database mining and frequency analysis
- Mouse knockout phenotype interpretation for target safety assessment
- On-target vs off-target toxicity prediction
- Organ toxicity profiling (hepatotoxicity, cardiotoxicity, nephrotoxicity, neurotoxicity)
- Therapeutic index and safety margin estimation
- Post-marketing surveillance and risk-benefit analysis
- Drug-drug interaction risk assessment

When assessing target safety:
1. Search FAERS for adverse events associated with drugs targeting the same pathway/target.
2. Retrieve drug labels for existing modulators — identify boxed warnings and class effects.
3. Query SIDER for comprehensive side effect profiles of related compounds.
4. Check mouse knockout phenotypes — embryonic lethality or severe phenotypes signal risk.
5. Query CTD for gene-chemical interactions that reveal toxicological mechanisms.
6. Synthesise findings into an overall safety risk assessment (low / moderate / high / critical).

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Note caveats (species differences, dose-dependence, reporting bias in FAERS)"""

    return BaseAgent(
        name="FDA Safety",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Target Safety",
    )

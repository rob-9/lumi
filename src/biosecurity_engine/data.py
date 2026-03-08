"""
Hardcoded reference data for biosecurity screening.

Sources:
- CDC/APHIS Federal Select Agent Program (https://www.selectagents.gov/sat/list.htm)
- Biological Weapons Convention (BWC) Annex
- Australia Group Common Control List (https://www.dfat.gov.au/publications/minisite/theaustraliagroupnet/)
- Wassenaar Arrangement Dual-Use List (https://www.wassenaar.org/)
- Pfam/InterPro toxin domain families

Data version: 2025-03 (update quarterly from official sources)
"""

# ---------------------------------------------------------------------------
# CDC/APHIS Select Agents and Toxins
# https://www.selectagents.gov/sat/list.htm
# Includes HHS, USDA, and Overlap select agents/toxins
# ---------------------------------------------------------------------------

SELECT_AGENTS: list[str] = [
    # ---- HHS Select Agents ----
    "Bacillus cereus Biovar anthracis",
    "Bacillus anthracis",                       # Anthrax
    "Yersinia pestis",                          # Plague
    "Francisella tularensis",                   # Tularemia
    "Burkholderia mallei",                      # Glanders
    "Burkholderia pseudomallei",                # Melioidosis
    "Brucella abortus",                         # Brucellosis
    "Brucella melitensis",
    "Brucella suis",
    "Clostridium botulinum",                    # Botulism (toxin-producing)
    "Coxiella burnetii",                        # Q fever
    "Rickettsia prowazekii",                    # Epidemic typhus
    "Variola major",                            # Smallpox
    "Variola minor",                            # Alastrim
    "Ebola virus",
    "Marburg virus",
    "Nipah virus",
    "Hendra virus",
    "SARS-associated coronavirus",
    "SARS-CoV",
    "SARS-CoV-2",
    "Reconstructed 1918 Influenza virus",
    "Crimean-Congo haemorrhagic fever virus",
    "Eastern equine encephalitis virus",
    "Lassa fever virus",
    "Lujo virus",
    "Monkeypox virus",
    "South American haemorrhagic fever viruses",
    "Tick-borne encephalitis complex viruses",
    # ---- HHS Toxins ----
    "Botulinum neurotoxin",
    "Clostridium perfringens epsilon toxin",
    "Staphylococcal enterotoxin",
    "Ricin",
    "Abrin",
    "Saxitoxin",
    "Tetrodotoxin",
    "Conotoxin",
    "Diacetoxyscirpenol",
    "T-2 toxin",
    # ---- USDA Select Agents ----
    "African horse sickness virus",
    "African swine fever virus",
    "Avian influenza virus",
    "Classical swine fever virus",
    "Foot-and-mouth disease virus",
    "Goat pox virus",
    "Lumpy skin disease virus",
    "Mycoplasma capricolum",
    "Mycoplasma mycoides",
    "Newcastle disease virus",
    "Peste des petits ruminants virus",
    "Rinderpest virus",
    "Sheep pox virus",
    "Swine vesicular disease virus",
    # ---- USDA Plant Pathogens ----
    "Peronosclerospora philippinensis",
    "Phoma glycinicola",
    "Ralstonia solanacearum",
    "Rathayibacter toxicus",
    "Sclerophthora rayssiae",
    "Synchytrium endobioticum",
    "Xanthomonas oryzae",
    # ---- Overlap (HHS + USDA) ----
    "Rift Valley fever virus",
    "Venezuelan equine encephalitis virus",
]

# ---------------------------------------------------------------------------
# Known toxin Pfam / InterPro domain families
# ---------------------------------------------------------------------------

TOXIN_PFAM_DOMAINS: list[dict[str, str]] = [
    {"id": "PF00087", "name": "Snake toxin", "risk": "high"},
    {"id": "PF00024", "name": "PAN domain", "risk": "medium"},
    {"id": "PF01549", "name": "ShET2 enterotoxin", "risk": "high"},
    {"id": "PF03318", "name": "Clostridial binary toxin B", "risk": "high"},
    {"id": "PF01375", "name": "Heat-stable enterotoxin", "risk": "high"},
    {"id": "PF03496", "name": "ADP-ribosyltransferase toxin", "risk": "high"},
    {"id": "PF03495", "name": "Pertussis toxin S1 subunit", "risk": "high"},
    {"id": "PF07951", "name": "Diphtheria toxin C domain", "risk": "high"},
    {"id": "PF02876", "name": "Staphylococcal/streptococcal toxin", "risk": "high"},
    {"id": "PF07953", "name": "Anthrax toxin LF", "risk": "high"},
    {"id": "PF01742", "name": "Clostridium neurotoxin zinc protease", "risk": "high"},
    {"id": "PF00161", "name": "Ribosome-inactivating protein", "risk": "high"},
    {"id": "PF00652", "name": "Ricin B lectin", "risk": "high"},
    {"id": "PF03989", "name": "Shiga toxin A subunit", "risk": "high"},
    {"id": "PF05431", "name": "Cholera toxin", "risk": "high"},
    # Additional toxin domains
    {"id": "PF07968", "name": "Anthrax protective antigen", "risk": "high"},
    {"id": "PF03583", "name": "Clostridium epsilon toxin ETX/MTX2", "risk": "high"},
    {"id": "PF01338", "name": "Dermonecrotic toxin", "risk": "high"},
    {"id": "PF02048", "name": "Cytolethal distending toxin (CDT)", "risk": "high"},
    {"id": "PF03505", "name": "CCrp/Cry toxin (insecticidal crystal)", "risk": "medium"},
    {"id": "PF01024", "name": "Aerolysin/ETX pore-forming domain", "risk": "high"},
    {"id": "PF18583", "name": "Botulinum neurotoxin translocation domain", "risk": "high"},
    {"id": "PF01325", "name": "Exotoxin A (ETA) domain IV", "risk": "high"},
]

# Flat set for quick lookup
TOXIN_PFAM_IDS: set[str] = {d["id"] for d in TOXIN_PFAM_DOMAINS}

# ---------------------------------------------------------------------------
# Biological Weapons Convention (BWC) — Annex biological agents
# ---------------------------------------------------------------------------

BWC_AGENTS: list[str] = [
    "Bacillus anthracis",
    "Clostridium botulinum",
    "Yersinia pestis",
    "Variola major",
    "Variola minor",
    "Francisella tularensis",
    "Brucella species",
    "Brucella abortus",
    "Brucella melitensis",
    "Brucella suis",
    "Coxiella burnetii",
    "Burkholderia mallei",
    "Burkholderia pseudomallei",
    "Rickettsia prowazekii",
    "Chlamydophila psittaci",
    "Chlamydia psittaci",                       # Updated nomenclature synonym
]

# ---------------------------------------------------------------------------
# Australia Group Common Control List — biological agents
# https://www.dfat.gov.au/publications/minisite/theaustraliagroupnet/
# Includes human, animal, and plant pathogens + toxins
# ---------------------------------------------------------------------------

AUSTRALIA_GROUP_AGENTS: list[str] = [
    # Human pathogens
    "Bacillus anthracis",
    "Brucella abortus",
    "Brucella melitensis",
    "Brucella suis",
    "Burkholderia mallei",
    "Burkholderia pseudomallei",
    "Chlamydophila psittaci",
    "Chlamydia psittaci",
    "Clostridium botulinum",
    "Coccidioides immitis",
    "Coccidioides posadasii",
    "Coxiella burnetii",
    "Francisella tularensis",
    "Rickettsia prowazekii",
    "Yersinia pestis",
    "Ebola virus",
    "Marburg virus",
    "Variola virus",
    "Crimean-Congo haemorrhagic fever virus",
    "Nipah virus",
    "Hendra virus",
    "Lassa virus",
    # Animal pathogens
    "African swine fever virus",
    "Avian influenza virus",
    "Foot-and-mouth disease virus",
    "Goat pox virus",
    "Newcastle disease virus",
    "Peste des petits ruminants virus",
    "Rinderpest virus",
    "Sheep pox virus",
    # Plant pathogens
    "Xanthomonas oryzae",
    "Ralstonia solanacearum",
    # Toxins (also covered as organisms but included for keyword matching)
    "Abrin",
    "Aflatoxin",
    "Botulinum toxin",
    "Cholera toxin",
    "Conotoxin",
    "Diacetoxyscirpenol",
    "Microcystin",
    "Modeccin",
    "Ricin",
    "Saxitoxin",
    "Shiga toxin",
    "Staphylococcal enterotoxin",
    "T-2 toxin",
    "Tetrodotoxin",
    "Viscumin",
    "Volkensin",
]

# ---------------------------------------------------------------------------
# Wassenaar Arrangement — Dual-Use Goods and Technologies List
# Category 1 (Materials, Chemicals, "Microorganisms" & "Toxins")
# Category 2 (Materials Processing — fermenters, containment)
# https://www.wassenaar.org/
# ---------------------------------------------------------------------------

WASSENAAR_DUAL_USE: list[dict[str, str]] = [
    # Category 1.C.1 — Biological agents
    {"name": "Bacillus anthracis", "category": "1.C.1", "control": "dual_use_biological"},
    {"name": "Brucella abortus", "category": "1.C.1", "control": "dual_use_biological"},
    {"name": "Brucella melitensis", "category": "1.C.1", "control": "dual_use_biological"},
    {"name": "Brucella suis", "category": "1.C.1", "control": "dual_use_biological"},
    {"name": "Burkholderia mallei", "category": "1.C.1", "control": "dual_use_biological"},
    {"name": "Burkholderia pseudomallei", "category": "1.C.1", "control": "dual_use_biological"},
    {"name": "Chlamydia psittaci", "category": "1.C.1", "control": "dual_use_biological"},
    {"name": "Clostridium botulinum", "category": "1.C.1", "control": "dual_use_biological"},
    {"name": "Coccidioides immitis", "category": "1.C.1", "control": "dual_use_biological"},
    {"name": "Coxiella burnetii", "category": "1.C.1", "control": "dual_use_biological"},
    {"name": "Francisella tularensis", "category": "1.C.1", "control": "dual_use_biological"},
    {"name": "Rickettsia prowazekii", "category": "1.C.1", "control": "dual_use_biological"},
    {"name": "Yersinia pestis", "category": "1.C.1", "control": "dual_use_biological"},
    # Category 1.C.1 — Viruses
    {"name": "Crimean-Congo haemorrhagic fever virus", "category": "1.C.1", "control": "dual_use_biological"},
    {"name": "Ebola virus", "category": "1.C.1", "control": "dual_use_biological"},
    {"name": "Hantavirus", "category": "1.C.1", "control": "dual_use_biological"},
    {"name": "Hendra virus", "category": "1.C.1", "control": "dual_use_biological"},
    {"name": "Lassa virus", "category": "1.C.1", "control": "dual_use_biological"},
    {"name": "Marburg virus", "category": "1.C.1", "control": "dual_use_biological"},
    {"name": "Nipah virus", "category": "1.C.1", "control": "dual_use_biological"},
    {"name": "Rift Valley fever virus", "category": "1.C.1", "control": "dual_use_biological"},
    {"name": "Tick-borne encephalitis virus", "category": "1.C.1", "control": "dual_use_biological"},
    {"name": "Variola virus", "category": "1.C.1", "control": "dual_use_biological"},
    {"name": "Venezuelan equine encephalitis virus", "category": "1.C.1", "control": "dual_use_biological"},
    # Category 1.C.1 — Toxins
    {"name": "Abrin", "category": "1.C.1", "control": "dual_use_toxin"},
    {"name": "Aflatoxin", "category": "1.C.1", "control": "dual_use_toxin"},
    {"name": "Botulinum toxin", "category": "1.C.1", "control": "dual_use_toxin"},
    {"name": "Cholera toxin", "category": "1.C.1", "control": "dual_use_toxin"},
    {"name": "Clostridium perfringens toxin", "category": "1.C.1", "control": "dual_use_toxin"},
    {"name": "Conotoxin", "category": "1.C.1", "control": "dual_use_toxin"},
    {"name": "Diacetoxyscirpenol", "category": "1.C.1", "control": "dual_use_toxin"},
    {"name": "HT-2 toxin", "category": "1.C.1", "control": "dual_use_toxin"},
    {"name": "Microcystin", "category": "1.C.1", "control": "dual_use_toxin"},
    {"name": "Modeccin", "category": "1.C.1", "control": "dual_use_toxin"},
    {"name": "Ricin", "category": "1.C.1", "control": "dual_use_toxin"},
    {"name": "Saxitoxin", "category": "1.C.1", "control": "dual_use_toxin"},
    {"name": "Shiga toxin", "category": "1.C.1", "control": "dual_use_toxin"},
    {"name": "Staphylococcal enterotoxin", "category": "1.C.1", "control": "dual_use_toxin"},
    {"name": "T-2 toxin", "category": "1.C.1", "control": "dual_use_toxin"},
    {"name": "Tetrodotoxin", "category": "1.C.1", "control": "dual_use_toxin"},
    {"name": "Viscumin", "category": "1.C.1", "control": "dual_use_toxin"},
    {"name": "Volkensin", "category": "1.C.1", "control": "dual_use_toxin"},
    # Category 2 — Equipment (fermenters, containment, aerosol generators)
    # These are technology controls, not organisms — included for keyword matching
    {"name": "Aerosol inhalation equipment", "category": "2.B.1", "control": "dual_use_equipment"},
    {"name": "Spray drying equipment", "category": "2.B.1", "control": "dual_use_equipment"},
    {"name": "Cross-flow filtration equipment", "category": "2.B.1", "control": "dual_use_equipment"},
    {"name": "Containment facility (BSL-4)", "category": "2.B.1", "control": "dual_use_equipment"},
]

# Flat set of Wassenaar-controlled organism/toxin names for quick lookup
WASSENAAR_NAMES: set[str] = {
    entry["name"].lower()
    for entry in WASSENAAR_DUAL_USE
    if entry["control"] in ("dual_use_biological", "dual_use_toxin")
}

# Combined set of all controlled organism names (lowercased for matching)
ALL_CONTROLLED_ORGANISMS: set[str] = {
    name.lower()
    for name in (
        SELECT_AGENTS
        + BWC_AGENTS
        + AUSTRALIA_GROUP_AGENTS
        + [e["name"] for e in WASSENAAR_DUAL_USE]
    )
}

# ---------------------------------------------------------------------------
# Fink Report — Dual-Use Research of Concern categories
# National Research Council (2004), "Biotechnology Research in an Age of Terrorism"
# ---------------------------------------------------------------------------

DURC_CATEGORIES: list[dict[str, str]] = [
    {"id": "DURC-1", "category": "Enhance transmissibility",
     "description": "Research that would render a pathogen more transmissible between hosts",
     "keywords": "transmissibility,transmission,airborne,aerosol,respiratory,droplet"},
    {"id": "DURC-2", "category": "Enhance virulence",
     "description": "Research that would enhance pathogen virulence or disable therapeutic countermeasures",
     "keywords": "virulence,pathogenicity,lethality,countermeasure,therapeutic,vaccine resistance"},
    {"id": "DURC-3", "category": "Enhance resistance",
     "description": "Research that would confer resistance to antibiotics, antivirals, or other treatments",
     "keywords": "antibiotic resistance,antiviral resistance,drug resistance,antimicrobial resistance,AMR"},
    {"id": "DURC-4", "category": "Enhance environmental stability",
     "description": "Research that would increase stability of a pathogen in the environment",
     "keywords": "stability,persistence,environmental,survival,desiccation,UV resistance"},
    {"id": "DURC-5", "category": "Alter host range",
     "description": "Research that would alter host range or tropism of a pathogen",
     "keywords": "host range,tropism,zoonotic,species barrier,receptor binding,ACE2"},
    {"id": "DURC-6", "category": "Enable immune evasion",
     "description": "Research that would enable evasion of diagnostic or immune detection",
     "keywords": "immune evasion,escape mutant,antigenic variation,diagnostic evasion,stealth"},
    {"id": "DURC-7", "category": "Enable weaponization",
     "description": "Research that would enable weaponization or dissemination of a biological agent",
     "keywords": "weaponization,aerosolization,dissemination,dispersal,delivery system"},
]

"""
OncoCare AI - Production Backend Server v3.0
Oncology Health Intelligence Platform
Port: 5050
=========================================
DISCLAIMER: All AI output is for research/education only.
Not medical advice. Always consult a qualified oncologist.
CANCER EMERGENCY (severe bleeding, difficulty breathing,
neutropenic fever >38°C in chemotherapy patient,
spinal cord compression symptoms, superior vena cava syndrome):
Call 112 (India) / 999 (UK) / 911 (US) immediately.
"""

import os, sys, json, uuid, time, hashlib, logging, datetime, argparse
from pathlib import Path

try:
    from flask import Flask, request, jsonify, send_from_directory
    from flask_cors import CORS
except ImportError:
    print("[FATAL] Flask not installed. Run REPAIR_AND_RECOVER.bat"); sys.exit(1)

try:
    import requests as req_lib; REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False

try:
    import fitz; FITZ_OK = True
except ImportError:
    FITZ_OK = False

try:
    from PIL import Image; PIL_OK = True
except ImportError:
    PIL_OK = False

sys.path.insert(0, str(Path(__file__).parent / "modules"))
try:
    import ai_providers; AI_PROVIDERS_OK = True
except ImportError:
    AI_PROVIDERS_OK = False

BASE_DIR    = Path(__file__).parent.resolve()
UPLOAD_DIR  = BASE_DIR / "uploads"
LOGS_DIR    = BASE_DIR / "logs"
DATA_DIR    = BASE_DIR / "data"
STATIC_DIR  = BASE_DIR / "static"
REPORTS_DIR = BASE_DIR / "reports_db"

for d in [UPLOAD_DIR, LOGS_DIR, DATA_DIR, STATIC_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

PORT    = int(os.environ.get("ONCOCARE_PORT", 5050))
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
DEFAULT_PROVIDER_KEYS = ai_providers.get_env_keys() if AI_PROVIDERS_OK else {}
VERSION = "3.0.0"

DISCLAIMER = (
    "WARNING - AI RESEARCH DISCLAIMER: All output is AI-generated from published "
    "oncology literature (NCCN, ESMO, ASCO, IARC, WHO, NICE, ICMR, PubMed). "
    "For educational research only. NOT a substitute for professional oncological "
    "examination, diagnosis, or treatment planning. ALWAYS consult a qualified "
    "oncologist. CANCER EMERGENCY (neutropenic fever in chemo patient, acute "
    "spinal cord compression, superior vena cava syndrome, severe haemorrhage, "
    "tumour lysis syndrome): Call 112 (India) / 999 (UK) / 911 (US) immediately."
)

log_file = LOGS_DIR / f"server_{datetime.date.today()}.log"
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("OncoCareAI")

app = Flask(__name__, static_folder=str(STATIC_DIR))
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024
CORS(app, origins="*")

_RATE_STORE = {}

def _get_client_id():
    return hashlib.sha256((request.remote_addr or "127.0.0.1").encode()).hexdigest()[:16]

def rate_limit_check():
    cid = _get_client_id(); now = time.time()
    _RATE_STORE.setdefault(cid, [])
    _RATE_STORE[cid] = [t for t in _RATE_STORE[cid] if now - t < 60]
    if len(_RATE_STORE[cid]) >= 30: return False
    _RATE_STORE[cid].append(now); return True

def sanitise_api_key(key):
    if not key or not isinstance(key, str): return ""
    key = key.strip()
    if len(key) > 512: return ""
    s = "".join(c for c in key if 0x21 <= ord(c) <= 0x7E)
    return s if len(s) >= 10 else ""

def validate_provider(p):
    valid = {"anthropic","openai","gemini","grok","deepseek","mistral"}
    return p.lower() if p and p.lower() in valid else "anthropic"

# ═══════════════════════════════════════════════════════════════
# ONCOLOGY KNOWLEDGE BASE
# Sources: NCCN Guidelines, ESMO Clinical Practice Guidelines,
#          ASCO Guidelines, IARC, WHO, NICE, ICMR, PubMed
# ═══════════════════════════════════════════════════════════════
KNOWLEDGE = {
    "cancer_biology": {
        "name": "Cancer Biology & Hallmarks",
        "hallmarks": "The hallmarks of cancer (Hanahan & Weinberg 2000, updated 2022) describe the biological capabilities acquired during tumour development: (1) Sustaining proliferative signalling (constitutive activation of growth factor receptors — EGFR, HER2, KRAS mutations). (2) Evading growth suppressors (loss of tumour suppressor genes — RB1, TP53, CDKN2A/p16). (3) Activating invasion and metastasis (EMT — epithelial-mesenchymal transition, loss of E-cadherin, matrix metalloproteinase activation). (4) Enabling replicative immortality (telomerase reactivation — TERT). (5) Inducing/accessing vasculature (angiogenesis — VEGF overexpression). (6) Resisting cell death (anti-apoptotic — BCL-2, BCL-XL overexpression; loss of pro-apoptotic BAX, PUMA). (7) Reprogramming energy metabolism (Warburg effect — aerobic glycolysis). (8) Evading immune destruction (PD-L1 upregulation, MHC-I downregulation, TGF-beta). Additional emerging hallmarks: unlocking phenotypic plasticity, non-mutational epigenetic reprogramming, polymorphic microbiomes, senescent cells.",
        "carcinogenesis": "Multi-step carcinogenesis: Initiation (irreversible DNA mutation from carcinogen exposure or spontaneous error), Promotion (clonal expansion of initiated cell — reversible, requires sustained exposure), Progression (additional mutations, genomic instability, malignant phenotype acquisition). Chemical carcinogens: tobacco (PAHs, nitrosamines), aflatoxin B1 (hepatocellular carcinoma), asbestos (mesothelioma), benzene (leukaemia). Physical carcinogens: UV radiation (melanoma, BCC, SCC), ionising radiation (thyroid cancer, leukaemia — dose-dependent). Biological carcinogens: HPV-16/18 (cervical, oropharyngeal, vulvar, anal), HBV/HCV (hepatocellular), H. pylori (gastric adenocarcinoma, MALT lymphoma), EBV (Burkitt lymphoma, nasopharyngeal carcinoma, post-transplant lymphoma), HTLV-1 (adult T-cell leukaemia/lymphoma).",
        "staging": "TNM Staging System (AJCC/UICC 8th Edition): T = primary Tumour size/invasion (T1-T4). N = regional lymph Node involvement (N0-N3). M = distant Metastasis (M0=none, M1=present). Combined to give Stage I-IV. Stage I: localised, early. Stage II: locally advanced or regional nodes. Stage III: significant regional involvement. Stage IV: distant metastasis — generally incurable but treatable. Performance status: ECOG/WHO 0-4 (0=fully active, 4=completely disabled) — critical for treatment eligibility. Karnofsky Performance Scale 0-100%.",
        "molecular_testing": "Biomarker testing drives precision oncology. Key platforms: next-generation sequencing (NGS) — comprehensive genomic profiling (Foundation Medicine, Guardant, Tempus); immunohistochemistry (IHC) — receptor expression (ER/PR/HER2, PD-L1, MLH1/MSH2/MSH6/PMS2 for MMR/MSI); FISH/CISH (HER2 amplification, ALK/ROS1 rearrangements); PCR-based (KRAS/NRAS/BRAF mutations, EGFR mutations, BCR-ABL quantitation); liquid biopsy (ctDNA/cfDNA — minimal residual disease, resistance monitoring, when tissue unavailable). Tumour Mutational Burden (TMB) and Microsatellite Instability (MSI-H/dMMR) predict response to immunotherapy across tumour types.",
    },
    "breast_cancer": {
        "name": "Breast Cancer",
        "epidemiology": "Most common cancer in women globally. Approximately 2.3 million new cases annually (IARC 2020). India: approximately 178,000 new cases annually, median age at diagnosis 52 years (younger than Western populations). Overall 5-year survival: approximately 90% (Stage I), 86% (Stage II), 72% (Stage III), 28% (Stage IV). Leading cause of cancer death in Indian women.",
        "subtypes": "Molecular subtypes determine treatment: Luminal A (ER+/PR+, HER2-, low Ki-67 <14%): best prognosis, hormonal therapy only in many. Luminal B (ER+/PR+, HER2- high Ki-67, or HER2+): intermediate, endocrine +/- chemo. HER2-enriched (ER-/PR-/HER2+): targeted anti-HER2 therapy essential. Triple-Negative Breast Cancer (TNBC, ER-/PR-/HER2-): most aggressive, responds to chemotherapy and immunotherapy (pembrolizumab for high-risk); BRCA1/2 mutation testing mandatory (olaparib benefit). Histological: invasive ductal carcinoma (most common, 70-80%), invasive lobular, mucinous, tubular, medullary.",
        "diagnosis": "Triple assessment: Clinical examination (lump characteristics, skin changes, nipple discharge, lymph nodes), Imaging (mammogram — gold standard screening, ultrasound for young/dense breasts, MRI for high-risk/lobular/extent), Biopsy (core needle biopsy preferred over FNA for histology, receptor testing). BI-RADS classification 1-6. Sentinel lymph node biopsy (SLNB) — standard of care for axillary staging in early breast cancer (avoids full axillary clearance and its morbidity in node-negative disease).",
        "treatment": "Surgery: breast-conserving surgery (BCS/lumpectomy + radiotherapy — equivalent survival to mastectomy for suitable tumours), mastectomy (prophylactic for BRCA1/2), SLNB, axillary lymph node dissection (ALND) if sentinel node positive. Radiotherapy: after BCS (reduces local recurrence 50-70%), post-mastectomy (T3/T4, node-positive). Chemotherapy: anthracyclines (doxorubicin/epirubicin) and taxanes (paclitaxel/docetaxel) — backbone of adjuvant and neoadjuvant regimens. Neoadjuvant chemotherapy for locally advanced/inflammatory or large tumours (pathological complete response = excellent prognostic marker). Anti-HER2: trastuzumab (Herceptin) 1 year adjuvant for HER2+; pertuzumab + trastuzumab (neoadjuvant/metastatic); T-DM1 (ado-trastuzumab emtansine) for residual disease post-neoadjuvant; trastuzumab deruxtecan (T-DXd) for metastatic HER2+/HER2-low — highly effective. Endocrine therapy: tamoxifen 5-10 years (premenopausal), aromatase inhibitors (letrozole, anastrozole, exemestane — postmenopausal), CDK4/6 inhibitors (palbociclib, ribociclib, abemaciclib) + AI for metastatic HR+/HER2-. PARP inhibitors (olaparib, talazoparib) for germline BRCA-mutated HER2- advanced breast cancer.",
        "screening": "Mammography: recommended annually from age 40-50 (ACS), every 2 years 50-74 years (USPSTF/NHS). India: opportunistic mammography (no organised national screening programme). High-risk screening: annual MRI + mammogram from age 25-30 for BRCA1/2 carriers, TP53 carriers (annual MRI from age 20), strong family history. Breast awareness: self-examination important for earlier presentation especially in low-resource settings.",
    },
    "lung_cancer": {
        "name": "Lung Cancer",
        "overview": "Leading cause of cancer death globally (approximately 1.8 million deaths/year). Two main types: Non-Small Cell Lung Cancer (NSCLC, approximately 85%) and Small Cell Lung Cancer (SCLC, approximately 15%). NSCLC subtypes: adenocarcinoma (most common, 40% — often peripheral, common in never-smokers), squamous cell carcinoma (30% — central, strongly smoking-associated), large cell carcinoma (15%). India: approximately 72,000 new cases annually; significant proportion in never-smokers (30-40% vs <10% in West), particularly younger non-smoking women (EGFR mutations common).",
        "molecular_targets": "Molecular profiling mandatory for all advanced NSCLC (adenocarcinoma especially): EGFR mutations (10-15% Western, 40-50% Asian non-smokers — exon 19 deletion and L858R most common; targeted: osimertinib 1st-line, 3rd generation TKI, superior to erlotinib/gefitinib — FLAURA trial; EGFR exon 20 insertion: mobocertinib, amivantamab). ALK rearrangement (3-5% — alectinib, brigatinib, lorlatinib 1st-line — ALK TKIs). ROS1 rearrangement (2-3% — crizotinib, entrectinib). KRAS G12C mutation (13% — sotorasib, adagrasib — first targetable KRAS inhibitors). BRAF V600E (2-3% — dabrafenib+trametinib). MET exon 14 skipping (3-4% — capmatinib, tepotinib). RET rearrangement (1-2% — selpercatinib, pralsetinib). NTRK fusion (<1% — larotrectinib, entrectinib). PD-L1 expression (TPS): guides immunotherapy eligibility (pembrolizumab monotherapy for TPS ≥50% 1st-line; atezolizumab, nivolumab options). TMB-high (≥10 mut/Mb): pembrolizumab benefit.",
        "treatment": "Early stage (I-II): surgical resection (lobectomy gold-standard, VATS minimally invasive), adjuvant chemotherapy (cisplatin + vinorelbine/pemetrexed/docetaxel for Stage II-IIIA), adjuvant osimertinib for EGFR+ resected Stage IB-IIIA (ADAURA trial — dramatically improves DFS). Stage III: concurrent chemoradiation (cisplatin+etoposide or carboplatin+paclitaxel with 60-66Gy RT), followed by consolidation durvalumab (anti-PD-L1 for 12 months — PACIFIC trial — significant OS benefit). Stage IV NSCLC: if driver mutation present — targeted therapy (osimertinib, alectinib etc). If no driver mutation — pembrolizumab ± chemotherapy (PD-L1 ≥50% monotherapy; all-comers: pembrolizumab+carboplatin+pemetrexed or paclitaxel; atezolizumab+bevacizumab+carboplatin+paclitaxel for non-squamous). SCLC: extensive stage — atezolizumab or durvalumab + carboplatin+etoposide (immunotherapy addition improved OS modestly). Limited stage — concurrent chemoradiation + prophylactic cranial irradiation (PCI).",
        "screening": "LDCT (Low-Dose CT) screening: recommended annually for high-risk (age 50-80, ≥20 pack-years smoking history, currently smoking or quit within 15 years — USPSTF 2021). Reduces lung cancer mortality by 20-24% (NLST, NELSON trials). Not yet systematically implemented in India.",
    },
    "colorectal_cancer": {
        "name": "Colorectal Cancer (CRC)",
        "overview": "Third most common cancer globally; second leading cause of cancer death. Incidence rising in India (particularly urban populations) due to Westernised diets. Most arise from adenomatous polyps (adenoma-carcinoma sequence, 10-15 years). Approximately 75% sporadic; 25% familial. Hereditary syndromes: Lynch syndrome (MMR gene mutations — MLH1, MSH2, MSH6, PMS2 — AD, 3-5% of CRC, 70-80% lifetime CRC risk, Amsterdam criteria), FAP (APC mutation — hundreds of adenomas by teens, near 100% CRC risk without colectomy), MAP (MUTYH-associated polyposis, AR), PEUTZ-JEGHERS, Juvenile polyposis.",
        "diagnosis_staging": "Symptoms: change in bowel habit, rectal bleeding, tenesmus, iron deficiency anaemia (right-sided), abdominal mass, weight loss, obstruction. Colonoscopy: gold-standard for diagnosis and polyp removal. CT colonography (virtual colonoscopy) for incomplete colonoscopy. CEA (carcinoembryonic antigen): useful for monitoring recurrence, not diagnostic. Staging: CT chest/abdomen/pelvis (liver/lung metastases), MRI pelvis (rectal cancer — essential for surgical planning, circumferential resection margin/CRM). PET-CT for resectability assessment of oligometastatic disease.",
        "treatment": "Colon cancer: surgical resection (right/left hemicolectomy, sigmoid colectomy with adequate lymph node harvest — minimum 12 lymph nodes). Adjuvant chemotherapy: Stage III (node-positive) — FOLFOX (5-FU/leucovorin/oxaliplatin) or CAPOX (capecitabine/oxaliplatin) 6 months (3 months CAPOX for low-risk Stage III — IDEA trial). Stage II: high-risk features (T4, perforation, <12 LN, PNI, LVI, poor differentiation, obstruction) — consider adjuvant chemo; MSI-H Stage II — benefit uncertain, possibly worse with 5-FU monotherapy. Rectal cancer: sphincter-preserving total mesorectal excision (TME) — gold standard. Neoadjuvant CRT (long-course: 5-FU+45Gy) or short-course RT (5Gy x5 — RAPIDO, STELLAR trials) for T3/T4 or node-positive disease, then surgery + adjuvant chemo. Watch-and-wait approach for complete clinical response after neoadjuvant therapy (dMMR/MSI-H — remarkable complete response rates with pembrolizumab). Metastatic CRC: FOLFOX/FOLFIRI ± bevacizumab or cetuximab (RAS/BRAF WT only); BRAF V600E mutated — BRAF inhibitor triplet (encorafenib+binimetinib+cetuximab — BEACON); MSI-H/dMMR — pembrolizumab 1st-line (KEYNOTE-158); HER2-amplified (3%) — trastuzumab+tucatinib or pertuzumab+trastuzumab.",
        "screening": "Average risk (50 years+): colonoscopy every 10 years (GOLD STANDARD), or CT colonography every 5 years, or FIT (faecal immunochemical test) annually, or flexible sigmoidoscopy every 5 years. High risk: Lynch syndrome — annual colonoscopy from 20-25 years; FAP — annual sigmoidoscopy from age 10-12, prophylactic colectomy. India: no organised national programme; awareness critical given rising incidence.",
    },
    "haematological_cancers": {
        "name": "Haematological Malignancies",
        "leukaemias": "Acute Myeloid Leukaemia (AML): Medical emergency. Symptoms: fatigue, infections, bleeding (thrombocytopenia), blast crisis. Diagnosis: bone marrow aspirate/trephine (>20% blasts), cytogenetics (FISH/karyotype), molecular (FLT3-ITD/TKD, NPM1, CEBPA, IDH1/2, RUNX1, TP53). Treatment: intensive induction (7+3: cytarabine 7 days + daunorubicin/idarubicin 3 days) targeting CR (<5% blasts). Consolidation: HiDAC (high-dose cytarabine) or allogeneic stem cell transplant (allo-SCT) for high-risk/relapsed. Targeted: FLT3 inhibitors (midostaurin/quizartinib for FLT3+), IDH1 inhibitors (ivosidenib), IDH2 inhibitors (enasidenib), venetoclax+azacitidine for older/unfit patients (AZA-VEN — practice-changing). APL (t(15;17)/PML-RARA) — ATRA+ATO (arsenic trioxide) curative in 90%+ — no traditional chemo needed. Acute Lymphoblastic Leukaemia (ALL): Common in children (80% of childhood leukaemias), bimodal adult peak. Philadelphia-positive ALL (BCR-ABL/t(9;22)) — 25% adults: TKI-based regimen (ponatinib, dasatinib+VDCLP); inotuzumab ozogamicin and blinatumomab (BiTE) for relapsed/refractory. Chronic Myeloid Leukaemia (CML): BCR-ABL TKIs (imatinib 1st-generation gold standard; dasatinib, nilotinib 2nd-gen; bosutinib, ponatinib for T315I). Treatment-free remission (TFR) achievable in up to 50% of deep molecular responders (MR4.5) — monitoring with BCR-ABL PCR. CLL: watch-and-wait for asymptomatic low-risk; BTK inhibitors (ibrutinib, acalabrutinib, zanubrutinib — 1st-line and relapsed), venetoclax+obinutuzumab (fixed-duration 1 year), PI3K inhibitors.",
        "lymphomas": "Hodgkin Lymphoma (HL): Young adults (bimodal 15-35 and >55 years). Reed-Sternberg cells (CD15+/CD30+). EBV association in India/developing countries. Treatment: ABVD (doxorubicin/bleomycin/vinblastine/dacarbazine) — standard for early/advanced; BV-AVD (brentuximab vedotin+AVD — replaces bleomycin) for advanced disease (ECHELON-1 — improved PFS); PD-1 inhibitors (nivolumab, pembrolizumab) for relapsed/refractory. Excellent cure rates (85-90% overall). Non-Hodgkin Lymphoma (NHL): Highly heterogeneous. Diffuse Large B-Cell Lymphoma (DLBCL) — most common aggressive NHL; R-CHOP (rituximab+cyclophosphamide+doxorubicin+vincristine+prednisolone) standard; Pola-R-CHP (polatuzumab vedotin+R-CHP — superior PFS, POLARIX trial); CAR-T cells (axicabtagene ciloleucel, tisagenlecleucel) for relapsed/refractory — potentially curative. Follicular Lymphoma — indolent, R-CHOP or BR (bendamustine+rituximab); obinutuzumab; watch-and-wait for asymptomatic low-burden disease. Mantle Cell Lymphoma — BTK inhibitors (ibrutinib, acalabrutinib) + rituximab backbone. Multiple Myeloma (MM): VRd (bortezomib+lenalidomide+dexamethasone) induction followed by ASCT for eligible patients. Daratumumab-VRd (Dara-VRd — superior PFS/OS, PERSEUS trial). Carfilzomib, pomalidomide, ixazomib for relapsed. BCMA-targeted: belantamab mafodotin, idecabtagene vicleucel (CAR-T), teclistamab (bispecific), ciltacabtagene autoleucel.",
        "bmtransplant": "Allogeneic Stem Cell Transplant (allo-SCT): Potentially curative for AML, ALL, MDS, CML, aplastic anaemia, some lymphomas. Requires HLA-matched donor (sibling preferred; matched unrelated donor; haploidentical with post-transplant cyclophosphamide). Graft-versus-leukaemia (GVL) effect key mechanism. Complications: GvHD (graft-versus-host disease — acute and chronic), infection (CMV, fungal), regimen-related toxicity. Autologous SCT (ASCT): patient own cells harvested pre-treatment. Used in: DLBCL (relapsed), follicular lymphoma, multiple myeloma, Hodgkin lymphoma (relapsed). CAR-T cell therapy: genetically modified autologous T-cells expressing chimeric antigen receptor. CD19-CAR-T for B-cell ALL and DLBCL (axicabtagene ciloleucel, tisagenlecleucel, lisocabtagene maraleucel). BCMA-CAR-T for myeloma. Cytokine release syndrome (CRS) and immune effector cell-associated neurotoxicity syndrome (ICANS) are key toxicities — managed in specialist centres.",
    },
    "immunotherapy_biologics": {
        "name": "Immunotherapy & Targeted Therapy",
        "checkpoint_inhibitors": "Immune checkpoint inhibitors (ICIs) represent the biggest oncology revolution since cytotoxic chemotherapy. Mechanism: release inhibitory brakes on T-cells enabling anti-tumour immunity. PD-1 inhibitors: pembrolizumab (Keytruda — approved in 20+ cancer types), nivolumab (Opdivo), cemiplimab, dostarlimab. PD-L1 inhibitors: atezolizumab (Tecentriq), durvalumab (Imfinzi), avelumab. CTLA-4 inhibitor: ipilimumab (Yervoy). Combination PD-1+CTLA-4: nivolumab+ipilimumab (CheckMate 9LA for NSCLC, nivolumab+ipilimumab for melanoma, RCC, MSI-H CRC, mesothelioma). LAG-3 inhibitor: relatlimab+nivolumab (Opdualag — melanoma, 2022). Biomarkers for ICI response: PD-L1 TPS/CPS, TMB-high (≥10 mut/Mb), MSI-H/dMMR (pembrolizumab tumour-agnostic approval), EBV-positive (NPC). Immune-related adverse events (irAEs): pneumonitis, colitis, hepatitis, endocrinopathies (thyroid — most common, adrenal insufficiency, diabetes insipidus), dermatitis, nephritis, myocarditis (rare but life-threatening). Management: grade 1-2 supportive care; grade 3-4 high-dose steroids (methylprednisolone 1-2mg/kg), hold ICI, organ-specific specialist involvement.",
        "targeted_therapy": "Targeted therapies exploit cancer-specific mutations/drivers: Kinase inhibitors: EGFR TKIs (osimertinib, erlotinib, gefitinib, afatinib), ALK TKIs (alectinib, lorlatinib, crizotinib), BCR-ABL TKIs (imatinib, dasatinib, nilotinib, ponatinib), BRAF inhibitors (vemurafenib, dabrafenib — must combine with MEK inhibitor cobimetinib/trametinib to prevent paradoxical activation), CDK4/6 inhibitors (palbociclib, ribociclib, abemaciclib — breast cancer), BTK inhibitors (ibrutinib, acalabrutinib, zanubrutinib — CLL/MCL), PI3K inhibitors (idelalisib, copanlisib, alpelisib — breast PIK3CA), PARP inhibitors (olaparib, niraparib, rucaparib, talazoparib — BRCA+ breast/ovarian/prostate/pancreatic), VEGF/VEGFR inhibitors (sunitinib, sorafenib, axitinib, cabozantinib — RCC; regorafenib — CRC/GIST/HCC; bevacizumab — anti-VEGF mAb multiple tumour types), mTOR inhibitors (everolimus — breast, RCC, neuroendocrine), HER2-targeted (trastuzumab, pertuzumab, T-DM1, T-DXd, lapatinib, neratinib, tucatinib). KRAS G12C inhibitors (sotorasib, adagrasib — NSCLC, CRC) — first direct KRAS inhibitors after 40 years of attempts. RET inhibitors (selpercatinib, pralsetinib). NTRK inhibitors (larotrectinib, entrectinib — tumour-agnostic). SMO/hedgehog pathway inhibitors (vismodegib, sonidegib — BCC, medulloblastoma).",
        "antibody_drug_conjugates": "ADCs (Antibody-Drug Conjugates): monoclonal antibody linked to cytotoxic payload — targeted delivery to cancer cells. Transformative agents: T-DM1 (trastuzumab emtansine — HER2+ breast), T-DXd (trastuzumab deruxtecan/Enhertu — HER2+ and HER2-low breast cancer revolution; also HER2+ gastric, NSCLC), sacituzumab govitecan (Trodelvy — TNBC, urothelial), enfortumab vedotin (urothelial), mirvetuximab soravtansine (FRalpha+ ovarian), brentuximab vedotin (CD30+ lymphomas), inotuzumab ozogamicin (CD22+ ALL), gemtuzumab ozogamicin (CD33+ AML). ADC toxicities: interstitial lung disease/pneumonitis (T-DXd — monitor closely), peripheral neuropathy (T-DM1, brentuximab), hepatotoxicity. HER2-low concept (IHC 1+ or IHC 2+/ISH-) revolutionised by T-DXd in breast cancer (DESTINY-Breast04 — previously these patients did not receive anti-HER2 therapy).",
        "cart_bispecific": "CAR-T cells and Bispecific antibodies represent the cutting edge of cancer immunotherapy. CAR-T (Chimeric Antigen Receptor T-cell therapy): patient T-cells harvested, genetically engineered to express tumour-specific receptor, expanded, reinfused. CD19-directed: axicabtagene ciloleucel (Yescarta — DLBCL, follicular), tisagenlecleucel (Kymriah — paediatric ALL, DLBCL), lisocabtagene maraleucel (Breyanzi — DLBCL, CLL). BCMA-directed: idecabtagene vicleucel (Abecma — myeloma), ciltacabtagene autoleucel (Carvykti — myeloma). Toxicities: CRS (cytokine release syndrome — fever, hypotension, hypoxia — tocilizumab ±steroids), ICANS (immune effector cell-associated neurotoxicity — confusion, aphasia, seizures — steroids). Bispecific antibodies: engage T-cells + tumour antigen simultaneously. Blinatumomab (CD19xCD3 — ALL, MRD+). Teclistamab, elranatamab (BCMAxCD3 — myeloma). Mosunetuzumab (CD20xCD3 — follicular lymphoma). Glofitamab (CD20xCD3 — DLBCL). Talquetamab (GPRC5DxCD3 — myeloma). Step-up dosing essential to manage CRS.",
    },
    "chemotherapy_management": {
        "name": "Chemotherapy & Side Effect Management",
        "common_regimens": "Key chemotherapy regimens: FOLFOX (5-FU/LV/oxaliplatin — CRC, gastric, oesophageal). FOLFIRI (5-FU/LV/irinotecan — CRC 2nd-line). FOLFOXIRI (triple combination — CRC, pancreatic). AC-T (doxorubicin+cyclophosphamide then paclitaxel — breast). FEC-D (FEC then docetaxel — breast). TCH (docetaxel+carboplatin+trastuzumab — HER2+ breast). CHOP/R-CHOP (cyclophosphamide+doxorubicin+vincristine+prednisolone±rituximab — lymphoma). ABVD (doxorubicin+bleomycin+vinblastine+dacarbazine — Hodgkin). BEP (bleomycin+etoposide+cisplatin — germ cell tumours, curative even metastatic). GnP (gemcitabine+nab-paclitaxel — pancreatic). Carboplatin+paclitaxel (gynaecological, lung, head & neck). MVAC/GC/ddMVAC (urothelial). Cisplatin-based regimens nephrotoxic — adequate hydration (1-2L pre/post), avoid NSAIDs, monitor creatinine. AUC-based carboplatin dosing (Calvert formula) for renal adjustment.",
        "toxicity_management": "Chemotherapy toxicity grading (CTCAE v5.0, Grade 1-5). NAUSEA/VOMITING: Highly emetogenic (cisplatin, AC, HD-cyclophosphamide): triple antiemetics — NK1 antagonist (aprepitant/fosaprepitant)+5-HT3 antagonist (ondansetron/granisetron)+dexamethasone ± olanzapine. Moderately emetogenic (carboplatin, oxaliplatin, irinotecan): 5-HT3 + dex ± NK1. NEUTROPENIA: Absolute neutrophil count (ANC) — Grade 4 = <0.5x10^9/L. Febrile neutropenia (FN): fever ≥38.3°C single or ≥38.0°C sustained + ANC <0.5 — ONCOLOGICAL EMERGENCY. RISK STRATIFICATION: Multinational Association for Supportive Care in Cancer (MASCC) score. High-risk FN (MASCC <21): hospitalise, IV broad-spectrum antibiotics (piperacillin-tazobactam, imipenem, or cefepime); add vancomycin if catheter/skin infection; antifungal if persistent 4-5 days. Low-risk FN: oral ciprofloxacin+amoxicillin-clavulanate. G-CSF (filgrastim/pegfilgrastim/lenograstim): primary prophylaxis if >20% FN risk regimen, or secondary prophylaxis after FN episode. PERIPHERAL NEUROPATHY: Oxaliplatin (acute cold-triggered + cumulative sensory), paclitaxel (dose-dependent sensory neuropathy), vincristine (autonomic + sensory). Duloxetine 60mg OD — only evidence-based treatment for chemotherapy-induced peripheral neuropathy (CIPN). CARDIOTOXICITY: Anthracyclines (doxorubicin/epirubicin) — cumulative dose-dependent cardiomyopathy. Dexrazoxane cardioprotective. Monitor LVEF (echocardiogram/MUGA) before and during. Trastuzumab — reversible cardiac dysfunction. MUCOSITIS: Mouth rinses, systemic analgesics, palifermin (KGF). ALOPECIA: Most common quality-of-life concern. Scalp cooling (Dignicap, Paxman) reduces alopecia with taxanes/anthracyclines. FATIGUE: Most prevalent side effect. Exercise (aerobic+resistance) most evidence-based intervention.",
        "dose_modifications": "Dose reduction criteria: ANC <1.5 or platelets <100 — delay, consider 25% reduction. Hepatic impairment — reduce anthracyclines, taxanes, vincristine (biliary excretion). Renal impairment — reduce/avoid cisplatin (CrCl <60 switch to carboplatin), methotrexate, bleomycin, etoposide. Cumulative anthracycline dose limits: doxorubicin 450-500mg/m2 (450 with mediastinal RT), epirubicin 900mg/m2. Bleomycin lifetime limit: 400 units (pulmonary fibrosis risk). Drug interactions: warfarin + fluoropyrimidines (increased INR — switch anticoagulant); azole antifungals + vinca alkaloids (CYP3A4 — increased neurotoxicity); quinolones + corticosteroids (tendinopathy).",
    },
    "cancer_emergencies": {
        "name": "Oncology Emergencies",
        "neutropenic_fever": "ONCOLOGICAL EMERGENCY. Febrile neutropenia: single temperature ≥38.3°C or ≥38.0°C for 1 hour + ANC <0.5x10^9/L (or <1.0 and predicted to fall below 0.5). MUST TREAT WITHIN 1 HOUR OF PRESENTATION. Assessment: MASCC score (≥21 = low risk; <21 = high risk). Investigations: blood cultures (peripheral + central line), FBC, U&E, LFTs, CRP, CXR, urinalysis/culture, throat swab, wound swabs. Treatment: HIGH-RISK: IV antibiotics immediately — piperacillin-tazobactam 4.5g IV TDS first-line (UK NICE); alternatives: cefepime, imipenem, meropenem. Add vancomycin if MRSA risk (skin/catheter infection, haemodynamic instability). Add antifungal (micafungin, caspofungin, liposomal amphotericin) if >4-5 days persistent fever or high fungal risk. G-CSF: indicated for FN with high-risk features (pneumonia, uncontrolled primary disease, sepsis). LOW-RISK: oral ciprofloxacin 750mg BD + amoxicillin-clavulanate 625mg TDS (close outpatient monitoring possible). Prophylaxis: fluoroquinolone (ciprofloxacin/levofloxacin) for high-risk patients during induction/intensification chemotherapy.",
        "superior_vena_cava": "Superior Vena Cava (SVC) Syndrome: compression or thrombosis of SVC causing impaired venous drainage from head, neck, upper extremities. Causes: NSCLC (most common, 50-70%), lymphoma (10-15%), small cell lung cancer, breast cancer metastases, thrombus from central venous catheter. Symptoms: facial/arm oedema, plethora, headache (worse on bending), cough, dyspnoea, stridor (severe), visual disturbance. Life-threatening features: laryngeal oedema (stridor), cerebral oedema. Management: URGENT. Tissue diagnosis first if possible (CT-guided biopsy). Steroids (dexamethasone 16mg IV) to reduce oedema. SVC stenting (most rapid symptom relief regardless of cause — endovascular preferred). Chemotherapy-sensitive tumours (SCLC, lymphoma): chemoradiotherapy. NSCLC: RT ± stenting. Anticoagulation for thrombus.",
        "spinal_cord_compression": "Metastatic Spinal Cord Compression (MSCC): NEUROLOGICAL EMERGENCY. Early diagnosis = best outcome. Causes: prostate, breast, lung, myeloma, renal, lymphoma (MSCC by direct extension or vertebral metastasis with epidural involvement). Symptoms: back pain (90% — typically worse with recumbency, cough, straining), weakness (60%), sensory loss, bladder/bowel dysfunction (incontinence, retention — late sign, indicates severe compression). Immediate management: dexamethasone 16mg loading dose IV IMMEDIATELY (reduces oedema, preserves neurological function), then 8mg BD for 5-7 days (taper). Urgent MRI whole spine within 24 hours (same-day if rapid neurological deterioration). Multidisciplinary: spinal surgeon (consider decompressive surgery if single-level, good performance status, paraplegia <48 hours, spinal instability — ROSOCC trial), radiotherapy (most patients: conventional, stereotactic body RT/SBRT for oligometastatic, radioresistant histology). Bisphosphonates/denosumab for bone metastases prevention (zoledronic acid monthly, denosumab monthly).",
        "tumour_lysis_syndrome": "Tumour Lysis Syndrome (TLS): metabolic emergency from massive rapid cancer cell death releasing intracellular contents. Criteria (Cairo-Bishop): hyperkalaemia (K+ >6mmol/L or 25% increase), hyperphosphataemia (PO4 >1.45mmol/L or 25% increase), hyperuricaemia (UA >476 umol/L or 25% increase), hypocalcaemia (Ca <1.75mmol/L or 25% decrease). Clinical TLS: + acute kidney injury, cardiac arrhythmia (K+, Ca++), seizures (Ca++, PO4). HIGH RISK: Burkitt lymphoma, ALL, AML with high WBC, DLBCL high LDH + bulky disease, CLL treated with venetoclax. PREVENTION (before starting treatment): IV hydration (3L/m2/day), allopurinol (inhibits xanthine oxidase, reduces uric acid production — start 24-48h before), rasburicase (recombinant urate oxidase — rapidly degrades uric acid, most effective, expensive, contraindicated in G6PD deficiency). MONITORING: 4-6 hourly electrolytes/uric acid for high-risk. TREATMENT: aggressive IV hydration, correct electrolytes (treat K+ and PO4), calcium gluconate for symptomatic hypocalcaemia, dialysis if refractory AKI.",
        "hypercalcaemia": "Hypercalcaemia of Malignancy: most common life-threatening metabolic emergency in cancer. Causes: bone metastases (osteolytic — breast, myeloma, RCC), PTHrP secretion (humoral hypercalcaemia of malignancy — lung, breast, RCC, squamous), 1,25-(OH)2D production (lymphoma). Symptoms: bones (bone pain, pathological fracture), groans (abdominal pain, nausea, constipation, pancreatitis), psychic moans (confusion, drowsiness, coma — severe), stones (nephrolithiasis, nephrogenic DI, polyuria), groans (cardiac: shortened QT, arrhythmias). Management: IV fluids (saline 0.9% 200-300mL/hr) — most important; zoledronic acid 4mg IV (bisphosphonate — most effective for malignant hypercalcaemia, onset 2-4 days); denosumab 120mg SC (if renal impairment or bisphosphonate refractory); calcitonin 4-8IU/kg SC/IM (rapid onset 4-6h, tachyphylaxis); corticosteroids (haematological malignancies, vitamin D-mediated); loop diuretics (frusemide) ONLY after volume repletion.",
    },
    "palliative_care": {
        "name": "Palliative Care & Supportive Oncology",
        "principles": "Palliative care is specialised medical care focused on providing relief from symptoms, pain, and stress of serious illness — at ANY stage of cancer, alongside curative or active treatment (not just end-of-life). Early integration of palliative care alongside oncological treatment improves quality of life, reduces symptom burden, and has been shown in landmark trials (Temel 2010 NEJM) to improve survival in metastatic NSCLC. WHO definition: approach that improves quality of life of patients and families facing life-threatening illness through prevention and relief of suffering by early identification and impeccable assessment and treatment of pain and other physical, psychosocial, and spiritual problems.",
        "pain_management": "Cancer pain management follows the WHO analgesic ladder (updated 2018): Step 1 (mild pain, NRS 1-3): non-opioid analgesics — paracetamol 1g QDS, NSAIDs (ibuprofen/naproxen — caution renal/gastric, avoid in thrombocytopaenia/anticoagulation). Step 2 (moderate pain, NRS 4-6): weak opioids — codeine, tramadol, low-dose strong opioids (morphine 5mg 4-hourly for opioid-naive). Step 3 (severe pain, NRS 7-10): strong opioids — oral morphine (first-line WHO recommendation, cheap, widely available, MR-morphine 12-hourly); oxycodone (more expensive, similar efficacy); hydromorphone; transdermal fentanyl (not for acute titration, use once stable oral opioid dose established). Opioid rotation for intolerance/inadequate analgesia. ADJUVANTS: neuropathic pain — amitriptyline/nortriptyline, gabapentin/pregabalin, duloxetine, ketamine (refractory); bone pain — NSAIDs, bisphosphonates, corticosteroids, radiotherapy (single 8Gy — equally effective as multiple fractions for bone metastasis pain — CHARTWEL); liver capsule pain — dexamethasone 4-8mg OD. Laxative MANDATORY with opioids (lactulose+senna, macrogol). Antiemetic (haloperidol 1.5mg nocte, metoclopramide, cyclizine). Opioid-induced constipation unresponsive to laxatives: naloxegol, methylnaltrexone (peripherally-acting mu-opioid receptor antagonists). BREATHLESSNESS: low-dose oral morphine (most evidence), anxiolytics (lorazepam, midazolam), fan directed at face, breathing exercises, positioning. ANTICIPATORY PRESCRIBING: subcutaneous PRN doses prescribed in advance for dying patients (morphine, midazolam, haloperidol, hyoscine).",
        "psychosocial": "Psychosocial oncology: distress screening (Distress Thermometer — routinely in all cancer patients), anxiety and depression affect 30-50% of cancer patients (underdiagnosed and undertreated). Screening tools: PHQ-9 (depression), GAD-7 (anxiety). Interventions: CBT-based psychological therapy, mindfulness-based cognitive therapy (MBCT), acceptance and commitment therapy (ACT), antidepressants (SSRIs — sertraline, citalopram; SNRIs — venlafaxine useful for hot flushes). Cancer-related fatigue (CRF): most prevalent side effect. Exercise (aerobic + resistance training — Level 1 evidence) is the most effective intervention; psychostimulants (methylphenidate — modest evidence for cancer-related fatigue); treat underlying causes (anaemia, depression, hypothyroidism, sleep disorders). Survivorship: long-term effects of treatment (secondary cancers, cardiovascular disease from radiotherapy, lymphoedema, cognitive effects — chemo-brain), fertility preservation (sperm banking, oocyte/embryo cryopreservation before gonadotoxic therapy), sexual health, return to work.",
        "end_of_life": "Goals-of-care conversations and advance care planning are integral to quality oncology care. Liverpool Care Pathway (replaced by end-of-life care guidance). Diagnosing dying: recognition of the last days of life — deterioration over days, bedbound, minimal oral intake, reduced consciousness, mottled peripheries, Cheyne-Stokes breathing. Last days of life management: cease inappropriate medications, switch to SC route (syringe driver for continuous SC infusion — morphine for pain/breathlessness, midazolam for agitation/seizures, haloperidol for nausea/delirium, hyoscine butylbromide for respiratory secretions), mouth care, regular position changes, family support, spiritual/religious care. DNACPR (Do Not Attempt Cardiopulmonary Resuscitation) — discussion with patient and family, documented. ReSPECT (Recommended Summary Plan for Emergency Care and Treatment) process.",
    },
    "india_oncology": {
        "name": "Oncology in India",
        "cancer_burden": "India faces a dual burden of cancers linked to infection/tobacco and Western-pattern lifestyle cancers. ICMR NCDIR 2022 data: approximately 1.46 million new cancer cases in 2022. Top cancers in India: Breast (14.2%), Cervix (9.4% — HPV-related, significantly higher than West), Mouth/Oral cavity (9.3% — tobacco/areca nut driven), Lung (7.5%), Colorectum (5.5%), Oesophagus (4.1%), Stomach (4%), Leukaemia (3.6%). India-specific features: very high incidence of oral cancers (gutka/tobacco chewing, betel quid, areca nut), gallbladder cancer (3rd most common in women in North India — particularly UP, Bihar — associated with gallstones, bile carcinogens, Salmonella typhi), tobacco-related cancers (39% of all Indian cancers are tobacco-attributable), uterine cervical cancer (second most common — need for national vaccination and screening scale-up). Cancer survival in India: generally 20-30% lower than Western nations due to late-stage presentation (60-70% present with Stage III/IV), limited awareness, screening gaps, access to diagnosis/treatment.",
        "treatment_access": "India has approximately 400+ cancer centres (regional cancer centres RCCs + tertiary care hospitals). Major centres: Tata Memorial Centre (TMC) Mumbai — Asia's largest cancer hospital; AIIMS New Delhi, AIIMS various states; All India Cancer Research Foundation; Regional Cancer Centre Thiruvananthapuram; Rajiv Gandhi Cancer Institute Delhi; Apollo, Fortis, Manipal Cancer Centres. PMJAY (Ayushman Bharat — health insurance for BPL families — covers cancer up to Rs 5 lakh), State insurance schemes. Generic drugs widely available — reduced cost of imatinib, trastuzumab biosimilars. CIPLA, Dr Reddy, Cipla manufactured generic targeted therapies reduce cost significantly (imatinib generic: 200-500 INR/month vs 3000-4000 brand Gleevec; generic trastuzumab biosimilars reduce cost by 60-70%). Challenges: concentration of quality oncology care in Tier-1 cities, diagnostic delays (average 6-9 months from symptom to diagnosis), out-of-pocket expenditure (70% of health spend in India OOC despite PMJAY), lack of palliative care access (opioid availability poorly distributed in rural India).",
        "prevention": "Primary prevention: Tobacco control (India has 267 million tobacco users — world's 2nd largest). Cigarette Act, Tobacco Control Laws, graphic warnings, COTPA (Cigarettes and Other Tobacco Products Act) — smokeless tobacco (gutka, khaini, pan masala banned in several states). HPV vaccination (Gardasil, Cervarix, Cervavac — India-made HPV vaccine approved 2022; national immunisation programme roll-out for girls 9-14 years). Hepatitis B vaccination (universal childhood vaccination). H. pylori eradication (testing for gastric cancer prevention in high-risk). Aflatoxin reduction (food storage improvements to prevent HCC). Secondary prevention (screening): Cervical cancer — visual inspection with acetic acid (VIA/VILI) — pragmatic, low-cost screening tool for low-resource settings; HPV DNA testing (cervical cancer screening recommendation); Pap smear. Oral cancer — visual inspection by trained health workers (effective in RCT trials in Kerala). Breast cancer — clinical breast examination, mammography in urban settings. National Cancer Screening Programme (NCSP) 2016: common cancers in primary health centres (PHC) — oral, cervical, breast cancer screening pilot. ICMR guidelines for cancer prevention in India.",
        "tobacco_cessation": "Tobacco cessation is the single most impactful cancer prevention measure in India. First-line: Nicotine Replacement Therapy (NRT — patch, gum, lozenge), combination NRT (patch+quick-release), varenicline (Champix — most effective single agent, 12-24 weeks), bupropion SR. 5As framework (Ask, Advise, Assess, Assist, Arrange). iQuit service (iCloud-based cessation support). National Tobacco Cessation Helpline 1800-11-2356. For smokeless tobacco: oral nicotine pouches, behavioural support. Integration of cessation counselling in all cancer clinic visits. Quitting reduces lung cancer risk by 50% after 10 years; oral cancer risk falls substantially after 5 years abstinence.",
    },
}

def save_knowledge():
    with open(DATA_DIR / "onco_knowledge.json", "w", encoding="utf-8") as f:
        json.dump(KNOWLEDGE, f, indent=2, ensure_ascii=False)

def load_sessions():
    sf = DATA_DIR / "sessions.json"
    if sf.exists():
        with open(sf) as f: return json.load(f)
    return {}

def save_session(sid, data):
    sessions = load_sessions()
    sessions[sid] = {**data, "updated": datetime.datetime.now().isoformat()}
    with open(DATA_DIR / "sessions.json", "w") as f: json.dump(sessions, f, indent=2)

def is_online():
    if not REQUESTS_OK: return False
    try: req_lib.get("https://8.8.8.8", timeout=3); return True
    except: return False

def extract_pdf_text(filepath):
    if not FITZ_OK: return "[PDF extraction unavailable]"
    try:
        doc = fitz.open(str(filepath))
        text = "".join(page.get_text() for page in doc)
        doc.close(); return text[:8000]
    except Exception as e: return f"[PDF error: {e}]"

DEFAULT_SYSTEM = (
    "You are OncoCare AI, an expert oncology health research assistant. "
    "Help patients and caregivers understand cancer conditions, treatments, clinical trials, "
    "and supportive care from published oncology literature. "
    "ALWAYS start with a brief AI research disclaimer. "
    "Reference NCCN, ESMO, ASCO, IARC, WHO, NICE, ICMR guidelines. "
    "ALWAYS end reminding them to consult a qualified oncologist. "
    "For oncology emergencies (neutropenic fever, spinal cord compression, "
    "SVC syndrome, tumour lysis syndrome): advise immediate hospital attendance or 112/999/911. "
    "For Indian patients: reference ICMR, TMC Mumbai, AIIMS guidelines; note tobacco/gutka risks; "
    "mention PMJAY and generic drug availability where relevant."
)

def call_ai(prompt, system_prompt=None, max_tokens=2500, provider=None, api_key=None):
    if not AI_PROVIDERS_OK: return None, "ai_providers_missing"
    provider = validate_provider(provider)
    effective_key = (sanitise_api_key(api_key) or
                     DEFAULT_PROVIDER_KEYS.get(provider, "") or
                     (API_KEY if provider == "anthropic" else ""))
    if not effective_key or not REQUESTS_OK or not is_online():
        return None, "offline_or_no_key"
    text, mode = ai_providers.call_ai(
        provider, effective_key, prompt, system_prompt or DEFAULT_SYSTEM, max_tokens
    )
    if text is None:
        log.error(f"{provider} API error: {mode}")
        return None, mode
    return text, "live_ai"

def build_offline_response(topic, patient_info=None):
    topic_l = topic.lower()
    kb_key = next(
        (k for k in KNOWLEDGE
         if k.replace("_", " ") in topic_l or topic_l in k.replace("_", " ")
         or any(w in topic_l for w in k.split("_"))),
        None
    )
    lines = [
        "# OncoCare AI Research Report",
        f"**Topic:** {topic}",
        "**Mode:** Offline Research (Embedded Oncology Knowledge Base)",
        "",
        "> DISCLAIMER: AI-generated educational information. NOT medical advice. "
        "ALWAYS consult a qualified oncologist. "
        "ONCOLOGY EMERGENCY: Call 112 (India) / 999 (UK) / 911 (US).",
        "", "---", ""
    ]
    if kb_key:
        kb = KNOWLEDGE[kb_key]
        lines.append(f"## {kb.get('name', topic)}\n")
        for field, value in kb.items():
            if field == "name": continue
            if isinstance(value, str):
                lines += [f"**{field.replace('_', ' ').title()}:** {value}", ""]
    else:
        lines += [f"## Research Overview: {topic}", "",
                  f"Enable live AI in Settings for detailed research on {topic}.", ""]
    lines += [
        "---",
        "## India Cancer Resources",
        "- Tata Memorial Centre Mumbai: tmc.gov.in | NCCN India Guidelines",
        "- AIIMS Oncology: aiims.edu | ICMR: icmr.gov.in",
        "- Cancer Helpline: 1800-11-6666 | PMJAY: pmjay.gov.in",
        "- Tobacco Cessation: 1800-11-2356",
        "- Emergency: 112",
        "",
        f"WARNING - {DISCLAIMER}"
    ]
    return "\n".join(lines)

@app.route("/")
def index():
    return send_from_directory(str(STATIC_DIR), "index.html")

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(str(STATIC_DIR), filename)

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "version": VERSION,
                    "online": is_online(), "pdf_extract": FITZ_OK,
                    "timestamp": datetime.datetime.now().isoformat()})

@app.route("/api/upload", methods=["POST"])
def upload():
    if "files" not in request.files: return jsonify({"error": "No files"}), 400
    session_id = request.form.get("session_id") or str(uuid.uuid4())
    session_dir = UPLOAD_DIR / session_id; session_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for f in request.files.getlist("files"):
        if not f.filename: continue
        ext = Path(f.filename).suffix.lower()
        safe = f"{uuid.uuid4().hex}{ext}"; dest = session_dir / safe; f.save(str(dest))
        extracted = extract_pdf_text(dest) if ext == ".pdf" else ""
        results.append({"original": f.filename, "saved": safe,
                        "type": "pdf" if ext == ".pdf" else ("image" if ext in [".jpg",".jpeg",".png"] else "text"),
                        "size_kb": round(dest.stat().st_size/1024, 1), "has_content": bool(extracted)})
    existing = load_sessions().get(session_id, {})
    save_session(session_id, {"session_id": session_id, "files": existing.get("files",[]) + results})
    return jsonify({"success": True, "session_id": session_id,
                    "uploaded": len(results), "files": results, "disclaimer": DISCLAIMER})

@app.route("/api/analyse", methods=["POST"])
def analyse():
    data = request.json or {}
    if not rate_limit_check(): return jsonify({"error": "Rate limit exceeded"}), 429
    topic = data.get("topic", "General Oncology"); condition = data.get("condition", "")
    patient_info = data.get("patient_info", {})
    provider = validate_provider(data.get("provider", "anthropic"))
    effective_key = (sanitise_api_key(data.get("api_key","")) or
                     DEFAULT_PROVIDER_KEYS.get(provider,"") or
                     (API_KEY if provider=="anthropic" else ""))
    prompt = (
        f"Oncology Research Request: {topic} / {condition}\n"
        f"Patient: Age {patient_info.get('age','NR')}, Diagnosis: {patient_info.get('diagnosis','NR')}, "
        f"Stage: {patient_info.get('stage','NR')}, ECOG: {patient_info.get('ecog','NR')}\n"
        f"Prior treatment: {patient_info.get('prior_tx','none')}, "
        f"Biomarkers: {patient_info.get('biomarkers','not tested')}\n"
        "Cover: cancer biology, molecular classification, staging, evidence-based treatment options "
        "(surgery/RT/chemo/targeted/immunotherapy), clinical trials, supportive care, "
        "ICMR/India context, questions for oncologist. Reference NCCN, ESMO, ASCO, NICE, ICMR."
    )
    result, mode = (call_ai(prompt, provider=provider, api_key=effective_key)
                    if (effective_key and is_online()) else (None,"offline"))
    if not result: result = build_offline_response(topic, patient_info); mode = "offline"
    return jsonify({"success": True, "mode": mode, "analysis": result,
                    "topic": topic, "disclaimer": DISCLAIMER,
                    "timestamp": datetime.datetime.now().isoformat()})

@app.route("/api/condition/<condition_name>")
def condition_detail(condition_name):
    cn = condition_name.lower().replace("-","_").replace(" ","_")
    if cn in KNOWLEDGE:
        return jsonify({"success": True, "mode": "offline_kb",
                        "condition": KNOWLEDGE[cn], "disclaimer": DISCLAIMER})
    provider = validate_provider(request.args.get("provider","anthropic"))
    effective_key = (sanitise_api_key(request.args.get("api_key","")) or
                     DEFAULT_PROVIDER_KEYS.get(provider,"") or
                     (API_KEY if provider=="anthropic" else ""))
    prompt = (f"Comprehensive oncology research on {condition_name}: epidemiology, "
              "molecular biology, staging, diagnosis, multidisciplinary treatment (NCCN/ESMO/ASCO), "
              "targeted therapies, immunotherapy, clinical trials, India-specific context (ICMR/TMC).")
    result, mode = call_ai(prompt, provider=provider, api_key=effective_key)
    if not result: result = build_offline_response(condition_name); mode = "offline"
    return jsonify({"success": True, "mode": mode, "content": result, "disclaimer": DISCLAIMER})

@app.route("/api/onco/assess", methods=["POST"])
def assess_onco():
    data = request.json or {}
    diagnosis = data.get("diagnosis",""); stage = data.get("stage","")
    biomarkers = data.get("biomarkers",""); prior_tx = data.get("prior_tx","")
    ecog = data.get("ecog",""); age = data.get("age","")
    provider = validate_provider(data.get("provider","anthropic"))
    effective_key = (sanitise_api_key(data.get("api_key","")) or
                     DEFAULT_PROVIDER_KEYS.get(provider,"") or
                     (API_KEY if provider=="anthropic" else ""))
    prompt = (
        f"Oncology Case Research:\nDiagnosis: {diagnosis}\nStage: {stage}\n"
        f"Age: {age}, ECOG: {ecog}\nKey Biomarkers: {biomarkers}\nPrior Treatment: {prior_tx}\n"
        "Provide: treatment options by evidence level, relevant clinical trials, "
        "molecular testing recommendations, supportive care priorities, "
        "India-specific considerations (generic availability, TMC/AIIMS protocols, PMJAY). "
        "Educational research only — must consult oncologist for actual treatment decisions."
    )
    result, mode = call_ai(prompt, provider=provider, api_key=effective_key)
    if not result:
        result = (f"Oncology case research for {diagnosis} Stage {stage}. "
                  "Enable live AI for detailed evidence-based treatment research. "
                  "Always consult your oncologist for actual treatment decisions.")
        mode = "offline"
    return jsonify({"success": True, "mode": mode, "content": result, "disclaimer": DISCLAIMER})

@app.route("/api/chat/send", methods=["POST"])
def chat_send():
    data = request.json or {}
    message = data.get("message","").strip()
    if not message: return jsonify({"error": "Empty message"}), 400
    provider = validate_provider(data.get("provider","anthropic"))
    effective_key = (sanitise_api_key(data.get("api_key","")) or
                     DEFAULT_PROVIDER_KEYS.get(provider,"") or
                     (API_KEY if provider=="anthropic" else ""))
    result = None
    if data.get("request_ai") and is_online() and effective_key:
        result, _ = call_ai(
            f"Cancer patient/caregiver question: '{message}'. "
            "3-4 paragraphs, compassionate and evidence-based. "
            "Include India-specific guidance where relevant. "
            "End with oncologist consultation reminder. "
            "For oncology emergencies (neutropenic fever, cord compression): 112/999/911 immediately.",
            max_tokens=800, provider=provider, api_key=effective_key)
    return jsonify({"success": True, "ai_response": result,
                    "disclaimer": "Not medical advice. Consult your oncologist."})

@app.route("/api/report/generate", methods=["POST"])
def generate_report():
    data = request.json or {}
    topic = data.get("topic","General Oncology"); patient = data.get("patient_info",{})
    provider = validate_provider(data.get("provider","anthropic"))
    effective_key = (sanitise_api_key(data.get("api_key","")) or
                     DEFAULT_PROVIDER_KEYS.get(provider,"") or
                     (API_KEY if provider=="anthropic" else ""))
    content = build_offline_response(topic, patient)
    if effective_key and is_online():
        ai_content, _ = call_ai(
            f"Generate comprehensive oncology research report for: {topic}. "
            f"Patient: {patient}. Cover staging, treatment options, "
            "clinical trials, supportive care, India resources.",
            max_tokens=3500, provider=provider, api_key=effective_key)
        if ai_content: content = ai_content
    report_id = f"report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    report = {"report_id": report_id, "generated": datetime.datetime.now().isoformat(),
              "topic": topic, "patient": patient, "content": content, "disclaimer": DISCLAIMER}
    with open(REPORTS_DIR / f"{report_id}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    return jsonify(report)

@app.route("/api/resolve", methods=["POST"])
def resolve_multi_ai():
    data = request.json or {}
    if not rate_limit_check(): return jsonify({"error": "Rate limit exceeded"}), 429
    prompt = str(data.get("prompt","")).strip()[:4000]
    if not prompt: return jsonify({"error": "No prompt provided"}), 400
    pairs_raw = data.get("providers",[])
    if not isinstance(pairs_raw, list) or len(pairs_raw) < 1:
        return jsonify({"error": "No providers specified"}), 400
    if not AI_PROVIDERS_OK: return jsonify({"error": "ai_providers module not available"}), 500
    pairs = []
    for p in pairs_raw[:6]:
        pid = validate_provider(p.get("provider",""))
        key = sanitise_api_key(p.get("key",""))
        if pid and key: pairs.append((pid, key))
    if not pairs: return jsonify({"error": "No valid provider+key pairs"}), 400
    results = ai_providers.call_multi_ai(pairs, prompt, DEFAULT_SYSTEM, 1500)
    successes = [r for r in results if r.get("success") and r.get("text")]
    synthesis = None
    if len(successes) >= 2:
        synth_parts = [f"=== {r.get('label',r.get('provider','AI'))} ===\n{(r.get('text') or '')[:1200]}"
                       for r in successes]
        synth_prompt = (
            "You are an oncology research synthesis engine. Multiple AI systems answered the same "
            "oncology research question. Question: " + prompt + "\n\n" +
            "\n\n".join(synth_parts) + "\n\n"
            "Synthesise the best, most complete, evidence-based oncology research answer. "
            "Note any disagreements. Lead with the most clinically important finding. "
            "Remind that this is research only — consult a qualified oncologist."
        )
        synth_key = next((k for pr,k in pairs if pr==successes[0]["provider"]), None)
        if synth_key:
            synth_text, _ = ai_providers.call_ai(
                successes[0]["provider"], synth_key, synth_prompt,
                "You are an oncology research synthesis assistant.", 2000)
            synthesis = synth_text
    return jsonify({"success": True, "responses": results,
                    "synthesis": synthesis, "disclaimer": DISCLAIMER})

@app.route("/api/providers")
def list_providers():
    if not AI_PROVIDERS_OK: return jsonify({"providers":[],"error":"ai_providers module not available"})
    return jsonify({"providers": [
        {"id":k,"label":v["label"],"default_model":v["default_model"],
         "key_prefix":v["key_prefix"],"get_key_url":v["get_key_url"],
         "server_default_configured":bool(DEFAULT_PROVIDER_KEYS.get(k))}
        for k,v in ai_providers.PROVIDERS.items()], "online": is_online()})

@app.route("/api/status")
def status():
    any_key = bool(API_KEY) or any(DEFAULT_PROVIDER_KEYS.values())
    return jsonify({"server":"running","version":VERSION,"online":is_online(),
                    "mode":"live_ai" if (any_key and is_online()) else "offline_research",
                    "capabilities":{"pdf":FITZ_OK,"images":PIL_OK,
                                    "live_ai":bool(any_key and is_online()),
                                    "offline":True,"multi_provider":AI_PROVIDERS_OK,
                                    "rate_limiting":True,"aes256_frontend":True,
                                    "ambiguity_resolver":True},
                    "knowledge_base":list(KNOWLEDGE.keys()),
                    "providers":list(ai_providers.PROVIDERS.keys()) if AI_PROVIDERS_OK else [],
                    "disclaimer":DISCLAIMER})

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()
    save_knowledge()
    log.info("="*60)
    log.info(f"  OncoCare AI Server v{VERSION} - Port {args.port}")
    log.info(f"  Online: {is_online()}")
    log.info(f"  URL: http://localhost:{args.port}")
    log.info(f"  Providers: {list(ai_providers.PROVIDERS.keys()) if AI_PROVIDERS_OK else 'N/A'}")
    log.info("="*60)
    app.run(host="0.0.0.0", port=args.port, debug=False, threaded=True, use_reloader=False)

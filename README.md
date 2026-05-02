# OncoCare AI v2.0
## Integrated Cancer Intelligence Platform
### Complete Setup, Usage & Troubleshooting Guide

---

## ⚠️ CRITICAL MEDICAL DISCLAIMER

**THIS IS AN AI-POWERED RESEARCH AND INFORMATION TOOL ONLY.**

- All analysis is AI-generated from multiple internet and medical sources
- Authenticity, accuracy, and clinical applicability **may be false or incorrect**
- This is **NOT** a medical diagnosis, prescription, or clinical recommendation
- **ALWAYS** consult a qualified oncologist or medical specialist before:
  - Taking any medication (allopathic, ayurvedic, or homeopathic)
  - Undergoing any test, scan, or procedure
  - Starting any treatment, diet, or exercise protocol
  - Making any health decision based on this output
- **FOR RESEARCH AND EDUCATIONAL PURPOSES ONLY**
- The creator accepts **no liability** for health decisions made using this platform

---

## 🚀 Quick Start

### Windows (Recommended)
1. Extract the ZIP to any folder (e.g., `C:\OncoCareAI\`)
2. Double-click **`START_OncoCare_AI.bat`**
3. Follow on-screen instructions — everything installs automatically
4. Browser opens automatically at `http://localhost:5050`
5. Accept the disclaimer and begin

### First Run Notes
- First run takes **3–8 minutes** (downloading Python packages)
- All packages install **inside this folder only** — nothing touches your system
- Internet required for first setup; works offline afterward (run `DOWNLOAD_OFFLINE_PACKAGES.bat` first)

---

## 📁 File Structure

```
OncoCareAI/
├── START_OncoCare_AI.bat          ← MAIN LAUNCHER (double-click this)
├── DIAGNOSTIC.bat                 ← Full system diagnostic tool
├── REPAIR_AND_RECOVER.bat         ← Fix broken installations
├── DOWNLOAD_OFFLINE_PACKAGES.bat  ← Save packages for offline use
├── UPDATE.bat                     ← Update to latest package versions
├── STOP_SERVER.bat                ← Stop the running server
├── server.py                      ← Python Flask backend
├── README.md                      ← This file
│
├── static/                        ← Web interface files
│   └── index.html                 ← Full frontend application
│
├── uploads/                       ← Your uploaded medical reports
├── offline_packages/              ← Cached Python packages (for offline use)
├── venv/                          ← Python virtual environment (auto-created)
├── python_runtime/                ← Local Python (if system Python not found)
├── logs/                          ← Server and diagnostic logs
├── data/                          ← Session data, chat history, knowledge base
└── reports_db/                    ← Generated AI reports (JSON)
```

---

## 🔧 BAT Files Explained

| File | Purpose | When to Use |
|------|---------|-------------|
| `START_OncoCare_AI.bat` | Main launcher | Every time you want to use OncoCare AI |
| `DIAGNOSTIC.bat` | Full system health check | When something isn't working |
| `REPAIR_AND_RECOVER.bat` | Fix broken installs | When errors occur |
| `DOWNLOAD_OFFLINE_PACKAGES.bat` | Cache packages offline | Once, while connected to internet |
| `UPDATE.bat` | Update Python packages | Monthly or when updates available |
| `STOP_SERVER.bat` | Stop the server | When you want to close OncoCare AI |

---

## 💻 System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Windows 10 | Windows 11 |
| RAM | 4 GB | 16 GB |
| Storage | 3 GB free | 20 GB free |
| Internet | For first setup | Broadband preferred |
| Python | Auto-installed | 3.10–3.12 |
| GPU | Not required | NVIDIA 8GB+ (for local LLM) |

---

## 🤖 Platform Features

### 1. 📁 Upload Reports
Supports: Blood tests, MRI, CT, PET scans, X-rays, biopsy, genetic/NGS reports, pathology, prescriptions, doctor notes
Formats: PDF, JPG, PNG, DICOM, TXT, DOCX, CSV

### 2. 🔬 AI Diagnostic Engine
- Pattern analysis across uploaded reports
- Cancer type and staging context research
- Biomarker identification
- Recommended further test suggestions
- Works online (live Claude AI) and offline (embedded knowledge base)

### 3. 📊 Deep Analysis
- Tumour marker research
- Imaging pattern cross-reference
- Drug sensitivity literature review
- Progression risk factor research

### 4. 🧬 Genetic & Personalised Medicine
Research into:
- BRCA1/2, HER2, EGFR, KRAS, ALK, ROS1, PD-L1, TMB, MSI mutations
- Matched targeted therapies (drug-mutation pairs)
- PARP inhibitor eligibility
- Immunotherapy biomarker matching
- Personalised neoantigen cancer vaccines (inspired by Sid Sijbrandij's case)
- CAR-T cell therapy eligibility
- Clinical trial matching (ClinicalTrials.gov + CTRI India)

### 5. 💊 Treatment Research
**Allopathic:** Chemotherapy, targeted therapy, immunotherapy, CAR-T, surgery, radiation, HIPEC, proton beam
**Ayurvedic:** Herbal research (Ashwagandha, Turmeric, Tulsi, Triphala, Guduchi, Shatavari), Panchakarma
**Homeopathic:** Constitutional and supportive care remedy literature

### 6. 🥗 Lifestyle & Diet
- Anti-inflammatory and anti-cancer dietary protocols
- Cancer-specific meal plans
- Supplement research (with drug interaction cautions)
- Gut microbiome support during chemotherapy

### 7. 🧘 Yoga & Exercise
- Pranayama breathwork protocols
- Restorative yoga sequences
- Evidence-based aerobic and resistance training
- MBSR (Mindfulness-Based Stress Reduction) programme

### 8. 🧠 Psychological Care
- CBT adapted for cancer patients
- ACT (Acceptance and Commitment Therapy)
- Meaning-Centred Psychotherapy (MSK protocol)
- CBT-I for cancer-related insomnia
- Caregiver support frameworks
- Crisis helplines (India + international)

### 9. 💬 Global Community Chat
- Patient-to-patient support
- Healthcare professional Q&A
- Survivor stories and encouragement
- AI-assisted responses when online

### 10. 📋 Generate Full Report
- Comprehensive AI-researched report for your cancer type and stage
- Print-ready format for sharing with your medical team
- Covers all treatment options, diet, genetics, psychology

---

## 🔑 API Key Setup (for Live AI)

Without an API key, the platform works in **offline research mode** using the embedded medical knowledge base.

**To enable live AI:**
1. Go to Settings in the sidebar
2. Enter your Anthropic API key (get at console.anthropic.com)
3. Click Save Key
4. The platform now uses live Claude AI for deeper, more personalised research

**API key is stored locally in your browser — never sent to external servers.**

---

## 🌐 Online vs Offline Mode

| Feature | Online (with API key) | Online (no key) | Offline |
|---------|----------------------|-----------------|---------|
| AI Analysis | Live Claude AI | Demo mode | Embedded knowledge base |
| Report Upload | ✔ | ✔ | ✔ |
| Treatment Research | Live AI | Demo | Embedded (50+ cancers) |
| Genetic Analysis | Live AI | Demo | Embedded |
| Diet & Yoga | Live AI | Demo | Embedded |
| Chat | AI-assisted | Basic | Basic |
| Report Generation | Full AI | Demo | Embedded |

**The embedded offline knowledge base covers:**
Breast, Lung, Colorectal, Leukemia (AML/CML/ALL/CLL), Prostate, and general cancer research
with biomarkers, treatments, ayurveda, genetics, diet, yoga, and India resources — all available without internet.

---

## 🏥 Best AI Models for Medical Use

| Model | Best For | Access |
|-------|----------|--------|
| **Claude 3.5 Sonnet** | Large document analysis (200K tokens) | API at console.anthropic.com |
| **Med-PaLM 2** | Medical Q&A and clinical reasoning | Google Cloud |
| **BioMedLM** (Stanford) | PubMed-trained biomedical research | Open source |
| **RadDINO** (Microsoft) | CT, MRI, X-ray, PET image analysis | Open source |
| **Llama 3 Med42** | Local offline medical reasoning | Ollama (free) |
| **GPT-4o** | Multi-modal, can read medical images | OpenAI API |
| **ClinicalBERT** | Parsing clinical notes and records | Open source |

### Running AI Locally (No Internet After Setup)
```bash
# Install Ollama from ollama.ai (free)
ollama pull llama3-med42          # Medical fine-tuned Llama 3
ollama pull medllama2             # Medical Llama 2

# For PDF document chat:
# Download AnythingLLM from anythingllm.com (free, runs locally)
# Upload your medical PDFs and ask questions

# For DICOM/MRI/CT viewing:
# Download 3D Slicer from slicer.org (free, with AI plugins)
```

---

## 🧬 Personalised Medicine & Custom Vaccines

### The Science
Personalised cancer treatment uses your tumour's unique genomic profile to:
- Create neoantigen vaccines targeting mutations only in YOUR cancer cells
- Match you to targeted therapies (drug + mutation pairs)
- Assess CAR-T cell therapy eligibility
- Identify clinical trials matching your genetic signature

### Real-World Cases
- **Sid Sijbrandij** (GitLab CEO): Stage 4 spinal cancer → 19 custom DNA-based neoantigen vaccines → cancer-free since 2025
- **Pratik Desai**: Fed 1,600 pages of medical records to Claude AI → caught missed diagnosis → extended mother's life

### How to Access This in India
1. **NGS Testing:** MedGenome Labs, Strand Life Sciences, Tata Memorial ACTREC
2. **Oncogenomics consultation:** AIIMS molecular oncology, Tata Memorial, Apollo Proton
3. **Clinical trials:** Search CTRI (ctri.nic.in) and ClinicalTrials.gov with your mutation profile
4. **Cost:** NGS panels: ₹15,000–₹1,50,000 depending on depth; some available under PM-JAY

---

## 🔧 Troubleshooting

### Problem: Double-clicking BAT shows nothing / closes immediately
**Fix:** Right-click → "Run as administrator"
**OR:** Open Command Prompt as Administrator, navigate to folder, type: `START_OncoCare_AI.bat`

### Problem: "Python not found"
**Fix:** The launcher will download Python automatically if connected. For manual install: python.org/downloads → check "Add Python to PATH"

### Problem: Browser doesn't open
**Fix:** Manually open browser and go to: `http://localhost:5050`

### Problem: "Port in use" error
**Fix:** Run `STOP_SERVER.bat` first, then try again. Or restart your computer.

### Problem: Package install fails
**Fix:** Run `REPAIR_AND_RECOVER.bat` → Option 2 (Reinstall all packages)

### Problem: Server starts but app shows errors
**Fix:** Check `logs\server_live.log` for details. Run `DIAGNOSTIC.bat` for full report.

### Problem: Want to use completely offline
**Fix:** While connected to internet, run `DOWNLOAD_OFFLINE_PACKAGES.bat` once. All packages cached locally.

---

## 🔒 Privacy & Security

- **Local first:** All data stays on YOUR computer
- **Uploads:** Stored in `uploads/` folder on your device only
- **API calls:** If you use live AI, anonymised text is sent to Anthropic's servers (same as using Claude.ai)
- **No telemetry:** No usage data collected by this application
- **Full offline mode:** Use `DOWNLOAD_OFFLINE_PACKAGES.bat` + local LLM (Ollama) for complete privacy

---

## 📞 Important Resources

### India Cancer Resources
| Resource | Contact |
|----------|---------|
| Tata Memorial Hospital, Mumbai | tmc.gov.in · 022-2417-7000 |
| AIIMS Cancer Centre, Delhi | aiims.edu · 011-2659-3308 |
| National Cancer Grid India | ncg.tmc.gov.in |
| CTRI (Clinical Trials India) | ctri.nic.in |
| CPAA Patient Support | cpaa.org.in · 022-2413-9445 |
| CanSupport Palliative | cansupport.in · 011-4165-5174 |
| iCall Mental Health | 9152987821 |
| Vandrevala 24/7 | 1860-2662-345 |
| National Cancer Helpline | 1800-180-1104 |

### Global Resources
- ClinicalTrials.gov — All cancer clinical trials
- PubMed — Medical research papers
- NCCN Guidelines — nccn.org/guidelines
- OncoKB — oncokb.org (precision oncology)
- WHO Cancer — who.int/cancer

---

## ⚖️ Legal Notice

This software is provided "as is" for research and educational purposes only. The creators make no representations about medical accuracy, completeness, or fitness for clinical use. Use of this tool does not constitute a medical consultation or create any professional relationship. The creators are not liable for any health outcomes related to use of this platform. By using this software, you acknowledge you have read and accepted the full medical disclaimer.

---

*OncoCare AI v2.0 — Built with care for patients seeking knowledge.*
*Knowledge empowers. Your oncologist heals. Use both.*

# OncoCare AI v3.0
## Oncology Health Intelligence Platform

## CRITICAL ONCOLOGY EMERGENCY DISCLAIMER
- **Neutropenic fever** (temp >38°C during chemotherapy): Hospital IMMEDIATELY — treat within 1 hour
- **Spinal cord compression** (new back pain + leg weakness/bladder changes): Urgent MRI same day
- **SVC syndrome** (facial/arm swelling, stridor): Urgent assessment
- **Tumour lysis syndrome**: Metabolic emergency after treatment of high-burden disease
- All content is AI-generated educational research only — NOT medical advice

## Quick Start (Windows)
1. Extract ZIP to any folder
2. Double-click **START_OncoCare_AI.bat**
3. Auto-installs everything (2-5 min first time)
4. Browser opens at **http://localhost:5050**
5. Accept disclaimer and begin

## Security — AES-256-GCM
- API keys AES-256-GCM encrypted client-side before localStorage
- PBKDF2 key derivation (100,000 iterations) from device fingerprint
- XSS protection: escapeHtml(), escapeFilename(), sanitizeAIResponse()
- Backend rate limiting (30 req/60s), input sanitisation, provider whitelist

## 6 AI Providers (All Real API Calls)
| Provider | Model | Get Key |
|---|---|---|
| Claude (Anthropic) | claude-sonnet-4-20250514 | console.anthropic.com |
| ChatGPT (OpenAI) | gpt-4o | platform.openai.com/api-keys |
| Gemini (Google) | gemini-2.0-flash | aistudio.google.com/apikey |
| Grok (xAI) | grok-2-latest | console.x.ai |
| DeepSeek | deepseek-chat | platform.deepseek.com/api_keys |
| Mistral AI | mistral-large-latest | console.mistral.ai/api-keys |

## Ambiguity Resolver
Query 2-6 AIs simultaneously (parallel) — synthesised best answer generated automatically.
Click **⚡ Ambiguity Resolver** in the Chat panel.

## Sections (15 Panels)
- **Conditions** — 30+ dropdown (solid tumours, haematological, India-specific, emergencies)
- **Breast** — 4 tabs: Subtypes/Diagnosis, Surgery/RT, Systemic therapy, Screening
- **Lung** — 4 tabs: Overview, Molecular targets (EGFR/ALK/KRAS G12C table), Treatment, Screening
- **Colorectal** — Hereditary syndromes, staging, treatment, screening
- **Haematology** — 3 tabs: Leukaemias, Lymphomas, Stem cell transplant/CAR-T
- **Immunotherapy** — 4 tabs: Checkpoint inhibitors, Targeted therapy, ADCs, CAR-T/Bispecifics
- **Chemotherapy** — Common regimens, toxicity management
- **Emergency** — Febrile neutropenia, cord compression, SVC syndrome, tumour lysis
- **Palliative Care** — WHO analgesic ladder, early integration evidence
- **India Oncology** — ICMR burden data, TMC/AIIMS access, PMJAY, prevention
- **Assessment** — Case-based AI research with diagnosis/stage/biomarkers/ECOG

## India Cancer Resources
- Tata Memorial Centre: tmc.gov.in | AIIMS: aiims.edu | ICMR: icmr.gov.in
- Cancer Helpline: 1800-11-6666 | Tobacco Cessation: 1800-11-2356 | PMJAY: pmjay.gov.in
- Emergency: **112**

## Clinical Sources
NCCN | ESMO | ASCO | IARC | WHO | NICE | ICMR | PubMed

*OncoCare AI v3.0 — For research and educational purposes only. Not medical advice.*
*ONCOLOGY EMERGENCY: 112 (India) / 999 (UK) / 911 (US)*

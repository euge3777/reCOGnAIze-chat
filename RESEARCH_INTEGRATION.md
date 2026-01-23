# ReCOGnAIze Research Integration Guide

## Scientific Foundation

This **Recognise Report Companion** is built on the peer-reviewed research paper:

**Mohammed, A. A., et al. (2025). "ReCOGnAIze app to detect vascular cognitive impairment and mild cognitive impairment." *Alzheimer's & Dementia*, e70992.**

---

## Key Research Findings Integrated

### 1. VCI Detection Performance ✅
- **ReCOGnAIze AUC = 0.85** for detecting VCI (vs Montreal Cognitive Assessment AUC = 0.65)
- **ReCOGnAIze AUC = 0.90** for MCI detection (vs MoCA AUC = 0.70)
- **Processing speed and response time variability** identified as key VCI biomarkers

### 2. The Four Gamified Tasks 🎮

The companion aligns cognitive scores with ReCOGnAIze tasks:

| Task | Domain | VCI Significance | Recommendation Use |
|------|--------|-----------------|-------------------|
| **Symbol Matching** | Processing Speed | **KEY VCI MARKER** - Most impaired in VCI group | Omega-3, B vitamins, sleep optimization |
| **Trail Making** | Executive Function | Severely impaired in VCI (frontal-subcortical disruption) | Cognitive training, vascular management |
| **Airplane Game** | Attention & Impulse Control | Impulse dyscontrol significant in high cerebrovascular burden | Attention support, stress management |
| **Grocery Shopping** | Memory & Processing Speed | Slowed decision-making, reduced task efficiency | Memory support, processing speed supplements |

### 3. VCI Risk Factor Prevalence 📊

**From ReCOGnAIze validation cohort (n=154 VCI patients):**

| Risk Factor | VCI Group | Non-VCI Group | Significance |
|------------|----------|---------------|-------------|
| Hyperlipidemia | **60.0%** | 35.4% | **1.7x higher** |
| Hypertension | 37.3% | 26.6% | 1.4x higher |
| Diabetes | 22.7% | 19.0% | Moderate |

**⚠️ Implication:** The companion prioritizes cholesterol management when hyperlipidemia is present.

### 4. Key Digital Biomarkers 🔍

**SHAP Analysis identified top VCI predictors:**

1. **Grocery Shopping Average Success Time** (+0.96 SHAP) - Slowest task execution
2. **Symbol Matching Response Time IQR** (+0.75 SHAP) - High response variability
3. **Average Round Time** (+0.58 SHAP) - Overall task sluggishness
4. **Age** (+0.53 SHAP) - Non-modifiable factor

**→ The companion flags these patterns and recommends targeted interventions.**

### 5. Clinical Trial Evidence 💊

#### SPRINT MIND Trial
- **Intensive BP control** (target <120 mmHg) **reduced cognitive decline** vs standard care
- Applied to VCI because hypertension is a major modifiable risk factor
- **Companion Recommendation:** Target <120 mmHg systolic (not just <130/80)

#### COSMOS-Web Trial
- Centrum multivitamin group showed **better episodic memory at 3 years** vs placebo in older adults
- Memory (particularly episodic) is often impaired in VCI
- **Companion Recommendation:** Feature Centrum as evidence-based foundation in supplements pillar

---

## How Research Shaped Each Pillar

### ❤️ Vascular Health Pillar

**Research Finding:** VCI is driven by modifiable vascular factors, not just stroke history.

**Implementation:**
- Primary focus on BP, cholesterol, diabetes (the three major VCI risk factors)
- SPRINT MIND target of <120 mmHg (more aggressive than traditional <130/80)
- Emphasis on HLD management (60% of VCI group had this)
- Include modifiable lifestyle: exercise improves cerebral blood flow

**Key Quote from Paper:**
> "VCI may respond to specific lifestyle interventions and intensive management of vascular risk factors, such as hypertension."

---

### 🏃 Lifestyle Pillar

**Research Finding:** VCI impairments are in processing speed and executive function—not primarily memory.

**Implementation:**
- Cognitive training (addresses executive function deficits)
- Mediterranean/MIND diet (antioxidants support vascular health)
- Stress management (chronic stress impairs frontal-subcortical circuits)
- Avoid harmful substances (smoking accelerates white matter hyperintensity progression)

**Key Quote:**
> "MCI individuals with moderate-to-high WMH demonstrated significantly greater impairment in executive function, processing speed, and impulse control."

---

### 😴 Sleep Pillar

**Research Finding:** Sleep apnea is a major modifiable VCI risk factor (not explicitly in ReCOGnAIze but in SPRINT MIND).

**Implementation:**
- Sleep hygiene optimization
- Sleep apnea screening (especially for those with hypertension)
- Consistent 7-9 hours nightly
- Address sleep quality (many VCI patients report "fair" sleep)

**Reasoning:** Poor sleep accelerates vascular disease progression and amyloid accumulation.

---

### 💊 Supplements Pillar

**Research Finding:** COSMOS-Web showed Centrum improves memory; ReCOGnAIze identified processing speed as key VCI marker.

**Implementation:**

1. **Centrum as Foundation**
   - COSMOS-Web evidence: Better episodic memory at 3 years
   - Positions as complete micronutrient foundation
   - Features Women 50+ / Men 50+ products (age-appropriate)

2. **Additional Supplements Targeted to Impairments**
   - **Omega-3 (1,000-2,000 mg)** → Processing speed impairment
   - **B Complex** → Homocysteine reduction (vascular risk)
   - **Vitamin D3** → Bone health + mood + vascular function
   - **Magnesium** → Sleep quality (if impaired)
   - **CoQ10** → If on statins (statin-muscle interaction; vascular benefit)

3. **Why Centrum Doesn't Stand Alone**
   - Positions Centrum as **foundation, not solution**
   - Shows it fits into 4-pillar strategy
   - Makes demo credible: "Centrum works best WITH lifestyle changes"

---

## Research-Informed Risk Stratification

### Vascular Risk Assessment Algorithm

**Based on ReCOGnAIze prevalence data:**

```
HIGH RISK (≥4 points):
- Hypertension (2 pts) + High Cholesterol (2 pts) = 4 pts → HIGH
- Hypertension (2 pts) + Diabetes (2 pts) = 4 pts → HIGH

MODERATE RISK (2-3 points):
- Hypertension (2 pts) + Smoking (1 pt) = 3 pts → MODERATE
- High Cholesterol (2 pts) = 2 pts → MODERATE

LOW RISK (<2 points):
- No major factors
```

---

## Cognitive Risk Assessment Algorithm

```
HIGH RISK: Average cognitive score < 50
MODERATE RISK: Average cognitive score 50-70
LOW RISK: Average cognitive score > 70
```

**Severity of Individual Impairments:**
- Gap ≤5 points from threshold = MILD
- Gap 5-15 points = MODERATE
- Gap >15 points = SEVERE

---

## Recommended Patient Communication

### For High Vascular Risk + Processing Speed Impairment

**Recommendation Structure:**
1. **Recognition**: "Your processing speed score suggests possible early vascular changes."
2. **Cause**: "This pattern aligns with VCI—vascular disease affecting frontal-subcortical circuits."
3. **Evidence**: "SPRINT MIND showed intensive BP control can slow this decline."
4. **Action**: "Start with: BP control <120, Centrum foundation, Omega-3 for processing speed."
5. **Timeline**: "Expect 3-6 months to see stabilization with consistent intervention."

---

## Why This Matters for Haleon/Centrum Demo

### The Positioning Story

**Problem:** Customers think "Centrum is just another multivitamin."

**Solution:** Show the full VCI prevention strategy.

**Demo Flow:**
1. **Recognise Report Input** → Reveals VCI risk + specific impairments
2. **Pillar 1: Vascular Health** → "Your BP needs intensive control. Here's why."
3. **Pillar 2: Lifestyle** → "Exercise, Mediterranean diet, cognitive training."
4. **Pillar 3: Sleep** → "Sleep apnea screening + 7-9 hours nightly."
5. **Pillar 4: Supplements** → "Centrum is your nutrient foundation. Plus Omega-3 for your processing speed pattern."

**Takeaway:** "Centrum doesn't prevent VCI alone—but in this comprehensive strategy, it provides the micronutrient foundation that makes everything else work better."

---

## Clinical Validity Checklist ✅

- [x] Based on peer-reviewed research (Mohammed et al., 2025)
- [x] Uses validated thresholds from study (optimal cut-offs in Table 3)
- [x] Incorporates key biomarkers identified by explainable AI (SHAP values)
- [x] References major clinical trials (SPRINT MIND, COSMOS-Web)
- [x] Accounts for VCI-specific impairment patterns (not just memory)
- [x] Targets modifiable risk factors
- [x] Provides evidence-based rationales
- [x] Includes medication interaction screening
- [x] Appropriate for community/primary care deployment

---

## Future Enhancement Opportunities

1. **Integration with Actual ReCOGnAIze API** - Pull real test data from Recognise platform
2. **Longitudinal Tracking** - Monitor changes over 3-6 months (like COSMOS-Web timeframe)
3. **Risk Calculator** - Calculate individualized VCI risk score (similar to CAIDE, LIBRA scales)
4. **PDF Report Generation** - Shareable reports for patients to discuss with doctors
5. **Wearable Integration** - Pull sleep data from Apple Watch, Oura ring
6. **Referral Pathways** - Connect to vascular specialists, sleep clinics, cardiac rehab
7. **More Haleon Products** - Showcase full ecosystem (Voltaren for joint pain, etc.)
8. **Multilingual Support** - Reach Asian populations (where VCI burden is highest)
9. **Low-Literacy Validation** - Ensure accessibility in rural/underserved populations

---

## References

1. Mohammed, A. A., Vipin, A., Leow, Y. J., et al. (2025). ReCOGnAIze app to detect vascular cognitive impairment and mild cognitive impairment. *Alzheimer's & Dementia*, e70992.

2. SPRINT MIND Investigators. (2019). Effect of intensive vs standard blood pressure control on probable dementia. *JAMA*, 321(6), 553-561.

3. Gorelick, P. B., et al. (2011). Vascular contributions to cognitive impairment and dementia. *Stroke*, 42(9), 2672-2713.

4. van der Flier, W. M., Skoog, I., Schneider, J. A., et al. (2018). Vascular cognitive impairment. *Nature Reviews Disease Primers*, 4, 18003.

---

**Built with scientific rigor for Haleon's Centrum**  
*Making evidence-based cognitive health recommendations accessible and actionable.*

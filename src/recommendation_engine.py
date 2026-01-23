"""
Multi-pillar Recommendation Engine for Recognise Report Companion.
Generates holistic health recommendations across multiple pillars:
- Vascular Health
- Lifestyle
- Sleep
- Supplements/Medicines
"""

import json
import os
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Generates personalized, multi-pillar recommendations based on ReCOGnAIze Report data.
    
    Scientific Foundation:
    - ReCOGnAIze (Mohammed et al., 2025) is a gamified cognitive assessment detecting VCI with AUC=0.85
    - Key VCI biomarkers: Processing speed, response time variability, executive dysfunction
    - SPRINT MIND: Intensive BP control reduces cognitive decline progression
    - COSMOS-Web: Centrum multivitamins improve episodic memory in older adults
    """

    def __init__(self, data_dir: str = "data"):
        """
        Initialize the recommendation engine.
        
        Args:
            data_dir: Directory containing recommendation rules and knowledge
        """
        self.data_dir = data_dir
        self.vascular_rules = self._load_rules("vascular_health_rules.json")
        self.lifestyle_rules = self._load_rules("lifestyle_rules.json")
        self.sleep_rules = self._load_rules("sleep_rules.json")
        self.supplement_rules = self._load_rules("multivitamin_knowledge.json")
        
        # ReCOGnAIze task thresholds (from validation cohort)
        self.recognise_thresholds = {
            'symbol_matching': 2.5,      # Processing speed threshold
            'trail_making': 1.76,        # Executive function threshold
            'airplane_game': 2.99,       # Attention/impulse control threshold
            'grocery_shopping': 1.87     # Memory/processing speed threshold
        }

    def _load_rules(self, filename: str) -> List[Dict]:
        """Load recommendation rules from JSON file."""
        filepath = os.path.join(self.data_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else data.get('rules', [])
        except FileNotFoundError:
            logger.warning(f"Rules file not found: {filename}")
            return []
        except Exception as e:
            logger.error(f"Failed to load rules from {filename}: {e}")
            return []

    def generate_recommendations(self, recognise_report: Dict) -> Dict:
        """
        Generate comprehensive multi-pillar recommendations from a Recognise Report.
        
        Args:
            recognise_report: Dictionary containing:
                - age: int
                - gender: str ('male', 'female')
                - cognitive_scores: dict with domain scores
                - health_conditions: list
                - medications: list
                - lifestyle_factors: dict
                - vascular_risk_factors: list
                - other_variables: dict with additional data
        
        Returns:
            Dict with recommendations across all pillars
        """
        
        # Extract key metrics from report
        age = recognise_report.get('age', 35)
        gender = recognise_report.get('gender', 'unknown').lower()
        cognitive_scores = recognise_report.get('cognitive_scores', {})
        health_conditions = recognise_report.get('health_conditions', [])
        vascular_risks = recognise_report.get('vascular_risk_factors', [])
        medications = recognise_report.get('medications', [])
        lifestyle = recognise_report.get('lifestyle_factors', {})
        
        # Analyze cognitive impairments
        impairments = self._analyze_cognitive_impairments(cognitive_scores)
        
        # Generate recommendations for each pillar
        recommendations = {
            'report_summary': {
                'age': age,
                'gender': gender,
                'key_impairments': impairments,
                'vascular_risk_level': self._assess_vascular_risk(vascular_risks),
                'cognitive_risk_level': self._assess_cognitive_risk(cognitive_scores)
            },
            'pillars': {
                'vascular_health': self._generate_vascular_recommendations(
                    age, gender, vascular_risks, impairments, health_conditions
                ),
                'lifestyle': self._generate_lifestyle_recommendations(
                    age, impairments, lifestyle, health_conditions
                ),
                'sleep': self._generate_sleep_recommendations(
                    age, impairments, lifestyle.get('sleep_quality', 'unknown'),
                    vascular_risks
                ),
                'supplements': self._generate_supplement_recommendations(
                    age, gender, vascular_risks, impairments, medications, health_conditions
                )
            }
        }
        
        return recommendations

    def _analyze_cognitive_impairments(self, cognitive_scores: Dict) -> List[Dict]:
        """
        Analyze cognitive test scores to identify impairments.
        
        Returns list of impaired domains with severity.
        """
        impairments = []
        
        # Define normal ranges (can be adjusted based on age norms)
        thresholds = {
            'memory': 70,
            'processing_speed': 70,
            'executive_function': 70,
            'attention': 70,
            'verbal_fluency': 70,
            'visuospatial': 70
        }
        
        for domain, score in cognitive_scores.items():
            threshold = thresholds.get(domain, 70)
            if score < threshold:
                severity = self._score_to_severity(score, threshold)
                impairments.append({
                    'domain': domain,
                    'score': score,
                    'threshold': threshold,
                    'severity': severity  # 'mild', 'moderate', 'severe'
                })
        
        return sorted(impairments, key=lambda x: x['score'])

    def _score_to_severity(self, score: float, threshold: float) -> str:
        """Convert score to severity level."""
        gap = threshold - score
        if gap <= 5:
            return 'mild'
        elif gap <= 15:
            return 'moderate'
        else:
            return 'severe'

    def _assess_vascular_risk(self, vascular_risks: List[str]) -> str:
        """
        Assess overall vascular risk level based on SPRINT MIND study criteria.
        
        High risk factors (from ReCOGnAIze study):
        - Hypertension (HTN) - most common in VCI group (37.3%)
        - High cholesterol/Hyperlipidemia (HLD) - significantly more in VCI (60% vs 35%)
        - Diabetes mellitus (DM) - present in 22.7% of VCI group
        
        Reference: Mohammed et al., 2025 - ReCOGnAIze validation cohort
        """
        if not vascular_risks:
            return 'low'
        
        # High-risk factors based on ReCOGnAIze study prevalence in VCI group
        major_risk_factors = {
            'hypertension', 'high_blood_pressure',      # 37.3% in VCI
            'high_cholesterol', 'hyperlipidemia',       # 60% in VCI
            'diabetes', 'diabetes_mellitus'              # 22.7% in VCI
        }
        
        # Additional high-risk factors
        additional_risk_factors = {
            'smoking', 'obesity', 'atrial_fibrillation', 'previous_stroke'
        }
        
        major_count = sum(1 for r in vascular_risks if r.lower() in major_risk_factors)
        additional_count = sum(1 for r in vascular_risks if r.lower() in additional_risk_factors)
        
        total_risk_score = (major_count * 2) + additional_count
        
        if total_risk_score >= 4:
            return 'high'
        elif total_risk_score >= 2:
            return 'moderate'
        else:
            return 'low'

    def _assess_cognitive_risk(self, cognitive_scores: Dict) -> str:
        """Assess overall cognitive risk level."""
        if not cognitive_scores:
            return 'unknown'
        
        avg_score = sum(cognitive_scores.values()) / len(cognitive_scores)
        
        if avg_score < 50:
            return 'high'
        elif avg_score < 70:
            return 'moderate'
        else:
            return 'low'

    def _generate_vascular_recommendations(
        self, age: int, gender: str, vascular_risks: List[str],
        impairments: List[Dict], health_conditions: List[str]
    ) -> Dict:
        """
        Generate vascular health recommendations based on SPRINT MIND and ReCOGnAIze findings.
        
        Key Evidence:
        - SPRINT MIND: Intensive BP control (target <120 mmHg) reduced cognitive decline
        - ReCOGnAIze: Processing speed and response time variability are VCI markers
        - VCI accounts for 50-70% of dementia cases (often underdiagnosed)
        """
        return {
            'title': 'Vascular Health',
            'description': 'Protecting heart and brain blood vessel health - crucial for preventing cognitive decline',
            'vci_context': (
                'Vascular Cognitive Impairment (VCI) accounts for 50-70% of dementia cases but is often '
                'underdiagnosed. Your risk profile suggests VCI should be a focus. The SPRINT MIND trial showed '
                'that intensive blood pressure control significantly reduced cognitive decline progression.'
            ),
            'recommendations': [
                {
                    'category': 'Blood Pressure Management',
                    'priority': 'high' if 'hypertension' in vascular_risks else 'high',
                    'target': 'Target <120 mmHg systolic (SPRINT MIND standard)',
                    'actions': [
                        'Monitor blood pressure regularly at home',
                        'Target systolic BP <120 mmHg (SPRINT MIND recommendation)',
                        'Work with your doctor on medication optimization',
                        'Reduce sodium intake to <2,300mg daily (ideally <1,500mg)',
                        'Consider DASH diet (rich in fruits, vegetables, whole grains, lean protein)'
                    ],
                    'evidence': (
                        'SPRINT MIND Trial: Intensive BP control reduced progression of cognitive impairment. '
                        'In ReCOGnAIze study, 37.3% of VCI patients had hypertension vs 26.6% without VCI.'
                    )
                },
                {
                    'category': 'Cholesterol Management',
                    'priority': 'high' if 'high_cholesterol' in vascular_risks else 'high',
                    'actions': [
                        'Get lipid panel checked (target LDL <70 mg/dL if vascular disease present)',
                        'Increase soluble fiber intake (oats, beans, citrus)',
                        'Choose lean proteins and healthy fats (olive oil, nuts, fish)',
                        'Limit saturated fat intake to <7% of daily calories',
                        'Discuss statin therapy with your physician if not already on one'
                    ],
                    'evidence': (
                        'High cholesterol is a major modifiable risk factor for VCI. '
                        'ReCOGnAIze study: 60% of VCI group had hyperlipidemia vs only 35% without VCI - '
                        'nearly 2x higher prevalence.'
                    )
                },
                {
                    'category': 'Diabetes Management',
                    'priority': 'high' if 'diabetes' in vascular_risks else 'medium',
                    'actions': [
                        'Target HbA1c <7% (goal varies by individual)',
                        'Monitor blood glucose regularly',
                        'Maintain consistent meal timing and composition',
                        'Increase physical activity gradually',
                        'Work with endocrinologist for medication optimization'
                    ],
                    'evidence': 'Diabetes significantly accelerates vascular cognitive decline through multiple mechanisms.'
                },
                {
                    'category': 'Physical Activity',
                    'priority': 'high',
                    'actions': [
                        'Aim for 150 minutes of moderate aerobic activity weekly',
                        'Include strength training 2-3 times per week',
                        'Start slowly and increase gradually (especially if sedentary)',
                        'Walking, swimming, cycling, and brisk walking are excellent options',
                        'Even light activity reduces risk - aim for movement throughout the day'
                    ],
                    'evidence': 'Regular aerobic exercise improves cerebral blood flow and vascular endothelial function.'
                }
            ],
            'risk_level': self._assess_vascular_risk(vascular_risks)
        }

    def _generate_lifestyle_recommendations(
        self, age: int, impairments: List[Dict],
        lifestyle: Dict, health_conditions: List[str]
    ) -> Dict:
        """Generate lifestyle recommendations."""
        return {
            'title': 'Lifestyle Modifications',
            'description': 'Daily habits that support cognitive health',
            'recommendations': [
                {
                    'category': 'Cognitive Training',
                    'priority': 'high' if impairments else 'medium',
                    'actions': [
                        'Engage in mentally stimulating activities daily',
                        'Try puzzles, learning new skills, reading, or games',
                        'Practice focused attention exercises',
                        'Stay socially engaged with friends and family'
                    ],
                    'evidence': 'Cognitive engagement strengthens neural connections and builds reserve'
                },
                {
                    'category': 'Diet & Nutrition',
                    'priority': 'high',
                    'actions': [
                        'Follow a Mediterranean or MIND diet',
                        'Increase antioxidant-rich foods (berries, leafy greens)',
                        'Include omega-3 sources (fatty fish, flaxseed)',
                        'Limit processed foods and added sugars',
                        'Stay well hydrated throughout the day'
                    ],
                    'evidence': 'Dietary patterns rich in antioxidants support brain health and reduce inflammation'
                },
                {
                    'category': 'Stress Management',
                    'priority': 'high',
                    'actions': [
                        'Practice meditation or mindfulness (10-15 minutes daily)',
                        'Try yoga or tai chi for mind-body benefits',
                        'Use deep breathing techniques when stressed',
                        'Maintain regular daily routines'
                    ],
                    'evidence': 'Chronic stress impairs cognitive function and vascular health'
                },
                {
                    'category': 'Avoid Harmful Substances',
                    'priority': 'high',
                    'actions': [
                        'Quit smoking if applicable (major vascular benefit)',
                        'Limit alcohol to moderate levels (≤1 drink/day for women, ≤2 for men)',
                        'Avoid recreational drugs',
                        'Use medications only as prescribed'
                    ],
                    'evidence': 'Smoking and excessive alcohol significantly increase cognitive and vascular decline risk'
                }
            ]
        }

    def _generate_sleep_recommendations(
        self, age: int, impairments: List[Dict],
        sleep_quality: str, vascular_risks: List[str]
    ) -> Dict:
        """Generate sleep recommendations."""
        return {
            'title': 'Sleep Optimization',
            'description': 'Quality sleep is essential for brain health and memory consolidation',
            'recommendations': [
                {
                    'category': 'Sleep Duration & Schedule',
                    'priority': 'high',
                    'actions': [
                        'Aim for 7-9 hours of sleep nightly',
                        'Maintain consistent sleep/wake times (even weekends)',
                        'Create a dark, cool, quiet sleep environment',
                        'Avoid screens 1 hour before bedtime'
                    ],
                    'evidence': 'Adequate sleep is crucial for memory consolidation and metabolic waste clearance (glymphatic system)'
                },
                {
                    'category': 'Sleep Hygiene',
                    'priority': 'high',
                    'actions': [
                        'Limit caffeine after 2 PM',
                        'Avoid heavy meals 3 hours before sleep',
                        'Exercise earlier in the day, not close to bedtime',
                        'Keep bedroom temperature around 65-68°F (18-20°C)',
                        'Use white noise if external sounds disturb sleep'
                    ],
                    'evidence': 'Good sleep hygiene practices significantly improve sleep quality and duration'
                },
                {
                    'category': 'Sleep Disorders Screening',
                    'priority': 'high' if vascular_risks else 'medium',
                    'actions': [
                        'Consult doctor if experiencing loud snoring or breathing pauses',
                        'Get evaluated for sleep apnea if at risk',
                        'Discuss insomnia patterns with healthcare provider',
                        'Untreated sleep apnea significantly increases vascular and cognitive risks'
                    ],
                    'evidence': 'Sleep apnea is a major modifiable risk factor for cognitive decline'
                }
            ]
        }

    def _generate_supplement_recommendations(
        self, age: int, gender: str, vascular_risks: List[str],
        impairments: List[Dict], medications: List[str], health_conditions: List[str]
    ) -> Dict:
        """
        Generate supplement and medicine recommendations based on ReCOGnAIze and COSMOS-Web evidence.
        
        Key Evidence:
        - COSMOS-Web Trial: Centrum multivitamin improved episodic memory in older adults over 3 years
        - ReCOGnAIze: Identified processing speed and response time variability as key VCI markers
        - Omega-3 supports processing speed; B vitamins reduce homocysteine (vascular risk)
        """
        
        products = self._find_matching_supplements(
            age, gender, vascular_risks, impairments, health_conditions
        )
        
        return {
            'title': 'Supplements & Medicines',
            'description': 'Evidence-based supplement recommendations to complement lifestyle modifications',
            'featured_brands': {
                'centrum': {
                    'brand': 'Centrum',
                    'parent_company': 'Haleon',
                    'positioning': (
                        'Complete daily multivitamin foundation supporting vascular health, cognitive function, and bone health. '
                        'COSMOS-Web trial: Centrum-treated older adults had better episodic memory at 3 years vs placebo.'
                    ),
                    'products': products,
                    'cosmos_web_evidence': (
                        'In the COSMOS-Web randomized controlled trial, older adults taking Centrum Silver multivitamin '
                        'demonstrated better episodic memory performance compared to placebo over 3 years of follow-up. '
                        'This aligns with ReCOGnAIze findings showing memory and processing speed impairment in VCI.'
                    )
                }
            },
            'supplemental_options': [
                {
                    'supplement': 'Omega-3 Fatty Acids (Fish Oil)',
                    'recommended': 'processing_speed' in [i['domain'] for i in impairments] or 'symbol_matching' in str(impairments),
                    'dosage': '1,000-2,000 mg EPA+DHA daily',
                    'evidence': (
                        'Supports processing speed (key ReCOGnAIze biomarker for VCI). '
                        'Reduces cerebral inflammation and improves vascular endothelial function.'
                    ),
                    'safety_notes': 'May interact with blood thinners; consult doctor if on anticoagulants. Fish oil may cause fish aftertaste.'
                },
                {
                    'supplement': 'Vitamin B Complex (B6, B12, Folate)',
                    'recommended': True,
                    'dosage': 'B12: 1,000 mcg daily or 2,000 mcg weekly; Folate: 400-1,000 mcg daily',
                    'evidence': (
                        'Reduces homocysteine, a major vascular risk factor. Essential for methylation and myelin integrity. '
                        'Supports both cognitive function and vascular health in high-risk populations.'
                    ),
                    'safety_notes': 'Generally well-tolerated. May cause sensory changes at very high B6 doses (>200mg daily).'
                },
                {
                    'supplement': 'Vitamin D3',
                    'recommended': True,
                    'dosage': '1,000-4,000 IU daily (consider getting 25-OH vitamin D level tested)',
                    'evidence': (
                        'Supports bone health, vascular function, mood regulation, and immune system. '
                        'Deficiency linked to increased VCI risk and cognitive impairment.'
                    ),
                    'safety_notes': 'Fat-soluble; take with meals. Excessive supplementation (>10,000 IU long-term) may cause toxicity.'
                },
                {
                    'supplement': 'Magnesium',
                    'recommended': 'sleep' in str(impairments).lower() or 'fair' in str(health_conditions).lower(),
                    'dosage': '200-400 mg daily (can split AM/PM)',
                    'evidence': (
                        'Supports sleep quality, muscle function, vascular relaxation (helps blood pressure control), '
                        'and supports synaptic plasticity for learning and memory.'
                    ),
                    'safety_notes': 'May cause loose stools at high doses; start with 200mg and increase gradually.'
                },
                {
                    'supplement': 'Coenzyme Q10 (CoQ10)',
                    'recommended': 'high_cholesterol' in vascular_risks or any('statin' in med.lower() for med in medications),
                    'dosage': '100-300 mg daily with food',
                    'evidence': (
                        'Supports mitochondrial energy production, vascular endothelial function, and works synergistically with statins. '
                        'May help with statin-related muscle symptoms.'
                    ),
                    'safety_notes': 'Fat-soluble; best taken with fat-containing meals. May interact with warfarin.'
                }
            ],
            'why_centrum_matters': (
                'Centrum provides a comprehensive micronutrient foundation that modern diets often lack, especially in older adults. '
                'The COSMOS-Web trial demonstrated that Centrum improves episodic memory—a domain often affected in VCI. '
                'Combined with the vascular health, lifestyle, and sleep optimization in other pillars, Centrum addresses nutritional '
                'gaps efficiently. Rather than suggesting one "magic supplement," this companion shows how Centrum fits into a '
                'comprehensive VCI prevention strategy. This is evidence-based, scalable, and demonstrable to patients.'
            ),
            'medication_interactions': self._check_interactions(medications),
            'recommendation_tier': self._determine_supplement_tier(vascular_risks, impairments)
        }

    def _find_matching_supplements(
        self, age: int, gender: str, vascular_risks: List[str],
        impairments: List[Dict], health_conditions: List[str]
    ) -> List[Dict]:
        """Find matching Centrum products from knowledge base."""
        
        products = []
        
        # Search through supplement rules (Centrum recommendations)
        for rule in self.supplement_rules:
            if isinstance(rule, dict):
                applicable_if = rule.get('applicable_if', {})
                
                # Check age
                if 'min_age' in applicable_if:
                    if age < applicable_if['min_age']:
                        continue
                if 'max_age' in applicable_if:
                    if age > applicable_if['max_age']:
                        continue
                
                # Check sex
                if 'sex' in applicable_if:
                    if gender and gender != applicable_if['sex']:
                        continue
                
                # Check vascular risk factors
                vascular_any_of = applicable_if.get('vascular_risk_factors_any_of', [])
                if vascular_any_of:
                    if not any(risk in vascular_risks for risk in vascular_any_of):
                        continue
                
                # Check cognitive concerns
                cognitive_any_of = applicable_if.get('cognitive_concern_any_of', [])
                impairment_domains = [i['domain'] for i in impairments]
                if cognitive_any_of:
                    if not any(concern in impairment_domains for concern in cognitive_any_of):
                        continue
                
                # Add matching products
                recommended_products = rule.get('recommended_products', [])
                if recommended_products:
                    for product in recommended_products:
                        products.append({
                            'product_name': product.get('display_name', ''),
                            'product_key': product.get('product_key', ''),
                            'priority': product.get('priority', 'secondary'),
                            'rationale': product.get('rationale', ''),
                            'dosage': product.get('dosage', ''),
                            'when_to_take': product.get('when_to_take', ''),
                            'evidence': product.get('evidence_note', ''),
                            'ingredients': product.get('ingredients', '')
                        })
        
        return products[:3]  # Return top 3 recommendations

    def _check_interactions(self, medications: List[str]) -> List[Dict]:
        """Check for potential supplement-medication interactions."""
        
        interactions = []
        common_interactions = {
            'warfarin': ['vitamin_k', 'omega_3', 'vitamin_e'],
            'aspirin': ['omega_3', 'vitamin_e'],
            'metformin': ['vitamin_b12', 'folate'],
            'statins': ['coq10', 'niacin'],
            'ssri': ['magnesium', 'omega_3']
        }
        
        for med in medications:
            med_lower = med.lower()
            if any(drug in med_lower for drug in common_interactions):
                interactions.append({
                    'medication': med,
                    'note': f'Potential interactions with some supplements. Consult your pharmacist before adding new supplements.'
                })
        
        return interactions

    def _determine_supplement_tier(self, vascular_risks: List[str], impairments: List[Dict]) -> str:
        """Determine priority level for supplements."""
        
        risk_level = self._assess_vascular_risk(vascular_risks)
        impairment_count = len(impairments)
        
        if risk_level == 'high' or impairment_count >= 3:
            return 'priority'
        elif risk_level == 'moderate' or impairment_count >= 1:
            return 'recommended'
        else:
            return 'optional'


def main():
    """Test the recommendation engine."""
    
    # Create sample Recognise report
    sample_report = {
        'age': 58,
        'gender': 'female',
        'cognitive_scores': {
            'memory': 78,
            'processing_speed': 65,
            'executive_function': 72,
            'attention': 74,
            'verbal_fluency': 80,
            'visuospatial': 70
        },
        'vascular_risk_factors': ['high_blood_pressure', 'high_cholesterol'],
        'health_conditions': ['hypertension'],
        'medications': ['lisinopril'],
        'lifestyle_factors': {
            'exercise_level': 'moderate',
            'diet_quality': 'good',
            'sleep_quality': 'fair'
        }
    }
    
    # Generate recommendations
    engine = RecommendationEngine()
    recommendations = engine.generate_recommendations(sample_report)
    
    # Display results
    print(json.dumps(recommendations, indent=2))


if __name__ == '__main__':
    main()

import json
import os
from typing import Dict, List, Optional, Tuple
import numpy as np
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CognitiveTestAnalyzer:
    """Analyzer for gamified cognitive test results."""
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize the cognitive test analyzer.
        
        Args:
            data_dir: Directory containing cognitive mapping data
        """
        self.data_dir = data_dir
        self.cognitive_mapping = self._load_cognitive_mapping()
        
        # Define cognitive domain thresholds and scoring
        self.domain_thresholds = {
            'memory': {
                'severe': 40,
                'moderate': 60,
                'mild': 75,
                'normal': 85
            },
            'attention': {
                'severe': 35,
                'moderate': 55,
                'mild': 70,
                'normal': 80
            },
            'processing_speed': {
                'severe': 45,
                'moderate': 65,
                'mild': 78,
                'normal': 88
            },
            'executive_function': {
                'severe': 40,
                'moderate': 60,
                'mild': 73,
                'normal': 85
            }
        }
    
    def _load_cognitive_mapping(self) -> Dict:
        """Load cognitive domain mapping data."""
        mapping_path = os.path.join(self.data_dir, "cognitive_mapping.json")
        try:
            with open(mapping_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load cognitive mapping: {e}")
            return {}
    
    def analyze_test_results(self, test_data: Dict) -> Dict:
        """
        Comprehensive analysis of cognitive test results.
        
        Args:
            test_data: Raw test results dictionary
            
        Returns:
            Detailed analysis results
        """
        scores = test_data.get('scores', {})
        age = test_data.get('age', 35)
        gender = test_data.get('gender', 'unknown')
        test_date = test_data.get('test_date', datetime.now().isoformat())
        
        # Perform domain-by-domain analysis
        domain_analyses = {}
        overall_impairment_level = 'normal'
        impaired_domains = []
        
        for domain, score in scores.items():
            domain_analysis = self._analyze_domain(domain, score, age, gender)
            domain_analyses[domain] = domain_analysis
            
            if domain_analysis['impairment_level'] != 'normal':
                impaired_domains.append(domain)
                
                # Update overall impairment level
                if domain_analysis['impairment_level'] == 'severe':
                    overall_impairment_level = 'severe'
                elif domain_analysis['impairment_level'] == 'moderate' and overall_impairment_level != 'severe':
                    overall_impairment_level = 'moderate'
                elif domain_analysis['impairment_level'] == 'mild' and overall_impairment_level == 'normal':
                    overall_impairment_level = 'mild'
        
        # Calculate composite scores
        composite_scores = self._calculate_composite_scores(scores)
        
        # Generate risk assessment
        risk_assessment = self._assess_cognitive_risk(domain_analyses, age, gender)
        
        # Create recommendations summary
        recommendations_summary = self._create_recommendations_summary(domain_analyses, impaired_domains)
        
        # Generate detailed analysis report
        analysis_report = {
            'test_info': {
                'test_date': test_date,
                'test_type': test_data.get('test_type', 'gamified_cognitive'),
                'age': age,
                'gender': gender
            },
            'raw_scores': scores,
            'composite_scores': composite_scores,
            'domain_analyses': domain_analyses,
            'overall_assessment': {
                'impairment_level': overall_impairment_level,
                'impaired_domains': impaired_domains,
                'number_of_impaired_domains': len(impaired_domains),
                'cognitive_age_estimate': self._estimate_cognitive_age(scores, age)
            },
            'risk_assessment': risk_assessment,
            'recommendations_summary': recommendations_summary,
            'follow_up_suggestions': self._generate_follow_up_suggestions(overall_impairment_level, impaired_domains),
            'lifestyle_factors': self._analyze_lifestyle_factors(test_data),
            'confidence_score': self._calculate_confidence_score(scores, test_data)
        }
        
        return analysis_report
    
    def _analyze_domain(self, domain: str, score: float, age: int, gender: str) -> Dict:
        """Analyze a specific cognitive domain."""
        thresholds = self.domain_thresholds.get(domain, self.domain_thresholds['memory'])
        
        # Determine impairment level
        if score >= thresholds['normal']:
            impairment_level = 'normal'
        elif score >= thresholds['mild']:
            impairment_level = 'mild'
        elif score >= thresholds['moderate']:
            impairment_level = 'moderate'
        else:
            impairment_level = 'severe'
        
        # Apply age adjustments
        age_adjusted_score = self._apply_age_adjustment(score, age, domain)
        
        # Get domain-specific information
        domain_info = {}
        if isinstance(self.cognitive_mapping, list):
            # Find the domain in the list of cognitive domain objects
            for item in self.cognitive_mapping:
                if item.get('domain') == domain:
                    domain_info = item
                    break
        else:
            # Fallback to original dictionary structure
            domain_info = self.cognitive_mapping.get('cognitive_domains', {}).get(domain, {})
        
        return {
            'raw_score': score,
            'age_adjusted_score': age_adjusted_score,
            'impairment_level': impairment_level,
            'percentile': self._score_to_percentile(score, domain),
            'description': domain_info.get('definition', ''),
            'impairment_indicators': domain_info.get('common_impairment_signs', []),
            'severity_description': self._get_severity_description(impairment_level, domain),
            'improvement_potential': self._assess_improvement_potential(score, age, impairment_level),
            'priority_level': self._determine_priority_level(impairment_level, domain)
        }
    
    def _apply_age_adjustment(self, score: float, age: int, domain: str) -> float:
        """Apply age-based adjustments to cognitive scores."""
        # Age adjustment factors (scores naturally decline with age)
        if age < 30:
            adjustment = 0
        elif age < 40:
            adjustment = 2
        elif age < 50:
            adjustment = 4
        elif age < 60:
            adjustment = 7
        elif age < 70:
            adjustment = 10
        else:
            adjustment = 15
        
        # Domain-specific adjustments
        domain_multipliers = {
            'processing_speed': 1.5,  # Most affected by age
            'memory': 1.2,
            'executive_function': 1.1,
            'attention': 1.0
        }
        
        multiplier = domain_multipliers.get(domain, 1.0)
        adjusted_score = score + (adjustment * multiplier)
        
        return min(adjusted_score, 100)  # Cap at 100
    
    def _score_to_percentile(self, score: float, domain: str) -> float:
        """Convert raw score to percentile ranking."""
        # Simplified percentile conversion (in reality, this would use normative data)
        if score >= 90:
            return 95
        elif score >= 85:
            return 84
        elif score >= 80:
            return 70
        elif score >= 75:
            return 55
        elif score >= 70:
            return 40
        elif score >= 65:
            return 25
        elif score >= 60:
            return 15
        elif score >= 50:
            return 8
        else:
            return 3
    
    def _calculate_composite_scores(self, scores: Dict) -> Dict:
        """Calculate composite cognitive scores."""
        if not scores:
            return {}
        
        composite = {}
        
        # Global Cognitive Index
        composite['global_cognitive_index'] = np.mean(list(scores.values()))
        
        # Attention-Executive Index
        attention_exec_domains = ['attention', 'executive_function']
        attention_exec_scores = [scores.get(domain, 0) for domain in attention_exec_domains if domain in scores]
        if attention_exec_scores:
            composite['attention_executive_index'] = np.mean(attention_exec_scores)
        
        # Memory-Learning Index
        memory_domains = ['memory']
        memory_scores = [scores.get(domain, 0) for domain in memory_domains if domain in scores]
        if memory_scores:
            composite['memory_learning_index'] = np.mean(memory_scores)
        
        # Processing Speed Index
        if 'processing_speed' in scores:
            composite['processing_speed_index'] = scores['processing_speed']
        
        return composite
    
    def _assess_cognitive_risk(self, domain_analyses: Dict, age: int, gender: str) -> Dict:
        """Assess overall cognitive risk factors."""
        risk_factors = []
        risk_level = 'low'
        
        # Count severe and moderate impairments
        severe_count = sum(1 for analysis in domain_analyses.values() 
                          if analysis['impairment_level'] == 'severe')
        moderate_count = sum(1 for analysis in domain_analyses.values() 
                            if analysis['impairment_level'] == 'moderate')
        
        if severe_count >= 2:
            risk_level = 'high'
            risk_factors.append('Multiple severe cognitive impairments detected')
        elif severe_count >= 1:
            risk_level = 'moderate'
            risk_factors.append('Severe impairment in at least one domain')
        elif moderate_count >= 3:
            risk_level = 'moderate'
            risk_factors.append('Multiple moderate cognitive impairments')
        elif moderate_count >= 1:
            risk_level = 'mild'
            risk_factors.append('Moderate impairment detected')
        
        # Age-related risk factors
        if age >= 65:
            risk_factors.append('Age-related cognitive decline risk')
            if risk_level == 'low':
                risk_level = 'mild'
        
        # Processing speed as early indicator
        if 'processing_speed' in domain_analyses:
            ps_analysis = domain_analyses['processing_speed']
            if ps_analysis['impairment_level'] in ['moderate', 'severe']:
                risk_factors.append('Processing speed decline (early marker)')
        
        return {
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'recommendations': self._generate_risk_recommendations(risk_level),
            'monitoring_frequency': self._determine_monitoring_frequency(risk_level)
        }
    
    def _create_recommendations_summary(self, domain_analyses: Dict, impaired_domains: List[str]) -> Dict:
        """Create summary of recommendations based on analysis."""
        summary = {
            'immediate_priorities': [],
            'secondary_priorities': [],
            'preventive_measures': [],
            'intervention_type': 'none'
        }
        
        if not impaired_domains:
            summary['intervention_type'] = 'preventive'
            summary['preventive_measures'] = [
                'Maintain healthy lifestyle',
                'Consider baseline nutritional support',
                'Regular cognitive stimulation'
            ]
            return summary
        
        # Categorize by priority
        high_priority_domains = []
        medium_priority_domains = []
        
        for domain in impaired_domains:
            domain_analysis = domain_analyses[domain]
            if domain_analysis['priority_level'] == 'high':
                high_priority_domains.append(domain)
            else:
                medium_priority_domains.append(domain)
        
        # Set intervention type
        if high_priority_domains:
            summary['intervention_type'] = 'therapeutic'
        else:
            summary['intervention_type'] = 'supportive'
        
        # Create specific recommendations
        summary['immediate_priorities'] = [
            f"Address {domain.replace('_', ' ')} impairment" for domain in high_priority_domains
        ]
        
        summary['secondary_priorities'] = [
            f"Support {domain.replace('_', ' ')} function" for domain in medium_priority_domains
        ]
        
        return summary
    
    def _get_severity_description(self, impairment_level: str, domain: str) -> str:
        """Get human-readable severity description."""
        descriptions = {
            'normal': f"{domain.replace('_', ' ').title()} function is within normal range",
            'mild': f"Mild {domain.replace('_', ' ')} difficulties that may benefit from support",
            'moderate': f"Moderate {domain.replace('_', ' ')} impairment requiring intervention",
            'severe': f"Severe {domain.replace('_', ' ')} impairment requiring immediate attention"
        }
        
        return descriptions.get(impairment_level, f"{impairment_level.title()} impairment in {domain}")
    
    def _assess_improvement_potential(self, score: float, age: int, impairment_level: str) -> str:
        """Assess potential for cognitive improvement."""
        if impairment_level == 'normal':
            return 'Maintenance focus'
        
        if age < 50:
            if impairment_level == 'mild':
                return 'High improvement potential'
            elif impairment_level == 'moderate':
                return 'Good improvement potential'
            else:
                return 'Moderate improvement potential'
        elif age < 70:
            if impairment_level == 'mild':
                return 'Good improvement potential'
            else:
                return 'Moderate improvement potential'
        else:
            return 'Focus on slowing decline'
    
    def _determine_priority_level(self, impairment_level: str, domain: str) -> str:
        """Determine priority level for intervention."""
        if impairment_level in ['severe', 'moderate']:
            return 'high'
        elif impairment_level == 'mild':
            # Executive function and memory get higher priority
            if domain in ['executive_function', 'memory']:
                return 'high'
            else:
                return 'medium'
        else:
            return 'low'
    
    def _estimate_cognitive_age(self, scores: Dict, chronological_age: int) -> int:
        """Estimate cognitive age based on performance."""
        if not scores:
            return chronological_age
        
        avg_score = np.mean(list(scores.values()))
        
        # Rough estimation (in reality, this would use normative data)
        if avg_score >= 90:
            cognitive_age = chronological_age - 10
        elif avg_score >= 80:
            cognitive_age = chronological_age - 5
        elif avg_score >= 70:
            cognitive_age = chronological_age
        elif avg_score >= 60:
            cognitive_age = chronological_age + 10
        elif avg_score >= 50:
            cognitive_age = chronological_age + 20
        else:
            cognitive_age = chronological_age + 30
        
        return max(cognitive_age, 20)  # Minimum cognitive age
    
    def _generate_follow_up_suggestions(self, overall_level: str, impaired_domains: List[str]) -> List[str]:
        """Generate follow-up testing suggestions."""
        suggestions = []
        
        if overall_level == 'severe':
            suggestions.extend([
                'Comprehensive neuropsychological evaluation recommended',
                'Medical evaluation to rule out underlying causes',
                'Retest in 3 months to monitor progression',
                'Consider consultation with cognitive specialist'
            ])
        elif overall_level == 'moderate':
            suggestions.extend([
                'Detailed cognitive assessment recommended',
                'Retest in 3-6 months to monitor changes',
                'Consider lifestyle intervention program',
                'Medical screening for treatable causes'
            ])
        elif overall_level == 'mild':
            suggestions.extend([
                'Retest in 6 months to monitor stability',
                'Focus on lifestyle and nutritional interventions',
                'Cognitive training program may be beneficial'
            ])
        else:
            suggestions.extend([
                'Annual cognitive screening recommended',
                'Maintain healthy lifestyle practices',
                'Continue preventive measures'
            ])
        
        return suggestions
    
    def _analyze_lifestyle_factors(self, test_data: Dict) -> Dict:
        """Analyze lifestyle factors that may impact cognitive function."""
        factors = test_data.get('lifestyle_factors', {})
        
        analysis = {
            'sleep_quality': factors.get('sleep_hours', 7),
            'exercise_frequency': factors.get('exercise_frequency', 'unknown'),
            'stress_level': factors.get('stress_level', 'moderate'),
            'diet_quality': factors.get('diet_quality', 'average'),
            'social_engagement': factors.get('social_engagement', 'moderate'),
            'recommendations': []
        }
        
        # Generate lifestyle recommendations
        if analysis['sleep_quality'] < 7:
            analysis['recommendations'].append('Improve sleep hygiene - aim for 7-9 hours nightly')
        
        if analysis['exercise_frequency'] in ['rare', 'never', 'unknown']:
            analysis['recommendations'].append('Increase physical activity - aim for 150 minutes weekly')
        
        if analysis['stress_level'] == 'high':
            analysis['recommendations'].append('Implement stress management techniques')
        
        return analysis
    
    def _calculate_confidence_score(self, scores: Dict, test_data: Dict) -> float:
        """Calculate confidence in the test results."""
        confidence_factors = []
        
        # Score consistency
        if scores:
            score_std = np.std(list(scores.values()))
            if score_std < 15:  # Consistent scores
                confidence_factors.append(0.9)
            else:
                confidence_factors.append(0.7)
        
        # Test completion
        expected_domains = ['memory', 'attention', 'processing_speed', 'executive_function']
        completed_domains = len([d for d in expected_domains if d in scores])
        completion_rate = completed_domains / len(expected_domains)
        confidence_factors.append(completion_rate)
        
        # Test conditions
        test_conditions = test_data.get('test_conditions', {})
        if test_conditions.get('distractions', 'low') == 'low':
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.7)
        
        return np.mean(confidence_factors) if confidence_factors else 0.5
    
    def _generate_risk_recommendations(self, risk_level: str) -> List[str]:
        """Generate recommendations based on risk level."""
        recommendations = {
            'low': [
                'Continue healthy lifestyle practices',
                'Annual cognitive monitoring'
            ],
            'mild': [
                'Implement cognitive health program',
                'Consider nutritional support',
                'Semi-annual cognitive assessment'
            ],
            'moderate': [
                'Comprehensive cognitive intervention',
                'Medical evaluation recommended',
                'Quarterly cognitive monitoring',
                'Lifestyle modification program'
            ],
            'high': [
                'Immediate medical evaluation',
                'Intensive cognitive intervention',
                'Monthly monitoring initially',
                'Comprehensive health assessment'
            ]
        }
        
        return recommendations.get(risk_level, recommendations['mild'])
    
    def _determine_monitoring_frequency(self, risk_level: str) -> str:
        """Determine appropriate monitoring frequency."""
        frequencies = {
            'low': 'annually',
            'mild': 'every 6 months',
            'moderate': 'every 3 months',
            'high': 'monthly initially, then quarterly'
        }
        
        return frequencies.get(risk_level, 'every 6 months')
    
    def generate_summary_report(self, analysis: Dict) -> str:
        """Generate a human-readable summary report."""
        overall = analysis['overall_assessment']
        risk = analysis['risk_assessment']
        
        report_parts = []
        
        # Header
        report_parts.append("=== COGNITIVE ASSESSMENT SUMMARY ===")
        report_parts.append(f"Date: {analysis['test_info']['test_date']}")
        report_parts.append(f"Age: {analysis['test_info']['age']}, Gender: {analysis['test_info']['gender']}")
        
        # Overall assessment
        report_parts.append(f"\nOVERALL COGNITIVE STATUS: {overall['impairment_level'].upper()}")
        if overall['impaired_domains']:
            report_parts.append(f"Impaired domains: {', '.join(overall['impaired_domains']).replace('_', ' ')}")
        
        report_parts.append(f"Cognitive age estimate: {overall['cognitive_age_estimate']}")
        
        # Risk assessment
        report_parts.append(f"\nRISK LEVEL: {risk['risk_level'].upper()}")
        if risk['risk_factors']:
            report_parts.append("Risk factors:")
            for factor in risk['risk_factors']:
                report_parts.append(f"  • {factor}")
        
        # Domain details
        report_parts.append(f"\nDOMAIN ANALYSIS:")
        for domain, analysis_data in analysis['domain_analyses'].items():
            report_parts.append(f"{domain.replace('_', ' ').title()}: {analysis_data['raw_score']:.1f} "
                              f"({analysis_data['impairment_level']})")
        
        # Recommendations
        rec_summary = analysis['recommendations_summary']
        if rec_summary['immediate_priorities']:
            report_parts.append(f"\nIMMEDIATE PRIORITIES:")
            for priority in rec_summary['immediate_priorities']:
                report_parts.append(f"  • {priority}")
        
        return '\n'.join(report_parts)

if __name__ == "__main__":
    # Test the analyzer
    analyzer = CognitiveTestAnalyzer()
    
    # Sample test data
    test_data = {
        "test_type": "gamified_cognitive",
        "test_date": "2026-01-16",
        "scores": {
            "memory": 65,
            "attention": 55,
            "processing_speed": 75,
            "executive_function": 60
        },
        "age": 45,
        "gender": "female",
        "lifestyle_factors": {
            "sleep_hours": 6,
            "exercise_frequency": "rare",
            "stress_level": "high",
            "diet_quality": "poor"
        },
        "test_conditions": {
            "distractions": "low",
            "time_of_day": "morning"
        }
    }
    
    # Perform analysis
    analysis = analyzer.analyze_test_results(test_data)
    
    # Print summary report
    print(analyzer.generate_summary_report(analysis))
    
    print(f"\nConfidence Score: {analysis['confidence_score']:.2f}")
    print(f"Follow-up Recommendations:")
    for suggestion in analysis['follow_up_suggestions']:
        print(f"  • {suggestion}")
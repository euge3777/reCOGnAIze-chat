import json
import os
from typing import List, Dict, Optional, Tuple
import logging

# Handle both relative and absolute imports
try:
    from .vector_store import VectorStore
except ImportError:
    from vector_store import VectorStore

try:
    from .mistral_llm import get_mistral_instance
except ImportError:
    try:
        from mistral_llm import get_mistral_instance
    except ImportError:
        # Create a simple fallback if mistral_llm doesn't exist
        def get_mistral_instance():
            return None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGRecommendationSystem:
    """RAG-based system for generating personalized multivitamin recommendations."""
    
    def __init__(self, data_dir: str = "data", knowledge_base_dir: str = "knowledge_base"):
        """
        Initialize the RAG recommendation system.
        
        Args:
            data_dir: Directory containing knowledge JSON files
            knowledge_base_dir: Directory for vector storage
        """
        self.data_dir = data_dir
        self.vector_store = VectorStore(knowledge_base_dir)
        
        # Initialize Mistral LLM
        self.mistral = get_mistral_instance()
        
        # Load cognitive mapping data
        self.cognitive_mapping = self._load_cognitive_mapping()
        
        # Ensure vector store is built
        self.vector_store.rebuild_index_if_needed()
    
    def _load_cognitive_mapping(self) -> Dict:
        """Load cognitive domain to vitamin mapping data."""
        mapping_path = os.path.join(self.data_dir, "cognitive_mapping.json")
        try:
            with open(mapping_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load cognitive mapping: {e}")
            return {}
    
    def analyze_cognitive_scores(self, test_results: Dict) -> Dict:
        """
        Analyze cognitive test results to identify impairments and severity.
        
        Args:
            test_results: Dictionary containing cognitive test scores
            
        Returns:
            Analysis results with identified impairments and recommendations
        """
        scores = test_results.get('scores', {})
        age = test_results.get('age', 35)
        gender = test_results.get('gender', 'unknown')
        
        analysis = {
            'impaired_domains': [],
            'severity_levels': {},
            'recommended_focus_areas': [],
            'demographic_adjustments': {},
            'risk_factors': []
        }
        
        # Analyze each cognitive domain
        for domain, score in scores.items():
            domain_info = self.cognitive_mapping.get('cognitive_domains', {}).get(domain, {})
            
            # Determine severity based on score
            severity = self._determine_severity(score)
            analysis['severity_levels'][domain] = severity
            
            # Check if domain is impaired (score below threshold)
            if score < 70:  # General impairment threshold
                analysis['impaired_domains'].append(domain)
                analysis['recommended_focus_areas'].append({
                    'domain': domain,
                    'score': score,
                    'severity': severity,
                    'description': domain_info.get('description', ''),
                    'indicators': domain_info.get('impairment_indicators', [])
                })
        
        # Add demographic adjustments
        analysis['demographic_adjustments'] = self._get_demographic_adjustments(age, gender)
        
        return analysis
    
    def _determine_severity(self, score: float) -> str:
        """Determine severity level based on cognitive score."""
        for severity, data in self.cognitive_mapping.get('severity_mappings', {}).items():
            score_range = data.get('score_range', [0, 100])
            if score_range[0] <= score <= score_range[1]:
                return severity
        return 'mild'
    
    def _get_demographic_adjustments(self, age: int, gender: str) -> Dict:
        """Get demographic-specific adjustments."""
        adjustments = {}
        
        # Age-based adjustments
        age_groups = self.cognitive_mapping.get('demographic_adjustments', {}).get('age_groups', {})
        for age_range, data in age_groups.items():
            if '-' in age_range:
                min_age, max_age = map(int, age_range.split('-'))
                if min_age <= age <= max_age:
                    adjustments['age_group'] = data
                    break
            elif '+' in age_range:
                min_age = int(age_range.replace('+', ''))
                if age >= min_age:
                    adjustments['age_group'] = data
        
        # Gender-based adjustments
        gender_considerations = self.cognitive_mapping.get('demographic_adjustments', {}).get('gender_considerations', {})
        if gender in gender_considerations:
            adjustments['gender'] = gender_considerations[gender]
        
        return adjustments
    
    def generate_recommendations(self, test_results: Dict, user_query: str = "") -> Dict:
        """
        Generate personalized Centrum product recommendations based on test results.
        
        Args:
            test_results: User information and cognitive test results
            user_query: Optional user query for additional context
            
        Returns:
            Comprehensive Centrum product recommendation
        """
        # Find matching Centrum product based on user profile
        centrum_recommendation = self._find_matching_centrum_product(test_results, user_query)
        
        # Analyze cognitive scores if provided
        cognitive_analysis = {}
        if 'scores' in test_results:
            cognitive_analysis = self.analyze_cognitive_scores(test_results)
        
        return {
            'centrum_product': centrum_recommendation,
            'cognitive_analysis': cognitive_analysis,
            'explanation': self._generate_centrum_explanation(centrum_recommendation, test_results),
            'safety_notes': centrum_recommendation.get('safety_notes', []),
            'alternative_products': centrum_recommendation.get('alternative_products', [])
        }
        
    def _find_matching_centrum_product(self, test_results: Dict, user_query: str = "") -> Dict:
        """
        Find the most appropriate Centrum product based on user criteria.
        
        Args:
            test_results: User profile and test data
            user_query: User's specific request
            
        Returns:
            Matching Centrum product recommendation
        """
        # Load Centrum product rules
        knowledge_path = os.path.join(self.data_dir, "multivitamin_knowledge.json")
        try:
            with open(knowledge_path, 'r', encoding='utf-8') as f:
                rules_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load Centrum product rules: {e}")
            return self._get_fallback_recommendation()
        
        # Extract user criteria
        age = test_results.get('age', 25)
        sex = test_results.get('gender', test_results.get('sex', 'any'))
        vascular_risks = test_results.get('vascular_risk_factors', [])
        cognitive_concerns = test_results.get('cognitive_concerns', [])
        life_stage = test_results.get('life_stage', '')
        on_glp1 = test_results.get('on_glp1_medication', False)
        user_goals = test_results.get('primary_goals', [])
        
        # Add cognitive concerns based on test scores
        if 'scores' in test_results:
            for domain, score in test_results['scores'].items():
                if score < 70:  # Below normal threshold
                    if 'memory' in domain.lower():
                        cognitive_concerns.append('memory_issues')
                    elif 'attention' in domain.lower():
                        cognitive_concerns.append('attention_deficit')
        
        # Find best matching rule
        best_match = None
        best_score = -1
        
        for rule in rules_data:
            match_score = self._calculate_rule_match_score(rule, age, sex, vascular_risks, 
                                                          cognitive_concerns, life_stage, on_glp1, user_goals)
            if match_score > best_score:
                best_score = match_score
                best_match = rule
        
        if best_match:
            return {
                'product': best_match.get('recommended_product', {}),
                'primary_goals': best_match.get('primary_goal', []),
                'safety_notes': best_match.get('safety_notes', []),
                'alternative_products': best_match.get('alternative_products', []),
                'rule_id': best_match.get('rule_id', ''),
                'match_score': best_score
            }
        
        return self._get_fallback_recommendation()
    
    def _get_domain_recommendations(self, impaired_domains: List[str]) -> List[Dict]:
        """Get base vitamin recommendations for impaired cognitive domains."""
        recommendations = []
        
        for domain in impaired_domains:
            domain_info = self.cognitive_mapping.get('cognitive_domains', {}).get(domain, {})
            recommended_vitamins = domain_info.get('recommended_vitamins', [])
            
            for vitamin_rec in recommended_vitamins:
                # Get detailed vitamin information
                vitamin_details = self.vector_store.get_vitamin_details(vitamin_rec['name'])
                
                if vitamin_details:
                    recommendations.append({
                        'vitamin': vitamin_details,
                        'priority': vitamin_rec['priority'],
                        'reasoning': vitamin_rec['reasoning'],
                        'target_domain': domain,
                        'evidence_level': vitamin_details.get('evidence_level', 'Unknown')
                    })
        
        return recommendations
    
    def _enhance_with_rag(self, base_recommendations: List[Dict], analysis: Dict, user_query: str) -> List[Dict]:
        """Enhance recommendations using RAG retrieval."""
        enhanced = base_recommendations.copy()
        
        # Search for additional relevant information
        search_queries = []
        
        # Create search queries based on impaired domains
        for domain in analysis['impaired_domains']:
            search_queries.append(f"vitamins for {domain.replace('_', ' ')} improvement")
            search_queries.append(f"supplements cognitive {domain.replace('_', ' ')} support")
        
        # Add user query if provided
        if user_query:
            search_queries.append(user_query)
        
        # Perform RAG retrieval for each query
        for query in search_queries:
            rag_results = self.vector_store.search(query, k=3)
            
            # Add relevant findings to recommendations
            for result in rag_results:
                if result['type'] == 'vitamin' and result['similarity_score'] > 0.7:
                    # Check if this vitamin is already in recommendations
                    existing_vitamin = next(
                        (rec for rec in enhanced if rec['vitamin']['name'] == result['metadata']['name']), 
                        None
                    )
                    
                    if existing_vitamin:
                        # Boost priority if found again
                        if existing_vitamin['priority'] == 'medium':
                            existing_vitamin['priority'] = 'high'
                        existing_vitamin['rag_score'] = result['similarity_score']
                    else:
                        # Add new recommendation
                        enhanced.append({
                            'vitamin': result['metadata'],
                            'priority': 'medium',
                            'reasoning': f"RAG-identified based on query: {query}",
                            'target_domain': 'multiple',
                            'evidence_level': result['metadata'].get('evidence_level', 'Unknown'),
                            'rag_score': result['similarity_score']
                        })
        
        return enhanced
    
    def _apply_demographic_adjustments(self, recommendations: List[Dict], adjustments: Dict) -> List[Dict]:
        """Apply demographic-specific adjustments to recommendations."""
        adjusted = []
        
        for rec in recommendations:
            adjusted_rec = rec.copy()
            
            # Apply age-based modifier
            age_data = adjustments.get('age_group', {})
            modifier = age_data.get('modifier', 1.0)
            
            # Adjust dosage recommendations
            vitamin = adjusted_rec['vitamin']
            if 'dosage' in vitamin:
                adjusted_rec['adjusted_dosage'] = self._adjust_dosage(vitamin['dosage'], modifier)
            
            # Add age-specific considerations
            adjusted_rec['age_considerations'] = age_data.get('additional_considerations', [])
            
            # Apply gender-specific emphasis
            gender_data = adjustments.get('gender', {})
            emphasized_nutrients = gender_data.get('emphasized_nutrients', [])
            
            if vitamin['name'] in emphasized_nutrients:
                if adjusted_rec['priority'] == 'medium':
                    adjusted_rec['priority'] = 'high'
                adjusted_rec['gender_emphasized'] = True
            
            adjusted.append(adjusted_rec)
        
        return adjusted
    
    def _adjust_dosage(self, original_dosage: str, modifier: float) -> str:
        """Adjust dosage string based on modifier."""
        try:
            # Extract numeric values from dosage string
            import re
            numbers = re.findall(r'\d+', original_dosage)
            if numbers:
                original_amount = int(numbers[0])
                adjusted_amount = int(original_amount * modifier)
                return original_dosage.replace(str(original_amount), str(adjusted_amount))
        except:
            pass
        
        return original_dosage
    
    def _check_contraindications(self, recommendations: List[Dict], medications: List[str], conditions: List[str]) -> List[Dict]:
        """Check for contraindications and add safety warnings."""
        contraindications = self.cognitive_mapping.get('contraindication_checks', {})
        
        safe_recommendations = []
        
        for rec in recommendations:
            vitamin_name = rec['vitamin']['name']
            safety_rec = rec.copy()
            safety_rec['warnings'] = []
            safety_rec['is_safe'] = True
            
            # Check medication interactions
            med_interactions = contraindications.get('medication_interactions', {})
            for med_type, problematic_vitamins in med_interactions.items():
                if any(med.lower() in med_type.lower() for med in medications):
                    if any(vit.lower() in vitamin_name.lower() for vit in problematic_vitamins):
                        safety_rec['warnings'].append(f"Potential interaction with {med_type}")
                        safety_rec['is_safe'] = False
            
            # Check health condition contraindications
            condition_contraindications = contraindications.get('health_conditions', {})
            for condition, problematic_vitamins in condition_contraindications.items():
                if any(cond.lower() in condition.lower() for cond in conditions):
                    if any(vit.lower() in vitamin_name.lower() for vit in problematic_vitamins):
                        safety_rec['warnings'].append(f"Contraindicated with {condition}")
                        safety_rec['is_safe'] = False
            
            safe_recommendations.append(safety_rec)
        
        return safe_recommendations
    
    def _generate_explanation(self, analysis: Dict, recommendations: List[Dict]) -> str:
        """Generate human-readable explanation of recommendations."""
        explanation = []
        
        # Summarize cognitive analysis
        impaired_domains = analysis['impaired_domains']
        if impaired_domains:
            explanation.append(f"Based on your cognitive test results, the following areas show impairment: {', '.join(impaired_domains).replace('_', ' ')}.")
        
        # Summarize recommendations
        high_priority = [rec for rec in recommendations if rec['priority'] == 'high' and rec['is_safe']]
        if high_priority:
            high_priority_names = [rec['vitamin']['name'] for rec in high_priority]
            explanation.append(f"High priority recommendations include: {', '.join(high_priority_names)}.")
        
        # Add safety warnings
        unsafe_recs = [rec for rec in recommendations if not rec['is_safe']]
        if unsafe_recs:
            explanation.append("⚠️ Some recommendations have potential contraindications. Please consult with a healthcare provider.")
        
        return ' '.join(explanation)
    
    def _generate_dosage_guidance(self, recommendations: List[Dict], analysis: Dict) -> Dict:
        """Generate specific dosage guidance."""
        guidance = {}
        
        for rec in recommendations:
            vitamin_name = rec['vitamin']['name']
            original_dosage = rec['vitamin'].get('dosage', 'Consult healthcare provider')
            adjusted_dosage = rec.get('adjusted_dosage', original_dosage)
            
            guidance[vitamin_name] = {
                'recommended_dosage': adjusted_dosage,
                'timing': 'With meals for better absorption',
                'duration': 'Long-term supplementation recommended',
                'monitoring': 'Assess cognitive improvement after 8-12 weeks'
            }
        
        return guidance
    
    def _generate_monitoring_suggestions(self, analysis: Dict) -> List[str]:
        """Generate monitoring and follow-up suggestions."""
        suggestions = [
            "Re-assess cognitive function after 3 months of supplementation",
            "Monitor for any adverse reactions or interactions",
            "Keep a cognitive function diary to track improvements",
            "Consider periodic blood tests to check nutrient levels"
        ]
        
        return suggestions
    
    def _generate_lifestyle_recommendations(self, analysis: Dict) -> List[str]:
        """Generate complementary lifestyle recommendations."""
        recommendations = [
            "Maintain regular exercise routine (3-5 times per week)",
            "Ensure 7-9 hours of quality sleep per night",
            "Practice stress management techniques (meditation, yoga)",
            "Engage in cognitive training activities (puzzles, reading)",
            "Follow a Mediterranean-style diet rich in antioxidants",
            "Stay socially active and engaged",
            "Limit alcohol consumption",
            "Stay hydrated (8-10 glasses of water daily)"
        ]
        
        return recommendations
    
    def chat_query(self, query: str, context: Dict = None) -> str:
        """
        Process a conversational query about multivitamins using RAG + Mistral.
        
        Args:
            query: User's question or query
            context: Optional context from previous conversation
            
        Returns:
            Response string
        """
        # Search for relevant information
        results = self.vector_store.search(query, k=5)
        
        if not results:
            return self.mistral.generate_response(
                query,
                system_prompt="You are a multivitamin and cognitive health expert. Provide helpful advice while recommending consultation with healthcare providers."
            )
        
        # Build context from search results
        context_info = []
        for result in results[:3]:  # Use top 3 results
            if result['type'] == 'vitamin':
                vitamin_info = result['metadata']
                context_info.append(f"Vitamin: {vitamin_info['name']} - {vitamin_info['description']}")
                if vitamin_info.get('cognitive_benefits'):
                    context_info.append(f"Benefits: {', '.join(vitamin_info['cognitive_benefits'][:2])}")
                if vitamin_info.get('dosage'):
                    context_info.append(f"Dosage: {vitamin_info['dosage']}")
        
        retrieved_context = " | ".join(context_info)
        
        # Generate response using Mistral with retrieved context
        response = self.mistral.generate_response(
            query,
            context=retrieved_context,
            system_prompt="You are a knowledgeable assistant specializing in cognitive health and multivitamins. Use the provided context to give accurate, helpful advice. Always recommend consulting healthcare providers for medical decisions."
        )
        
        # Add disclaimer
        if not response.endswith("⚠️ This information is for educational purposes only. Please consult with a healthcare provider before starting any new supplements."):
            response += "\n\n⚠️ This information is for educational purposes only. Please consult with a healthcare provider before starting any new supplements."
        
        return response

if __name__ == "__main__":
    # Test the RAG system
    rag_system = RAGRecommendationSystem()
    
    # Sample test results
    test_results = {
        "test_type": "gamified_cognitive",
        "scores": {
            "memory": 65,
            "attention": 55,
            "processing_speed": 75,
            "executive_function": 60
        },
        "impairments": ["mild_memory_loss", "attention_deficit"],
        "age": 45,
        "gender": "female",
        "medications": [],
        "health_conditions": []
    }
    
    # Generate recommendations
    recommendations = rag_system.generate_recommendations(test_results)
    
    print("=== COGNITIVE ANALYSIS ===")
    print(f"Impaired domains: {recommendations['analysis']['impaired_domains']}")
    
    print("\n=== RECOMMENDATIONS ===")
    for i, rec in enumerate(recommendations['recommendations'][:5], 1):
        print(f"{i}. {rec['vitamin']['name']} ({rec['priority']} priority)")
        print(f"   Reasoning: {rec['reasoning']}")
        print(f"   Safe: {rec['is_safe']}")
        if rec['warnings']:
            print(f"   Warnings: {', '.join(rec['warnings'])}")
    
    print(f"\n=== EXPLANATION ===")
    print(recommendations['explanation'])
    
    # Test chat functionality
    print(f"\n=== CHAT TEST ===")
    test_queries = [
        "What vitamins help with memory problems?",
        "I have trouble concentrating, what do you recommend?",
        "Tell me about Omega-3 supplements"
    ]
    
    for query in test_queries:
        print(f"\nQ: {query}")
        print(f"A: {rag_system.chat_query(query)}")
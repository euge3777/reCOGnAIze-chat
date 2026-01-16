import json
import os
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CentrumRecommender:
    """Centrum product recommendation system based on user profile and cognitive test results."""
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize the Centrum recommendation system.
        
        Args:
            data_dir: Directory containing Centrum product rules
        """
        self.data_dir = data_dir
        self.product_rules = self._load_product_rules()
    
    def reload_rules(self):
        """Force reload the product rules from file."""
        print("DEBUG: Reloading Centrum product rules...")
        self.product_rules = self._load_product_rules()
        print(f"DEBUG: Loaded {len(self.product_rules)} rules")
        for rule in self.product_rules[:3]:  # Show first 3 rules
            print(f"  - {rule.get('rule_id', 'unknown')}")
    
    def _load_product_rules(self) -> List[Dict]:
        """Load Centrum product recommendation rules."""
        knowledge_path = os.path.join(self.data_dir, "multivitamin_knowledge.json")
        try:
            with open(knowledge_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Handle both list format (new) and dict format (old)
                if isinstance(data, list):
                    return data
                else:
                    return data.get('rules', [])
        except Exception as e:
            logger.error(f"Failed to load Centrum product rules: {e}")
            return []
    
    def get_recommendation(self, user_profile: Dict, user_query: str = "") -> Dict:
        """
        Get Centrum product recommendation based on user profile.
        
        Args:
            user_profile: User information including age, gender, health conditions, etc.
            user_query: User's specific question or request
            
        Returns:
            Centrum product recommendation with explanation
        """
        # Extract user criteria from profile
        age = user_profile.get('age', 25)
        sex = user_profile.get('gender', user_profile.get('sex', 'any')).lower()
        vascular_risks = user_profile.get('vascular_risk_factors', [])
        cognitive_concerns = user_profile.get('cognitive_concerns', [])
        life_stage = user_profile.get('life_stage', [])
        on_glp1 = user_profile.get('on_glp1_medication', False)
        user_goals = user_profile.get('primary_goals', [])
        symptoms = user_profile.get('symptoms', [])
        
        # Add cognitive concerns based on test scores if provided
        if 'scores' in user_profile:
            cognitive_concerns.extend(self._analyze_test_scores(user_profile['scores']))
        
        # Add cognitive concerns based on user query
        if user_query:
            cognitive_concerns.extend(self._extract_concerns_from_query(user_query))
        
        # Find best matching rule
        best_match = self._find_best_matching_rule(
            age, sex, vascular_risks, cognitive_concerns, life_stage, 
            on_glp1, user_goals, symptoms
        )
        
        if best_match:
            # Filter products by gender if applicable_gender is specified
            all_products = best_match.get('recommended_products', [best_match.get('recommended_product', {})])
            if isinstance(all_products, dict):
                all_products = [all_products]
            
            # Filter products based on gender
            gender_matched_products = []
            for product in all_products:
                applicable_gender = product.get('applicable_gender')
                if not applicable_gender or applicable_gender == sex:
                    gender_matched_products.append(product)
            
            # Use gender-matched products if any, otherwise use all products
            products = gender_matched_products if gender_matched_products else all_products
            
            return {
                'products': products,
                'primary_goals': best_match.get('primary_goal', []),
                'safety_notes': best_match.get('safety_notes', []),
                'rule_id': best_match.get('rule_id', ''),
                'explanation': self._generate_explanation(best_match, user_profile),
                'match_criteria': self._explain_match_criteria(best_match, user_profile)
            }
        
        return self._get_fallback_recommendation()
    
    def _analyze_test_scores(self, scores: Dict) -> List[str]:
        """Analyze cognitive test scores to identify concerns."""
        concerns = []
        for domain, score in scores.items():
            if score < 70:  # Below normal threshold
                if 'memory' in domain.lower():
                    concerns.append('memory_issues')
                elif 'attention' in domain.lower():
                    concerns.append('attention_deficit')
                elif 'processing' in domain.lower():
                    concerns.append('processing_speed_issues')
                elif 'executive' in domain.lower():
                    concerns.append('executive_function_issues')
        return concerns
    
    def _extract_concerns_from_query(self, query: str) -> List[str]:
        """Extract health concerns from user query."""
        concerns = []
        query_lower = query.lower()
        
        # Map query terms to concerns - more comprehensive mapping
        concern_mapping = {
            # Memory related
            'memory': 'memory_issues',
            'forgetful': 'memory_issues', 
            'forget': 'memory_issues',
            'recall': 'memory_issues',
            'remembering': 'memory_issues',
            'brain fog': 'memory_issues',
            # Attention/Focus
            'focus': 'attention_deficit',
            'attention': 'attention_deficit',
            'concentrate': 'attention_deficit',
            'distracted': 'attention_deficit',
            'adhd': 'attention_deficit',
            # Age-related
            'aging': 'age_related_cognitive_decline',
            'older': 'age_related_cognitive_decline',
            'senior': 'age_related_cognitive_decline',
            # Stress/Mood
            'stress': 'stress',
            'stressed': 'stress',
            'anxiety': 'anxiety',
            'anxious': 'anxiety',
            'tired': 'fatigue',
            'fatigue': 'fatigue',
            'exhausted': 'fatigue',
            'energy': 'energy_support',
            # Life stages
            'pregnant': 'pregnancy',
            'pregnancy': 'pregnancy',
            'trying to conceive': 'planning_pregnancy',
            'ttc': 'planning_pregnancy',
            'breastfeeding': 'breastfeeding',
            'postpartum': 'postpartum',
            'menopause': 'menopause',
            'hot flash': 'hot_flashes',
            'night sweat': 'night_sweats',
            'sleep': 'sleep_difficulty',
            # Health conditions
            'blood pressure': 'high_blood_pressure',
            'hypertension': 'high_blood_pressure',
            'cholesterol': 'high_cholesterol',
            'diabetes': 'diabetes',
            'diabetic': 'diabetes',
            'glp-1': 'glp1_medication',
            'ozempic': 'glp1_medication',
            'wegovy': 'glp1_medication',
            'semaglutide': 'glp1_medication',
            # Lifestyle
            'athlete': 'athletic_performance',
            'exercise': 'athletic_performance',
            'workout': 'athletic_performance',
            'performance': 'mental_performance',
            'study': 'mental_performance',
            'work': 'mental_performance'
        }
        
        for term, concern in concern_mapping.items():
            if term in query_lower:
                concerns.append(concern)
                
        # Special age detection from context
        if any(word in query_lower for word in ['50', 'fifty', '60', 'sixty', '70', 'seventy']):
            concerns.append('age_related_concerns')
            
        return concerns
    
    def _find_best_matching_rule(self, age: int, sex: str, vascular_risks: List, 
                                cognitive_concerns: List, life_stage: List, 
                                on_glp1: bool, user_goals: List, symptoms: List) -> Optional[Dict]:
        """Find the best matching Centrum product rule."""
        best_match = None
        best_score = -1
        
        for rule in self.product_rules:
            score = self._calculate_rule_match_score(
                rule, age, sex, vascular_risks, cognitive_concerns, 
                life_stage, on_glp1, user_goals, symptoms
            )
            
            if score > best_score:
                best_score = score
                best_match = rule
        
        return best_match
    
    def _calculate_rule_match_score(self, rule: Dict, age: int, sex: str, 
                                  vascular_risks: List, cognitive_concerns: List,
                                  life_stage: List, on_glp1: bool, 
                                  user_goals: List, symptoms: List) -> float:
        """Calculate how well a rule matches the user profile."""
        criteria = rule.get('applicable_if', {})
        score = 0.0
        
        # AGE MATCHING - CRITICAL: Must match age range exactly or get severe penalty
        age_matches = True
        if 'min_age' in criteria:
            if age < criteria['min_age']:
                age_matches = False
        
        if 'max_age' in criteria:
            if age > criteria['max_age']:
                age_matches = False
        
        # If age doesn't match, return very low score immediately
        if not age_matches:
            return 0.001  # Almost zero score for age mismatch
        
        # Age matches, now calculate other scores
        max_possible_score = 1.0  # Start with base score
        
        # Age matching bonus (only if age matches)
        if 'min_age' in criteria and age >= criteria['min_age']:
            score += 2.0
            max_possible_score += 2.0
            # Additional bonus for being in optimal range
            if 'max_age' in criteria and age <= criteria['max_age']:
                score += 1.0
                max_possible_score += 1.0
        
        # Gender matching
        if 'sex' in criteria:
            max_possible_score += 2.0
            if criteria['sex'] == 'any' or criteria['sex'] == sex:
                score += 2.0
        
        # Vascular risk factors matching
        if 'vascular_risk_factors_any_of' in criteria:
            vascular_criteria = criteria['vascular_risk_factors_any_of']
            max_possible_score += 4.0
            if not vascular_criteria:  # Empty list means no vascular risks required
                if not vascular_risks:
                    score += 4.0  # Perfect match for no risks
                else:
                    score += 1.0  # Partial score if user has risks but rule doesn't require them
            else:  # Rule requires specific vascular risks
                matching_risks = set(vascular_risks) & set(vascular_criteria)
                if matching_risks:
                    score += 4.0  # Full score for matching risks
                elif vascular_risks:
                    score += 1.0  # Some score for having risks but not matching
        
        # Cognitive concerns matching - very important
        if 'cognitive_concern_any_of' in criteria:
            cognitive_criteria = criteria['cognitive_concern_any_of']
            max_possible_score += 5.0  # Highest weight
            if not cognitive_criteria:  # Empty list means no cognitive concerns required
                if not cognitive_concerns:
                    score += 5.0  # Perfect match for no concerns
                else:
                    score += 1.0  # Low score if user has concerns but rule doesn't address them
            else:  # Rule addresses specific cognitive concerns
                matching_concerns = set(cognitive_concerns) & set(cognitive_criteria)
                if matching_concerns:
                    score += 5.0  # Full score for matching concerns
                    # Bonus for multiple matches
                    score += min(len(matching_concerns) * 0.5, 2.0)  # Cap bonus at 2.0
        
        # Life stage matching
        if 'life_stage_any_of' in criteria:
            life_criteria = criteria['life_stage_any_of']
            max_possible_score += 4.0
            matching_stages = set(life_stage) & set(life_criteria)
            if matching_stages:
                score += 4.0
        
        # GLP-1 medication - exact match required
        if 'on_glp1_medication' in criteria:
            max_possible_score += 3.0
            if criteria['on_glp1_medication'] == on_glp1:
                score += 3.0
            # No penalty for mismatch since it's boolean
        
        # Symptoms matching
        if 'symptom_any_of' in criteria:
            symptom_criteria = criteria['symptom_any_of']
            max_possible_score += 3.0
            matching_symptoms = set(symptoms) & set(symptom_criteria)
            if matching_symptoms:
                score += 3.0
        
        # User goals matching
        if 'primary_user_goal_any_of' in criteria:
            goal_criteria = criteria['primary_user_goal_any_of']
            max_possible_score += 2.0
            matching_goals = set(user_goals) & set(goal_criteria)
            if matching_goals:
                score += 2.0
        
        # Return normalized score
        if max_possible_score > 0:
            return min(1.0, score / max_possible_score)  # Cap at 1.0
        else:
            return 0.1  # Low default score
    
    def _generate_explanation(self, rule: Dict, user_profile: Dict) -> str:
        """Generate explanation for why these products were recommended."""
        products = rule.get('recommended_products', [rule.get('recommended_product', {})])
        primary_product = products[0] if products else {}
        product_name = primary_product.get('display_name', 'Centrum Product')
        rationale = primary_product.get('rationale', '')
        evidence = primary_product.get('evidence_note', '')
        
        explanation = f"**{product_name}** is my top recommendation because:\n\n"
        explanation += f"• {rationale}\n"
        
        if evidence:
            explanation += f"• Clinical evidence: {evidence}\n"
        
        # Add specific reasons based on user profile
        age = user_profile.get('age', 0)
        if age >= 50:
            explanation += f"• Age-appropriate formula for adults {age}+\n"
        
        if user_profile.get('gender') == 'female':
            explanation += "• Formulated specifically for women's nutritional needs\n"
        elif user_profile.get('gender') == 'male':
            explanation += "• Formulated specifically for men's nutritional needs\n"
        
        primary_goals = rule.get('primary_goal', [])
        if primary_goals:
            explanation += f"• Supports your health goals: {', '.join(primary_goals)}\n"
        
        # Add information about alternatives if available
        if len(products) > 1:
            explanation += f"\n**Alternative options:**\n"
            for product in products[1:]:
                alt_name = product.get('display_name', 'Alternative')
                alt_rationale = product.get('rationale', '')
                explanation += f"• **{alt_name}**: {alt_rationale}\n"
        
        return explanation
    
    def get_product_details(self, product_name: str) -> Dict:
        """Get detailed information about a specific Centrum product."""
        product_name_lower = product_name.lower()
        
        for rule in self.product_rules:
            products = rule.get('recommended_products', [rule.get('recommended_product', {})])
            for product in products:
                if product_name_lower in product.get('display_name', '').lower():
                    return {
                        'product': product,
                        'rule_context': rule,
                        'found': True
                    }
        
        return {'found': False}
    
    def answer_product_question(self, query: str) -> str:
        """Answer specific questions about Centrum products."""
        query_lower = query.lower()
        
        # Extract product name from query
        product_name = self._extract_product_name_from_query(query_lower)
        
        if not product_name:
            return "I'd be happy to help! Could you specify which Centrum product you're asking about? For example: 'What ingredients are in Centrum Silver Adults 50+?'"
        
        product_details = self.get_product_details(product_name)
        
        if not product_details['found']:
            return f"I couldn't find information about '{product_name}'. Could you double-check the product name? I can help with questions about Centrum Adults, Centrum Silver, Centrum MultiGummies, and other Centrum products."
        
        product = product_details['product']
        product_display_name = product.get('display_name', product_name)
        
        # Answer based on what they're asking
        if any(word in query_lower for word in ['ingredient', 'what\'s in', 'contains', 'composition']):
            ingredients = product.get('ingredients', 'Ingredients information not available')
            return f"**{product_display_name} contains:**\n\n{ingredients}\n\n💡 Always check the product label for the most current ingredient list and allergen information."
        
        elif any(word in query_lower for word in ['dosage', 'how much', 'how many', 'dose']):
            dosage = product.get('dosage', 'Dosage information not available')
            when_to_take = product.get('when_to_take', '')
            response = f"**{product_display_name} dosage:**\n\n• {dosage}"
            if when_to_take:
                response += f"\n• {when_to_take}"
            response += "\n\n⚠️ Always follow the directions on the product label and consult your healthcare provider for personalized dosing advice."
            return response
        
        elif any(word in query_lower for word in ['when', 'time', 'take']):
            when_to_take = product.get('when_to_take', 'Take as directed on the package')
            dosage = product.get('dosage', '')
            return f"**{product_display_name} - When to take:**\n\n• {when_to_take}\n• {dosage}\n\n💡 Taking with food generally improves absorption and reduces stomach upset."
        
        elif any(word in query_lower for word in ['benefit', 'what does', 'help with', 'good for']):
            rationale = product.get('rationale', '')
            evidence = product.get('evidence_note', '')
            goals = product_details['rule_context'].get('primary_goal', [])
            
            response = f"**{product_display_name} benefits:**\n\n• {rationale}\n"
            if evidence:
                response += f"• Clinical support: {evidence}\n"
            if goals:
                response += f"• Primary goals: {', '.join(goals)}\n"
            return response
        
        elif any(word in query_lower for word in ['side effect', 'safe', 'safety', 'reaction']):
            safety_notes = product_details['rule_context'].get('safety_notes', [])
            response = f"**{product_display_name} safety information:**\n\n"
            if safety_notes:
                for note in safety_notes:
                    response += f"• {note}\n"
            response += "• Generally well-tolerated when taken as directed\n"
            response += "• May cause mild stomach upset if taken on empty stomach\n"
            response += "• Rare allergic reactions possible\n\n"
            response += "⚠️ Always inform your healthcare provider about all supplements you're taking."
            return response
        
        else:
            # General product information
            rationale = product.get('rationale', '')
            dosage = product.get('dosage', '')
            when_to_take = product.get('when_to_take', '')
            
            response = f"**About {product_display_name}:**\n\n• {rationale}\n"
            if dosage:
                response += f"• Dosage: {dosage}\n"
            if when_to_take:
                response += f"• Best taken: {when_to_take}\n"
            
            response += "\n💡 Ask me about ingredients, dosage, benefits, or safety for more specific information!"
            return response
    
    def _extract_product_name_from_query(self, query_lower: str) -> str:
        """Extract Centrum product name from user query."""
        # Common product name patterns
        product_patterns = [
            'centrum silver women 50+',
            'centrum silver men 50+',
            'centrum silver adults 50+',
            'centrum silver',
            'centrum multigummies adults 50+',
            'centrum multigummies women 50+',
            'centrum multigummies men 50+',
            'centrum multigummies multi + mental focus',
            'centrum multigummies adults',
            'centrum multigummies',
            'centrum maternal health prenatal',
            'centrum maternal prenatal',
            'centrum menopause support',
            'centrum nutrient replenish',
            'centrum adults',
            'centrum women',
            'centrum men',
            'centrum kids'
        ]
        
        for pattern in product_patterns:
            if pattern in query_lower:
                return pattern
        
        # Try to extract from common variations
        if 'silver' in query_lower:
            if 'women' in query_lower or 'woman' in query_lower:
                return 'centrum silver women 50+'
            elif 'men' in query_lower or 'man' in query_lower:
                return 'centrum silver men 50+'
            else:
                return 'centrum silver adults 50+'
        
        if 'gummies' in query_lower or 'gummy' in query_lower:
            if 'mental focus' in query_lower or 'focus' in query_lower:
                return 'centrum multigummies multi + mental focus'
            elif 'adults' in query_lower:
                return 'centrum multigummies adults'
            else:
                return 'centrum multigummies'
        
        if 'maternal' in query_lower or 'prenatal' in query_lower or 'pregnancy' in query_lower:
            return 'centrum maternal health prenatal'
        
        if 'menopause' in query_lower:
            return 'centrum menopause support'
        
        if 'glp-1' in query_lower or 'glp1' in query_lower or 'nutrient replenish' in query_lower:
            return 'centrum nutrient replenish'
        
        if 'women' in query_lower or 'woman' in query_lower:
            return 'centrum women'
        
        if 'men' in query_lower or 'man' in query_lower:
            return 'centrum men'
        
        if 'kids' in query_lower or 'children' in query_lower:
            return 'centrum kids'
        
        if 'centrum' in query_lower and 'adults' in query_lower:
            return 'centrum adults'
        
        return ""
    
    def _explain_match_criteria(self, rule: Dict, user_profile: Dict) -> List[str]:
        """Explain which criteria matched for this recommendation."""
        criteria = []
        applicable_if = rule.get('applicable_if', {})
        
        if 'min_age' in applicable_if:
            age = user_profile.get('age', 0)
            min_age = applicable_if['min_age']
            if age >= min_age:
                max_age = applicable_if.get('max_age', 'no limit')
                criteria.append(f"Age range: {min_age}+ (you are {age})")
        
        if 'sex' in applicable_if and applicable_if['sex'] != 'any':
            user_sex = user_profile.get('gender', 'any')
            if applicable_if['sex'] == user_sex:
                criteria.append(f"Gender: {user_sex}")
        
        return criteria
    
    def _get_fallback_recommendation(self) -> Dict:
        """Return fallback recommendation when no specific rule matches."""
        return {
            'products': [
                {
                    'product_key': 'centrum_adults',
                    'display_name': 'Centrum Adults',
                    'priority': 'primary',
                    'rationale': 'Complete, balanced multivitamin suitable for most adults seeking comprehensive nutritional support.',
                    'ingredients': '23 essential vitamins and minerals including Vitamins A, C, D, E, B-vitamins, Iron, Calcium, Magnesium, Zinc',
                    'dosage': 'Take 1 tablet daily with food',
                    'when_to_take': 'Take with breakfast or lunch for best absorption',
                    'evidence_note': 'Backed by decades of nutritional research and clinical studies.'
                }
            ],
            'primary_goals': ['provide comprehensive nutritional support', 'fill potential dietary gaps'],
            'safety_notes': ['Consult healthcare provider for personalized advice', 'Consider individual health conditions and medications'],
            'rule_id': 'fallback_recommendation',
            'explanation': 'This is our general recommendation for adults seeking comprehensive nutritional support.',
            'match_criteria': ['General adult recommendation']
        }
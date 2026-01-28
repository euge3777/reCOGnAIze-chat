import streamlit as st
import json
from typing import Dict, List, Optional
from datetime import datetime
import sys
import os

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.append(os.path.dirname(__file__))

from centrum_recommender import CentrumRecommender
from cognitive_analyzer import CognitiveTestAnalyzer
from file_processor import FileProcessor

class MultivitaminChatbot:
    """Streamlit-based chatbot interface for Centrum product recommendations."""
    
    def __init__(self):
        """Initialize the chatbot with Centrum recommender and analyzer."""
        if 'centrum_system' not in st.session_state:
            with st.spinner("Initializing Centrum recommendation system..."):
                st.session_state.centrum_system = CentrumRecommender()
                st.session_state.analyzer = CognitiveTestAnalyzer()
        
        self.centrum_system = st.session_state.centrum_system
        self.analyzer = st.session_state.analyzer
        
        # Initialize session state
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        if 'test_results' not in st.session_state:
            st.session_state.test_results = None
        
        if 'analysis_results' not in st.session_state:
            st.session_state.analysis_results = None
        
        if 'recommendations' not in st.session_state:
            st.session_state.recommendations = None
        
        if 'uploaded_files' not in st.session_state:
            st.session_state.uploaded_files = []
    
    def render_sidebar(self):
        """Render the sidebar with test input and settings."""
        st.sidebar.title("Cognitive Test Input")
        
        # Test results input section
        st.sidebar.subheader("Enter Test Results")
        
        with st.sidebar.expander("Cognitive Scores", expanded=True):
            memory_score = st.slider("Memory Score", 0, 100, 75, help="Memory and recall abilities")
            attention_score = st.slider("Attention Score", 0, 100, 70, help="Focus and concentration")
            processing_speed = st.slider("Processing Speed", 0, 100, 80, help="Mental processing speed")
            executive_function = st.slider("Executive Function", 0, 100, 75, help="Planning and decision making")
        
        with st.sidebar.expander("Personal Information"):
            age = st.number_input("Age", min_value=18, max_value=100, value=35)
            gender = st.selectbox("Gender", ["female", "male", "other"])
            
        with st.sidebar.expander("Health Information", expanded=False):
            medications = st.text_area("Current Medications (one per line)", 
                                     help="List any medications you're currently taking")
            health_conditions = st.text_area("Health Conditions (one per line)", 
                                           help="List any relevant health conditions")
        
        with st.sidebar.expander("Lifestyle Factors", expanded=False):
            sleep_hours = st.slider("Average Sleep Hours", 4, 12, 7)
            exercise_frequency = st.selectbox("Exercise Frequency", 
                                            ["never", "rare", "weekly", "daily"])
            stress_level = st.selectbox("Stress Level", ["low", "moderate", "high"])
            diet_quality = st.selectbox("Diet Quality", ["poor", "average", "good", "excellent"])
        
        # Analyze button
        if st.sidebar.button("🔍 Analyze Test Results", type="primary"):
            self.process_test_results(
                memory_score, attention_score, processing_speed, executive_function,
                age, gender, medications, health_conditions,
                sleep_hours, exercise_frequency, stress_level, diet_quality
            )
        
        # Clear results button
        if st.sidebar.button("Clear Results"):
            self.clear_session_state()
            
        # Force reload rules button (for development)
        if st.sidebar.button("Reload Rules", help="Force reload Centrum product rules from file"):
            if hasattr(self, 'centrum_system'):
                self.centrum_system.reload_rules()
                st.sidebar.success("Rules reloaded!")
    
    def process_test_results(self, memory, attention, processing, executive,
                           age, gender, medications, conditions,
                           sleep, exercise, stress, diet):
        """Process and analyze the cognitive test results."""
        
        # Format medications and conditions
        medication_list = [med.strip() for med in medications.split('\n') if med.strip()]
        condition_list = [cond.strip() for cond in conditions.split('\n') if cond.strip()]
        
        # Create test data structure
        test_data = {
            "test_type": "gamified_cognitive",
            "test_date": datetime.now().isoformat(),
            "scores": {
                "memory": memory,
                "attention": attention,
                "processing_speed": processing,
                "executive_function": executive
            },
            "age": age,
            "gender": gender,
            "medications": medication_list,
            "health_conditions": condition_list,
            "lifestyle_factors": {
                "sleep_hours": sleep,
                "exercise_frequency": exercise,
                "stress_level": stress,
                "diet_quality": diet
            }
        }
        
        # Store in session state
        st.session_state.test_results = test_data
        
        # Perform cognitive analysis
        with st.spinner("Analyzing cognitive test results..."):
            st.session_state.analysis_results = self.analyzer.analyze_test_results(test_data)
        
        # Create user profile for Centrum recommendation
        user_profile = {
            'age': age,
            'gender': gender,
            'scores': {
                "memory": memory,
                "attention": attention,
                "processing_speed": processing,
                "executive_function": executive
            },
            'medications': medication_list,
            'health_conditions': condition_list,
            'lifestyle_factors': {
                'sleep_hours': sleep,
                'exercise_frequency': exercise,
                'stress_level': stress,
                'diet_quality': diet
            },
            # Map lifestyle to health factors
            'vascular_risk_factors': [],
            'cognitive_concerns': [],
            'primary_goals': ['general_health']
        }
        
        # Add vascular risk factors based on conditions and lifestyle
        if any('diabetes' in cond.lower() for cond in condition_list):
            user_profile['vascular_risk_factors'].append('diabetes')
        if any('blood pressure' in cond.lower() or 'hypertension' in cond.lower() for cond in condition_list):
            user_profile['vascular_risk_factors'].append('high_blood_pressure')
        if any('cholesterol' in cond.lower() for cond in condition_list):
            user_profile['vascular_risk_factors'].append('high_cholesterol')
        
        # Add cognitive concerns based on test scores
        if memory < 70:
            user_profile['cognitive_concerns'].append('memory_issues')
        if attention < 70:
            user_profile['cognitive_concerns'].append('attention_deficit')
        if processing < 70:
            user_profile['cognitive_concerns'].append('processing_speed_issues')
        if executive < 70:
            user_profile['cognitive_concerns'].append('executive_function_issues')
        
        # Add goals based on stress and lifestyle
        if stress == 'high':
            user_profile['primary_goals'].append('stress_management')
        if exercise == 'daily':
            user_profile['primary_goals'].append('athletic_performance')
        
        # Generate Centrum product recommendation with detailed cognitive analysis
        with st.spinner("Finding the perfect Centrum products for you..."):
            # Create detailed cognitive findings
            cognitive_findings = self.analyze_cognitive_domains(memory, attention, processing, executive, age, gender)
            user_profile['cognitive_findings'] = cognitive_findings
            
            st.session_state.recommendations = self.centrum_system.get_recommendation(user_profile)
            
            # Add cognitive findings to recommendations for display
            if st.session_state.recommendations:
                st.session_state.recommendations['cognitive_findings'] = cognitive_findings
        
        # Add domain-specific messages to chat history
        self.add_cognitive_findings_to_chat(memory, attention, processing, executive, age, gender)
        
        # Add to chat history
        products = st.session_state.recommendations.get('products', [])
        if products:
            primary_product = products[0].get('display_name', 'Centrum product')
            if len(products) > 1:
                self.add_system_message(f"Analysis complete! Based on your cognitive profile, I recommend **{primary_product}** as your top choice, with {len(products)-1} alternative option(s). The recommendations above explain how each cognitive domain relates to brain health and which Centrum products best support your needs.")
            else:
                self.add_system_message(f"Analysis complete! Based on your profile, I recommend **{primary_product}**. You can now ask me questions about this recommendation, ingredients, dosage, or explore other options.")
    
    def clear_session_state(self):
        """Clear all session state data."""
        st.session_state.test_results = None
        st.session_state.analysis_results = None
        st.session_state.recommendations = None
        st.session_state.chat_history = []
        st.session_state.uploaded_files = []
        st.rerun()
    
    def handle_file_uploads(self, uploaded_files):
        """
        Process uploaded files and store them in session state.
        
        Args:
            uploaded_files: List of Streamlit UploadedFile objects
        """
        new_files = []
        
        for uploaded_file in uploaded_files:
            # Check if file already uploaded (by filename)
            existing_filenames = [f['filename'] for f in st.session_state.uploaded_files]
            if uploaded_file.name not in existing_filenames:
                file_data = FileProcessor.process_uploaded_file(uploaded_file)
                if file_data:
                    new_files.append(file_data)
                    st.sidebar.success(f"Loaded: {uploaded_file.name}")
                else:
                    st.sidebar.error(f"✗ Failed to process: {uploaded_file.name}")
        
        # Add new files to session state
        if new_files:
            st.session_state.uploaded_files.extend(new_files)
        
        # Display uploaded files summary
        if st.session_state.uploaded_files:
            st.sidebar.markdown("**Uploaded Files:**")
            for file_info in st.session_state.uploaded_files:
                size_kb = file_info['size_bytes'] / 1024
                st.sidebar.markdown(f"• {file_info['filename']} ({size_kb:.1f} KB)")
            
            if st.sidebar.button("Clear Uploaded Files"):
                st.session_state.uploaded_files = []
                st.rerun()

    
    def render_main_interface(self):
        """Render the main chat interface."""
        
        # Title with logo
        col1, col2 = st.columns([1, 10])
        with col1:
            # Add some spacing to align with title
            st.write("")  # Empty space
            
            # Try multiple potential logo paths
            logo_paths = [
                os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png"),
                os.path.join(os.path.dirname(__file__), "assets", "logo.png"),
                "assets/logo.png",
                "../assets/logo.png"
            ]
            
            logo_loaded = False
            for logo_path in logo_paths:
                try:
                    if os.path.exists(logo_path):
                        st.image(logo_path, width=60)
                        logo_loaded = True
                        break
                except:
                    continue
            
            if not logo_loaded:
                st.markdown("## Cognitive Assistant")
                
        with col2:
            st.title("ReCOGnAIze Chatbot")
        
        st.markdown("*Your personalized AI assistant for Centrum product selection based on cognitive health and wellness needs*")
        
        # Display analysis results if available
        if st.session_state.analysis_results:
            self.render_analysis_summary()
        
        # Display Centrum recommendation if available
        if st.session_state.recommendations:
            self.render_recommendations()
        
        # Chat interface
        st.markdown("---")
        st.subheader("Ask Me About Centrum Products")
        
        # Display uploaded files info
        if st.session_state.uploaded_files:
            with st.info():
                st.write("Files loaded in context:")
                file_list = ", ".join([f["filename"] for f in st.session_state.uploaded_files])
                st.write(file_list)
                st.write("These files will be included in your chat context for better, more relevant answers.")
        
        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # File upload and chat input
        col1, col2 = st.columns([6, 1])
        
        with col2:
            uploaded_files = st.file_uploader(
                "Upload",
                accept_multiple_files=True,
                type=['txt', 'pdf', 'csv', 'json', 'xlsx', 'xls'],
                key='file_uploader'
            )
            if uploaded_files:
                self.handle_file_uploads(uploaded_files)
        
        with col1:
            prompt = st.chat_input("Ask about Centrum products, your results, or get recommendations...")
        
        if prompt:
            # Add user message
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            # Generate response
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("Finding the right Centrum product for you..."):
                    response = self.generate_response(prompt)
                st.markdown(response)
            
            # Add assistant response
            st.session_state.chat_history.append({"role": "assistant", "content": response})
    
    def render_analysis_summary(self):
        """Render the cognitive analysis summary."""
        analysis = st.session_state.analysis_results
        overall = analysis['overall_assessment']
        
        st.subheader("Cognitive Analysis Summary")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Overall Status", overall['impairment_level'].title(), 
                     delta=f"{len(overall['impaired_domains'])} domains affected")
        
        with col2:
            confidence = analysis['confidence_score']
            st.metric("Analysis Confidence", f"{confidence:.1%}", 
                     delta="High" if confidence > 0.8 else "Medium" if confidence > 0.6 else "Low")
        
        with col3:
            cognitive_age = overall['cognitive_age_estimate']
            chronological_age = analysis['test_info']['age']
            delta = cognitive_age - chronological_age
            st.metric("Cognitive Age", f"{cognitive_age} years", 
                     delta=f"{delta:+d} years" if delta != 0 else "Normal")
        
        # Domain breakdown
        with st.expander("Domain-by-Domain Analysis", expanded=True):
            for domain, domain_analysis in analysis['domain_analyses'].items():
                col1, col2, col3 = st.columns([2, 1, 2])
                
                with col1:
                    st.write(f"**{domain.replace('_', ' ').title()}**")
                
                with col2:
                    score = domain_analysis['raw_score']
                    level = domain_analysis['impairment_level']
                    
                    # Color coding
                    if level == 'severe':
                        st.error(f"{score:.0f} ({level})")
                    elif level == 'moderate':
                        st.warning(f"{score:.0f} ({level})")
                    elif level == 'mild':
                        st.info(f"{score:.0f} ({level})")
                    else:
                        st.success(f"{score:.0f} ({level})")
                
                with col3:
                    st.write(domain_analysis['severity_description'])
    
    def render_recommendations(self):
        """Render the Centrum product recommendations."""
        recommendation = st.session_state.recommendations
        
        st.subheader("Your Recommended Centrum Products")
        
        # Get all products
        products = recommendation.get('products', [])
        if not products:
            st.error("No products found in recommendations")
            return
        
        # Main product recommendation
        primary_product = products[0]
        product_name = primary_product.get('display_name', 'Centrum Product')
        product_key = primary_product.get('product_key', '')
        rationale = primary_product.get('rationale', '')
        evidence = primary_product.get('evidence_note', '')
        
        # Create a nice product card for primary recommendation
        with st.container():
            st.markdown(f"""
            <div style='border: 2px solid #1f77b4; border-radius: 10px; padding: 20px; margin: 10px 0; background-color: #f8f9ff;'>
                <h3 style='color: #1f77b4; margin-top: 0;'>PRIMARY RECOMMENDATION: {product_name}</h3>
                <p><strong>Why this product:</strong> {rationale}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Product details in columns
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Primary Health Goals:**")
            goals = recommendation.get('primary_goals', [])
            if goals:
                for goal in goals:
                    st.markdown(f"• {goal.replace('_', ' ').title()}")
            else:
                st.markdown("• General health and wellness support")
            
            # Dosage information
            dosage = primary_product.get('dosage', '')
            when_to_take = primary_product.get('when_to_take', '')
            if dosage or when_to_take:
                st.markdown("**Usage Instructions:**")
                if dosage:
                    st.markdown(f"• {dosage}")
                if when_to_take:
                    st.markdown(f"• {when_to_take}")
        
        with col2:
            if evidence:
                st.markdown("**Clinical Evidence:**")
                st.markdown(f"*{evidence}*")
            
            # Ingredients if available
            ingredients = primary_product.get('ingredients', '')
            if ingredients:
                with st.expander("Key Ingredients"):
                    st.markdown(ingredients)
        
        # Alternative products if available
        if len(products) > 1:
            st.markdown("---")
            st.markdown("### Alternative Options")
            
            for i, alt_product in enumerate(products[1:], 1):
                alt_name = alt_product.get('display_name', f'Alternative {i}')
                alt_rationale = alt_product.get('rationale', 'Alternative option')
                alt_dosage = alt_product.get('dosage', '')
                
                with st.expander(f"Option {i}: {alt_name}"):
                    st.markdown(f"**About:** {alt_rationale}")
                    if alt_dosage:
                        st.markdown(f"**Dosage:** {alt_dosage}")
                    
                    alt_ingredients = alt_product.get('ingredients', '')
                    if alt_ingredients:
                        st.markdown(f"**Key Ingredients:** {alt_ingredients}")
        
        # Safety information
        safety_notes = recommendation.get('safety_notes', [])
        if safety_notes:
            with st.expander("Important Safety Information"):
                for note in safety_notes:
                    st.markdown(f"• {note}")
        
        # Match criteria explanation
        match_criteria = recommendation.get('match_criteria', [])
        if match_criteria:
            with st.expander("Why These Products Match You"):
                for criterion in match_criteria:
                    st.markdown(f"- {criterion}")
                    
        st.markdown("---")
        st.info(recommendation.get('explanation', 'Recommendations based on your profile.'))
        
        # Priority recommendations
        high_priority = [rec for rec in recommendation.get('recommendations', []) 
                        if rec.get('priority') == 'high' and rec.get('is_safe', True)]
        medium_priority = [rec for rec in recommendation.get('recommendations', []) 
                          if rec.get('priority') == 'medium' and rec.get('is_safe', True)]
        
        if high_priority:
            st.markdown("### High Priority Recommendations")
            for rec in high_priority:
                self.render_vitamin_card(rec)
        
        if medium_priority:
            with st.expander("Additional Recommendations", expanded=False):
                for rec in medium_priority:
                    self.render_vitamin_card(rec)
        
        # Safety warnings
        unsafe_recs = [rec for rec in recommendation.get('recommendations', []) if not rec.get('is_safe', True)]
        if unsafe_recs:
            st.markdown("### Contraindications Detected")
            st.warning("The following supplements may not be safe for you:")
            for rec in unsafe_recs:
                st.write(f"- **{rec['vitamin']['name']}**: {', '.join(rec['warnings'])}")
        
        # Lifestyle recommendations
        with st.expander("Lifestyle Recommendations", expanded=False):
            for lifestyle_rec in recommendation.get('lifestyle_recommendations', []):
                st.write(f"• {lifestyle_rec}")
    
    def render_vitamin_card(self, recommendation: Dict):
        """Render a vitamin recommendation card."""
        vitamin = recommendation['vitamin']
        
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**{vitamin['name']}** - {vitamin['category']}")
                st.write(vitamin['description'])
                
                # Benefits
                benefits = vitamin.get('cognitive_benefits', [])
                if benefits:
                    st.write("**Benefits:** " + ", ".join(benefits[:3]))
                
                # Reasoning
                st.write(f"**Why recommended:** {recommendation['reasoning']}")
                
                # Dosage
                dosage = recommendation.get('adjusted_dosage', vitamin.get('dosage', 'Consult healthcare provider'))
                st.write(f"**Suggested dosage:** {dosage}")
            
            with col2:
                # Priority badge
                priority = recommendation['priority']
                if priority == 'high':
                    st.error(f"🔴 {priority.upper()}")
                elif priority == 'medium':
                    st.warning(f"🟡 {priority.upper()}")
                else:
                    st.info(f"🔵 {priority.upper()}")
                
                # Evidence level
                evidence = vitamin.get('evidence_level', 'Unknown')
                st.write(f"**Evidence:** {evidence}")
            
            st.markdown("---")
    
    def build_augmented_prompt(self, user_query: str) -> str:
        """
        Build an augmented prompt that includes uploaded file contents.
        
        Args:
            user_query: The user's chat query
            
        Returns:
            The augmented prompt with file context
        """
        augmented_prompt = user_query
        
        # Add file context if files are uploaded
        if st.session_state.uploaded_files:
            augmented_prompt += "\n\n" + "="*60
            augmented_prompt += "\n[CONTEXT FROM UPLOADED FILES]\n"
            augmented_prompt += "="*60 + "\n\n"
            
            for file_data in st.session_state.uploaded_files:
                formatted_content = FileProcessor.format_file_content_for_prompt(file_data)
                augmented_prompt += formatted_content + "\n\n"
            
            augmented_prompt += "="*60 + "\n"
            augmented_prompt += "[END OF FILE CONTEXT]\n"
            augmented_prompt += "="*60
        
        return augmented_prompt
    
    def generate_response(self, query: str) -> str:
        """Generate a response to user query using Centrum recommendation system."""
        try:
            # Build augmented prompt with file context
            augmented_query = self.build_augmented_prompt(query)
            
            # First check if this is a specific product question
            if any(word in query.lower() for word in ['ingredient', 'dosage', 'when to take', 'what\'s in', 'how much', 'how many', 'benefit', 'side effect']):
                product_answer = self.centrum_system.answer_product_question(augmented_query)
                if "Could you specify" not in product_answer and "couldn't find" not in product_answer:
                    return product_answer
            
            # If user has no analysis yet, process their query directly
            if not st.session_state.recommendations:
                # Extract basic info from query and provide general recommendation
                user_profile = self.extract_profile_from_query(query)
                centrum_rec = self.centrum_system.get_recommendation(user_profile, augmented_query)
                
                products = centrum_rec.get('products', [])
                if products:
                    primary_product = products[0]
                    product_name = primary_product.get('display_name', 'Centrum Adults')
                    explanation = centrum_rec.get('explanation', '')
                    
                    response = f"**{product_name}** is recommended for you.\n\n{explanation}"
                    
                    # Add alternative products if available
                    if len(products) > 1:
                        response += "\n\n**Alternative options:**\n"
                        for product in products[1:]:
                            alt_name = product.get('display_name', 'Alternative')
                            alt_rationale = product.get('rationale', '')
                            response += f"• **{alt_name}**: {alt_rationale}\n"
                    
                    # Add safety notes
                    safety_notes = centrum_rec.get('safety_notes', [])
                    if safety_notes:
                        response += "\n\n**Important Safety Information:**\n"
                        for note in safety_notes:
                            response += f"• {note}\n"
                    
                    response += "\nThis information is for educational purposes only. Please consult with a healthcare provider before starting any new supplements."
                    return response
            
            # If user has recommendations, provide contextual responses
            recommendation = st.session_state.recommendations
            products = recommendation.get('products', [])
            if not products:
                return "I don't have any recommendations loaded. Please enter your information in the sidebar to get personalized Centrum product recommendations."
            
            primary_product = products[0]
            product_name = primary_product.get('display_name', 'your recommended product')
            
            # Check what user is asking about
            query_lower = query.lower()
            
            if any(word in query_lower for word in ['why', 'reason', 'recommend']):
                explanation = recommendation.get('explanation', '')
                return f"I recommended **{product_name}** because:\n\n{explanation}"
            
            elif any(word in query_lower for word in ['how', 'take', 'dosage', 'use']):
                dosage = primary_product.get('dosage', 'Take as directed on package')
                when_to_take = primary_product.get('when_to_take', '')
                response = f"**{product_name}** dosage information:\n\n• {dosage}\n"
                if when_to_take:
                    response += f"• {when_to_take}\n"
                response += "\n Always follow the package instructions and consult your healthcare provider for personalized dosing advice."
                return response
            
            elif any(word in query_lower for word in ['ingredient', 'what\'s in', 'contains']):
                ingredients = primary_product.get('ingredients', 'Ingredients information not available')
                return f"**{product_name} contains:**\n\n{ingredients}\n\n💡 Always check the product label for the most current ingredient list."
            
            elif any(word in query_lower for word in ['side effect', 'safe', 'interaction']):
                safety_notes = recommendation.get('safety_notes', [])
                response = f"**Safety information for {product_name}:**\n\n"
                if safety_notes:
                    for note in safety_notes:
                        response += f"• {note}\n"
                else:
                    response += "• Generally well-tolerated when taken as directed\n• May cause mild stomach upset if taken on empty stomach\n• Rare allergic reactions possible\n"
                response += "\n Always inform your healthcare provider about all supplements you're taking, especially if you have medical conditions or take medications."
                return response
            
            elif any(word in query_lower for word in ['alternative', 'other', 'different', 'option']):
                if len(products) > 1:
                    response = f"**Alternative Centrum products for you:**\n\n"
                    for i, product in enumerate(products[1:], 1):
                        response += f"{i}. **{product.get('display_name', 'Alternative product')}**\n"
                        response += f"   • {product.get('rationale', 'Alternative option')}\n"
                        if product.get('dosage'):
                            response += f"   • Dosage: {product.get('dosage')}\n"
                        response += "\n"
                else:
                    response = f"**{product_name}** is the best match for your profile, but you could also consider:\n\n• Centrum Adults (if you prefer a general formula)\n• Centrum MultiGummies (if you prefer gummy format)\n• Centrum Silver 50+ (if you're over 50)"
                return response
            
            else:
                # General response about their recommendation
                explanation = recommendation.get('explanation', '')
                return f"Based on your profile, **{product_name}** is recommended for you. {explanation}\n\nFeel free to ask specific questions about ingredients, dosage, safety, alternatives, or why this was recommended!"
                
        except Exception as e:
            return f"I apologize, but I encountered an error: {str(e)}. Please try asking your question differently, or consider entering your test results first for personalized recommendations."
    
    def extract_profile_from_query(self, query: str) -> Dict:
        """Extract basic user profile information from their query."""
        query_lower = query.lower()
        
        profile = {
            'age': 25,  # Default adult age
            'gender': 'any',
            'vascular_risk_factors': [],
            'cognitive_concerns': [],
            'primary_goals': ['general_health'],
            'life_stage': []
        }
        
        # Extract age if mentioned
        import re
        age_match = re.search(r'\b(\d{1,2})\s*year|age\s*(\d{1,2})|i\'m\s*(\d{1,2})', query_lower)
        if age_match:
            age = int(age_match.group(1) or age_match.group(2) or age_match.group(3))
            if 18 <= age <= 100:
                profile['age'] = age
        
        # Extract gender
        if any(word in query_lower for word in ['woman', 'female', 'girl']):
            profile['gender'] = 'female'
        elif any(word in query_lower for word in ['man', 'male', 'boy']):
            profile['gender'] = 'male'
        
        # Extract health conditions and concerns - Enhanced mapping
        concern_mapping = {
            # Memory concerns - expanded
            'memory': 'memory_issues',
            'forgetful': 'memory_issues',
            'forget': 'memory_issues',
            'remembering': 'memory_issues',
            'recall': 'memory_issues',
            'brain fog': 'memory_issues',
            # Focus and attention
            'focus': 'attention_deficit',
            'attention': 'attention_deficit',
            'concentrate': 'attention_deficit',
            'distracted': 'attention_deficit',
            # Stress and lifestyle
            'stress': 'stress',
            'stressed': 'stress_management',
            'tired': 'fatigue',
            'fatigue': 'fatigue',
            'exhausted': 'fatigue',
            # Life stages
            'pregnant': 'pregnancy',
            'pregnancy': 'planning_pregnancy',
            'menopause': 'menopause',
            'breastfeeding': 'breastfeeding',
            # Performance
            'athlete': 'athletic_performance',
            'exercise': 'athletic_performance',
            'study': 'support_focus',
            'studying': 'mental_performance',
            'work performance': 'mental_performance',
            # Health conditions
            'diabetes': 'diabetes',
            'diabetic': 'diabetes',
            'blood pressure': 'high_blood_pressure',
            'hypertension': 'high_blood_pressure',
            'cholesterol': 'high_cholesterol',
            'obesity': 'obesity',
            'overweight': 'obesity',
            'smoke': 'smoking',
            'smoking': 'smoking',
            # Age clues for better matching
            '50+': 'age_related',
            'older': 'age_related',
            'senior': 'age_related',
            'elderly': 'age_related'
        }
        
        # Adjust age based on memory concerns + age context
        if any(term in query_lower for term in ['forgetful', 'memory', 'forget', 'recall']) and profile['age'] < 50:
            if any(word in query_lower for word in ['older', 'aging', '50', 'senior']):
                profile['age'] = 55  # Bump up age for memory + age context
        
        for term, condition in concern_mapping.items():
            if term in query_lower:
                if condition in ['diabetes', 'high_blood_pressure', 'high_cholesterol', 'obesity', 'smoking']:
                    profile['vascular_risk_factors'].append(condition)
                elif condition in ['pregnancy', 'planning_pregnancy']:
                    profile['life_stage'].append('planning_pregnancy')
                elif condition in ['menopause']:
                    profile['life_stage'].append('menopause')
                elif condition in ['breastfeeding']:
                    profile['life_stage'].append('breastfeeding')
                elif condition in ['athletic_performance', 'support_focus', 'mental_performance', 'stress_management']:
                    profile['primary_goals'].append(condition)
                elif condition == 'age_related':
                    # Age-related terms should bump up the age
                    if profile['age'] < 50:
                        profile['age'] = 55
                else:
                    profile['cognitive_concerns'].append(condition)
        
        return profile
    
    def add_personal_context(self, response: str, query: str, context: Dict) -> str:
        """Add personal context to responses when available."""
        if 'analysis' not in context:
            return response
        
        analysis = context['analysis']
        personal_additions = []
        
        # Add relevant personal insights
        if 'memory' in query.lower() and 'memory' in analysis['domain_analyses']:
            memory_analysis = analysis['domain_analyses']['memory']
            personal_additions.append(f"Based on your memory score of {memory_analysis['raw_score']:.0f}, which shows {memory_analysis['impairment_level']} impairment...")
        
        if 'attention' in query.lower() and 'attention' in analysis['domain_analyses']:
            attention_analysis = analysis['domain_analyses']['attention']
            personal_additions.append(f"Your attention score of {attention_analysis['raw_score']:.0f} indicates {attention_analysis['impairment_level']} difficulties...")
        
        if personal_additions:
            return f"{' '.join(personal_additions)} {response}"
        
        return response
    
    def add_system_message(self, message: str):
        """Add a system message to chat history."""
        st.session_state.chat_history.append({"role": "assistant", "content": message})
    
    def analyze_cognitive_domains(self, memory, attention, processing, executive, age, gender):
        """Analyze cognitive domains and create detailed findings."""
        findings = {}
        
        # Memory analysis
        if memory < 70:
            findings['memory'] = {
                'score': memory,
                'status': 'LOW',
                'explanation': f"Your Grocery Shopping score of {memory} indicates short-term memory challenges. Short-term memory is crucial for daily tasks like remembering shopping lists, names, or recent conversations. These challenges may relate to vascular brain health changes or natural aging processes that affect the hippocampus and prefrontal cortex.",
                'recommendation': self.get_domain_recommendation('memory', age, gender)
            }
        
        # Processing Speed analysis  
        if processing < 70:
            findings['processing_speed'] = {
                'score': processing,
                'status': 'LOW',
                'explanation': f"Your Symbol Matching score of {processing} is below average, indicating slowed processing speed. Processing speed reflects how quickly your brain can perform simple cognitive tasks. This can decline with vascular changes that affect white matter integrity or age-related changes in neural efficiency.",
                'recommendation': self.get_domain_recommendation('processing_speed', age, gender)
            }
        
        # Executive Function analysis
        if executive < 70:
            findings['executive_function'] = {
                'score': executive,
                'status': 'LOW', 
                'explanation': f"Your Trail Making score of {executive} is low, suggesting executive function challenges with planning and task switching. Executive function involves higher-order thinking skills like problem-solving, planning, and cognitive flexibility. Vascular burden and cognitive aging particularly affect the frontal lobe networks responsible for these abilities.",
                'recommendation': self.get_domain_recommendation('executive_function', age, gender)
            }
        
        # Attention analysis
        if attention < 70:
            findings['attention'] = {
                'score': attention,
                'status': 'LOW',
                'explanation': f"Your Airplane Game score of {attention} indicates reduced sustained attention or impulse control. Attention control involves maintaining focus and resisting distractions. Vascular burden can affect the brain networks that support sustained attention, and this often changes with age.",
                'recommendation': self.get_domain_recommendation('attention', age, gender)
            }
            
        return findings
    
    def get_domain_recommendation(self, domain, age, gender):
        """Get domain-specific Centrum product recommendations."""
        # Age-based product selection
        is_senior = age >= 50
        
        if domain == 'memory':
            if is_senior:
                primary = {
                    'name': 'Centrum Silver Adults' if gender == 'any' else f'Centrum Silver {gender.title()}',
                    'reason': 'Specifically formulated for adults 50+ with nutrients that support brain health and memory function including B-vitamins, vitamin D, and antioxidants.'
                }
                alternative = {
                    'name': 'Centrum Adults',
                    'reason': 'Comprehensive multivitamin with brain-supporting nutrients including B12, folate, and vitamin E.'
                }
            else:
                primary = {
                    'name': 'Centrum Adults',
                    'reason': 'Complete multivitamin with B-vitamins and antioxidants that support cognitive function and memory.'
                }
                alternative = {
                    'name': 'Centrum MultiGummies',
                    'reason': 'Easy-to-take gummy format with essential brain-supporting vitamins.'
                }
        
        elif domain == 'processing_speed':
            if is_senior:
                primary = {
                    'name': 'Centrum Silver Adults',
                    'reason': 'Designed for 50+ adults with nutrients supporting cognitive processing and overall brain health.'
                }
                alternative = {
                    'name': 'Centrum Adults',
                    'reason': 'Broad cognitive support with B-vitamins and antioxidants for mental sharpness.'
                }
            else:
                primary = {
                    'name': 'Centrum Adults',
                    'reason': 'Comprehensive support for cognitive processing with B-vitamins, vitamin C, and E.'
                }
                alternative = {
                    'name': 'Centrum MultiGummies',
                    'reason': 'Alternative format with key nutrients for cognitive function.'
                }
        
        elif domain == 'executive_function':
            if is_senior:
                primary = {
                    'name': 'Centrum Silver Adults',
                    'reason': 'Optimized for healthy aging with nutrients supporting executive function and cognitive flexibility.'
                }
                alternative = {
                    'name': 'Centrum Adults',
                    'reason': 'Complete multivitamin supporting higher-order cognitive functions.'
                }
            else:
                primary = {
                    'name': 'Centrum Adults',
                    'reason': 'Supports executive function with essential B-vitamins and antioxidants for brain health.'
                }
                alternative = {
                    'name': 'Centrum MultiGummies',
                    'reason': 'Convenient option with cognitive-supporting nutrients.'
                }
        
        elif domain == 'attention':
            if is_senior:
                primary = {
                    'name': 'Centrum Silver Adults',
                    'reason': 'Age-appropriate formula supporting sustained attention and cognitive focus.'
                }
                alternative = {
                    'name': 'Centrum Adults',
                    'reason': 'Comprehensive support for attention and focus with B-vitamins and antioxidants.'
                }
            else:
                primary = {
                    'name': 'Centrum Adults',
                    'reason': 'Supports attention and focus with nutrients essential for cognitive performance.'
                }
                alternative = {
                    'name': 'Centrum MultiGummies',
                    'reason': 'Easy-to-take format with attention-supporting vitamins.'
                }
        
        return {'primary': primary, 'alternative': alternative}
    
    def add_cognitive_findings_to_chat(self, memory, attention, processing, executive, age, gender):
        """Add cognitive findings and recommendations to chat history."""
        findings_messages = []
        
        # Memory findings
        if memory < 70:
            msg = f"**LOW SHORT-TERM MEMORY** (Grocery Shopping)\n\nYour score: {memory}/100\n\nShort-term memory is crucial for daily tasks like remembering shopping lists, names, or recent conversations. These challenges may relate to vascular brain health changes or natural aging processes that affect the hippocampus and prefrontal cortex.\n\n"
            rec = self.get_domain_recommendation('memory', age, gender)
            msg += f"**Recommended:** {rec['primary']['name']} - {rec['primary']['reason']}\n\n**Alternative:** {rec['alternative']['name']} - {rec['alternative']['reason']}"
            findings_messages.append(msg)
        
        # Processing speed findings  
        if processing < 70:
            msg = f"**LOW PROCESSING SPEED** (Symbol Matching)\n\nYour score: {processing}/100\n\nProcessing speed reflects how quickly your brain can perform simple cognitive tasks. This can decline with vascular changes that affect white matter integrity or age-related changes in neural efficiency.\n\n"
            rec = self.get_domain_recommendation('processing_speed', age, gender)
            msg += f"**Recommended:** {rec['primary']['name']} - {rec['primary']['reason']}\n\n**Alternative:** {rec['alternative']['name']} - {rec['alternative']['reason']}"
            findings_messages.append(msg)
        
        # Executive function findings
        if executive < 70:
            msg = f"**LOW EXECUTIVE FUNCTION** (Trail Making)\n\nYour score: {executive}/100\n\nExecutive function involves higher-order thinking skills like problem-solving, planning, and cognitive flexibility. Vascular burden and cognitive aging particularly affect the frontal lobe networks responsible for these abilities.\n\n"
            rec = self.get_domain_recommendation('executive_function', age, gender)
            msg += f"**Recommended:** {rec['primary']['name']} - {rec['primary']['reason']}\n\n**Alternative:** {rec['alternative']['name']} - {rec['alternative']['reason']}"
            findings_messages.append(msg)
        
        # Attention findings
        if attention < 70:
            msg = f"**LOW ATTENTION / IMPULSE CONTROL** (Airplane Game)\n\nYour score: {attention}/100\n\nAttention control involves maintaining focus and resisting distractions. Vascular burden can affect the brain networks that support sustained attention, and this often changes with age.\n\n"
            rec = self.get_domain_recommendation('attention', age, gender)
            msg += f"**Recommended:** {rec['primary']['name']} - {rec['primary']['reason']}\n\n**Alternative:** {rec['alternative']['name']} - {rec['alternative']['reason']}"
            findings_messages.append(msg)
        
        # Add all findings to chat
        for msg in findings_messages:
            self.add_system_message(msg)
    
    def render_help_section(self):
        """Render help and information section."""
        with st.sidebar.expander("❓ How to Use", expanded=False):
            st.markdown("""
            **Step 1:** Enter your cognitive test scores using the sliders above.
            
            **Step 2:** Fill in personal and health information.
            
            **Step 3:** Click "Analyze Test Results" to get personalized recommendations.
            
            **Step 4:** Ask questions about your results, specific vitamins, or cognitive health.
            
            **Example Questions:**
            - "Why was Omega-3 recommended for me?"
            - "What are the side effects of Magnesium?"
            - "How should I take these supplements?"
            - "Can I take these with my medications?"
            """)
        
        with st.sidebar.expander(" Disclaimer", expanded=False):
            st.markdown("""
            **Important Notice:**
            
            This tool provides educational information only and is not a substitute for professional medical advice.
            
            Always consult with a healthcare provider before starting any new supplements, especially if you have medical conditions or take medications.
            
            The recommendations are based on general research and should be personalized by a qualified healthcare professional.
            """)
    
    def run(self):
        """Main application runner."""
        # Page configuration
        # Try to load logo for browser tab
        tab_icon = ""  # Default fallback, no emoji
        logo_paths = [
            os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png"),
            os.path.join(os.path.dirname(__file__), "assets", "logo.png"),
            "assets/logo.png",
            "../assets/logo.png"
        ]
        
        for logo_path in logo_paths:
            try:
                if os.path.exists(logo_path):
                    from PIL import Image
                    tab_icon = Image.open(logo_path)
                    break
            except:
                continue
        
        st.set_page_config(
            page_title="Multivitamin Recommendation Chatbot",
            page_icon=tab_icon,  
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Custom CSS
        st.markdown("""
        <style>
        .stApp {
            max-width: 1200px;
            margin: 0 auto;
        }
        .main-header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
        }
        .metric-card {
            background: #f0f2f6;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Render interface
        self.render_sidebar()
        self.render_help_section()
        self.render_main_interface()

def main():
    """Main entry point for the Streamlit app."""
    chatbot = MultivitaminChatbot()
    chatbot.run()

if __name__ == "__main__":
    main()
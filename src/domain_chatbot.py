"""
Domain-focused chatbot for ReCOGnAIze Cognitive Health Companion
Provides answers within the cognitive health and vascular risk management domain
"""

import os
from typing import List, Dict
from openai import OpenAI
import sys

# Import vector store
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.vector_store import initialize_vector_store


class DomainChatbot:
    """
    Chatbot that answers questions within the cognitive health domain
    using the knowledge base from vascular_health, lifestyle, and sleep rules
    """
    
    def __init__(self):
        """Initialize the chatbot with OpenAI and vector store."""
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4')
        self.vector_store = initialize_vector_store()
        
        self.system_prompt = """You are an expert AI health advisor specialized in cognitive health, 
vascular cognitive impairment (VCI), and brain-protective lifestyle interventions. You have access to 
evidence-based information from the ReCOGnAIze research study (Mohammed et al., 2025), SPRINT MIND trial, 
and validated lifestyle intervention frameworks.

Your role is to:
1. Answer questions about cognitive health, VCI, processing speed, executive function, and related topics
2. Provide evidence-based information about blood pressure management, cholesterol, diabetes control, 
   and their relationship to cognitive health
3. Recommend lifestyle interventions including physical activity, diet (DASH/Mediterranean), sleep 
   optimization, and cognitive engagement
4. Contextualize information within the framework of vascular risk factors and brain health
5. Be conversational, warm, and supportive while maintaining scientific accuracy
6. Direct users to healthcare providers for medical decisions or diagnoses

IMPORTANT CONSTRAINTS:
- You are NOT a substitute for medical advice - always encourage consultation with healthcare providers
- Stay within the cognitive health and vascular risk domain - decline off-topic questions politely
- Support your answers with relevant research or evidence when appropriate
- Be honest about uncertainty - if you don't know, say so
- Avoid making diagnostic claims - frame guidance as educational and risk-reduction focused"""
    
    def get_context(self, query: str, k: int = 5) -> str:
        """
        Search the knowledge base for relevant context
        
        Args:
            query: User question
            k: Number of documents to retrieve
            
        Returns:
            Formatted context string from knowledge base
        """
        try:
            # Use lower threshold to get more results
            results = self.vector_store.search(query, k=k, threshold=0.3)
            
            if not results:
                # Fallback: try again with even lower threshold
                results = self.vector_store.search(query, k=k, threshold=0.1)
            
            if not results:
                return ""
            
            context_parts = []
            for i, result in enumerate(results, 1):
                metadata = result.get('metadata', {})
                source = metadata.get('domain', 'unknown')
                context_parts.append(f"[{source}]: {result['content']}")
            
            return "\n\n".join(context_parts)
        
        except Exception as e:
            print(f"Error retrieving context: {e}")
            return ""
    
    def generate_response(self, query: str, conversation_history: List[Dict] = None) -> str:
        """
        Generate a response to the user query using the knowledge base
        
        Args:
            query: User question or prompt
            conversation_history: List of previous messages for context
            
        Returns:
            AI-generated response
        """
        try:
            # Get relevant context from knowledge base
            context = self.get_context(query, k=5)
            
            # Build messages for the API call
            messages = []
            
            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add current query with context
            if context:
                user_message = f"""Based on the following knowledge base information, please answer this question:

KNOWLEDGE BASE:
{context}

QUESTION: {query}

Please provide a helpful, evidence-based answer that addresses the question directly."""
            else:
                user_message = query
            
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt}
                ] + messages,
                temperature=0.7,
                max_tokens=1500
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            return f"I encountered an error while processing your question: {str(e)}. Please try again."
    
    def check_domain_relevance(self, query: str) -> bool:
        """
        Check if the query is relevant to the cognitive health domain
        
        Args:
            query: User question
            
        Returns:
            True if relevant to domain, False otherwise
        """
        try:
            # Search knowledge base for relevant documents with low threshold
            results = self.vector_store.search(query, k=1, threshold=0.1)
            
            # If we found anything or query contains domain keywords, consider it relevant
            domain_keywords = ['cognitive', 'brain', 'health', 'memory', 'blood pressure', 'exercise', 
                             'diet', 'sleep', 'vascular', 'dementia', 'assessment', 'recognaize',
                             'processing', 'attention', 'executive', 'cholesterol', 'diabetes',
                             'dash', 'mediterranean', 'intervention', 'lifestyle']
            
            query_lower = query.lower()
            has_keywords = any(keyword in query_lower for keyword in domain_keywords)
            
            return len(results) > 0 or has_keywords
        
        except Exception as e:
            print(f"Error checking domain relevance: {e}")
            # Default to True if there's an error - better to try than refuse
            return True


def initialize_chatbot() -> DomainChatbot:
    """Initialize and return the domain chatbot."""
    return DomainChatbot()

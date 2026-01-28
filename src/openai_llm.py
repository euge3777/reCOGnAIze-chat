"""
OpenAI GPT-5.2 integration for language model responses.
Provides natural language generation for the chatbot and recommendation system.
"""

import os
import logging
from typing import Optional, Dict, List
from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

load_dotenv()
logger = logging.getLogger(__name__)


class OpenAILLM:
    """OpenAI GPT-5.2 language model for generating natural responses."""
    
    def __init__(self, model: str = "gpt-5.2"):
        """
        Initialize OpenAI LLM client.
        
        Args:
            model: OpenAI model to use (default: gpt-5.2)
        """
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.is_initialized = True
        logger.info(f"OpenAI LLM initialized with model: {model}")
    
    def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: User prompt
            system_prompt: System instructions for the model
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated text response
        """
        try:
            messages: List[ChatCompletionMessageParam] = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})  # type: ignore
            
            messages.append({"role": "user", "content": prompt})  # type: ignore
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            result = response.choices[0].message.content
            return result if result else ""
        except Exception as e:
            logger.error(f"Error generating response from OpenAI: {e}")
            raise
    
    def generate_health_recommendation(
        self,
        user_profile: Dict,
        analysis_results: Dict,
        pillar: str = "general"
    ) -> str:
        """
        Generate health recommendations for a specific pillar.
        
        Args:
            user_profile: User profile data
            analysis_results: Analysis results from recommendation engine
            pillar: Health pillar (vascular_health, lifestyle, sleep, supplements)
            
        Returns:
            Generated recommendation text
        """
        
        pillar_descriptions = {
            "vascular_health": "vascular health and cardiovascular optimization",
            "lifestyle": "lifestyle modifications and daily habits",
            "sleep": "sleep quality and sleep optimization",
            "supplements": "supplements and nutritional support"
        }
        
        pillar_desc = pillar_descriptions.get(pillar, "health")
        
        system_prompt = f"""You are a health advisor specializing in {pillar_desc}.
Based on the user's profile and cognitive assessment results, provide evidence-based, personalized recommendations.
Keep recommendations actionable, specific, and grounded in research.
Be encouraging and practical, not alarmist."""
        
        profile_str = f"""User Profile:
- Age: {user_profile.get('age', 'Unknown')}
- Gender: {user_profile.get('gender', 'Unknown')}
- Cognitive Concerns: {', '.join(user_profile.get('cognitive_concerns', []))}
- Vascular Risk Factors: {', '.join(user_profile.get('vascular_risk_factors', []))}
- Current Medications: {', '.join(user_profile.get('medications', []))}"""
        
        analysis_str = f"""Assessment Results:
- Key Impairments: {', '.join([i.get('domain', '') for i in analysis_results.get('key_impairments', [])])}
- Risk Level: {analysis_results.get('risk_level', 'Unknown')}"""
        
        prompt = f"""{profile_str}

{analysis_str}

Based on this information, provide 3-5 specific, evidence-based recommendations for {pillar_desc}. 
For each recommendation, briefly explain why it matters for cognitive health."""
        
        return self.generate_response(
            prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=800
        )
    
    def generate_supplement_explanation(
        self,
        supplement_name: str,
        benefit: str,
        user_condition: str
    ) -> str:
        """
        Generate an explanation for why a supplement is recommended.
        
        Args:
            supplement_name: Name of the supplement (e.g., "Centrum Silver Women 50+")
            benefit: Health benefit (e.g., "memory support")
            user_condition: User's condition (e.g., "processing speed decline")
            
        Returns:
            Generated explanation
        """
        
        system_prompt = """You are a knowledgeable health science communicator.
Explain supplements and their mechanisms in clear, accessible language.
Reference scientific evidence when relevant but keep explanations digestible for general audiences."""
        
        prompt = f"""Why is {supplement_name} recommended for someone with {user_condition}?

Specifically, how does it support {benefit}?

Provide a 2-3 sentence explanation that:
1. Connects the supplement to the user's specific condition
2. Explains the mechanism of action
3. References any relevant clinical evidence if available"""
        
        return self.generate_response(
            prompt,
            system_prompt=system_prompt,
            temperature=0.6,
            max_tokens=400
        )
    
    def generate_cognitive_explanation(
        self,
        domain: str,
        score: float,
        threshold: float
    ) -> str:
        """
        Generate an explanation of cognitive test results.
        
        Args:
            domain: Cognitive domain (e.g., "processing_speed")
            score: User's score
            threshold: Normal threshold
            
        Returns:
            Generated explanation
        """
        
        severity = "mild" if (threshold - score) < 10 else "moderate" if (threshold - score) < 20 else "significant"
        
        system_prompt = """You are a neuropsychology communicator.
Explain cognitive test results in a supportive, non-alarming way.
Help users understand what scores mean and what they can do about it."""
        
        prompt = f"""Explain this cognitive test result in simple, supportive terms:

Domain: {domain.replace('_', ' ').title()}
User's Score: {score}/100
Normal Threshold: {threshold}/100
Severity: {severity}

Create a brief (2-3 sentences), supportive explanation that:
1. Acknowledges the finding without being alarming
2. Explains what this domain measures
3. Suggests this is often addressable through targeted interventions"""
        
        return self.generate_response(
            prompt,
            system_prompt=system_prompt,
            temperature=0.5,
            max_tokens=300
        )


def get_openai_instance(model: str = "gpt-5.2") -> Optional[OpenAILLM]:
    """
    Get or create OpenAI LLM instance.
    
    Args:
        model: OpenAI model to use
        
    Returns:
        OpenAILLM instance or None if initialization fails
    """
    try:
        return OpenAILLM(model=model)
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI LLM: {e}")
        return None


if __name__ == "__main__":
    # Test OpenAI LLM
    llm = OpenAILLM()
    
    # Test basic response
    response = llm.generate_response(
        "What are the key factors affecting cognitive health in aging?"
    )
    print("Response:")
    print(response)

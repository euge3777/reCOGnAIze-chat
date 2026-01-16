"""
Mistral integration for local language model inference.
Provides natural language generation for the chatbot responses.
"""

import os
import logging
from typing import Optional, Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)

class MistralLLM:
    """Local Mistral-7B language model for generating natural responses."""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize Mistral model.
        
        Args:
            model_path: Path to Mistral model directory
        """
        self.model_path = model_path or str(Path.home() / 'mistral_models' / '7B-Instruct-v0.3')
        self.model = None
        self.tokenizer = None
        self.is_initialized = False
        
        # Try to initialize the model
        self._try_initialize()
    
    def _try_initialize(self):
        """Try to initialize Mistral model if available."""
        try:
            if not os.path.exists(self.model_path):
                logger.warning(f"Mistral model not found at {self.model_path}")
                logger.info("Using fallback responses until Mistral model is downloaded")
                return False
            
            # Try importing mistral dependencies (optional)
            try:
                from mistral_inference.transformer import Transformer
                from mistral_common.tokens.tokenizers.mistral import MistralTokenizer
                from mistral_common.protocol.instruct.messages import UserMessage, SystemMessage
                from mistral_common.protocol.instruct.request import ChatCompletionRequest
                from mistral_inference.generate import generate
                
                # Initialize tokenizer and model
                tokenizer_path = os.path.join(self.model_path, "tokenizer.model.v3")
                if not os.path.exists(tokenizer_path):
                    logger.error(f"Tokenizer not found at {tokenizer_path}")
                    return False
                
                # TODO: Complete Mistral initialization here
                logger.info("Mistral dependencies available but initialization not yet complete")
                return False
                
            except ImportError:
                logger.warning("Mistral inference dependencies not installed, using fallback")
                return False
                return False
                
            self.tokenizer = MistralTokenizer.from_file(tokenizer_path)
            self.model = Transformer.from_folder(self.model_path)
            
            # Store classes for later use
            self.UserMessage = UserMessage
            self.SystemMessage = SystemMessage
            self.ChatCompletionRequest = ChatCompletionRequest
            self.generate = generate
            
            self.is_initialized = True
            logger.info("Mistral model initialized successfully")
            return True
            
        except ImportError as e:
            logger.warning(f"Mistral dependencies not installed: {e}")
            logger.info("Install with: pip install mistral-inference mistral-common")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Mistral model: {e}")
            return False
    
    def generate_response(self, 
                         user_message: str, 
                         system_prompt: str = None, 
                         context: str = None,
                         max_tokens: int = 256,
                         temperature: float = 0.3) -> str:
        """
        Generate a response using Mistral.
        
        Args:
            user_message: User's input message
            system_prompt: System prompt for context
            context: Additional context (e.g., retrieved information)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated response string
        """
        if not self.is_initialized:
            # Fallback to simple template-based response
            return self._fallback_response(user_message, context)
        
        try:
            # Prepare messages
            messages = []
            
            # System message
            if system_prompt:
                messages.append(self.SystemMessage(content=system_prompt))
            else:
                messages.append(self.SystemMessage(
                    content="You are a knowledgeable AI assistant specializing in cognitive health and multivitamin recommendations. Provide helpful, accurate, and personalized advice based on the user's needs and any provided context."
                ))
            
            # Add context if provided
            user_content = user_message
            if context:
                user_content = f"Context: {context}\n\nQuestion: {user_message}"
            
            messages.append(self.UserMessage(content=user_content))
            
            # Create completion request
            completion_request = self.ChatCompletionRequest(messages=messages)
            
            # Encode and generate
            tokens = self.tokenizer.encode_chat_completion(completion_request).tokens
            out_tokens, _ = self.generate(
                [tokens], 
                self.model, 
                max_tokens=max_tokens, 
                temperature=temperature, 
                eos_id=self.tokenizer.instruct_tokenizer.tokenizer.eos_id
            )
            
            # Decode response
            result = self.tokenizer.instruct_tokenizer.tokenizer.decode(out_tokens[0])
            
            # Clean up the response (remove system tokens, etc.)
            result = self._clean_response(result, user_message)
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating Mistral response: {e}")
            return self._fallback_response(user_message, context)
    
    def _clean_response(self, response: str, original_query: str) -> str:
        """Clean up the generated response."""
        # Remove common artifacts
        response = response.replace("[INST]", "").replace("[/INST]", "")
        response = response.replace("<s>", "").replace("</s>", "")
        
        # Remove the original question if it appears in the response
        if original_query in response:
            response = response.replace(original_query, "").strip()
        
        # Remove "Context:" prefix if it appears
        if response.startswith("Context:"):
            lines = response.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("Question:") or not line.startswith("Context:"):
                    response = "\n".join(lines[i:])
                    break
        
        return response.strip()
    
    def _fallback_response(self, user_message: str, context: str = None) -> str:
        """Generate a fallback response when Mistral is not available."""
        logger.debug("Using fallback response generation")
        
        # Simple keyword-based responses
        user_lower = user_message.lower()
        
        if context:
            return f"Based on the available information: {context[:200]}..."
        
        if any(word in user_lower for word in ['memory', 'forget', 'recall']):
            return "Memory concerns are common and can often be supported with proper nutrition. Omega-3 fatty acids, B-vitamins, and phosphatidylserine are commonly recommended for memory support. However, please consult with a healthcare provider for personalized advice."
        
        elif any(word in user_lower for word in ['attention', 'focus', 'concentrate']):
            return "Attention and focus issues can be addressed through various approaches. Magnesium, Rhodiola, and certain B-vitamins may help support cognitive focus. Consider lifestyle factors like sleep, stress management, and regular exercise as well."
        
        elif any(word in user_lower for word in ['omega', 'fish oil', 'dha', 'epa']):
            return "Omega-3 fatty acids (DHA and EPA) are essential for brain health. They support memory, reduce inflammation, and may help with cognitive function. Typical dosages range from 1000-2000mg daily, but consult your healthcare provider for personalized recommendations."
        
        elif any(word in user_lower for word in ['vitamin d', 'vitamin d3']):
            return "Vitamin D3 plays an important role in cognitive health and mood regulation. Deficiency has been linked to cognitive impairment. Typical supplementation ranges from 1000-4000 IU daily, but it's important to test your blood levels first."
        
        elif any(word in user_lower for word in ['magnesium']):
            return "Magnesium is essential for cognitive function, sleep quality, and stress management. It supports memory formation and can help with anxiety. Common forms include magnesium glycinate and citrate. Typical dosages range from 200-400mg daily."
        
        else:
            return "I'd be happy to help with your question about cognitive health and vitamins. Could you please provide more specific details about what you'd like to know? You can ask about specific vitamins, cognitive concerns, or your test results."
    
    def enhance_rag_response(self, rag_response: str, user_query: str, retrieved_context: str) -> str:
        """
        Use Mistral to enhance a RAG response with more natural language.
        
        Args:
            rag_response: Original RAG response
            user_query: User's original query
            retrieved_context: Context retrieved from vector store
            
        Returns:
            Enhanced response
        """
        if not self.is_initialized:
            return rag_response
        
        try:
            system_prompt = """You are enhancing a response about multivitamins and cognitive health. 
            Take the provided factual information and make it more conversational and personalized 
            while maintaining accuracy. Keep the medical disclaimer and safety information."""
            
            enhancement_query = f"""
            Please improve this response to be more natural and helpful:
            
            Original response: {rag_response}
            
            User's question: {user_query}
            
            Make it more conversational while keeping all the important facts and safety information.
            """
            
            enhanced = self.generate_response(
                enhancement_query, 
                system_prompt=system_prompt,
                max_tokens=400,
                temperature=0.2
            )
            
            return enhanced if len(enhanced) > 50 else rag_response
            
        except Exception as e:
            logger.error(f"Error enhancing response: {e}")
            return rag_response

# Global instance
mistral_llm = None

def get_mistral_instance() -> MistralLLM:
    """Get or create global Mistral instance."""
    global mistral_llm
    if mistral_llm is None:
        mistral_llm = MistralLLM()
    return mistral_llm

def download_mistral_model():
    """Download Mistral model if not present."""
    try:
        from huggingface_hub import snapshot_download
        from pathlib import Path
        
        mistral_models_path = Path.home().joinpath('mistral_models', '7B-Instruct-v0.3')
        mistral_models_path.mkdir(parents=True, exist_ok=True)
        
        print("Downloading Mistral-7B-Instruct-v0.3 model...")
        print("This may take a while (several GB download)...")
        
        snapshot_download(
            repo_id="mistralai/Mistral-7B-Instruct-v0.3", 
            allow_patterns=["params.json", "consolidated.safetensors", "tokenizer.model.v3"], 
            local_dir=mistral_models_path
        )
        
        print(f"Model downloaded to {mistral_models_path}")
        return True
        
    except Exception as e:
        print(f"Failed to download model: {e}")
        return False

if __name__ == "__main__":
    # Test Mistral integration
    mistral = MistralLLM()
    
    if mistral.is_initialized:
        print("✅ Mistral model loaded successfully")
        
        # Test response generation
        response = mistral.generate_response("What vitamins help with memory?")
        print(f"Test response: {response}")
        
    else:
        print("❌ Mistral model not available")
        print("Would you like to download it? (y/n)")
        
        if input().lower() == 'y':
            download_mistral_model()